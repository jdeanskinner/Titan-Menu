r"""
SuperPutty Configuration Generator for NRE Jumpbox

Generates SuperPutty session profiles for easy GUI access to:
  1. NRE Oser jumpbox (TACACS+ authentication)
  2. Network devices through jumpbox
  3. Multiple jumpbox/device combinations

SuperPutty profiles are stored in:
  Windows: %APPDATA%\SuperPutty\Sessions

Usage:
    gen = SuperPuttyConfigGenerator()
    profile = gen.create_jumpbox_profile()
    gen.save_profile(profile)
    
    device_profile = gen.create_device_profile(
        device_name="core-switch-01",
        device_ip="10.20.30.40",
        device_username="neteng"
    )
    gen.save_profile(device_profile)

"""
import os
import json
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime


class SuperPuttyProfile:
    """
    Represents a SuperPutty session profile.
    
    SuperPutty is a PuTTY wrapper with tabbed interface.
    Each profile corresponds to a .xml session file.
    """
    
    def __init__(
        self,
        session_name: str,
        host: str,
        port: int = 22,
        username: str = "",
        password: str = "",
        session_type: str = "ssh",
        description: str = ""
    ):
        """
        Initialize SuperPutty profile.
        
        Args:
            session_name: Name of the session (e.g., "NRE Oser Jumpbox")
            host: Hostname or IP address
            port: SSH port (default 22)
            username: SSH username
            password: SSH password (can be empty for prompt)
            session_type: Protocol (ssh, telnet, raw, rlogin)
            description: Human-readable description
        """
        self.session_name = session_name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.session_type = session_type
        self.description = description
        self.created = datetime.now().isoformat()
    
    def to_putty_format(self) -> Dict:
        """
        Convert to PuTTY registry format (used by SuperPutty).
        
        Returns:
            Dictionary with PuTTY settings
        """
        settings = {
            "HostName": self.host,
            "Port": str(self.port),
            "Protocol": self.session_type,
            "UserName": self.username,
            "StrictHostKeyChecking": "0",
            "ServerAliveInterval": "60",
            "X11Forward": "0",
            "X11Display": "",
            "ForwardAgent": "0",
            "ProxyCommand": "",
            "ProxyUsername": "",
            "ProxyPassword": "",
            "ProxyTelnetCommand": "",
            "ProxyLocalhost": "0",
            "BuggyMAC": "0",
            "RekeyTime": "3600",
            "RekeyBytes": "",
        }
        

        
        return settings
    
    def to_xml(self) -> str:
        """
        Export profile as XML (SuperPutty format).
        
        Returns:
            XML string representing the profile
        """
        settings = self.to_putty_format()
        
        xml = '<?xml version="1.0" encoding="utf-8"?>\n'
        xml += '<Session>\n'
        xml += f'  <SessionName>{self._escape_xml(self.session_name)}</SessionName>\n'
        xml += f'  <Description>{self._escape_xml(self.description)}</Description>\n'
        xml += f'  <CreatedDate>{self.created}</CreatedDate>\n'
        xml += '  <Settings>\n'
        
        for key, value in settings.items():
            xml += f'    <{key}>{self._escape_xml(str(value))}</{key}>\n'
        
        xml += '  </Settings>\n'
        xml += '</Session>\n'
        
        return xml
    
    @staticmethod
    def _escape_xml(text: str) -> str:
        """
        Escape XML special characters.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text


class SuperPuttyConfigGenerator:
    """
    Generates SuperPutty configuration files for NRE jumpbox access.
    
    Creates profiles for:
    1. Direct jumpbox connection
    2. Device connections through jumpbox
    3. Batch device connections
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize SuperPutty generator.
        
        Args:
            base_path: Base directory for saving profiles (auto-detected if None)
        """
        self.base_path = base_path or self._get_superputty_path()
        self.profiles: List[SuperPuttyProfile] = []
    
    @staticmethod
    def _get_superputty_path() -> str:
        """
        Get default SuperPutty configuration directory.
        
        Returns:
            Path to SuperPutty sessions directory
        """
        if os.name == 'nt':
            appdata = os.getenv('APPDATA')
            if appdata:
                return os.path.join(appdata, 'SuperPutty', 'Sessions')
        

        return os.path.expanduser('~/.superputty/sessions')
    
    def create_jumpbox_profile(
        self,
        session_name: str = "NRE Oser Jumpbox (TACACS+)",
        primary_host: str = "Oser500521.homeoffice.wal-mart.com",
        fallback_host: Optional[str] = "Oser500522.homeoffice.wal-mart.com",
        port: int = 22,
        username: str = ""
    ) -> SuperPuttyProfile:
        """
        Create SuperPutty profile for NRE Oser jumpbox.
        
        Args:
            session_name: Display name in SuperPutty
            primary_host: Primary Oser host
            fallback_host: Fallback Oser host (optional)
            port: SSH port
            username: Default username (can be empty for prompt)
            
        Returns:
            SuperPuttyProfile instance
        """
        description = (
            f"NRE Enterprise Jumpbox - TACACS+ Authentication\n"
            f"Primary: {primary_host}\n"
            f"Fallback: {fallback_host or 'N/A'}\n"
            f"\n"
            f"PASSCODE Format: PCI_TOKEN(8 digits) + RSA_PIN(6 digits)\n"
            f"Example: 12345678901234\n"
            f"\n"
            f"Required AD Groups:\n"
            f"  - NetEng_servers_Role-Login\n"
            f"  - NetEng_servers_Role-Listed"
        )
        
        profile = SuperPuttyProfile(
            session_name=session_name,
            host=primary_host,
            port=port,
            username=username,
            session_type="ssh",
            description=description
        )
        
        self.profiles.append(profile)
        return profile
    
    def create_device_profile(
        self,
        device_name: str,
        device_ip: str,
        device_username: str = "",
        device_port: int = 22,
        jumpbox_host: str = "Oser500521.homeoffice.wal-mart.com"
    ) -> SuperPuttyProfile:
        """
        Create SuperPutty profile for device access through jumpbox.
        
        Note: User will need to establish jumpbox connection first,
        then SSH from jumpbox to device. This profile documents the final hop.
        
        Args:
            device_name: Device name/hostname
            device_ip: Device management IP
            device_username: SSH username on device
            device_port: SSH port on device
            jumpbox_host: Jumpbox to tunnel through
            
        Returns:
            SuperPuttyProfile instance
        """
        session_name = f"{device_name} ({device_ip})"
        
        description = (
            f"Network Device via NRE Jumpbox\n"
            f"Device: {device_name}\n"
            f"IP Address: {device_ip}\n"
            f"SSH Port: {device_port}\n"
            f"Username: {device_username or 'neteng (or device-specific)'}\n"
            f"\n"
            f"Connection Steps:\n"
            f"1. Connect to jumpbox first: {jumpbox_host}\n"
            f"2. From jumpbox: ssh {device_username}@{device_ip}\n"
            f"3. Once in, run show commands as needed\n"
            f"\n"
            f"Or use ssh-T tunnel:\n"
            f"  ssh -t {jumpbox_host} ssh -t {device_username}@{device_ip}"
        )
        
        profile = SuperPuttyProfile(
            session_name=session_name,
            host=device_ip,
            port=device_port,
            username=device_username,
            session_type="ssh",
            description=description
        )
        
        self.profiles.append(profile)
        return profile
    
    def save_profile(
        self,
        profile: SuperPuttyProfile,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Save profile to disk as SuperPutty XML file.
        
        Args:
            profile: SuperPuttyProfile to save
            output_dir: Override output directory (uses self.base_path if None)
            
        Returns:
            Path to saved file
        """
        output_dir = output_dir or self.base_path
        

        os.makedirs(output_dir, exist_ok=True)
        

        filename = self._sanitize_filename(profile.session_name) + ".xml"
        filepath = os.path.join(output_dir, filename)
        

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(profile.to_xml())
        
        print(f"[+] Saved SuperPutty profile: {filepath}")
        return filepath
    
    def save_all_profiles(self, output_dir: Optional[str] = None) -> List[str]:
        """
        Save all created profiles to disk.
        
        Args:
            output_dir: Override output directory
            
        Returns:
            List of saved file paths
        """
        saved_files = []
        for profile in self.profiles:
            filepath = self.save_profile(profile, output_dir)
            saved_files.append(filepath)
        return saved_files
    
    def generate_batch_config(
        self,
        devices: List[Dict],
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate batch configuration for multiple devices.
        
        Args:
            devices: List of device dicts with 'name', 'ip', 'username'
            output_file: Path to output batch config file
            
        Returns:
            Path to generated config file
        """
        if not output_file:
            output_file = os.path.join(self.base_path, "nre_devices_batch.json")
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        config = {
            "generated": datetime.now().isoformat(),
            "jumpbox": "Oser500521.homeoffice.wal-mart.com",
            "devices": devices,
            "note": "Use this file with bulk_create_devices() to generate profiles"
        }
        
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"[+] Saved batch config: {output_file}")
        return output_file
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize string to valid filename.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        import re

        filename = re.sub(r'[<>:"|?*\]', '', filename)
        filename = re.sub(r'[\s/]+', '_', filename)
        return filename


def generate_nre_superputty_config():
    """
    Generate default NRE SuperPutty configuration.
    
    Creates:
    1. Jumpbox profile (Oser500521)
    2. Sample device profiles
    """
    print("\n" + "="*70)
    print("NRE SuperPutty Configuration Generator")
    print("="*70)
    
    gen = SuperPuttyConfigGenerator()
    

    print("\n[*] Creating NRE Oser Jumpbox profile...")
    jumpbox = gen.create_jumpbox_profile(username="")
    gen.save_profile(jumpbox)
    

    print("\n[*] Creating sample device profiles...")
    
    sample_devices = [
        {
            "name": "core-switch-01",
            "ip": "10.20.30.40",
            "username": "neteng",
            "os": "cisco_ios"
        },
        {
            "name": "access-switch-01",
            "ip": "10.20.30.41",
            "username": "admin",
            "os": "arista_eos"
        },
        {
            "name": "border-router-01",
            "ip": "10.20.30.50",
            "username": "root",
            "os": "juniper_junos"
        },
    ]
    
    for device in sample_devices:
        print(f"  - Creating profile for {device['name']} ({device['ip']})")
        profile = gen.create_device_profile(
            device_name=device['name'],
            device_ip=device['ip'],
            device_username=device['username']
        )
        gen.save_profile(profile)
    

    print("\n[*] Creating batch configuration file...")
    gen.generate_batch_config(sample_devices)
    
    print("\n[+] SuperPutty configuration complete!")
    print(f"[+] Profiles saved to: {gen.base_path}")
    print("\n[*] Next steps:")
    print("   1. Open SuperPutty")
    print("   2. Sessions should auto-load from disk")
    print("   3. Click 'NRE Oser Jumpbox' to connect")
    print("   4. Enter PASSCODE when prompted")
    print("   5. From jumpbox, SSH to your devices")
    print("\n[*] Documentation: https://confluence.walmart.com/display/NRE/New+Hire+Onboarding")


if __name__ == "__main__":
    generate_nre_superputty_config()