"""
Main entry point for Titan Database Interactive Menu.
"""

import sys
import getpass
from .queries import TitanQueries
from .display import print_results, export_csv, show_main_menu, print_banner


def main():
    """Main interactive menu."""
    print_banner()
    
    print("\nPlease login with your AD credentials:")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    
    tq = TitanQueries(username, password)
    if not tq.connect():
        print("[!] Failed to connect. Exiting.\n")
        sys.exit(1)
    
    last_results = []
    current_device = None
    data_availability = None
    device_info_result = None
    
    try:
        while True:
            if not current_device:
                print("\n" + "="*60)
                device_input = input("Enter device name (or 'search' to search): ").strip()
                
                if device_input.lower() == 'search':
                    search_term = input("Enter search term: ").strip()
                    devices = tq.search_devices(search_term)
                    
                    if devices:
                        print_results(devices, f"Search Results for '{search_term}'")
                        device_input = input("\nEnter device name from results: ").strip()
                    else:
                        continue
                
                current_device = device_input
                print(f"\n[*] Current device: {current_device}")
                print("[*] Fetching device information...")
                
                device_info_result = tq.get_device_header_info(current_device)
                
                print("[*] Checking data availability...")
                data_availability = tq.check_data_availability(current_device)
                print("[+] Ready!")
            
            show_main_menu(data_availability, device_info_result)
            choice = input("\nSelect option (0-14): ").strip()
            
            if choice == '0':
                print("\n[*] Exiting...")
                break
            
            elif choice == '1':
                data = tq.get_node_info(current_device)
                print_results(data, f"Device Information: {current_device}", vertical=True)
                last_results = data
            
            elif choice == '2':
                data = tq.get_inventory(current_device)
                print_results(data, f"Hardware Inventory: {current_device}")
                last_results = data
            
            elif choice == '3':
                data = tq.get_interfaces(current_device)
                print_results(data, f"All Interfaces: {current_device}")
                last_results = data
            
            elif choice == '4':
                data = tq.get_interfaces(current_device, state='up')
                print_results(data, f"UP Interfaces: {current_device}")
                last_results = data
            
            elif choice == '5':
                data = tq.get_interfaces(current_device, state='down')
                print_results(data, f"DOWN Interfaces: {current_device}")
                last_results = data
            
            elif choice == '6':
                data = tq.get_interface_stats(current_device)
                print_results(data, f"Interface Statistics: {current_device}")
                last_results = data
            
            elif choice == '7':
                data = tq.get_neighbors(current_device)
                print_results(data, f"L2 Neighbors: {current_device}")
                last_results = data
            
            elif choice == '8':
                data = tq.get_circuits(current_device)
                print_results(data, f"Circuit Interfaces: {current_device}")
                last_results = data
            
            elif choice == '9':
                data = tq.get_ospf_neighbors(current_device)
                print_results(data, f"OSPF Neighbors: {current_device}")
                last_results = data
            
            elif choice == '10':
                data = tq.get_isis_circuits(current_device)
                print_results(data, f"IS-IS Circuits: {current_device}")
                last_results = data
            
            elif choice == '11':
                data = tq.get_ip_sla(current_device)
                if data:
                    print_results(data, f"IP SLA Performance (Last 24h): {current_device}")
                    last_results = data
                else:
                    print("\n[!] No IP SLA data found for this device's site\n")
            
            elif choice == '12':
                current_device = None
                data_availability = None
                device_info_result = None
                continue
            
            elif choice == '13':
                if last_results:
                    filename = input("Enter filename (e.g., output.csv): ").strip()
                    if filename:
                        export_csv(last_results, filename)
                else:
                    print("\n[!] No results to export\n")
            
            elif choice == '14':
                try:
                    from .nre_jumpbox import NREJumpbox, prompt_for_jumpbox_credentials
                    
                    device_os = device_info_result.get('os', 'Unknown')
                    device_mgmt_ip = device_info_result.get('mgmt_ip', 'N/A')
                    
                    print(f"\n" + "="*70)
                    print(f"NRE Jumpbox - Interactive Bash Shell")
                    print(f"="*70)
                    
                    if device_mgmt_ip != 'N/A':
                        print(f"\nTarget Device: {current_device}")
                        print(f"Management IP: {device_mgmt_ip}")
                        print(f"OS Type: {device_os}")
                    
                    print(f"\n[*] Connecting to oser500521 jumpbox...")
                    
                    jb_username, jb_password = prompt_for_jumpbox_credentials()
                    
                    jumpbox = NREJumpbox(jb_username, jb_password)
                    
                    if not jumpbox.connect():
                        print("\n[!] Failed to connect to jumpbox.\n")
                        continue
                    
                    print(f"\n[+] Jumpbox connection established!")
                    print(f"[*] You now have an interactive bash shell")
                    
                    if device_mgmt_ip != 'N/A':
                        print(f"[*] To SSH to {current_device}:")
                        print(f"    ssh neteng@{device_mgmt_ip}")
                        print(f"    OR: ssh <username>@{device_mgmt_ip}")
                    
                    print(f"[*] Type 'exit' or 'logout' to close\n")
                    
                    jumpbox.start_interactive_shell()
                    
                    jumpbox.disconnect()
                    print(f"\n[+] Jumpbox session closed\n")
                
                except ImportError as e:
                    print(f"\n[!] SSH module not available: {e}\n")
                except Exception as e:
                    print(f"\n[!] Error: {e}\n")
            
            else:
                print("\n[!] Invalid option. Please try again.\n")
            
            input("\nPress Enter to continue...")
    
    finally:
        tq.disconnect()


if __name__ == "__main__":
    main()
