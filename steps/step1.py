"""
Bu fayllarda qadamlar bo'ladi 1-qadam ayni shu device ni serverdan get qilish va agar mavjud bo'lsa bu device unga socket orqali ulanaman keyin ma'lumotlarini yangilayman
agar mavjud bo'lmasa create qiladi undan keyin socket ga ulanadi va o'z ma'lumotlarini yangilab ulanib turadi
"""
import requests, sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from components.GetDeviceInfo import Device

class Step1:
    
    def __init__(self):
        pass
        
    def get_device_from_server(self):
        device = Device()
        response = requests.get(f'http://localhost:8000/hosts/devices/?bios_uuid={device.get_windows_bios_uuid()}')
        data = response.json()
        device_id = data['results'][0]['id']
        if data['results'] and data['count']==1:
            print("Bor")
            patch_ip = requests.patch(f"http://localhost:8000/hosts/devices/{device_id}/", data={
                'ip_address': str(device.find_my_global_ip())
            })
            print(patch_ip)
        else:
            print("Yo'q create qilinayabdi")
            send_new_device = requests.post('http://localhost:8000/hosts/devices/', data=device.get_device())
            print(send_new_device.status_code)