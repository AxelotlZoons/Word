import asyncio
import shutil

class Ffmpeg:

    def __init__(self, url):
        self.url = url
        self.process = None


    async def __aenter__(self):
        """Starts FFmpeg when entering the 'with' block."""
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg not found in PATH")

        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-i", self.url,
            "-f", "s16le",
            "-ac", "1",
            "-ar", "16000",
            "-"
        ]
        
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        return self


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Kills FFmpeg when exiting the 'with' block."""
        if self.process and self.process.returncode is None:
            try:
                self.process.kill()
            except ProcessLookupError:
                pass
            print("[Audio] FFmpeg process stopped.")


    async def read_chunk(self, size=4096):
        """Reads a chunk of raw audio."""
        if self.process and self.process.stdout:
            data = await self.process.stdout.read(size)
            return data
