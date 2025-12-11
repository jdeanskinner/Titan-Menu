"""
Display and UI functions for Titan Menu.
"""

from typing import List, Dict, Optional
from tabulate import tabulate
import pandas as pd


def print_results(data: List[Dict], title: str = "", vertical: bool = False):
    """Print results in table format.
    
    Args:
        data: List of dictionaries to display
        title: Optional title for the output
        vertical: If True and single record, display as key-value pairs
    """
    if not data:
        print(f"\n[!] No results found\n")
        return
    
    print(f"\n{'='*100}")
    if title:
        print(f"{title}")
        print(f"{'='*100}")
    
    if vertical and len(data) == 1:
        print()
        record = data[0]
        max_key_len = max(len(str(k)) for k in record.keys())
        for key, value in record.items():
            if value in [None, '', 'N/A', 'unknown']:
                continue
            print(f"  {key:<{max_key_len}} : {value}")
        print()
    else:
        print(tabulate(data, headers='keys', tablefmt='grid'))
        print(f"\nTotal: {len(data)} record(s)\n")


def export_csv(data: List[Dict], filename: str):
    """Export results to CSV."""
    if not data:
        print("[!] No data to export")
        return
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"[+] Exported {len(data)} records to {filename}\n")


def show_main_menu(availability: Optional[Dict[str, int]] = None, device_info: Optional[Dict[str, str]] = None):
    """Display main menu with data availability indicators."""
    print("\n" + "="*70)
    print("TITAN DATABASE - DEVICE QUERY MENU")
    print("="*70)
    
    if device_info:
        print(f"\n📍 Device: {device_info.get('name', 'N/A')}")
        print(f"   IP: {device_info.get('mgmt_ip', 'N/A')}")
        print(f"   Status: {device_info.get('state', 'Unknown')}")
        print()
    
    def format_option(num: int, text: str, data_key: Optional[str] = None) -> str:
        """Format menu option with availability indicator."""
        if availability and data_key:
            count = availability.get(data_key, 0)
            if count > 0:
                indicator = f"[{count}]"
                return f"{num:2}. {text:50} {indicator}"
            else:
                return f"{num:2}. {text:50} [No Data]"
        return f"{num:2}. {text}"
    
    print("\n[Device Info]")
    print(format_option(1, "Device Information (Overview)"))
    print(format_option(2, "Hardware Inventory", "inventory"))
    
    print("\n[Interfaces]")
    print(format_option(3, "All Interfaces", "interfaces"))
    print(format_option(4, "UP Interfaces Only", "interfaces"))
    print(format_option(5, "DOWN Interfaces Only", "interfaces"))
    print(format_option(6, "Interface Statistics Summary", "interfaces"))
    
    print("\n[Layer 2/3]")
    print(format_option(7, "L2 Neighbors (LLDP/CDP)", "l2_neighbors"))
    print(format_option(8, "Circuit Interfaces", "circuits"))
    
    print("\n[Routing Protocols]")
    print(format_option(9, "OSPF Neighbors", "ospf"))
    print(format_option(10, "IS-IS Circuits", "isis"))
    print(format_option(11, "IP SLA Performance (Site-based)", "ip_sla"))
    
    print("\n[Remote SSH Commands]")
    print(format_option(14, "SSH Remote Command Execution"))
    
    print("\n[Actions]")
    print("12.  Search for Different Device")
    print("13.  Export Last Results to CSV")
    print(" 0.  Exit")
    print("="*70)


def print_banner():
    """Print welcome banner."""
    print("\n" + "*"*60)
    print("*** TITAN DATABASE - INTERACTIVE QUERY TOOL ***")
    print("*"*60)
