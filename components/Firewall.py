import subprocess
import json

class FirewallManager:
    def __init__(self):
        pass

    def run_command(self, args: list, shell: bool = False):
        try:
            result = subprocess.check_output(args, text=True, stderr=subprocess.STDOUT, shell=shell)
            return result.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.output}"

    def list_rules(self, name: str = "*"):
        raw_output = self.run_command([
            "powershell", "-Command", f"Get-NetFirewallRule -DisplayName '{name}' | Format-List *"
        ])
        
        if raw_output.startswith("Error:"):
            return raw_output
        
        return self._parse_rules_to_json(raw_output)

    def _parse_rules_to_json(self, raw_output: str):
        rules = []
        current_rule = {}
        
        lines = raw_output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if current_rule:
                    rules.append(current_rule.copy())
                    current_rule = {}
                continue
            
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip() if value.strip() else "None"
                current_rule[key] = value
        
        if current_rule:
            rules.append(current_rule)
        
        return json.dumps(rules, indent=2, ensure_ascii=False)

    def add_rule(self, name: str, action: str, direction: str,
             protocol: str = "TCP", localport: str = "Any",
             remoteport: str = "Any", description: str = "",
             profile: str = "Any", enabled: bool = True,
             program: str = None):
    
        enabled_str = "True" if enabled else "False"

        ps_command = f'New-NetFirewallRule -DisplayName "{name}" -Direction {direction} -Action {action}'

        if protocol and protocol != "Any":
            ps_command += f' -Protocol {protocol}'

        if localport and localport != "Any":
            ps_command += f' -LocalPort {localport}'

        if remoteport and remoteport != "Any":
            ps_command += f' -RemotePort {remoteport}'

        if program:  # faqat bo‘lsa qo‘shamiz
            ps_command += f' -Program "{program}"'

        if description:
            ps_command += f' -Description "{description}"'

        ps_command += f' -Enabled {enabled_str} -Profile {profile} -PolicyStore PersistentStore'

        return self.run_command(["powershell", "-Command", ps_command])

    
    def delete_rule(self, name: str):
        return self.run_command([
            "powershell", "-Command", f"Remove-NetFirewallRule -DisplayName '{name}'"
        ])