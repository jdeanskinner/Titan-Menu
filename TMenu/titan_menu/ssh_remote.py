"""
SSH Remote Command Execution Module

Handles SSH connections through jump host and remote command execution
on network devices with multi-OS support and username rotation.
"""

import paramiko
import socket
from typing import Optional, Dict, List, Tuple
from io import StringIO

from .ssh_config import (
    JUMP_HOST, JUMP_HOST_PORT, DEFAULT_USERNAMES,
    SSH_TIMEOUT, SSH_CONNECT_TIMEOUT, COMMAND_TIMEOUT,
    OS_TYPES, SHOW_COMMANDS, DEVICE_SPECIFIC_USERNAMES,
    CISCO_IOS_USERNAMES
)
from .bastion_manager import BastionManager
from .ssh_parsers import OutputParser


class SSHConnection:
    """
    Manages SSH connection through jump host to remote device.
    Handles authentication with username rotation.
    Supports both traditional SSH and Google Cloud bastion hosts.
    """
    
    def __init__(self, username: str, password: str, bastion_id: str = "nre_traditional"):
        """
        Initialize SSH connection.
        
        Args:
            username: AD username for jump host / gcloud auth
            password: AD password for jump host
            bastion_id: Bastion host ID to use (from bastion_config.py)
        """
        self.username = username
        self.password = password
        self.bastion_id = bastion_id
        self.ssh_client = None
        self.ssh_transport = None
        self.connected = False
        self.bastion_manager = None
        self._init_bastion_manager()
    
    def _init_bastion_manager(self):
        """
        Initialize bastion manager based on bastion_id.
        Supports both SSH and Google Cloud bastions.
        """
        try:
            self.bastion_manager = BastionManager(
                bastion_id=self.bastion_id,
                username=self.username,
                password=self.password
            )
        except ValueError as e:
            print(f"[!] Invalid bastion ID: {e}")
            self.bastion_manager = None
    
    def connect_to_jumphost(self) -> bool:
        """
        Connect to jump host (bastion).
        Automatically selects SSH or Google Cloud method based on bastion type.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.bastion_manager:
            print("[!] Bastion manager not initialized")
            return False
        
        if self.bastion_manager.connect():
            self.connected = True
            return True
        
        try:
            print(f"[*] Connecting to jump host: {JUMP_HOST}...")
            
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            
            self.ssh_client.connect(
                hostname=JUMP_HOST,
                port=JUMP_HOST_PORT,
                username=self.username,
                password=self.password,
                timeout=SSH_CONNECT_TIMEOUT,
                allow_agent=False,
                look_for_keys=False
            )
            
            print(f"[+] Connected to jump host!")
            self.connected = True
            return True
            
        except paramiko.AuthenticationException:
            print(f"[!] Authentication failed. Check your AD credentials.")
            return False
        except socket.timeout:
            print(f"[!] Connection timeout to jump host.")
            return False
        except Exception as e:
            print(f"[!] Connection error: {e}")
            return False
    
    def execute_command_on_device(
        self,
        device_ip: str,
        device_username: str,
        command: str
    ) -> Tuple[bool, str]:
        """
        Execute command on remote device through jump host.
        
        Args:
            device_ip: Target device IP address
            device_username: Username on target device
            command: Command to execute
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        if not self.connected:
            return False, "[!] Not connected to jump host"
        
        try:
            print(f"[*] Running: {command}")
            
            stdin, stdout, stderr = self.ssh_client.exec_command(
                f"ssh -o StrictHostKeyChecking=no {device_username}@{device_ip} '{command}'",
                timeout=COMMAND_TIMEOUT
            )
            
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            if error and "Warning" not in error:
                return False, error
            
            print(f"[+] Command completed")
            return True, output
            
        except socket.timeout:
            return False, "[!] Command timeout"
        except Exception as e:
            return False, f"[!] Command error: {e}"
    
    def disconnect(self):
        """
        Close SSH connection.
        """
        if self.ssh_client:
            self.ssh_client.close()
            self.connected = False
            print("[*] Disconnected from jump host")


class DeviceCommandRunner:
    """
    Runs commands on remote devices with OS-specific handling.
    Manages username rotation and output parsing.
    """
    
    def __init__(
        self,
        device_ip: str,
        device_os: str,
        ssh_connection: SSHConnection,
        usernames: Optional[List[str]] = None
    ):
        """
        Initialize device command runner.
        
        Args:
            device_ip: Device management IP
            device_os: Device OS type (IOS, EOS, JUNOS, SONIC)
            ssh_connection: Active SSH connection to jump host
            usernames: List of usernames to try (rotates on failure)
        """
        self.device_ip = device_ip
        self.device_os = self._normalize_os_type(device_os)
        self.ssh_connection = ssh_connection
        
        if usernames:
            self.usernames = usernames
        else:
            self.usernames = self._build_username_list()
        
        self.current_username = None
        self.authenticated = False
        self.failed_usernames = []
    
    def _normalize_os_type(self, os_type: str) -> str:
        """
        Normalize OS type to standard format.
        
        Args:
            os_type: Raw OS type from database
            
        Returns:
            Normalized OS type
        """
        os_upper = os_type.upper().strip()
        
        if os_upper in OS_TYPES:
            return OS_TYPES[os_upper]
        
        for key, value in OS_TYPES.items():
            if key in os_upper or os_upper in key:
                return value
        
        return os_upper.lower()
    
    def _build_username_list(self) -> List[str]:
        """
        Build comprehensive username list based on device OS type.
        Combines device-specific usernames with defaults.
        
        Returns:
            List of usernames to try in order
        """
        device_specific = DEVICE_SPECIFIC_USERNAMES.get(self.device_os, [])
        
        usernames = list(dict.fromkeys(device_specific + DEFAULT_USERNAMES))
        
        if "cisco" in self.device_os.lower():
            cisco_specific = [u for u in CISCO_IOS_USERNAMES if u not in usernames]
            usernames.extend(cisco_specific)
        
        return usernames
    
    def get_available_commands(self) -> Dict[str, str]:
        """
        Get available show commands for this device OS.
        
        Returns:
            Dictionary of command aliases to actual commands
        """
        return SHOW_COMMANDS.get(
            self.device_os,
            {"custom": "custom command"}
        )
    
    def run_command(self, command_alias: str = "version") -> Tuple[bool, Dict]:
        """
        Run a show command on the device.
        Tries usernames in order, prioritizing device-specific ones first.
        
        Args:
            command_alias: Command alias (version, bgp_summary, etc.)
            
        Returns:
            Tuple of (success: bool, parsed_output: Dict)
        """
        available_commands = self.get_available_commands()
        
        if command_alias not in available_commands:
            return False, {"error": f"Command '{command_alias}' not available for {self.device_os}"}
        
        actual_command = available_commands[command_alias]
        
        attempted = 0
        for username in self.usernames:
            attempted += 1
            print(f"[*] Trying username: {username} ({attempted}/{len(self.usernames)})")
            
            success, output = self.ssh_connection.execute_command_on_device(
                self.device_ip,
                username,
                actual_command
            )
            
            if success and output and "permission denied" not in output.lower():
                self.current_username = username
                self.authenticated = True
                print(f"[+] Authenticated as: {username}")
                
                if command_alias == "version":
                    parsed = OutputParser.parse_show_version(output, self.device_os)
                elif command_alias == "bgp_summary":
                    parsed = OutputParser.parse_bgp_summary(output, self.device_os)
                else:
                    parsed = {"raw_output": output[:200]}
                
                return True, parsed
            else:
                self.failed_usernames.append(username)
        
        error_msg = self._build_auth_failure_message()
        return False, {"error": error_msg}
    
    def _build_auth_failure_message(self) -> str:
        """
        Build helpful error message when authentication fails.
        
        Returns:
            Helpful error message with troubleshooting steps
        """
        msg = "Authentication failed. "
        msg += f"Tried {len(self.failed_usernames)} username(s): {', '.join(self.failed_usernames[:3])}"
        
        msg += "\n\nTroubleshooting steps:\n"
        msg += "1. Check device SSH config: show ip ssh\n"
        msg += "2. Check your user account exists on device\n"
        msg += "3. Verify your AD account has device access\n"
        msg += "4. Contact network team: nocenterprise@wal-mart.com\n"
        msg += "\nNote: This device requires specific username(s)."
        msg += f"\nDevice type: {self.device_os}"
        
        return msg
    
    def run_custom_command(self, command: str) -> Tuple[bool, str]:
        """
        Run a custom command on the device.
        
        Args:
            command: Full command string
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        if not self.authenticated and not self.current_username:
            success, _ = self.run_command("version")
            if not success:
                return False, "[!] Failed to authenticate to device"
        
        success, output = self.ssh_connection.execute_command_on_device(
            self.device_ip,
            self.current_username,
            command
        )
        
        return success, output
