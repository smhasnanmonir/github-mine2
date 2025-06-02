import sys
import argparse

def show_help():
    """Display help information about available modes."""
    print("""
GitHub Miner - Comprehensive GitHub Profile Discovery and Mining Tool

Usage:
    python main_entry.py [mode] [options]

Available Modes:
    gui         Launch the graphical user interface (default)
    cli         Run command-line interface for automated discovery
    repo        Run command-line interface for repository mining
    
Examples:
    # Launch GUI (default)
    python main_entry.py
    python main_entry.py gui
    
    # Run CLI with automated discovery
    python main_entry.py cli --token YOUR_TOKEN --mode trending --language python
    
    # Mine repository contributors
    python main_entry.py repo --token YOUR_TOKEN --repo-url https://github.com/owner/repo
    
    # Get help for CLI options
    python main_entry.py cli --help
    python main_entry.py repo --help

For detailed CLI options, use: python main_entry.py cli --help or python main_entry.py repo --help
    """)

def main():
    """Main entry point for the GitHub Miner application."""
    # If no arguments, launch GUI
    if len(sys.argv) == 1:
        from github_miner.gui import create_gui
        create_gui()
        return
    
    # Parse the mode argument
    if sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        return
    
    mode = sys.argv[1]
    
    if mode == 'gui':
        print("Launching GitHub Miner GUI...")
        from github_miner.gui import create_gui
        create_gui()
        
    elif mode == 'cli':
        print("Starting GitHub Miner CLI...")
        # Remove the 'cli' argument and pass the rest to the CLI module
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from github_miner.cli import run_cli_auto_discovery
        run_cli_auto_discovery()
        
    elif mode == 'repo':
        print("Starting GitHub Repository Mining CLI...")
        # Remove the 'repo' argument and pass the rest to the CLI module
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from github_miner.cli import run_repository_mining
        run_repository_mining()
        
    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: gui, cli, repo")
        print("Use 'python main_entry.py --help' for more information")
        sys.exit(1)

if __name__ == "__main__":
    main() 