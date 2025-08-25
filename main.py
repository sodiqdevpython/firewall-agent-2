# main.py
from steps.step1 import Step1
from steps.step2 import Step2
import time
import threading
import asyncio
import json
import websockets
from components.GetDeviceInfo import Device
# from components.TrafficMonitor import TrafficMonitor
from components.Firewall import FirewallManager

async def firewall_listener(device_bios: str):
    ws_url = f"ws://localhost:8000/ws/device/fire_wall/{device_bios}/"
    print(f"[Firewall WS] Ulanmoqda: {ws_url}")
    fw = FirewallManager()

    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"[Firewall WS] ✅ Ulandi: {ws_url}")
            async for message in websocket:
                print(f"[Firewall WS] Raw message: {message}")
                try:
                    data = json.loads(message)
                except Exception as e:
                    print(f"[Firewall WS] JSON parse xato: {e}")
                    continue

                if data.get("type") != "firewall_rule":
                    continue

                event = data.get("event")
                payload = data.get("data", {})

                title = payload.get("title", f"WS_{payload.get('id')}")
                action = payload.get("action")
                direction = payload.get("direction")
                protocol = payload.get("protocol")
                port = payload.get("port")

                app_info = payload.get("application") or {}
                image_path = app_info.get("image_path") if isinstance(app_info, dict) else None

                if event == "created":
                    direction = (direction.capitalize() 
                    if direction else "Inbound")
                    protocol = protocol.upper() if protocol else "TCP"

                    localport = None
                    remoteport = None
                    if str(port).lower() != "any":
                        if direction == "Inbound":
                            localport = str(port)
                        else:
                            remoteport = str(port)

                    res = fw.add_rule(
                        name=title,
                        action=action.capitalize(),
                        direction=direction,
                        protocol=protocol,
                        localport=localport or "Any",
                        remoteport=remoteport or "Any",
                        description=f"WS dan keldi, rule_id={payload.get('id')}",
                        program=image_path if image_path else None
                    )
                    print(f"[Firewall WS] Qoida qo‘shildi: {res}")

                elif event == "deleted":
                    res = fw.delete_rule(title)
                    print(f"[Firewall WS] Qoida o‘chirildi: {res}")

    except Exception as e:
        print(f"[Firewall WS] ❌ Xato: {e}, qayta ulanmoqda...")
        await asyncio.sleep(3)



# def run_traffic_monitor(device_bios):
#     """TrafficMonitor asyncio loopini alohida threadda ishlatadi"""
#     monitor = TrafficMonitor(
#         app_url="http://10.10.111.12:8000/applications/applications/",
#         connect_url="http://10.10.111.12:8000/applications/connections/",
#         interval=2,
#         device_bios=device_bios
#     )
#     asyncio.run(monitor.run())


def run():
    device = Device()
    device_bios = device.get_windows_bios_uuid().lower()
    print(f"Device BIOS UUID: {device_bios}")

    try:
        step1 = Step1()
        step1.get_device_from_server()
        print("[Main] Step1 tugadi")

        ws_url = f"ws://localhost:8000/ws/device/{device_bios}/"
        step2 = Step2(ws_url, device_bios)
        step2.run_in_thread()

        # TrafficMonitor alohida threadda
        # threading.Thread(target=run_traffic_monitor, args=(device_bios,), daemon=True).start()

        # Asosiy thread firewall rules ws listener bo‘ladi
        asyncio.run(firewall_listener(device_bios))

    except Exception as e:
        print(f"[Main] Step1 muvaffaqiyatsiz: {e}, Step2 ishga tushmadi.")


if __name__ == "__main__":
    run()
