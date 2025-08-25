import threading
import asyncio
import websockets

class Step2:
    def __init__(self, ws_url: str, device_bios):
        self.ws_url = ws_url
        self.thread = None
        self.device_bios = device_bios

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    print(f"[+] Connected to {self.ws_url}")
                    async for message in websocket:
                        print(f"[WS] Message: {message}")
            except Exception as e:
                print(f"[!] WebSocket error: {e}, reconnecting...")
                await asyncio.sleep(5)

    def run_in_thread(self):
        def runner():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect())
        
        self.thread = threading.Thread(target=runner, daemon=True)
        self.thread.start()
        print("[*] Step2 WebSocket thread started")
