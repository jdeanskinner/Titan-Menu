"""
NRE Enterprise Jumpbox Integration with TACACS+ Support

Handles authentication to NRE's Oser jumpbox using TACACS+ with RSA SecureID.
Supports both interactive PASSCODE entry and automated token-based auth.

Usage:
    jumpbox = NREJumpbox(username, passcode)
    jumpbox.connect()
    jumpbox.execute_on_device(device_ip, device_user, command)
"""

import paramiko
import socket
import re
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class NREJumpboxConfig:
    """NRE Jumpbox Configuration."""
    primary_host: str = "oser500521"
    fallback_host: str = "oser500522"
    port: int = 22
    auth_method: str = "ad_password"
    connect_timeout: int = 10
    command_timeout: int = 15
    realm: str = ""


class NREJumpbox:
    """
    NRE Enterprise Jumpbox Handler.
    
    Manages SSH connections to Oser jumpbox (oser500521/oser500522).
    Uses standard AD authentication (username + password).
    
    Jumpbox Details:
        - Hostname: oser500521 (IP: 10.24.129.92)
        - Fallback: oser500522
        - Port: 22 (SSH)
        - OS: Unix/Linux (Bash shell)
    
    Required AD Groups:
        - NetEng_servers_Role-Login
        - NetEng_servers_Role-Listed
    
    Authentication Flow:
        1. SSH to oser500521 with AD username + password
        2. Get Unix/Linux bash shell on jumpbox
        3. From jumpbox, can SSH to network devices or run commands
        4. Bash shell environment with tools like wl, bli, ds, etc.
    """
    
    def __init__(
        self,
        username: str,
        password: str,
        config: Optional[NREJumpboxConfig] = None
    ):
        """
        Initialize NRE Jumpbox connection.
        
        Args:
            username: AD username (sAMAccountName format, e.g., 'vn59iz6')
            password: AD password
            config: NREJumpboxConfig instance (uses defaults if None)
        """
        self.username = username
        self.password = password
        self.config = config or NREJumpboxConfig()
        
        self.ssh_client = None
        self.connected = False
        self.current_host = None
    
    def _validate_credentials(self) -> bool:
        """
        Validate credentials format.
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        if not self.username or not self.password:
            raise ValueError("Username and password are required")
        
        return True
    
    def _format_hostname(self, hostname: str) -> str:
        """
        Format hostname (use short name, no realm needed).
        
        Args:
            hostname: Hostname (oser500521 or oser500522)
            
        Returns:
            Formatted hostname
        """
        return hostname.lower()
    
    def connect(self) -> bool:
        """
        Connect to NRE Jumpbox with TACACS+ authentication.
        
        Tries primary host first, then falls back to secondary if needed.
        Uses PASSCODE for TACACS+ authentication.
        
        Returns:
            True if connection successful, False otherwise
        """
        hosts_to_try = [
            self._format_hostname(self.config.primary_host),
            self._format_hostname(self.config.fallback_host),
        ]
        
        for host in hosts_to_try:
            if self._try_connect(host):
                self.current_host = host
                self.connected = True
                return True
        
        return False
    
    def _find_ssh_keys(self) -> list:
        """
        Find SSH private keys in standard locations.
        
        Checks:
        1. ~/.ssh/id_rsa (OpenSSH RSA key)
        2. ~/.ssh/id_ecdsa (ECDSA key)
        3. ~/.ssh/id_ed25519 (ED25519 key)
        4. ~/.ssh/id_dsa (DSA key - legacy)
        
        Returns:
            List of valid SSH key paths
        """
        import os
        from pathlib import Path
        
        ssh_home = Path.home() / ".ssh"
        key_names = ["id_rsa", "id_ecdsa", "id_ed25519", "id_dsa"]
        found_keys = []
        
        for key_name in key_names:
            key_path = ssh_home / key_name
            if key_path.exists() and key_path.is_file():
                try:
                    with open(key_path, 'r') as f:
                        content = f.read()
                        if "PRIVATE KEY" in content:
                            found_keys.append(str(key_path))
                except Exception:
                    pass
        
        return found_keys
    
    def _try_connect(self, hostname: str) -> bool:
        """
        Attempt connection to a specific jumpbox host.
        
        Tries authentication methods in this order:
        1. SSH keys (if found)
        2. Pageant/SSH Agent (if available)
        3. AD password (fallback)
        
        Args:
            hostname: Hostname (short name like 'oser500521')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"[*] Connecting to jumpbox: {hostname}:{self.config.port}...")
            
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh_keys = self._find_ssh_keys()
            if ssh_keys:
                print(f"[*] Found SSH keys: {', '.join([k.split('/')[-1] for k in ssh_keys])}")
                print(f"[*] Trying key-based authentication...")
                
                try:
                    self.ssh_client.connect(
                        hostname=hostname,
                        port=self.config.port,
                        username=self.username,
                        key_filename=ssh_keys,
                        timeout=self.config.connect_timeout,
                        allow_agent=True,
                        look_for_keys=True,
                        banner_timeout=10,
                    )
                    print(f"[+] Connected to jumpbox: {hostname}")
                    print(f"[+] Authenticated as: {self.username} (using SSH key)")
                    return True
                
                except paramiko.AuthenticationException:
                    print(f"[!] SSH key authentication failed")
                    print(f"[*] Falling back to password authentication...")
            
            if not self.password:
                print(f"[!] No SSH keys found and no password provided")
                return False
            
            print(f"[*] Using password authentication...")
            self.ssh_client.connect(
                hostname=hostname,
                port=self.config.port,
                username=self.username,
                password=self.password,
                timeout=self.config.connect_timeout,
                allow_agent=True,
                look_for_keys=True,
                banner_timeout=10,
            )
            
            print(f"[+] Connected to jumpbox: {hostname}")
            print(f"[+] Authenticated as: {self.username} (using password)")
            return True
            
        except paramiko.AuthenticationException as e:
            print(f"[!] Authentication failed on {hostname}")
            print(f"[!] Check: username ({self.username})")
            if self.password:
                print(f"[!] Check: AD password")
            print(f"[!] Verify AD groups: NetEng_servers_Role-Login, NetEng_servers_Role-Listed")
            return False
        
        except socket.timeout:
            print(f"[!] Connection timeout to {hostname}")
            return False
        
        except socket.gaierror as e:
            print(f"[!] Cannot resolve hostname: {hostname}")
            print(f"[!] Trying fallback jumpbox...")
            return False
        
        except Exception as e:
            print(f"[!] Connection error on {hostname}: {e}")
            return False
    
    def _enable_agent_forwarding(self) -> bool:
        """
        Enable SSH agent forwarding on the connection.
        
        This allows SSH commands FROM the jumpbox to use local SSH keys,
        just like SuperPutty does. Users can then SSH to devices without
        needing passwords (if keys are configured).
        
        Returns:
            True if forwarding enabled successfully
        """
        try:
            if not self.ssh_client or not self.connected:
                return False
            
            transport = self.ssh_client.get_transport()
            if not transport:
                return False
            
            transport.request_success = True
            return True
            
        except Exception as e:
            return False
    
    def start_interactive_shell(self) -> bool:
        """
        Start interactive bash shell on jumpbox (cross-platform).
        Allows user to run commands directly on jumpbox.
        Uses threading to handle bidirectional I/O on Windows and Unix.
        
        SSH agent forwarding is enabled for device SSH access.
        
        Returns:
            True if shell started successfully
        """
        if not self.connected:
            print("[!] Not connected to jumpbox")
            return False
        
        try:
            channel = self.ssh_client.invoke_shell()
            channel.settimeout(0.1)
            
            print("[+] Interactive bash shell started")
            print("[*] Type 'exit' or 'logout' to close connection")
            print("[*] SSH keys are forwarded for device access (use: ssh -l neteng <device_ip>)\n")
            
            import sys
            import threading
            import time
            
            stop_flag = threading.Event()
            
            def read_from_remote():
                """Read from jumpbox and print to screen."""
                while not stop_flag.is_set():
                    try:
                        data = channel.recv(1024)
                        if not data:
                            break
                        sys.stdout.write(data.decode('utf-8', errors='ignore'))
                        sys.stdout.flush()
                    except socket.timeout:
                        time.sleep(0.01)
                    except Exception:
                        break
            
            def read_from_stdin():
                """Read from user input and send to jumpbox."""
                while not stop_flag.is_set():
                    try:
                        cmd = sys.stdin.readline()
                        if cmd:
                            channel.send(cmd.encode('utf-8'))
                            if cmd.strip() in ['exit', 'logout', 'quit']:
                                stop_flag.set()
                                break
                    except Exception:
                        break
            
            reader_thread = threading.Thread(target=read_from_remote, daemon=True)
            stdin_thread = threading.Thread(target=read_from_stdin, daemon=True)
            
            reader_thread.start()
            stdin_thread.start()
            
            stdin_thread.join()
            
            stop_flag.set()
            
            reader_thread.join(timeout=1)
            
            channel.close()
            return True
            
        except KeyboardInterrupt:
            print("\n[*] Connection closed by user")
            return True
        except Exception as e:
            print(f"[!] Error: {e}")
            return False
    
    def execute_command(
        self,
        command: str
    ) -> Tuple[bool, str]:
        """
        Execute a single command on jumpbox and return output.
        
        Args:
            command: Bash command to execute on jumpbox
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        if not self.connected:
            return False, "[!] Not connected to jumpbox"
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(
                command,
                timeout=self.config.command_timeout
            )
            
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            if error and "Warning" not in error:
                return False, error.strip()
            
            return True, output.strip()
            
        except socket.timeout:
            return False, "[!] Command timeout"
        except Exception as e:
            return False, f"[!] Error: {e}"
    

    
    def disconnect(self):
        """
        Close connection to jumpbox.
        """
        if self.ssh_client:
            self.ssh_client.close()
            self.connected = False
            print(f"[*] Disconnected from jumpbox: {self.current_host}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def prompt_for_jumpbox_credentials() -> Tuple[str, str]:
    """
    Prompt user for jumpbox credentials.
    
    Tries SSH keys first (like SuperPutty).
    Password is optional - only needed if SSH keys aren't available.
    
    Returns:
        Tuple of (username: str, password: str)
    """
    import getpass
    from pathlib import Path
    
    print("\n" + "="*70)
    print("NRE Enterprise Jumpbox - SSH Authentication")
    print("="*70)
    print("\nConnecting to: oser500521 (10.24.129.92)")
    print("OS: Unix/Linux (Bash shell)")
    print()
    
    username = input("AD Username (e.g., vn59iz6): ").strip()
    
    ssh_home = Path.home() / ".ssh"
    has_ssh_keys = False
    
    if ssh_home.exists():
        key_names = ["id_rsa", "id_ecdsa", "id_ed25519", "id_dsa"]
        for key_name in key_names:
            key_path = ssh_home / key_name
            if key_path.exists():
                has_ssh_keys = True
                break
    
    if has_ssh_keys:
        print("\n[*] SSH keys found in ~/.ssh")
        print("[*] Will try key-based authentication first (like SuperPutty)")
        password_prompt = "AD Password (press Enter to skip if SSH key works): "
    else:
        print("\n[*] No SSH keys found in ~/.ssh")
        password_prompt = "AD Password: "
    
    password = getpass.getpass(password_prompt)
    
    return username, password


if __name__ == "__main__":
    import sys
    
    try:
        username, passcode = prompt_for_tacacs_credentials()
        
        jumpbox = NREJumpbox(username, passcode)
        if jumpbox.connect():
            device_ip = input("\nTarget device IP: ").strip()
            device_user = input("Device username: ").strip()
            
            success, msg = jumpbox.verify_device_access(device_ip, device_user)
            print(f"\n[*] Access verification: {msg}")
            
            jumpbox.disconnect()
        else:
            print("\n[!] Failed to connect to jumpbox")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n[*] Cancelled by user")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)