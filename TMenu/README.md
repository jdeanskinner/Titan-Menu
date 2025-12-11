# Titan Menu v2.0 - Standalone Copy

This is a complete, standalone copy of the Titan Menu v2.0 application.

## Files Included

```
TMenu/
├── titan_menu_v2.py          (Main entry point)
└── titan_menu/               (Package directory)
    ├── __init__.py
    ├── database.py           (Database connection handler)
    ├── queries.py            (Query methods for Titan DB)
    ├── display.py            (UI/display functions)
    ├── main.py               (Main interactive menu loop)
    ├── bastion_config.py     (Bastion host configuration)
    ├── bastion_manager.py    (Bastion manager)
    ├── nre_jumpbox.py        (NRE Jumpbox integration)
    ├── ssh_config.py         (SSH configuration)
    ├── ssh_menu.py           (SSH menu interface)
    ├── ssh_remote.py         (Remote SSH execution)
    ├── ssh_parsers.py        (Output parsers)
    ├── superputty_config.py  (SuperPutty configuration)
    └── napa_gateway.py       (NAPA gateway integration)
```

## Running the Program

```bash
python titan_menu_v2.py
```

## Requirements

The following Python packages are required:
- psycopg2 (PostgreSQL database adapter)
- paramiko (SSH library)
- pandas (Data manipulation)
- tabulate (Table formatting)

## Installation

1. Install required packages:
   ```bash
   pip install psycopg2 paramiko pandas tabulate
   ```

2. Run the program:
   ```bash
   python titan_menu_v2.py
   ```

## Features

- Interactive menu for querying Titan Database
- Device information lookup
- Interface and neighbor discovery
- OSPF and IS-IS routing protocol queries
- IP SLA performance monitoring
- Remote SSH command execution
- Bastion host support (SSH and Google Cloud)
- SuperPutty configuration generation
