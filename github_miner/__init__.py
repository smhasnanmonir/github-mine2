"""
GitHub Miner - A comprehensive tool for discovering and analyzing GitHub profiles.

This package provides tools for:
- Discovering GitHub profiles using various strategies
- Mining detailed user and repository data
- Analyzing development patterns and contributions
- Exporting data for machine learning applications
- GUI and CLI interfaces for easy usage
- Incremental data saving for robust data collection
"""

__version__ = "1.0.0"
__author__ = "GitHub Miner Team"

from .discovery import AutoProfileDiscovery
from .miner import AdvancedGitHubMiner
from .gui import GitHubMinerGUI
from .cli import run_cli_auto_discovery
from .config import GITHUB_TOKEN, set_github_token

__all__ = [
    'AutoProfileDiscovery',
    'AdvancedGitHubMiner', 
    'GitHubMinerGUI',
    'run_cli_auto_discovery',
    'GITHUB_TOKEN',
    'set_github_token'
] 