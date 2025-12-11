"""
SSH Configuration for Titan Remote Command Execution

Stores default credentials, jump host info, and OS-specific commands.
"""

JUMP_HOST = "Oser500521.homeoffice.wal-mart.com"
JUMP_HOST_FALLBACK = "Oser500522.homeoffice.wal-mart.com"
JUMP_HOST_PORT = 22

TACASC_PASSCODE_FORMAT = "PCI_TOKEN(8) + RSA_PIN(6) = 14 chars total"
TACACS_PORT = 49
TACACS_TIMEOUT = 10

DEFAULT_USERNAMES = [
    "vn59iz6",
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
]

DEVICE_SPECIFIC_USERNAMES = {
    "cisco_ios": [
        "vn59iz6",
        "admin",
        "netadmin",
        "operator",
        "root",
        "network",
        "automation",
        "neteng",
    ],
    "arista_eos": [
        "admin",
        "automation",
        "netadmin",
        "operator",
        "neteng",
    ],
    "juniper_junos": [
        "root",
        "admin",
        "netops",
        "automation",
        "neteng",
    ],
    "sonic_cli": [
        "admin",
        "netadmin",
        "automation",
        "neteng",
    ],
}

CISCO_IOS_USERNAMES = [
    "admin",
    "root",
    "netadmin",
    "operator",
    "network",
    "monitor",
    "view",
    "automation",
    "service",
    "support",
    "neteng",
    "netman",
    "bootstrap",
]

TACACUS_USERNAMES = [
    "neteng",
    "network",
    "operations",
    "engineers",
    "administrator",
    "monitoring",
    "automation",
    "netengineer",
    "sysadmin",
]

SSH_TIMEOUT = 30
SSH_CONNECT_TIMEOUT = 10
COMMAND_TIMEOUT = 15

OS_TYPES = {
    "IOS": "cisco_ios",
    "EOS": "arista_eos",
    "JUNOS": "juniper_junos",
    "SONIC": "sonic_cli",
}

SHOW_COMMANDS = {
    "cisco_ios": {
        "version": "show version",
        "bgp_summary": "show ip bgp summary",
        "interfaces": "show interfaces brief",
        "routes": "show ip route",
        "neighbors": "show cdp neighbors brief",
    },
    "arista_eos": {
        "version": "show version",
        "bgp_summary": "show ip bgp summary",
        "interfaces": "show interfaces brief",
        "routes": "show ip route",
        "neighbors": "show lldp neighbors",
    },
    "juniper_junos": {
        "version": "show version",
        "bgp_summary": "show bgp summary",
        "interfaces": "show interfaces brief",
        "routes": "show route",
        "neighbors": "show lldp neighbors",
    },
    "sonic_cli": {
        "version": "show version",
        "bgp_summary": "show ip bgp summary",
        "interfaces": "show interfaces brief",
        "routes": "show ip route",
        "neighbors": "show lldp neighbors",
    },
}

CONNECTING_MSG = "[*] Connecting to jump host..."
CONNECTED_MSG = "[+] Connected to jump host!"
AUTH_FAILED_MSG = "[!] Authentication failed. Please check your password."
COMMAND_RUNNING_MSG = "[*] Running: {cmd}"
COMMAND_COMPLETE_MSG = "[+] Command completed"
