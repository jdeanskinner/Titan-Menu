"""
Query methods for Titan DB device information.
"""

from typing import List, Dict, Optional
from .database import TitanDatabase


class TitanQueries(TitanDatabase):
    """
    Query handler for Titan DB - extends TitanDatabase with query methods.
    """
    
    def __init__(self, username: str, password: str):
        """Initialize with credentials."""
        super().__init__(username, password)
        self.current_device = None
    
    def get_node_info(self, node: str) -> List[Dict]:
        """Query general node information."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        query = """
            SELECT 
                n.name,
                n.fqdn,
                n.mgmt_ip,
                n.serial,
                n.model_name,
                n.state,
                o.os,
                o.platform,
                o.version,
                s.name as site_name,
                s.address,
                s.city,
                s.state as site_state,
                s.country_code
            FROM node n
            LEFT JOIN os o ON n.os_id = o.id
            LEFT JOIN site s ON n.site_id = s.id
            WHERE n.fqdn ILIKE %s OR n.name ILIKE %s
        """
        
        self.cur.execute(query, (f'%{node}%', f'%{node}%'))
        results = self.cur.fetchall()
        
        data = []
        for row in results:

            fqdn = row[1].rstrip('.') if row[1] else 'N/A'
            
            data.append({
                'Name': row[0] or 'N/A',
                'FQDN': fqdn,
                'Management_IP': row[2] or 'N/A',
                'Serial': row[3] or 'N/A',
                'Model': row[4] or 'N/A',
                'Device_State': row[5] or 'unknown',
                'OS': row[6] or 'N/A',
                'OS_Version': row[8] or 'N/A',
                'Site_ID': row[9] or 'N/A',
                'Site_Address': row[10] or 'N/A',
                'City': row[11] or 'N/A',
                'State': row[12] or 'N/A',
                'Country': row[13] or 'N/A'
            })
        
        return data
    
    def get_interfaces(self, node: str, state: Optional[str] = None) -> List[Dict]:
        """Query interface information."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        query = """
            SELECT DISTINCT 
                interface.name, 
                interface.link_speed, 
                interface.state,
                interface.description
            FROM interface
            JOIN node ON node.id = interface.node_id
            WHERE node.fqdn ILIKE %s
        """
        
        params = [f'%{node}%']
        
        if state:
            query += " AND interface.state = %s"
            params.append(state)
        
        query += " ORDER BY interface.name"
        
        self.cur.execute(query, params)
        results = self.cur.fetchall()
        
        data = []
        for row in results:
            data.append({
                'Interface': row[0],
                'Speed': row[1] or 0,
                'Oper_State': row[2],
                'Description': row[3] or ''
            })
        
        return data
    
    def get_inventory(self, node: str) -> List[Dict]:
        """Query hardware inventory."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        try:
            query = """
                SELECT 
                    ni.name,
                    ni.description,
                    ni.serial_number
                FROM node_inventory ni
                JOIN node n ON n.id = ni.node_id
                WHERE n.fqdn ILIKE %s OR n.name ILIKE %s
                ORDER BY ni.name
            """
            
            self.cur.execute(query, (f'%{node}%', f'%{node}%'))
            results = self.cur.fetchall()
            
            data = []
            for row in results:
                desc = row[1] or ''
                data.append({
                    'Component': row[0],
                    'Description': (desc[:50] + '...') if len(desc) > 50 else desc,
                    'Serial': row[2] or ''
                })
            
            return data
        except Exception as e:
            print(f"[!] Inventory query failed: {e}")
            if self.conn:
                self.conn.rollback()
            return []
    
    def get_neighbors(self, node: str) -> List[Dict]:
        """Query L2 neighbor information from l2_neighbor table."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        try:
            query = """
                SELECT DISTINCT
                    l2.local_interface_name,
                    l2.system_name,
                    l2.remote_interface_name,
                    l2.management_address,
                    CASE WHEN l2.lldp THEN 'LLDP' WHEN l2.cdp THEN 'CDP' ELSE 'Other' END as protocol
                FROM l2_neighbor l2
                JOIN node n ON n.id = l2.node_id
                WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)
                AND l2.deleted_at IS NULL
                ORDER BY l2.local_interface_name
            """
            
            self.cur.execute(query, (f'%{node}%', f'%{node}%'))
            results = self.cur.fetchall()
            
            data = []
            for row in results:

                neighbor = row[1] or ''
                if '(' in neighbor:
                    neighbor = neighbor.split('(')[0].strip()
                if '.wal-mart.com' in neighbor:
                    neighbor = neighbor.replace('.wal-mart.com', '')
                if '.homeoffice.wal-mart.com' in neighbor:
                    neighbor = neighbor.replace('.homeoffice.wal-mart.com', '')
                if '.mgt.wal-mart.com' in neighbor:
                    neighbor = neighbor.replace('.mgt.wal-mart.com', '')
                
                data.append({
                    'Local_Port': row[0] or '',
                    'Neighbor': neighbor,
                    'Remote_Port': row[2] or '',
                    'IP': row[3] or '',
                    'Type': row[4]
                })
            
            return data
        except Exception as e:
            print(f"[!] L2 Neighbor query failed: {e}")
            if self.conn:
                self.conn.rollback()
            return []
    
    def get_interface_stats(self, node: str) -> List[Dict]:
        """Get interface statistics summary."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        query = """
            SELECT 
                interface.state,
                COUNT(*) as count
            FROM interface
            JOIN node ON node.id = interface.node_id
            WHERE node.fqdn ILIKE %s
            GROUP BY interface.state
            ORDER BY count DESC
        """
        
        self.cur.execute(query, (f'%{node}%',))
        results = self.cur.fetchall()
        
        data = []
        for row in results:
            data.append({
                'State': row[0],
                'Count': row[1]
            })
        
        return data
    
    def get_circuits(self, node: str) -> List[Dict]:
        """Query circuits using circuit and circuit_interface tables."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        try:
            query = """
                SELECT DISTINCT
                    i.name as interface_name,
                    i.link_speed,
                    i.state,
                    c.vendor_circuit_id,
                    c.speed as circuit_speed,
                    i.description
                FROM interface i
                JOIN circuit_interface ci ON ci.interface_id = i.id
                JOIN circuit c ON c.id = ci.circuit_id
                JOIN node n ON n.id = i.node_id
                WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)
                ORDER BY i.name
            """
            
            self.cur.execute(query, (f'%{node}%', f'%{node}%'))
            results = self.cur.fetchall()
            
            print(f"[DEBUG] Circuit table query returned {len(results)} rows")
            
            if results:
                data = []
                for row in results:
                    desc = row[5] or ''

                    vrf = ''
                    if 'VRF:' in desc:
                        vrf_part = desc.split('VRF:')[1].split()[0] if 'VRF:' in desc else ''
                        vrf = vrf_part
                    

                    speed_mbps = int(row[1] / 1000) if row[1] else 0
                    
                    data.append({
                        'Interface': row[0],
                        'Speed_Mbps': speed_mbps,
                        'State': row[2],
                        'Circuit_ID': row[3] or '',
                        'VRF': vrf,
                        'Description': desc
                    })
                return data
            else:

                print("[*] No circuits found in circuit table, searching interface descriptions...\n")
                query2 = """
                    SELECT DISTINCT 
                        interface.name, 
                        interface.short_name, 
                        interface.link_speed, 
                        interface.state, 
                        interface.state_start,
                        interface.description
                    FROM interface
                    JOIN node ON node.id = interface.node_id
                    WHERE (node.fqdn ILIKE %s OR node.name ILIKE %s)
                    AND interface.description ILIKE '%%CID:%%'
                    ORDER BY interface.name
                """
                
                self.cur.execute(query2, (f'%{node}%', f'%{node}%'))
                results2 = self.cur.fetchall()
                
                print(f"[DEBUG] Description search returned {len(results2)} rows")
                
                data = []
                for row in results2:
                    description = row[5] or ""
                    cid = ""
                    vrf = ''
                    
                    if "CID:" in description.upper():
                        parts = description.upper().split("CID:")
                        if len(parts) > 1:
                            cid = parts[1].strip().split()[0] if parts[1].strip() else ""
                    
                    if 'VRF:' in description:
                        vrf_part = description.split('VRF:')[1].split()[0] if 'VRF:' in description else ''
                        vrf = vrf_part
                    

                    speed_mbps = int(row[2] / 1000) if row[2] else 0
                    
                    data.append({
                        'Interface': row[0],
                        'Speed_Mbps': speed_mbps,
                        'State': row[3],
                        'Circuit_ID': cid,
                        'VRF': vrf,
                        'Description': description
                    })
                
                return data
                
        except Exception as e:
            print(f"[!] Circuit query failed: {e}")
            if self.conn:
                self.conn.rollback()
            return []
    
    def get_bgp_info(self, node: str) -> List[Dict]:
        """Query BGP information from bgp_stats table."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        try:
            query = """
                SELECT 
                    bs.ip,
                    bs.as_num,
                    bs.state,
                    bs.accepted_pfx,
                    bs.advertised_pfx,
                    bs.denied_pfx,
                    bs.time
                FROM bgp_stats bs
                JOIN node n ON n.id = bs.node_id
                WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)
                ORDER BY bs.ip
            """
            
            self.cur.execute(query, (f'%{node}%', f'%{node}%'))
            results = self.cur.fetchall()
            
            data = []
            for row in results:
                data.append({
                    'Peer_IP': row[0] or '',
                    'AS_Number': row[1] or 0,
                    'State': row[2] or '',
                    'Accepted_Prefixes': row[3] or 0,
                    'Advertised_Prefixes': row[4] or 0,
                    'Denied_Prefixes': row[5] or 0,
                    'Timestamp': row[6].strftime("%Y-%m-%d %H:%M:%S") if row[6] else ''
                })
            
            return data
        except Exception as e:
            print(f"[!] BGP query failed: {e}")
            if self.conn:
                self.conn.rollback()
            return []
    
    def get_ospf_neighbors(self, node: str) -> List[Dict]:
        """Query OSPF neighbor information."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        try:
            query = """
                SELECT 
                    ospf.router_id,
                    ospf.ip,
                    ospf.state,
                    ospf.priority,
                    ospf.state_start
                FROM ospf_neighbor ospf
                JOIN ospf_area_interface oai ON oai.id = ospf.ospf_area_interface_id
                JOIN interface i ON i.id = oai.interface_id
                JOIN node n ON n.id = i.node_id
                WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)
                AND ospf.deleted_at IS NULL
                ORDER BY ospf.ip
            """
            
            self.cur.execute(query, (f'%{node}%', f'%{node}%'))
            results = self.cur.fetchall()
            
            data = []
            for row in results:
                data.append({
                    'Router_ID': str(row[0]) if row[0] else '',
                    'IP_Address': str(row[1]) if row[1] else '',
                    'State': row[2] or '',
                    'Priority': row[3] or 0,
                    'State_Start': row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else ''
                })
            
            return data
        except Exception as e:
            print(f"[!] OSPF query failed: {e}")
            if self.conn:
                self.conn.rollback()
            return []
    
    def get_isis_circuits(self, node: str) -> List[Dict]:
        """Query IS-IS circuit information."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        try:
            query = """
                SELECT 
                    i.name as interface_name,
                    isis.state,
                    isis.type,
                    isis.level_type,
                    isis.is_passive,
                    isis.state_start
                FROM isis_circuit isis
                JOIN interface i ON i.id = isis.interface_id
                JOIN node n ON n.id = i.node_id
                WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)
                AND isis.deleted_at IS NULL
                ORDER BY i.name
            """
            
            self.cur.execute(query, (f'%{node}%', f'%{node}%'))
            results = self.cur.fetchall()
            
            data = []
            for row in results:
                data.append({
                    'Interface': row[0] or '',
                    'State': row[1] or '',
                    'Type': row[2] or '',
                    'Level': row[3] or '',
                    'Passive': 'Yes' if row[4] else 'No',
                    'State_Start': row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else ''
                })
            
            return data
        except Exception as e:
            print(f"[!] IS-IS query failed: {e}")
            if self.conn:
                self.conn.rollback()
            return []
    
    def get_ip_sla(self, node: str, hours_back: int = 24) -> List[Dict]:
        """Query IP SLA data (latency/performance metrics).
        
        Note: IP SLA is site-based, so this returns SLA data for the device's site.
        """
        self.ensure_connected()
        node = self.validate_node(node)
        
        try:

            site_query = """
                SELECT DISTINCT n.site_id, s.name as site_name
                FROM node n
                LEFT JOIN site s ON s.id = n.site_id
                WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)
                LIMIT 1
            """
            
            self.cur.execute(site_query, (f'%{node}%', f'%{node}%'))
            site_result = self.cur.fetchone()
            
            if not site_result or not site_result[0]:
                print(f"[!] No site found for device {node}")
                return []
            
            site_id = site_result[0]
            site_name = site_result[1] or 'Unknown'
            

            query = """
                SELECT 
                    sla.name,
                    sla.destination,
                    sla.rtt_total,
                    sla.rtt_dns,
                    sla.rtt_tcp,
                    sla.rtt_status,
                    sla.admin_status,
                    sla.time
                FROM ip_sla sla
                WHERE sla.site_id = %s
                AND sla.time > NOW() - interval '%s hours'
                ORDER BY sla.time DESC
                LIMIT 100
            """
            
            self.cur.execute(query, (site_id, hours_back))
            results = self.cur.fetchall()
            
            data = []
            for row in results:
                data.append({
                    'SLA_Name': row[0] or '',
                    'Destination': str(row[1]) if row[1] else '',
                    'RTT_Total': f"{row[2]}ms" if row[2] else 'N/A',
                    'RTT_DNS': f"{row[3]}ms" if row[3] else 'N/A',
                    'RTT_TCP': f"{row[4]}ms" if row[4] else 'N/A',
                    'Status': row[5] or '',
                    'Admin_Status': row[6] or '',
                    'Timestamp': row[7].strftime("%Y-%m-%d %H:%M:%S") if row[7] else '',
                    'Site': site_name
                })
            
            return data
        except Exception as e:
            print(f"[!] IP SLA query failed: {e}")
            if self.conn:
                self.conn.rollback()
            return []
    
    def get_interface_metrics(self, node: str) -> List[Dict]:
        """Query interface performance metrics."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        try:
            query = """
                SELECT 
                    i.name as interface_name,
                    im.tx_bytes,
                    im.rx_bytes,
                    im.tx_errors,
                    im.rx_errors,
                    im.tx_drops,
                    im.rx_drops,
                    im.speed,
                    im.time
                FROM interface_metrics im
                JOIN interface i ON i.id = im.interface_id
                JOIN node n ON n.id = i.node_id
                WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)
                AND i.state = 'up'
                ORDER BY im.rx_bytes DESC
                LIMIT 50
            """
            
            self.cur.execute(query, (f'%{node}%', f'%{node}%'))
            results = self.cur.fetchall()
            
            data = []
            for row in results:
                data.append({
                    'Interface': row[0],
                    'TX_Bytes': f"{row[1]:,}" if row[1] else '0',
                    'RX_Bytes': f"{row[2]:,}" if row[2] else '0',
                    'TX_Errors': row[3] or 0,
                    'RX_Errors': row[4] or 0,
                    'TX_Drops': row[5] or 0,
                    'RX_Drops': row[6] or 0,
                    'Speed': row[7] or 0,
                    'Timestamp': row[8].strftime("%Y-%m-%d %H:%M:%S") if row[8] else ''
                })
            
            return data
        except Exception as e:
            print(f"[!] Interface metrics query failed: {e}")
            if self.conn:
                self.conn.rollback()
            return []
    
    def get_device_header_info(self, node: str) -> Dict[str, str]:
        """Get basic device info for menu header display."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        try:
            clean_node = node.replace('.wal-mart.com', '').replace('.homeoffice.wal-mart.com', '').replace('.mgt.wal-mart.com', '').rstrip('.')
            
            query = """
                SELECT 
                    n.name,
                    n.mgmt_ip,
                    n.state
                FROM node n
                WHERE n.fqdn ILIKE %s OR n.name ILIKE %s OR n.fqdn ILIKE %s
                ORDER BY 
                    CASE 
                        WHEN n.name = %s THEN 1
                        WHEN n.fqdn ILIKE %s THEN 2
                        ELSE 3
                    END
                LIMIT 1
            """
            

            self.cur.execute(query, (
                f'{clean_node}.wal-mart.com%',
                clean_node,
                f'%{clean_node}%',
                clean_node,
                f'{clean_node}.wal-mart.com%'
            ))
            result = self.cur.fetchone()
            
            if result:

                state = result[2] or 'unknown'
                if state.lower() == 'online':
                    state_display = '🟢 Online'
                elif state.lower() == 'offline':
                    state_display = '🔴 Offline'
                elif state.lower() == 'decommissioned':
                    state_display = '⚫ Decommissioned'
                else:
                    state_display = f'⚪ {state.title()}'
                
                return {
                    'name': result[0] or 'Unknown',
                    'mgmt_ip': result[1] or 'N/A',
                    'state': state_display
                }
            else:
                return {'name': node, 'mgmt_ip': 'N/A', 'state': '⚪ Unknown'}
        except Exception as e:
            print(f"[!] Failed to get device info: {e}")
            if self.conn:
                self.conn.rollback()
            return {'name': node, 'mgmt_ip': 'N/A', 'state': '⚪ Unknown'}
    
    def check_data_availability(self, node: str) -> Dict[str, int]:
        """Check what data is available for a device."""
        self.ensure_connected()
        node = self.validate_node(node)
        
        availability = {}
        
        checks = [
            ('interfaces', 'SELECT COUNT(*) FROM interface i JOIN node n ON n.id = i.node_id WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)'),
            ('inventory', 'SELECT COUNT(*) FROM node_inventory ni JOIN node n ON n.id = ni.node_id WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)'),
            ('interface_metrics', 'SELECT COUNT(*) FROM interface_metrics im JOIN interface i ON i.id = im.interface_id JOIN node n ON n.id = i.node_id WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)'),
            ('l2_neighbors', 'SELECT COUNT(*) FROM l2_neighbor l2 JOIN node n ON n.id = l2.node_id WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s) AND l2.deleted_at IS NULL'),
            ('ospf', 'SELECT COUNT(*) FROM ospf_neighbor o JOIN ospf_area_interface oai ON oai.id = o.ospf_area_interface_id JOIN interface i ON i.id = oai.interface_id JOIN node n ON n.id = i.node_id WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s) AND o.deleted_at IS NULL'),
            ('isis', 'SELECT COUNT(*) FROM isis_circuit isis JOIN interface i ON i.id = isis.interface_id JOIN node n ON n.id = i.node_id WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s) AND isis.deleted_at IS NULL'),
        ]
        
        for key, query in checks:
            try:
                self.cur.execute(query, (f'%{node}%', f'%{node}%'))
                count = self.cur.fetchone()[0]
                availability[key] = count
            except Exception as e:
                availability[key] = 0
                if self.conn:
                    self.conn.rollback()
        
        try:
            circuit_query = 'SELECT COUNT(*) FROM circuit_interface ci JOIN interface i ON i.id = ci.interface_id JOIN node n ON n.id = i.node_id WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s)'
            self.cur.execute(circuit_query, (f'%{node}%', f'%{node}%'))
            circuit_count = self.cur.fetchone()[0]
            print(f"[DEBUG] Circuit table count: {circuit_count} for node: {node}")
            
            if circuit_count == 0:
                cid_query = "SELECT COUNT(*) FROM interface i JOIN node n ON n.id = i.node_id WHERE (n.fqdn ILIKE %s OR n.name ILIKE %s) AND i.description ILIKE '%%CID:%%'"
                self.cur.execute(cid_query, (f'%{node}%', f'%{node}%'))
                circuit_count = self.cur.fetchone()[0]
                print(f"[DEBUG] CID description count: {circuit_count} for node: {node}")
            
            availability['circuits'] = circuit_count
        except Exception as e:
            print(f"[ERROR] Circuit availability check failed: {e}")
            availability['circuits'] = 0
            if self.conn:
                self.conn.rollback()
        
        try:
            site_query = "SELECT site_id FROM node WHERE (fqdn ILIKE %s OR name ILIKE %s) LIMIT 1"
            self.cur.execute(site_query, (f'%{node}%', f'%{node}%'))
            site_result = self.cur.fetchone()
            
            if site_result and site_result[0]:
                sla_query = "SELECT COUNT(*) FROM ip_sla WHERE site_id = %s AND time > NOW() - interval '24 hours'"
                self.cur.execute(sla_query, (site_result[0],))
                availability['ip_sla'] = self.cur.fetchone()[0]
            else:
                availability['ip_sla'] = 0
        except Exception as e:
            availability['ip_sla'] = 0
            if self.conn:
                self.conn.rollback()
        
        return availability
    
    def search_devices(self, search_term: str, limit: int = 20) -> List[Dict]:
        """Search for devices by name pattern. Includes all devices including -old versions."""
        self.ensure_connected()
        
        clean_term = search_term.replace('.wal-mart.com', '').replace('.homeoffice.wal-mart.com', '').rstrip('.')
        
        query = """
            SELECT 
                n.fqdn,
                n.name,
                n.mgmt_ip,
                n.state,
                s.name as site_name,
                s.city,
                s.state as site_state
            FROM node n
            LEFT JOIN site s ON n.site_id = s.id
            WHERE (n.name ILIKE %s OR n.fqdn ILIKE %s)
            ORDER BY 
                CASE 
                    WHEN n.name = %s THEN 1
                    WHEN n.fqdn = %s OR n.fqdn = %s THEN 2
                    WHEN n.name ILIKE %s THEN 3
                    WHEN n.fqdn ILIKE %s THEN 4
                    ELSE 5
                END,
                CASE 
                    WHEN n.state = 'online' THEN 1
                    WHEN n.state = 'offline' THEN 2
                    WHEN n.state = 'decommissioned' THEN 3
                    ELSE 4
                END,
                n.name
            LIMIT %s
        """
        params = (
            f'%{clean_term}%', f'%{clean_term}%',
            clean_term,
            f'{clean_term}.wal-mart.com.',
            f'{clean_term}.wal-mart.com',
            f'{clean_term}%',
            f'{clean_term}%',
            limit
        )
        
        self.cur.execute(query, params)
        results = self.cur.fetchall()
        
        data = []
        for row in results:

            state = row[3] or 'unknown'
            if state.lower() == 'online':
                state_display = '🟢 Online'
            elif state.lower() == 'offline':
                state_display = '🔴 Offline'
            elif state.lower() == 'decommissioned':
                state_display = '⚫ Decomm'
            else:
                state_display = f'⚪ {state.title()}'
            

            fqdn = row[0].rstrip('.') if row[0] else None
            name = row[1] or 'N/A'
            device_identifier = fqdn if fqdn else name
            
            data.append({
                'Device_FQDN': device_identifier,
                'Mgmt_IP': row[2] if row[2] else 'N/A',
                'Status': state_display,
                'Site': row[4] if row[4] else 'N/A',
                'City': row[5] if row[5] else 'N/A',
                'State': row[6] if row[6] else 'N/A'
            })
        
        return data
