"""
NAPA Gateway - Network Automation Platform and Analytics

Integration with Walmart's NAPA system for secure authenticated access
to network devices with TACACS+ and 2FA (AD + RSA OTP).

NAPA provides:
- Centralized authentication via ISE
- TACACS+ protocol for device access
- 2FA enforcement (AD username + RSA OTP)
- Comprehensive audit logging
- Access control lists (ACLs) per device

Available NAPA Instances:
- NAPA_1-5: Non-PCI (AD auth only)
- NAPA_6-9: PCI (2FA required)

Usage:
    from napa_gateway import NAPAGateway
    
    napa = NAPAGateway(username="vn59iz6", napa_instance="NAPA_1")
    if napa.connect():
        napa.connect_to_device(device_ip="10.0.4.2", username="neteng")
        napa.execute_command("show version")
        napa.disconnect()
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import getpass
import paramiko
import socket


@dataclass
class NAPAInstance:
    """NAPA instance configuration."""
    name: str
    host: str
    port: int
    environment: str
    auth_type: str
    description: str


class NAPAGateway:
    """
    NAPA Gateway for authenticated network device access.
    
    NAPA (Network Automation Platform and Analytics) provides secure,
    authenticated access to Walmart network devices through TACACS+ with
    comprehensive audit logging and access control.
    """
    
    INSTANCES = {
        "NAPA_1": NAPAInstance(
            name="NAPA_1",
            host="161.170.234.61",
            port=4000,
            environment="MCC BM (dfw replacement)",
            auth_type="ad",
            description="Non-PCI, AD Authentication"
        ),
        "NAPA_2": NAPAInstance(
            name="NAPA_2",
            host="oseu2015023.homeoffice.wal-mart.com",
            port=4000,
            environment="New - CDC",
            auth_type="ad",
            description="Non-PCI, AD Authentication"
        ),
        "NAPA_3": NAPAInstance(
            name="NAPA_3",
            host="oseu2015024.homeoffice.wal-mart.com",
            port=4000,
            environment="New - CDC",
            auth_type="ad",
            description="Non-PCI, AD Authentication"
        ),
        "NAPA_4": NAPAInstance(
            name="NAPA_4",
            host="oseu2015025.homeoffice.wal-mart.com",
            port=4000,
            environment="New - NDC",
            auth_type="ad",
            description="Non-PCI, AD Authentication"
        ),
        "NAPA_5": NAPAInstance(
            name="NAPA_5",
            host="oseu2015026.homeoffice.wal-mart.com",
            port=4000,
            environment="New - EDC",
            auth_type="ad",
            description="Non-PCI, AD Authentication"
        ),
        "NAPA_6": NAPAInstance(
            name="NAPA_6",
            host="10.120.62.177",
            port=30167,
            environment="PCI - NDC",
            auth_type="2fa",
            description="PCI Instance, 2FA Required (AD + RSA OTP)"
        ),
        "NAPA_7": NAPAInstance(
            name="NAPA_7",
            host="10.120.62.178",
            port=30167,
            environment="PCI - NDC",
            auth_type="2fa",
            description="PCI Instance, 2FA Required (AD + RSA OTP)"
        ),
        "NAPA_8": NAPAInstance(
            name="NAPA_8",
            host="10.225.158.187",
            port=30167,
            environment="PCI - CDC",
            auth_type="2fa",
            description="PCI Instance, 2FA Required (AD + RSA OTP)"
        ),
        "NAPA_9": NAPAInstance(
            name="NAPA_9",
            host="10.225.158.188",
            port=30167,
            environment="PCI - CDC",
            auth_type="2fa",
            description="PCI Instance, 2FA Required (AD + RSA OTP)"
        ),
    }
    
    def __init__(
        self,
        username: str,
        napa_instance: str = "NAPA_1",
        otp: Optional[str] = None
    ):
        """
        Initialize NAPA gateway connection.
        
        Args:
            username: AD username (sAMAccountName)
            napa_instance: NAPA instance name (NAPA_1 to NAPA_9)
            otp: RSA OTP for 2FA instances (optional, will prompt if needed)
        """
        self.username = username
        self.otp = otp
        
        if napa_instance not in self.INSTANCES:
            raise ValueError(f"Invalid NAPA instance: {napa_instance}")
        
        self.instance = self.INSTANCES[napa_instance]
        self.ssh_client = None
        self.connected = False
        self.current_device = None
    
    def connect(self, password: Optional[str] = None) -> bool:
        """
        Connect to NAPA instance.
        
        Args:
            password: AD password (will prompt if not provided)
            
        Returns:
            True if connection successful
        """
        try:
            if not password:
                password = getpass.getpass(f"AD Password for {self.username}: ")
            
            passcode = password
            if self.instance.auth_type == "2fa":
                if not self.otp:
                    self.otp = getpass.getpass("RSA OTP (6 digits): ")
                passcode = password + self.otp
            
            print(f"[*] Connecting to {self.instance.name} ({self.instance.host}:{self.instance.port})...")
            
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.instance.host,
                port=self.instance.port,
                username=self.username,
                password=passcode,
                timeout=10,
                allow_agent=False,
                look_for_keys=False,
                banner_timeout=10,
            )
            
            self.connected = True
            print(f"[+] Connected to NAPA: {self.instance.name}")
            print(f"[+] Environment: {self.instance.environment}")
            print(f"[+] Authenticated as: {self.username}")
            print(f"[+] NAPA provides authenticated access to network devices")
            return True
            
        except paramiko.AuthenticationException as e:
            print(f"[!] NAPA authentication failed")
            if self.instance.auth_type == "2fa":
                print(f"[!] Check: AD password and RSA OTP")
            else:
                print(f"[!] Check: AD password")
            return False
        
        except socket.timeout:
            print(f"[!] Connection timeout to {self.instance.name}")
            return False
        
        except Exception as e:
            print(f"[!] Connection error: {e}")
            return False
    
    def execute_command(self, command: str) -> Tuple[bool, str]:
        """
        Execute command on connected device via NAPA.
        
        Args:
            command: Command to execute on device
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        if not self.connected:
            return False, "Not connected to NAPA"
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            if error and "Warning" not in error:
                return False, error
            
            return True, output
        
        except Exception as e:
            return False, str(e)
    
    def disconnect(self) -> None:
        """
        Disconnect from NAPA.
        """
        if self.ssh_client:
            self.ssh_client.close()
        self.connected = False
        print(f"[+] Disconnected from NAPA")
    
    @staticmethod
    def list_instances() -> None:
        """
        Display all available NAPA instances.
        """
        print("\n" + "="*80)
        print("Available NAPA Instances")
        print("="*80)
        
        print("\nNON-PCI Instances (AD Authentication):")
        print("-" * 80)
        for name in ["NAPA_1", "NAPA_2", "NAPA_3", "NAPA_4", "NAPA_5"]:
            inst = NAPAGateway.INSTANCES[name]
            print(f"  {name:8} | {inst.host:40} | {inst.environment:30}")
        
        print("\nPCI Instances (2FA - AD + RSA OTP):")
        print("-" * 80)
        for name in ["NAPA_6", "NAPA_7", "NAPA_8", "NAPA_9"]:
            inst = NAPAGateway.INSTANCES[name]
            print(f"  {name:8} | {inst.host:40} | {inst.environment:30}")
        
        print("\nRecommendation:")
        print("  - Use NAPA_6 to NAPA_9 for external/remote access (more secure)")
        print("  - Use NAPA_1 to NAPA_5 for internal network access (AD only)")
        print()


def prompt_for_napa_access() -> Tuple[str, str, str]:
    """
    Prompt user for NAPA access details.
    
    Returns:
        Tuple of (username: str, napa_instance: str, password: str)
    """
    print("\n" + "="*70)
    print("NAPA Gateway - Secure Network Device Access")
    print("="*70)
    
    print("\nAvailable NAPA Instances:")
    print("  Non-PCI (AD auth): NAPA_1, NAPA_2, NAPA_3, NAPA_4, NAPA_5")
    print("  PCI (2FA):         NAPA_6, NAPA_7, NAPA_8, NAPA_9")
    
    username = input("\nAD Username: ").strip()
    napa_instance = input("NAPA Instance (default NAPA_1): ").strip() or "NAPA_1"
    password = getpass.getpass("AD Password: ")
    
    return username, napa_instance, password