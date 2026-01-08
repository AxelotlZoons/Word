import asyncio
import sys
from config import Config
from ffmpeg import Ffmpeg
from deepgram import Deepgram
from spotter import Spotter

async def main():

    spotter = Spotter(Config.KEYWORDS)
    
    def on_message(data):
        # Print transcripts (partial + final)
        if "channel" in data and data["channel"]["alternatives"]:
            transcript = data["channel"]["alternatives"][0].get("transcript", "")
            if transcript:
                prefix = "Final" if data.get("is_final") else "Interim"
                print(f"[{prefix}] {transcript}")

    print(f"\nStarting stream from: {Config.STREAM_URL}")
    
    # 1. Start Audio Stream
    async with Ffmpeg(Config.STREAM_URL) as stream:
        
        # 2. Start AI Engine
        transcriber = Deepgram(
            api_key=Config.DEEPGRAM_API_KEY,
            ws_url=Config.DEEPGRAM_URL,
            on_message=on_message
        )
        
        # 3. Go
        await transcriber.start(stream)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)