import asyncio
import json
import websockets
import sys

class Deepgram:
    def __init__(self, api_key, ws_url, on_message = None):
        self.api_key = api_key
        self.ws_url = ws_url
        self.on_message = on_message

    async def start(self, audio_stream):
        """
        Connects to Deepgram and manages the send/receive loops.
        """
        headers = {"Authorization": f"Token {self.api_key}"}
        
        # 'additional_headers' is for websockets v14+
        async with websockets.connect(self.ws_url, additional_headers=headers) as ws:
            print("[Transcriber] Connected to Deepgram.")
            
            # Run tasks in parallel
            await asyncio.gather(
                self._sender(ws, audio_stream),
                self._receiver(ws),
                self._keepalive(ws)
            )

    async def _sender(self, ws, stream):
        """Reads from stream, sends to WS."""
        while True:
            data = await stream.read_chunk()
            if not data:
                break
            await ws.send(data)
        
        await ws.send(json.dumps({"type": "Finalize"}))

    async def _receiver(self, ws):
        """Reads transcripts from WS."""
        async for msg in ws:
            data = json.loads(msg)
            if self.on_message:
                self.on_message(data)

    async def _keepalive(self, ws):
        """Keeps connection open during silence."""
        while True:
            await asyncio.sleep(5)
            await ws.send(json.dumps({"type": "KeepAlive"}))