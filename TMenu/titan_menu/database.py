"""
Database connection and base query functionality for Titan DB.
"""

import socket
from typing import Optional
import psycopg2
import psycopg2.extras


class TitanDatabase:
    """
    Handles database connection and basic query execution for Titan DB.
    """
    
    def __init__(self, username: str, password: str):
        """Initialize with credentials."""
        self.username = username
        self.password = password
        self.conn = None
        self.cur = None
    
    def connect(self) -> bool:
        """Connect to Titan DB."""
        try:
            print("\n[*] Connecting to Titan DB...")
            rdbconnstr = 'dbname={0} user={1} host={2} port={3} password={4}'.format(
                'gorm',
                self.username,
                'titandb.wal-mart.com',
                '5432',
                self.password
            )
            
            self.conn = psycopg2.connect(rdbconnstr)
            self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            print("[+] Connected successfully!\n")
            return True
            
        except Exception as e:
            print(f"\n[!] Connection failed: {e}\n")
            return False
    
    def disconnect(self):
        """Close connection."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            print("\n[*] Disconnected from Titan DB\n")
    
    def ensure_connected(self) -> bool:
        """Ensure database connection is alive, reconnect if needed."""
        try:
            if self.conn is None or self.conn.closed:
                print("[*] Connection lost, reconnecting...")
                return self.connect()
            self.cur.execute("SELECT 1")
            return True
        except Exception:
            print("[*] Connection lost, reconnecting...")
            return self.connect()
    
    def validate_node(self, node: str) -> str:
        """Validate and return best matching node from database."""
        query = """
            SELECT fqdn, name, state
            FROM node 
            WHERE fqdn ILIKE %s OR name ILIKE %s
            ORDER BY 
                -- First, exclude devices with '.old' or '-old' in name/fqdn
                CASE 
                    WHEN name ILIKE '%.old%' OR fqdn ILIKE '%.old%' THEN 3
                    WHEN name ILIKE '%-old%' OR fqdn ILIKE '%-old%' THEN 3
                    ELSE 1
                END,
                -- Then prioritize exact matches
                CASE 
                    WHEN name = %s THEN 1
                    WHEN fqdn = %s THEN 2
                    WHEN name ILIKE %s THEN 3
                    ELSE 4
                END,
                -- Finally prioritize online devices over offline/decommissioned
                CASE 
                    WHEN state = 'online' THEN 1
                    WHEN state = 'offline' THEN 2
                    WHEN state = 'decommissioned' THEN 3
                    ELSE 4
                END
            LIMIT 1
        """
        
        try:
            self.cur.execute(query, (f'%{node}%', f'%{node}%', node, f'{node}.wal-mart.com.', node))
            result = self.cur.fetchone()
            
            if result:
                return result[0]
        except Exception:
            pass
        

        if '/' not in node[-3:]:
            try:
                name = socket.gethostbyaddr(node)
                node = name[0]
                node = node.split('.')[0].split('_')[0]
            except:
                pass
        
        return node
