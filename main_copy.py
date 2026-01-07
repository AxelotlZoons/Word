import asyncio
import json
import os
import shutil
import sys
import websockets
import yt_dlp
from dotenv import load_dotenv

# Load API Key
load_dotenv()
DG_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

DG_WSS = (
    "wss://api.deepgram.com/v1/listen"
    "?model=nova-2&language=en&smart_format=true"
    "&interim_results=true&encoding=linear16&sample_rate=16000"
)

def get_real_stream_url(url):
    """
    Uses yt-dlp to extract the direct stream URL from a webpage link.
    Works for YouTube, Twitch, Soundcloud, CNN, BBC, etc.
    """
    print(f"[Resolver] analyzing {url} ...")
    ydl_opts = {
        'format': 'bestaudio/best',  # Try to get audio-only if available (faster)
        'quiet': True,
        'noplaylist': True,
        'live_from_start': False,    # Start at 'now', don't download history
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Some live streams are HLS manifests (.m3u8)
            real_url = info.get('url')
            print(f"[Resolver] Success! Stream found.")
            return real_url
    except Exception as e:
        print(f"[Resolver] Warning: yt-dlp failed ({e}). Trying original URL directly.")
        return url

async def get_ffmpeg_process(stream_url):
    """
    Spawns FFmpeg to pull audio from the remote stream URL.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found.")

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        
        # Latency Optimizations for HLS/Video Streams
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-live_start_index", "-1", # Jump to most recent segment (crucial for HLS)
        
        "-i", stream_url,
        "-f", "s16le",             # Raw PCM audio
        "-ac", "1",                # Mono
        "-ar", "16000",            # 16kHz
        "-"                        # Stdout
    ]

    return await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

async def sender(ws, proc):
    """
    Reads audio from FFmpeg and pushes to Deepgram.
    """
    print("[Sender] Streaming audio...")
    try:
        while True:
            data = await proc.stdout.read(4096)
            if not data:
                break
            await ws.send(data)
    except Exception:
        pass
    finally:
        # If we exit, try to close cleanly
        if proc.returncode is None:
            proc.kill()

async def receiver(ws):
    """
    Prints the transcript.
    """
    print("[Receiver] Ready.")
    async for msg in ws:
        res = json.loads(msg)
        if "channel" in res:
            alts = res["channel"].get("alternatives", [])
            if alts and alts[0]["transcript"]:
                txt = alts[0]["transcript"]
                is_final = res.get("is_final")
                
                # Overwrite line for interim, Newline for final
                prefix = "[Final]" if is_final else "[Interim]"
                sys.stdout.write(f"\r{prefix} {txt}")
                sys.stdout.flush()
                
                if is_final:
                    print("")

async def keepalive(ws):
    while True:
        await asyncio.sleep(5)
        await ws.send(json.dumps({"type": "KeepAlive"}))

async def main():
    if not DG_API_KEY:
        print("Please set DEEPGRAM_API_KEY in your .env file")
        return

    # 1. Get User Input
    user_url = "https://www.youtube.com/watch?v=pqzh65k7ekw"

    # 2. Resolve the "Real" Stream URL
    stream_url = get_real_stream_url(user_url)

    # 3. Start FFmpeg
    print(f"[FFmpeg] Starting stream...")
    proc = await get_ffmpeg_process(stream_url)

    # 4. Connect to Deepgram
    headers = {"Authorization": f"Token {DG_API_KEY}"}
    async with websockets.connect(DG_WSS, additional_headers=headers) as ws:
        # Run tasks
        await asyncio.gather(
            sender(ws, proc),
            receiver(ws),
            keepalive(ws)
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass