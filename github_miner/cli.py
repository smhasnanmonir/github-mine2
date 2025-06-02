"""
Command Line Interface Module for GitHub Miner.

This module provides CLI functionality for automated discovery and mining
of GitHub profiles with various configuration options.
"""

import argparse
import sys
from datetime import datetime
import time
from typing import List

from .discovery import AutoProfileDiscovery
from .miner import AdvancedGitHubMiner
from .config import set_github_token, DEFAULT_BATCH_SIZE, DEFAULT_MAX_WORKERS, RATE_LIMIT_DELAY


def run_cli_auto_discovery():
    """
    Main CLI function for automated GitHub profile discovery and mining.
    
    Provides various discovery methods and mining options through command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Automated GitHub Profile Discovery and Mining Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover trending Python developers
  python -m github_miner.cli --mode trending --language python --max-users 20

  # Search for machine learning developers with specific criteria
  python -m github_miner.cli --mode search --language python --location "San Francisco" --min-followers 100

  # Comprehensive discovery combining all methods
  python -m github_miner.cli --mode comprehensive --language javascript --max-users 50

  # Discover from popular repositories in specific topics
  python -m github_miner.cli --mode popular --topics machine-learning,web-development --max-users 30
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--token', 
        required=True,
        help='GitHub personal access token (required for API access)'
    )
    
    parser.add_argument(
        '--mode',
        required=True,
        choices=['trending', 'search', 'popular', 'active', 'organizations', 'comprehensive'],
        help='Discovery mode to use'
    )
    
    parser.add_argument(
        '--output',
        default='github_mining_results',
        help='Output filename prefix (default: github_mining_results)'
    )
    
    # Discovery options
    parser.add_argument(
        '--max-users',
        type=int,
        default=50,
        help='Maximum number of users to discover (default: 50)'
    )
    
    parser.add_argument(
        '--language',
        help='Programming language filter (e.g., python, javascript, java)'
    )
    
    parser.add_argument(
        '--location',
        help='Location filter (e.g., "San Francisco", "New York", "London")'
    )
    
    # Search-specific options
    parser.add_argument(
        '--min-followers',
        type=int,
        help='Minimum number of followers (for search mode)'
    )
    
    parser.add_argument(
        '--min-repos',
        type=int,
        help='Minimum number of repositories (for search mode)'
    )
    
    parser.add_argument(
        '--company',
        help='Company filter (for search mode)'
    )
    
    # Popular repositories options
    parser.add_argument(
        '--topics',
        help='Comma-separated list of topics (for popular mode, e.g., machine-learning,web-development)'
    )
    
    # Active developers options
    parser.add_argument(
        '--activity-days',
        type=int,
        default=7,
        help='Days to look back for activity (for active mode, default: 7)'
    )
    
    # Organizations options
    parser.add_argument(
        '--orgs',
        help='Comma-separated list of organization names (for organizations mode)'
    )
    
    # Mining options
    parser.add_argument(
        '--batch-size',
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f'Batch size for processing users (default: {DEFAULT_BATCH_SIZE})'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'Maximum number of worker threads (default: {DEFAULT_MAX_WORKERS})'
    )
    
    # Verbose output
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Set the global token
        set_github_token(args.token)
        
        print("=" * 60)
        print("GITHUB PROFILE DISCOVERY AND MINING TOOL")
        print("=" * 60)
        print(f"Discovery mode: {args.mode}")
        print(f"Maximum users: {args.max_users}")
        print(f"Output prefix: {args.output}")
        
        if args.language:
            print(f"Language filter: {args.language}")
        if args.location:
            print(f"Location filter: {args.location}")
        
        print("-" * 60)
        
        # Initialize discovery
        discoverer = AutoProfileDiscovery(args.token)
        discovered_users = []
        
        # Run discovery based on mode
        if args.mode == 'trending':
            print("Starting trending developers discovery...")
            discovered_users = discoverer.discover_trending_developers(
                language=args.language,
                location=args.location,
                limit=args.max_users
            )
            
        elif args.mode == 'search':
            print("Starting search-based discovery...")
            criteria = {}
            if args.language:
                criteria['language'] = args.language
            if args.location:
                criteria['location'] = args.location
            if args.min_followers:
                criteria['min_followers'] = args.min_followers
            if args.min_repos:
                criteria['min_repos'] = args.min_repos
            if args.company:
                criteria['company'] = args.company
            
            discovered_users = discoverer.discover_by_search_criteria(criteria, args.max_users)
            
        elif args.mode == 'popular':
            print("Starting popular repositories discovery...")
            topics = None
            if args.topics:
                topics = [topic.strip() for topic in args.topics.split(',')]
            discovered_users = discoverer.discover_from_popular_repos(topics, args.max_users)
            
        elif args.mode == 'active':
            print("Starting active developers discovery...")
            discovered_users = discoverer.discover_active_developers(args.activity_days, args.max_users)
            
        elif args.mode == 'organizations':
            print("Starting organization-based discovery...")
            if not args.orgs:
                print("Error: --orgs parameter is required for organizations mode")
                return
            org_names = [org.strip() for org in args.orgs.split(',')]
            discovered_users = discoverer.discover_by_organization(org_names, args.max_users)
            
        elif args.mode == 'comprehensive':
            print("Starting comprehensive discovery...")
            preferences = {}
            if args.language:
                preferences['language'] = args.language
            if args.location:
                preferences['location'] = args.location
            if args.min_followers:
                preferences['min_followers'] = args.min_followers
            if args.min_repos:
                preferences['min_repos'] = args.min_repos
            if args.activity_days:
                preferences['activity_days'] = args.activity_days
            if args.topics:
                preferences['topics'] = [topic.strip() for topic in args.topics.split(',')]
            
            discovered_users = discoverer.discover_comprehensive(preferences, args.max_users)
        
        # Remove duplicates
        discovered_users = list(set(discovered_users))[:args.max_users]
        
        if not discovered_users:
            print("No users discovered. Try different parameters.")
            return
        
        print(f"\nDiscovered {len(discovered_users)} unique users:")
        for i, user in enumerate(discovered_users[:10], 1):
            print(f"  {i}. {user}")
        if len(discovered_users) > 10:
            print(f"  ... and {len(discovered_users) - 10} more")
        
        print(f"\nStarting mining process...")
        print("-" * 50)
        
        # Initialize miner
        def progress_callback(message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] {message}")
        
        miner = AdvancedGitHubMiner(args.token, progress_callback=progress_callback)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{args.output}_{timestamp}"
        
        print(f"\nStarting data collection with immediate saving...")
        print(f"Data will be saved immediately after each user is processed")
        print(f"Files: {final_filename}_raw.json and {final_filename}_ml_features.csv")
        print("-" * 50)
        
        # Use immediate saving with standard parallel_data_collection
        try:
            all_results = miner.parallel_data_collection(
                discovered_users,
                max_workers=args.max_workers,
                save_immediately=True,
                filename=final_filename
            )
            
            # Final summary
            if all_results:
                print(f"\n" + "=" * 50)
                print(f"AUTOMATED DISCOVERY AND MINING COMPLETED!")
                print(f"=" * 50)
                print(f"Users discovered: {len(discovered_users)}")
                print(f"Users successfully mined: {len(all_results)}")
                print(f"Success rate: {len(all_results)/len(discovered_users)*100:.1f}%")
                print(f"Final output files:")
                print(f"  - CSV: {final_filename}_ml_features.csv")
                print(f"  - JSON: {final_filename}_raw.json")
                print(f"Data was saved immediately after each user - no data loss!")
                
            else:
                print("No data was successfully collected")
                
        except Exception as e:
            print(f"Error during data collection: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def test_json_to_csv_conversion(json_file_path: str):
    """
    Standalone function to test JSON to CSV conversion.
    
    Args:
        json_file_path (str): Path to the JSON file to convert
        
    Returns:
        str: Path to the converted CSV file, or None if conversion failed
    """
    try:
        print(f"Testing JSON to CSV conversion for: {json_file_path}")
        miner = AdvancedGitHubMiner()
        # Note: This would need a convert_json_to_csv method in the miner
        # result = miner.convert_json_to_csv(json_file_path)
        # print(f"Conversion successful: {result}")
        # return result
        print("Conversion method not yet implemented")
        return None
    except Exception as e:
        print(f"Conversion failed: {e}")
        return None


def debug_export_function(dataset_file: str = None):
    """
    Debug function to test the export functionality.
    
    Args:
        dataset_file (str, optional): Path to existing dataset file to test with
    """
    try:
        if dataset_file:
            import json
            with open(dataset_file, 'r') as f:
                dataset = json.load(f)
        else:
            # Create a sample dataset for testing
            dataset = [{
                'username': 'test_user',
                'followers': 100,
                'following': 50,
                'public_repos': 25,
                'created_at': datetime.now(),
                'extended_user_data': {
                    'public_gists': 5,
                    'organizations': ['org1', 'org2'],
                    'starred_repos': [{'name': 'repo1'}, {'name': 'repo2'}],
                    'watched_repos': [{'name': 'repo3'}],
                    'events': [{'type': 'PushEvent'}, {'type': 'IssuesEvent'}]
                },
                'development_patterns': {
                    'commit_frequency': ['2024-01-01', '2024-01-02'],
                    'productivity_streaks': {'max_streak': 5},
                    'commit_comments': [],
                    'issue_comments': [],
                    'pr_reviews': []
                },
                'commit_activity': {
                    'total_recent_commits': 15,
                    'active_days': ['2024-01-01', '2024-01-02'],
                    'avg_commits_per_day': 7.5,
                    'repositories_analyzed': 3,
                }
            }]
        
        print("Testing export function with sample/loaded data...")
        miner = AdvancedGitHubMiner()
        miner.export_for_machine_learning(dataset, "debug_test")
        print("Export test completed successfully!")
        
    except Exception as e:
        print(f"Debug export failed: {e}")
        import traceback
        traceback.print_exc()


def run_repository_mining():
    """
    CLI function for mining GitHub repository contributors.
    """
    parser = argparse.ArgumentParser(
        description="GitHub Repository Contributor Mining Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mine contributors from a specific repository
  python -m github_miner.cli repo --token YOUR_TOKEN --repo-url https://github.com/owner/repo

  # Mine with custom output filename
  python -m github_miner.cli repo --token YOUR_TOKEN --repo-url https://github.com/owner/repo --output my_repo_data
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--token', 
        required=True,
        help='GitHub personal access token (required for API access)'
    )
    
    parser.add_argument(
        '--repo-url',
        required=True,
        help='GitHub repository URL (e.g., https://github.com/owner/repo)'
    )
    
    parser.add_argument(
        '--output',
        default='repository_mining_results',
        help='Output filename prefix (default: repository_mining_results)'
    )
    
    # Mining options
    parser.add_argument(
        '--max-workers',
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f'Maximum number of worker threads (default: {DEFAULT_MAX_WORKERS})'
    )
    
    # Verbose output
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Set the global token
        set_github_token(args.token)
        
        print("=" * 60)
        print("GITHUB REPOSITORY CONTRIBUTOR MINING TOOL")
        print("=" * 60)
        print(f"Repository URL: {args.repo_url}")
        print(f"Output prefix: {args.output}")
        print("-" * 60)
        
        # Initialize miner
        def progress_callback(message):
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] {message}")
        
        miner = AdvancedGitHubMiner(args.token, progress_callback=progress_callback)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{args.output}_{timestamp}"
        
        print(f"\nStarting repository mining with immediate saving...")
        print(f"Data will be saved immediately after each contributor is processed")
        print(f"Files: {final_filename}_raw.json and {final_filename}_ml_features.csv")
        print("-" * 50)
        
        # Mine repository contributors with immediate saving
        try:
            results = miner.mine_repository_contributors(
                args.repo_url,
                save_immediately=True,
                filename=final_filename
            )
            
            # Final summary
            if results:
                print(f"\n" + "=" * 50)
                print(f"REPOSITORY MINING COMPLETED!")
                print(f"=" * 50)
                print(f"Contributors successfully mined: {len(results)}")
                print(f"Final output files:")
                print(f"  - CSV: {final_filename}_ml_features.csv")
                print(f"  - JSON: {final_filename}_raw.json")
                print(f"Data was saved immediately after each contributor - no data loss!")
                
            else:
                print("No contributor data was successfully collected")
                
        except Exception as e:
            print(f"Error during repository mining: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_cli_auto_discovery() 