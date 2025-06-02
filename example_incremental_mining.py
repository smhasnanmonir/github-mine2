#!/usr/bin/env python3
"""
Example script demonstrating immediate data saving with GitHub Miner.

This script shows how to use the immediate saving functionality
to preserve data after each user is processed.
"""

import os
import time
from github_miner import AutoProfileDiscovery, AdvancedGitHubMiner
from github_miner.config import set_github_token

def demo_immediate_saving():
    """Demonstrate immediate saving functionality."""
    
    # Set your GitHub token (you can also set GITHUB_TOKEN environment variable)
    token = input("Enter your GitHub token: ").strip()
    if not token:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("Error: GitHub token is required!")
            return
    
    set_github_token(token)
    
    print("=" * 60)
    print("GITHUB MINER - IMMEDIATE SAVING DEMO")
    print("=" * 60)
    
    # Discover some users
    print("1. Discovering Python developers...")
    discoverer = AutoProfileDiscovery(token)
    
    # Discover a small set for demo
    users = discoverer.discover_trending_developers(language="python", limit=5)
    
    if not users:
        print("No users discovered. Exiting...")
        return
    
    print(f"Found {len(users)} users: {', '.join(users)}")
    
    # Create a progress callback
    def progress_callback(message):
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    # Initialize miner with immediate saving
    print("\n2. Starting data mining with immediate saving...")
    print("Note: Data will be saved immediately after each user is processed")
    print("If the process is interrupted, all collected data will be preserved!\n")
    
    miner = AdvancedGitHubMiner(token, progress_callback=progress_callback)
    
    # Use immediate saving method
    filename = "demo_immediate_mining"
    
    try:
        # Mine with immediate saving after each user
        results = miner.parallel_data_collection(
            users, 
            max_workers=2,
            save_immediately=True,
            filename=filename
        )
        
        print(f"\n" + "=" * 40)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 40)
        print(f"Users processed: {len(results)}/{len(users)}")
        print(f"Success rate: {len(results)/len(users)*100:.1f}%")
        print(f"\nOutput files:")
        print(f"- JSON: {filename}_raw.json")
        print(f"- CSV: {filename}_ml_features.csv")
        print("\nTry interrupting the process next time (Ctrl+C) to see data preservation!")
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user!")
        print("Checking if any data was saved...")
        
        # Check if files exist
        json_file = f"{filename}_raw.json"
        csv_file = f"{filename}_ml_features.csv"
        
        if os.path.exists(json_file):
            print(f"✓ JSON file preserved: {json_file}")
        if os.path.exists(csv_file):
            print(f"✓ CSV file preserved: {csv_file}")
        
        print("Data collection was interrupted but collected data is preserved!")
        
    except Exception as e:
        print(f"Error during mining: {e}")

def demo_single_user_immediate():
    """Demo immediate saving for a single user."""
    
    token = input("Enter your GitHub token: ").strip()
    if not token:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("Error: GitHub token is required!")
            return
    
    username = input("Enter GitHub username to mine: ").strip()
    if not username:
        print("Username is required!")
        return
    
    print(f"\nMining data for user: {username}")
    print("Using immediate saving...")
    
    def progress_callback(message):
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    miner = AdvancedGitHubMiner(token, progress_callback=progress_callback)
    
    # Mine single user with immediate saving
    filename = f"single_user_{username}"
    
    try:
        results = miner.parallel_data_collection(
            [username], 
            max_workers=1,
            save_immediately=True,
            filename=filename
        )
        
        if results:
            print(f"\nSuccess! Data saved to:")
            print(f"- {filename}_raw.json")
            print(f"- {filename}_ml_features.csv")
        else:
            print("No data collected.")
            
    except Exception as e:
        print(f"Error: {e}")

def demo_repository_mining():
    """Demo immediate saving for repository contributors."""
    
    token = input("Enter your GitHub token: ").strip()
    if not token:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("Error: GitHub token is required!")
            return
    
    repo_url = input("Enter GitHub repository URL (e.g., https://github.com/owner/repo): ").strip()
    if not repo_url:
        print("Repository URL is required!")
        return
    
    print(f"\nMining contributors for repository: {repo_url}")
    print("Using immediate saving...")
    
    def progress_callback(message):
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    miner = AdvancedGitHubMiner(token, progress_callback=progress_callback)
    
    # Mine repository contributors with immediate saving
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    filename = f"repo_{repo_name}_contributors"
    
    try:
        results = miner.mine_repository_contributors(
            repo_url,
            save_immediately=True,
            filename=filename
        )
        
        if results:
            print(f"\nSuccess! Data saved to:")
            print(f"- {filename}_raw.json")
            print(f"- {filename}_ml_features.csv")
            print(f"Contributors processed: {len(results)}")
        else:
            print("No contributors found or no data collected.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Choose demo option:")
    print("1. Multi-user immediate saving demo")
    print("2. Single user immediate saving")
    print("3. Repository contributors mining")
    
    choice = input("Enter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        demo_immediate_saving()
    elif choice == "2":
        demo_single_user_immediate()
    elif choice == "3":
        demo_repository_mining()
    else:
        print("Invalid choice!") 