"""
SSH Interactive Menu for Titan

Handles user selection for:
  - Bastion host selection
  - Command selection
  - Custom command input
"""

from typing import Optional, Tuple
from .bastion_manager import BastionManager
from .bastion_config import BASTION_HOSTS
from .ssh_config import SHOW_COMMANDS
from .ssh_remote import DeviceCommandRunner


def display_bastion_menu() -> str:
    """
    Display bastion host selection menu.
    
    Returns:
        Selected bastion ID
    """
    manager = BastionManager()
    bastions = manager.list_available_bastions()
    
    print("\n" + "="*70)
    print("[Bastion Host Selection]")
    print("="*70)
    
    for i, bastion in enumerate(bastions, 1):
        print(f"\n{i}. {bastion['name']}")
        print(f"   Type: {bastion['type']}")
        print(f"   Region: {bastion['region']}")
        print(f"   {bastion['description']}")
    
    print(f"\n{len(bastions) + 1}. Exit")
    print("\n" + "="*70)
    
    while True:
        try:
            choice = int(input(f"\nSelect bastion (1-{len(bastions)}): ").strip())
            if 1 <= choice <= len(bastions):
                return bastions[choice - 1]["id"]
            elif choice == len(bastions) + 1:
                return None
            else:
                print(f"Invalid choice. Enter 1-{len(bastions)}")
        except ValueError:
            print("Invalid input. Enter a number.")
        except KeyboardInterrupt:
            return None


def display_command_menu(device_runner: DeviceCommandRunner) -> Optional[str]:
    """
    Display command selection menu for device OS.
    
    Args:
        device_runner: DeviceCommandRunner instance
        
    Returns:
        Selected command or None
    """
    commands = device_runner.get_available_commands()
    command_list = list(commands.items())
    
    print("\n" + "="*70)
    print(f"[Available Commands - {device_runner.device_os.upper()}]")
    print("="*70)
    
    for i, (alias, cmd) in enumerate(command_list, 1):
        print(f"{i}. {alias:<20} -> {cmd}")
    
    print(f"{len(command_list) + 1}. Custom command")
    print(f"{len(command_list) + 2}. Back")
    print("\n" + "="*70)
    
    while True:
        try:
            choice = int(input(f"\nSelect command (1-{len(command_list) + 1}): ").strip())
            
            if 1 <= choice <= len(command_list):
                return command_list[choice - 1][0]
            elif choice == len(command_list) + 1:
                custom_cmd = input("\nEnter custom command: ").strip()
                if custom_cmd:
                    return f"custom:{custom_cmd}"
            elif choice == len(command_list) + 2:
                return None
            else:
                print(f"Invalid choice. Enter 1-{len(command_list) + 1}")
        except ValueError:
            print("Invalid input. Enter a number.")
        except KeyboardInterrupt:
            return None


def display_ssh_menu(device_info: dict) -> Optional[str]:
    """
    Display main SSH menu with device info.
    
    Args:
        device_info: Device information dict
        
    Returns:
        Selected option or None
    """
    print("\n" + "="*70)
    print("[SSH Remote Command Execution]")
    print("="*70)
    print(f"\nDevice: {device_info.get('name', 'N/A')}")
    print(f"Management IP: {device_info.get('mgmt_ip', 'N/A')}")
    print(f"OS Type: {device_info.get('os_type', 'Unknown')}")
    print(f"State: {device_info.get('state', 'Unknown')}")
    print("\n" + "="*70)
    print("\n1. Select Bastion Host")
    print("2. Run Show Commands")
    print("3. Execute Custom Command")
    print("0. Back")
    print("\n" + "="*70)
    
    while True:
        try:
            choice = input("\nSelect option (0-3): ").strip()
            if choice in ['0', '1', '2', '3']:
                return choice
            else:
                print("Invalid choice. Enter 0-3")
        except KeyboardInterrupt:
            return None


def display_bastion_info(bastion_id: str):
    """
    Display information about selected bastion.
    
    Args:
        bastion_id: Bastion ID to display info for
    """
    if bastion_id not in BASTION_HOSTS:
        print("[!] Invalid bastion ID")
        return
    
    config = BASTION_HOSTS[bastion_id]
    
    print("\n" + "="*70)
    print(f"[Bastion Details]")
    print("="*70)
    print(f"Name: {config.get('name')}")
    print(f"Type: {config.get('type')}")
    print(f"Region: {config.get('region')}")
    print(f"Description: {config.get('description')}")
    print(f"Auth Method: {config.get('auth_method')}")
    
    if config.get('type') == 'ssh':
        print(f"\nSSH Details:")
        print(f"  Host: {config.get('host')}")
        print(f"  Port: {config.get('port')}")
    elif config.get('type') == 'gcloud':
        print(f"\nGoogle Cloud Details:")
        print(f"  Instance: {config.get('instance_name')}")
        print(f"  Zone: {config.get('zone')}")
        print(f"  Project: {config.get('project')}")
    
    print("\n" + "="*70)


def prompt_for_password(prompt_text: str = "Enter password") -> str:
    """
    Prompt for password securely.
    
    Args:
        prompt_text: Text to display in prompt
        
    Returns:
        Entered password (or empty string if cancelled)
    """
    import getpass
    try:
        return getpass.getpass(f"\n{prompt_text}: ")
    except KeyboardInterrupt:
        return ""


def confirm_action(action_text: str) -> bool:
    """
    Prompt user for confirmation.
    
    Args:
        action_text: Action description
        
    Returns:
        True if confirmed, False otherwise
    """
    while True:
        response = input(f"\n{action_text} (yes/no)? ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Enter 'yes' or 'no'")
