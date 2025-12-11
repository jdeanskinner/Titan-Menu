"""
Bastion/Jump Host Configuration for NRE Enterprise

Supports multiple bastion types:
  1. Traditional SSH Jump Hosts (e.g., oseu2015026.homeoffice.wal-mart.com)
  2. Google Cloud Bastion Hosts (using gcloud CLI)
  3. Custom SSH Jump Servers
"""

from typing import Dict, List

BASTION_TYPE_SSH = "ssh"
BASTION_TYPE_GCLOUD = "gcloud"

BASTION_HOSTS: Dict[str, Dict] = {
    "nre_oser_jumpbox": {
        "name": "NRE Enterprise Oser Jumpbox (TACACS+)",
        "type": "nre_jumpbox",
        "primary_host": "Oser500521",
        "fallback_host": "Oser500522",
        "port": 22,
        "realm": "homeoffice.wal-mart.com",
        "description": "Primary NRE jumpbox with TACACS+ authentication via RSA SecureID",
        "region": "Walmart On-Prem (Network Engineering)",
        "auth_method": "TACACS+ (PCI token + RSA PIN)",
        "required_groups": [
            "NetEng_servers_Role-Login",
            "NetEng_servers_Role-Listed"
        ],
        "features": [
            "TACACS+ with RSA SecureID",
            "Cisco/Juniper/Arista device access",
            "Store topology support",
            "Network device management",
        ],
        "contact": "nocenterprise@wal-mart.com",
        "documentation": "https://confluence.walmart.com/display/NRE/New+Hire+Onboarding",
    },
    "nre_traditional": {
        "name": "NRE Traditional SSH Jump Host (Legacy)",
        "type": BASTION_TYPE_SSH,
        "host": "oseu2015026.homeoffice.wal-mart.com",
        "port": 22,
        "description": "Legacy SSH bastion host for network device access (deprecated, use Oser jumpbox)",
        "region": "Walmart On-Prem",
        "auth_method": "AD Password",
        "note": "Use NRE Oser Jumpbox instead for proper TACACS+ support",
    },
    "nre_gcloud_us_central": {
        "name": "NRE Google Cloud Bastion (US Central)",
        "type": BASTION_TYPE_GCLOUD,
        "instance_name": "jumphost-group-6184",
        "zone": "us-central1-a",
        "project": "wmt-network-prod",
        "description": "Google Cloud bastion for accessing private VPC resources",
        "region": "us-central1",
        "auth_method": "gcloud auth",
    },
    "nre_gcloud_us_west": {
        "name": "NRE Google Cloud Bastion (US West)",
        "type": BASTION_TYPE_GCLOUD,
        "instance_name": "jumphost-group-6185",
        "zone": "us-west1-a",
        "project": "wmt-network-prod",
        "description": "Google Cloud bastion for US West private resources",
        "region": "us-west1",
        "auth_method": "gcloud auth",
    },
}

SSH_CONFIG = {
    "timeout": 30,
    "connect_timeout": 10,
    "command_timeout": 15,
    "retry_count": 3,
    "retry_delay": 2,
    "strict_host_key": False,
}

GCLOUD_CONFIG = {
    "use_internal_ip": True,
    "ssh_key_location": "~/.ssh/id_rsa",
    "tunnel_timeout": 30,
}

DEVICE_SSH_CONFIG = {
    "default_username": "neteng",
    "usernames": [
        "neteng",
        "admin",
        "netman",
        "svc_netman",
        "bvneteng",
        "bootstrap",
        "vendor",
        "nettitansvc",
        "gec_netengmonitor",
        "svc_netengmonitor",
    ],
    "auth_method": "password",
    "port": 22,
}

AUTH_METHODS = {
    "password": {
        "description": "AD Password (via jump host)",
        "mfa_required": False,
        "note": "Direct password authentication through bastion",
    },
    "key": {
        "description": "SSH Key-based Authentication",
        "mfa_required": False,
        "note": "Uses SSH keys stored locally",
    },
    "gcloud_auth": {
        "description": "Google Cloud Authentication (gcloud CLI)",
        "mfa_required": True,
        "note": "Requires 'gcloud auth login' setup, uses MFA if configured",
    },
    "tacacs_ise": {
        "description": "TACACS+ via Cisco ISE (Enterprise)",
        "mfa_required": True,
        "note": "Uses RSA SecureID token + 8-digit PIN",
    },
}

DEVICE_CONNECTION_METHODS = {
    "ssh_bastion": {
        "name": "SSH via Bastion Host",
        "description": "SSH tunnel through jump host to device",
        "command": "ssh -o StrictHostKeyChecking=no {user}@{device_ip}",
        "requires_bastion": True,
    },
    "direct_ssh": {
        "name": "Direct SSH (if accessible)",
        "description": "Direct SSH without bastion",
        "command": "ssh -o StrictHostKeyChecking=no {user}@{device_ip}",
        "requires_bastion": False,
    },
    "serial_console": {
        "name": "Serial Console via iDRAC",
        "description": "Out-of-band access via Dell iDRAC",
        "note": "Requires iDRAC credentials",
        "requires_bastion": False,
    },
}

COMMAND_METHODS = {
    "ssh_command": {
        "name": "SSH Command Execution",
        "description": "Execute show commands via SSH",
        "timeout": 15,
    },
    "expect_interactive": {
        "name": "Interactive Shell (Expect)",
        "description": "Full interactive terminal via Expect",
        "timeout": 60,
    },
}

DEFAULT_BASTION = "nre_traditional"
DEFAULT_DEVICE_TIMEOUT = 15
DEFAULT_RETRIES = 3

LOGGING_CONFIG = {
    "log_ssh_commands": True,
    "log_file_path": "~/.titan_menu/ssh_logs/",
    "log_level": "INFO",
    "audit_trail": True,
}

FEATURES = {
    "enable_mfa_prompt": True,
    "enable_key_auth": True,
    "enable_gcloud": True,
    "enable_tacacs": False,
    "enable_logging": True,
    "enable_audit": True,
}

CISCO_ISE_CONFIG = {
    "enabled": False,
    "servers": [
    ],
    "tacacs_port": 49,
    "fallback_to_local": True,
}
