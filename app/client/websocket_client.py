import asyncio
import websockets
import threading
import concurrent.futures

class WebSocketClient:
    def __init__(self, uri, message_handler):
        self.uri = uri
        self.connection = None
        self.message_handler = message_handler
        self.loop = asyncio.new_event_loop()
        self.reconnect_delay = 5
        self.running = False
        self.thread = None
        self.ping_interval = 20
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    async def connect(self):
        while self.running:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.connection = websocket
                    print(f"Connected to WebSocket server: {(self.uri[:47] + '...') if len(self.uri) > 50 else self.uri}")
                    ping_task = asyncio.ensure_future(self.send_pings(websocket))
                    await self.message_handler_with_offloading(websocket)
                    ping_task.cancel()

            except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as e:
                print(f"Connection closed normally: {e}")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)

            except Exception as e:
                print(f"Connection error: {e}")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)

    async def send_pings(self, websocket):
        """Send pings to keep the WebSocket connection alive."""
        try:
            while self.running:
                if websocket.open:
                    await websocket.ping()
                    await asyncio.sleep(self.ping_interval)
                else:
                    print("WebSocket connection closed, stopping pings.")
                    break
        except asyncio.CancelledError:
            print("Ping task cancelled.")
        except websockets.ConnectionClosedError as e:
            print(f"Ping task detected connection closure: {e}")
        except Exception as e:
            print(f"Error sending ping: {e}")

    async def message_handler_with_offloading(self, websocket):
        """Handles WebSocket messages and offloads post-processing to a separate thread."""
        try:
            async for message in websocket:
                loop = asyncio.get_event_loop()
                loop.run_in_executor(self.executor, self.post_process, message)

        except websockets.ConnectionClosedError as e:
            print(f"WebSocket connection closed: {e}")
        except Exception as e:
            print(f"Error handling messages: {e}")

    def post_process(self, message):
        self.message_handler(message)

    def __run_forever(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())

    def restart(self):
        if self.running:
            self.stop()
        if self.thread is not None:
            self.thread.join()
        self.loop = asyncio.new_event_loop()
        self.running = True
        self.thread = threading.Thread(target=self.__run_forever, daemon=True)
        self.thread.start()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.__run_forever, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
