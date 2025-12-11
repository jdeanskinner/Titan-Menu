"""
SSH Command Output Parsers for Different Network OS Types

Parsers for Cisco IOS, Arista EOS, Juniper JUNOS, and Sonic CLI output.
"""

import re
from typing import Dict, List, Optional


class OutputParser:
    """
    Base class for parsing network device command output.
    """
    
    @staticmethod
    def parse_show_version(output: str, os_type: str) -> Dict:
        """
        Parse show version output based on OS type.
        
        Args:
            output: Raw command output
            os_type: Device OS type (cisco_ios, arista_eos, etc.)
            
        Returns:
            Dictionary with parsed version info
        """
        if os_type == "cisco_ios":
            return OutputParser._parse_cisco_version(output)
        elif os_type == "arista_eos":
            return OutputParser._parse_arista_version(output)
        elif os_type == "juniper_junos":
            return OutputParser._parse_juniper_version(output)
        elif os_type == "sonic_cli":
            return OutputParser._parse_sonic_version(output)
        else:
            return {"raw_output": output}
    
    @staticmethod
    def parse_bgp_summary(output: str, os_type: str) -> Dict:
        """
        Parse BGP summary output based on OS type.
        
        Args:
            output: Raw command output
            os_type: Device OS type
            
        Returns:
            Dictionary with parsed BGP info
        """
        if os_type == "cisco_ios":
            return OutputParser._parse_cisco_bgp(output)
        elif os_type == "arista_eos":
            return OutputParser._parse_arista_bgp(output)
        elif os_type == "juniper_junos":
            return OutputParser._parse_juniper_bgp(output)
        elif os_type == "sonic_cli":
            return OutputParser._parse_sonic_bgp(output)
        else:
            return {"raw_output": output}
    
    @staticmethod
    def _parse_cisco_version(output: str) -> Dict:
        """Parse Cisco IOS show version output."""
        data = {}
        
        model_match = re.search(r"Cisco (.*?) Software", output)
        if model_match:
            data["Model"] = model_match.group(1).strip()
        
        version_match = re.search(r"Version\s+([\d.]+)", output)
        if version_match:
            data["IOS_Version"] = version_match.group(1)
        
        uptime_match = re.search(r"uptime is (.+)$", output, re.MULTILINE)
        if uptime_match:
            data["Uptime"] = uptime_match.group(1).strip()
        
        serial_match = re.search(r"Serial Number\s*:\s*([A-Z0-9]+)", output)
        if serial_match:
            data["Serial"] = serial_match.group(1)
        
        return data or {"raw_output": output[:500]}
    
    @staticmethod
    def _parse_cisco_bgp(output: str) -> Dict:
        """Parse Cisco IOS show ip bgp summary output."""
        data = {}
        lines = output.split("\n")
        
        for line in lines:
            if "BGP router identifier" in line:
                match = re.search(r"([0-9.]+),", line)
                if match:
                    data["Router_ID"] = match.group(1)
        
        neighbor_count = 0
        for line in lines:
            if "neighbor" in line.lower() and ("up" in line.lower() or "down" in line.lower()):
                neighbor_count += 1
        
        if neighbor_count > 0:
            data["BGP_Neighbors"] = neighbor_count
        
        return data or {"raw_output": output[:500]}
    
    @staticmethod
    def _parse_arista_version(output: str) -> Dict:
        """Parse Arista EOS show version output."""
        data = {}
        lines = output.split("\n")
        
        for line in lines:
            if "Model:" in line:
                data["Model"] = line.split(":")[1].strip()
            elif "System uptime:" in line:
                data["Uptime"] = line.split(":")[1].strip()
            elif "Software image version:" in line:
                data["EOS_Version"] = line.split(":")[1].strip()
            elif "Serial number:" in line:
                data["Serial"] = line.split(":")[1].strip()
        
        return data or {"raw_output": output[:500]}
    
    @staticmethod
    def _parse_arista_bgp(output: str) -> Dict:
        """Parse Arista EOS show ip bgp summary output."""
        data = {}
        lines = output.split("\n")
        
        for line in lines:
            if "BGP summary" in line:
                match = re.search(r"AS (\d+)", line)
                if match:
                    data["AS_Number"] = match.group(1)
        
        neighbor_count = 0
        for line in lines:
            if re.match(r"^\s*\d+\.\d+\.\d+\.\d+", line):
                neighbor_count += 1
        
        if neighbor_count > 0:
            data["BGP_Neighbors"] = neighbor_count
        
        return data or {"raw_output": output[:500]}
    
    @staticmethod
    def _parse_juniper_version(output: str) -> Dict:
        """Parse Juniper JUNOS show version output."""
        data = {}
        lines = output.split("\n")
        
        for line in lines:
            if "Model:" in line:
                data["Model"] = line.split(":")[1].strip()
            elif "JUNOS Software Release" in line:
                match = re.search(r"Release\s+([\d.]+)", line)
                if match:
                    data["JUNOS_Version"] = match.group(1)
            elif "Serial ID:" in line:
                data["Serial"] = line.split(":")[1].strip()
        
        return data or {"raw_output": output[:500]}
    
    @staticmethod
    def _parse_juniper_bgp(output: str) -> Dict:
        """Parse Juniper JUNOS show bgp summary output."""
        data = {}
        lines = output.split("\n")
        
        for line in lines:
            if "Router ID:" in line:
                data["Router_ID"] = line.split(":")[1].strip()
            elif "Local AS:" in line:
                data["AS_Number"] = line.split(":")[1].strip()
        
        return data or {"raw_output": output[:500]}
    
    @staticmethod
    def _parse_sonic_version(output: str) -> Dict:
        """Parse Sonic CLI show version output."""
        data = {}
        lines = output.split("\n")
        
        for line in lines:
            if "Platform:" in line:
                data["Platform"] = line.split(":")[1].strip()
            elif "SONiC Software Version:" in line:
                data["Sonic_Version"] = line.split(":")[1].strip()
            elif "System uptime:" in line:
                data["Uptime"] = line.split(":")[1].strip()
        
        return data or {"raw_output": output[:500]}
    
    @staticmethod
    def _parse_sonic_bgp(output: str) -> Dict:
        """Parse Sonic CLI show ip bgp summary output."""
        data = {}
        lines = output.split("\n")
        
        neighbor_count = 0
        for line in lines:
            if re.match(r"^\s*\d+\.\d+\.\d+\.\d+", line):
                neighbor_count += 1
        
        if neighbor_count > 0:
            data["BGP_Neighbors"] = neighbor_count
        
        return data or {"raw_output": output[:500]}
    
    @staticmethod
    def format_output(parsed_data: Dict) -> str:
        """
        Format parsed output for display.
        
        Args:
            parsed_data: Dictionary of parsed output
            
        Returns:
            Formatted string for console display
        """
        if not parsed_data:
            return "No output"
        
        lines = []
        for key, value in parsed_data.items():
            if key != "raw_output":
                lines.append(f"  {key:20} : {value}")
        
        if "raw_output" in parsed_data and not lines:
            lines.append(parsed_data["raw_output"])
        
        return "\n".join(lines) if lines else "No data parsed"
