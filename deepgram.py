import asyncio
import json
import websockets


class Deepgram:
    def __init__(self, api_key, websocket_url, on_message = None):
        self.api_key = api_key
        self.websocket_url = websocket_url
        self.on_message = on_message

    async def start(self, audio_stream):
        """
        Connects to Deepgram and manages the send/receive loops.
        """
        headers = {"Authorization": f"Token {self.api_key}"}
        
        # 'additional_headers' is for websockets v14+
        async with websockets.connect(self.websocket_url, additional_headers=headers) as websocket:
            print("[Transcriber] Connected to Deepgram.")
            
            # Run tasks in parallel
            await asyncio.gather(
                self._sender(websocket, audio_stream),
                self._receiver(websocket),
                self._keepalive(websocket)
            )

    async def _sender(self, websocket, stream):
        """Reads from stream, sends to websocket."""
        while True:
            data = await stream.read_chunk()
            if not data:
                break
            await websocket.send(data)
        
        await websocket.send(json.dumps({"type": "Finalize"}))

    async def _receiver(self, websocket):
        """Reads transcripts from websocket."""
        async for msg in websocket:
            data = json.loads(msg)
            if self.on_message:
                self.on_message(data)

    async def _keepalive(self, websocket):
        """Keeps connection open during silence."""
        while True:
            await asyncio.sleep(5)
            await websocket.send(json.dumps({"type": "KeepAlive"}))