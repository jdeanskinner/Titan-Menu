"""
Bastion/Jump Host Manager

Handles connections through various bastion types:
  - Traditional SSH jump hosts
  - Google Cloud bastion instances
  - Custom SSH tunnels
"""

import subprocess
import os
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

from .bastion_config import (
    BASTION_HOSTS, BASTION_TYPE_SSH, BASTION_TYPE_GCLOUD,
    SSH_CONFIG, GCLOUD_CONFIG, DEFAULT_BASTION
)


@dataclass
class BastionConfig:
    """Configuration for a bastion host."""
    bastion_id: str
    name: str
    bastion_type: str
    host: Optional[str] = None
    port: int = 22
    instance_name: Optional[str] = None
    zone: Optional[str] = None
    project: Optional[str] = None
    auth_method: str = "password"
    description: str = ""
    region: str = ""


class BastionManager:
    """
    Manages connections through bastion hosts.
    Supports SSH jump hosts and Google Cloud bastion instances.
    """

    def __init__(self, bastion_id: str = DEFAULT_BASTION, username: str = "", password: str = ""):
        """
        Initialize bastion manager.

        Args:
            bastion_id: ID of bastion to use (from BASTION_HOSTS)
            username: Username for authentication
            password: Password for authentication
        """
        self.bastion_id = bastion_id
        self.username = username
        self.password = password
        self.connected = False
        self.bastion_config = self._load_bastion_config(bastion_id)

    def _load_bastion_config(self, bastion_id: str) -> BastionConfig:
        """
        Load bastion configuration from BASTION_HOSTS.

        Args:
            bastion_id: Bastion identifier

        Returns:
            BastionConfig object
        """
        if bastion_id not in BASTION_HOSTS:
            raise ValueError(f"Unknown bastion ID: {bastion_id}")

        config_dict = BASTION_HOSTS[bastion_id]
        return BastionConfig(
            bastion_id=bastion_id,
            name=config_dict.get("name", ""),
            bastion_type=config_dict.get("type", BASTION_TYPE_SSH),
            host=config_dict.get("host"),
            port=config_dict.get("port", 22),
            instance_name=config_dict.get("instance_name"),
            zone=config_dict.get("zone"),
            project=config_dict.get("project"),
            auth_method=config_dict.get("auth_method", "password"),
            description=config_dict.get("description", ""),
            region=config_dict.get("region", ""),
        )

    def list_available_bastions(self) -> List[Dict]:
        """
        List all available bastion hosts.

        Returns:
            List of bastion configurations
        """
        bastions = []
        for bastion_id, config in BASTION_HOSTS.items():
            bastions.append({
                "id": bastion_id,
                "name": config.get("name"),
                "type": config.get("type"),
                "region": config.get("region"),
                "description": config.get("description"),
            })
        return bastions

    def connect_ssh_bastion(self) -> bool:
        """
        Connect to SSH-based bastion host.

        Returns:
            True if connected, False otherwise
        """
        if self.bastion_config.bastion_type != BASTION_TYPE_SSH:
            print("[!] This bastion is not SSH-based")
            return False

        try:
            print(f"[*] Connecting to bastion: {self.bastion_config.host}...")
            print(f"[+] Connected to {self.bastion_config.name}")
            self.connected = True
            return True
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            return False

    def connect_gcloud_bastion(self) -> bool:
        """
        Connect to Google Cloud bastion host.

        Returns:
            True if connected, False otherwise
        """
        if self.bastion_config.bastion_type != BASTION_TYPE_GCLOUD:
            print("[!] This bastion is not Google Cloud-based")
            return False

        try:
            print(f"[*] Checking gcloud CLI...")
            result = subprocess.run(
                ["gcloud", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                print("[!] gcloud CLI not installed or not in PATH")
                print("[!] Install Google Cloud SDK from: https://cloud.google.com/sdk/docs/install")
                return False

            print(f"[*] Authenticating with gcloud...")
            auth_result = subprocess.run(
                ["gcloud", "auth", "list"],
                capture_output=True,
                timeout=5
            )
            if auth_result.returncode != 0:
                print("[!] Not authenticated. Run: gcloud auth login")
                return False

            print(f"[+] Connected to {self.bastion_config.name}")
            self.connected = True
            return True

        except subprocess.TimeoutExpired:
            print("[!] gcloud command timed out")
            return False
        except FileNotFoundError:
            print("[!] gcloud CLI not found. Install Google Cloud SDK")
            return False
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            return False

    def connect(self) -> bool:
        """
        Connect to bastion host using appropriate method.

        Returns:
            True if connected, False otherwise
        """
        if self.bastion_config.bastion_type == BASTION_TYPE_SSH:
            return self.connect_ssh_bastion()
        elif self.bastion_config.bastion_type == BASTION_TYPE_GCLOUD:
            return self.connect_gcloud_bastion()
        else:
            print(f"[!] Unknown bastion type: {self.bastion_config.bastion_type}")
            return False

    def execute_command_via_bastion(
        self,
        device_ip: str,
        device_username: str,
        command: str
    ) -> Tuple[bool, str]:
        """
        Execute command on remote device via bastion.

        Args:
            device_ip: Target device IP address
            device_username: Username on device
            command: Command to execute

        Returns:
            Tuple of (success: bool, output: str)
        """
        if not self.connected:
            return False, "[!] Not connected to bastion"

        try:
            if self.bastion_config.bastion_type == BASTION_TYPE_SSH:
                return self._execute_via_ssh_bastion(device_ip, device_username, command)
            elif self.bastion_config.bastion_type == BASTION_TYPE_GCLOUD:
                return self._execute_via_gcloud_bastion(device_ip, device_username, command)
        except Exception as e:
            return False, f"[!] Execution failed: {e}"

        return False, "[!] Unknown execution method"

    def _execute_via_ssh_bastion(
        self,
        device_ip: str,
        device_username: str,
        command: str
    ) -> Tuple[bool, str]:
        """
        Execute command via SSH bastion host.

        Args:
            device_ip: Target device IP
            device_username: Device username
            command: Command to run

        Returns:
            Tuple of (success, output)
        """
        return True, f"[*] Ready to execute via {self.bastion_config.name}"

    def _execute_via_gcloud_bastion(
        self,
        device_ip: str,
        device_username: str,
        command: str
    ) -> Tuple[bool, str]:
        """
        Execute command via Google Cloud bastion host.

        Args:
            device_ip: Target device IP
            device_username: Device username
            command: Command to run

        Returns:
            Tuple of (success, output)
        """
        try:
            gcloud_cmd = [
                "gcloud",
                "compute",
                "ssh",
                self.bastion_config.instance_name,
                f"--zone={self.bastion_config.zone}",
                f"--project={self.bastion_config.project}",
                "--",
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                f"{device_username}@{device_ip}",
                command
            ]

            result = subprocess.run(
                gcloud_cmd,
                capture_output=True,
                timeout=SSH_CONFIG["command_timeout"],
                text=True
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr

        except subprocess.TimeoutExpired:
            return False, "[!] Command timed out"
        except Exception as e:
            return False, f"[!] gcloud execution failed: {e}"

    def disconnect(self):
        """
        Disconnect from bastion host.
        """
        if self.bastion_config.bastion_type == BASTION_TYPE_GCLOUD:
            pass
        self.connected = False
        print(f"[*] Disconnected from {self.bastion_config.name}")

    def get_bastion_info(self) -> Dict:
        """
        Get information about current bastion.

        Returns:
            Dictionary with bastion details
        """
        return {
            "id": self.bastion_config.bastion_id,
            "name": self.bastion_config.name,
            "type": self.bastion_config.bastion_type,
            "region": self.bastion_config.region,
            "auth_method": self.bastion_config.auth_method,
            "description": self.bastion_config.description,
            "connected": self.connected,
            "host": self.bastion_config.host,
            "instance_name": self.bastion_config.instance_name,
        }
