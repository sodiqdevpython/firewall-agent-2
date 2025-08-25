import socket, platform, wmi, requests

class Device:
    def __init__(self):
        pass
    
    def find_my_global_ip(self):
        try:
            ip = requests.get("https://api.ipify.org?format=json").json()["ip"]
            return str(ip)
        except Exception as e:
            print(f"Global IP topishda xato: {e}")
            return None
    
    def get_windows_bios_uuid(self):
        try:
            c = wmi.WMI()
            for product in c.Win32_ComputerSystemProduct():
                return str(product.UUID)
        except Exception as e:
            print(f"BIOS UUID ni olib bo'lmadi: {e}\n(Python dan components/get_bios.py dan bo'ldi)")
            return None
    
    def get_device_name(self):
        self.host_name = socket.gethostname()
        return self.host_name

    def get_device_ip_daress(self):
        self.device_ip_daress = socket.gethostbyname(self.host_name)
        return self.device_ip_daress

    def get_device_os_version(self):
        self.device_os_version = platform.version()
        return self.device_os_version
    
    def get_device(self):
        data = {
            'bios_uuid': self.get_windows_bios_uuid(),
            'host_name': self.get_device_name(),
            'ip_address': self.get_device_ip_daress(),
            'os_version': self.get_device_os_version(),
            'status': 'Online'
        }
        return data