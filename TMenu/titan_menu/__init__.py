"""
Titan Database Interactive Menu Package

A modular tool for querying device information from Walmart's Titan DB.
"""

from .database import TitanDatabase
from .queries import TitanQueries
from .display import print_results, export_csv, show_main_menu, print_banner
from .main import main
from .nre_jumpbox import NREJumpbox, NREJumpboxConfig, prompt_for_jumpbox_credentials
from .superputty_config import SuperPuttyConfigGenerator, SuperPuttyProfile

__version__ = "2.0.0"
__all__ = [
    "TitanDatabase",
    "TitanQueries",
    "print_results",
    "export_csv",
    "show_main_menu",
    "print_banner",
    "main",
    "NREJumpbox",
    "NREJumpboxConfig",
    "prompt_for_jumpbox_credentials",
    "SuperPuttyConfigGenerator",
    "SuperPuttyProfile",
]
