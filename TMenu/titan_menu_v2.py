"""
Titan Menu v2.0 - Main Entry Point

Modular Titan Database query tool for Walmart's network infrastructure.

Package Structure:
  titan_menu/
    ├── __init__.py      - Package exports
    ├── database.py      - Database connection (TitanDatabase)
    ├── queries.py       - Query methods (TitanQueries)
    ├── display.py       - UI/display functions
    └── main.py          - Main interactive menu loop

Usage:
    python titan_menu_v2.py
"""

from titan_menu import main

if __name__ == "__main__":

    main()
