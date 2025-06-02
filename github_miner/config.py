"""
Configuration module for GitHub Miner.

Contains global settings, constants, and configuration utilities.
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global GitHub token (can be set via GUI, CLI, or environment variable)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

def set_github_token(token: str):
    """Set the global GitHub token."""
    global GITHUB_TOKEN
    GITHUB_TOKEN = token

def get_github_token() -> str:
    """Get the current GitHub token."""
    return GITHUB_TOKEN

# API Rate limiting constants
DEFAULT_BATCH_SIZE = 5
DEFAULT_MAX_WORKERS = 2
RATE_LIMIT_DELAY = 30  # seconds

# Discovery constants
DEFAULT_DISCOVERY_LIMIT = 50
DEFAULT_TOPIC_LIST = [
    'machine-learning', 'web-development', 'mobile', 'data-science', 
    'artificial-intelligence', 'blockchain', 'devops', 'frontend', 'backend'
]

# Analysis constants
DEFAULT_COMMIT_ANALYSIS_DAYS = 90
DEFAULT_ACTIVITY_DAYS = 7
DEFAULT_TOP_REPOS_LIMIT = 10 