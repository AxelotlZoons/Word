import asyncio
import json
import os
import shutil
import sys
import websockets
from dotenv import load_dotenv

# Load API Key
load_dotenv()
DG_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

# BBC World Service (High quality stream)
# We use a direct MP3 stream URL.
STREAM_URL = "https://npr-ice.streamguys1.com/live.mp3"

# Deepgram WebSocket URL
# model=nova-2: Optimized for speed/cost.
# smart_format=true: Adds punctuation/capitalization.
# interim_results=true: CRITICAL for low latency (shows text while speaking).
# encoding=linear16&sample_rate=16000: explicitly tells DG what we are sending.
DG_WSS = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-2"
    "&language=en"
    "&smart_format=true"
    "&interim_results=true"
    "&encoding=linear16"
    "&sample_rate=16000"
)

async def get_ffmpeg_process():
    """
    Creates an async subprocess that pipes the BBC stream to stdout as raw PCM.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found. Please install it and add to PATH.")

    # flags low_delay + fflags nobuffer are crucial for real-time latency
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",      # Only show errors
        "-fflags", "nobuffer",     # Reduce input buffer latency
        "-flags", "low_delay",     # Low delay flag
        "-i", STREAM_URL,
        "-f", "s16le",             # Output format: Signed 16-bit Little Endian
        "-ac", "1",                # Channels: 1 (Mono)
        "-ar", "16000",            # Sample Rate: 16kHz
        "-"                        # Output to stdout
    ]
    
    # Create the subprocess
    return await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

async def sender(ws, proc):
    """
    Reads raw audio from FFmpeg and sends it to Deepgram.
    """
    print(f"[Sender] Streaming from {STREAM_URL}...")
    chunk_size = 4096 # Small chunks for lower latency
    
    try:
        while True:
            data = await proc.stdout.read(chunk_size)
            if not data:
                # If no data, check if ffmpeg crashed
                if proc.returncode is not None:
                    print("[Sender] FFmpeg process exited unexpectedly.")
                    stderr_out = await proc.stderr.read()
                    print(f"[FFmpeg Error] {stderr_out.decode()}")
                break
            
            await ws.send(data)
            
    except websockets.exceptions.ConnectionClosedOK:
        print("[Sender] Connection closed gracefully.")
    except Exception as e:
        print(f"[Sender] Error: {e}")
    finally:
        # Send finalizing message to tell Deepgram we are done
        try:
            await ws.send(json.dumps({"type": "Finalize"}))
        except:
            pass

async def receiver(ws):
    """
    Prints transcription results.
    """
    print("[Receiver] Listening for transcripts...")
    try:
        async for msg in ws:
            res = json.loads(msg)
            
            # Handle standard transcription results
            if "channel" in res:
                alternatives = res["channel"]["alternatives"]
                if alternatives:
                    transcript = alternatives[0]["transcript"]
                    if transcript.strip():
                        # Clear line to prevent scrolling mess with interim results
                        # \r returns cursor to start of line
                        is_final = res.get("is_final")
                        prefix = "[Final]" if is_final else "[Interim]"
                        sys.stdout.write(f"\r{prefix} {transcript}")
                        sys.stdout.flush()
                        if is_final:
                            print("") # New line for final results
            
            # Handle metadata/errors
            if "error" in res:
                print(f"\n[Server Error] {res['error']}")
                
    except websockets.exceptions.ConnectionClosed:
        print("\n[Receiver] Stream ended.")

async def keepalive(ws):
    """
    Prevents Deepgram from closing the connection due to inactivity 
    (though continuous audio usually prevents this).
    """
    try:
        while True:
            await asyncio.sleep(5)
            await ws.send(json.dumps({"type": "KeepAlive"}))
    except:
        pass

async def main():
    if not DG_API_KEY:
        print("Error: DEEPGRAM_API_KEY is not set.")
        return

    # Start FFmpeg first to ensure the stream is alive
    proc = await get_ffmpeg_process()
    
    # Connect to Deepgram
    # Note: 'additional_headers' is for websockets v14+, 'extra_headers' for older
    extra_headers = {"Authorization": f"Token {DG_API_KEY}"}
    
    print("Connecting to Deepgram...")
    try:
        async with websockets.connect(DG_WSS, additional_headers=extra_headers) as ws:
            print("Connected!")
            
            # Create tasks
            send_task = asyncio.create_task(sender(ws, proc))
            recv_task = asyncio.create_task(receiver(ws))
            alive_task = asyncio.create_task(keepalive(ws))
            
            # Wait for sender or receiver to stop
            done, pending = await asyncio.wait(
                [send_task, recv_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                
    except websockets.exceptions.InvalidStatus as e:
        print(f"\nConnection Rejected: {e}")
        print("Check your API Key and Network.")
    finally:
        if proc.returncode is None:
            proc.kill()
            print("FFmpeg killed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)