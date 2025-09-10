# websocket_client.py

import asyncio
import websockets
import threading

class WebSocketClient:
    def __init__(self, uri, message_handler):
        self.uri = uri
        self.connection = None
        self.loop = asyncio.new_event_loop()
        self.reconnect_delay = 5
        self.running = True
        self.message_handler = message_handler

    async def connect(self):
        while self.running:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.connection = websocket
                    print("Connected to WebSocket server")
                    await self.message_handler(websocket)
            except (websockets.ConnectionClosedError, websockets.InvalidURI, Exception) as e:
                print(f"Connection error: {e}")
                await asyncio.sleep(self.reconnect_delay)

    def start(self):
        threading.Thread(target=self.run_forever, daemon=True).start()

    def run_forever(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())

    def stop(self):
        self.running = False
        self.loop.call_soon_threadsafe(self.loop.stop)
