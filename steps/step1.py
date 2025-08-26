"""
Bu fayllarda qadamlar bo'ladi 1-qadam ayni shu device ni serverdan get qilish va agar mavjud bo'lsa bu device unga socket orqali ulanaman keyin ma'lumotlarini yangilayman
agar mavjud bo'lmasa create qiladi undan keyin socket ga ulanadi va o'z ma'lumotlarini yangilab ulanib turadi
"""
import requests, sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from components.GetDeviceInfo import Device

class Step1:
    def __init__(self):
        self.base_url = "http://94.141.85.114:4555/hosts/devices/"
        self.device = Device()

    def get_device_from_server(self):
        bios_uuid = self.device.get_windows_bios_uuid()
        response = requests.get(f"{self.base_url}?bios_uuid={bios_uuid}")

        if response.status_code != 200:
            print(f"[Xato] GET request muvaffaqiyatsiz: {response.status_code} {response.text}")
            return

        try:
            data = response.json()
        except Exception as e:
            print("[Xato] JSON parse bo‘lmadi:", e, response.text)
            return

        results = data.get("results", [])
        count = data.get("count", 0)

        if results and count == 1:
            device_id = results[0]["id"]
            print("[Step1] Bor:", device_id)

            patch_ip = requests.patch(
                f"{self.base_url}{device_id}/",
                data={"ip_address": str(self.device.find_my_global_ip())}
            )
            print("[Step1] Patch javobi:", patch_ip.status_code, patch_ip.text)

        else:
            print("[Step1] Yo‘q, create qilinayapti...")
            send_new_device = requests.post(
                self.base_url,
                data=self.device.get_device()
            )
            print("[Step1] Post javobi:", send_new_device.status_code, send_new_device.text)