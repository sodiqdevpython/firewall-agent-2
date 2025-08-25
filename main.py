from steps.step1 import Step1
from steps.step2 import Step2
import time
from components.GetDeviceInfo import Device

def run():
    device = Device()
    device_bios = device.get_windows_bios_uuid().lower()
    print(f"ws://localhost:8000/ws/device/{device_bios}/")
    try:
        step1 = Step1()
        step1.get_device_from_server()
        print("[Main] Step1 tugadi")
        
        ws_url = f"ws://localhost:8000/ws/device/{device_bios}/"
        step2 = Step2(ws_url)
        step2.run_in_thread()

        # Main thread ishlashda davom etadi
        while True:
            print("[Main] Asosiy thread ishlayapti...")
            time.sleep(5)

    except Exception as e:
        print(f"[Main] Step1 muvaffaqiyatsiz: {e}, Step2 ishga tushmadi.")

if __name__ == "__main__":
    run()
