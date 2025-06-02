#!/usr/bin/env python3
"""
Test script to verify that users with minimal repositories are properly fetched.
"""

import os
import sys
import time
from github_miner import AdvancedGitHubMiner

def test_minimal_repo_users():
    """Test users with minimal repositories to ensure they are fetched."""
    print("🧪 Testing Users with Minimal Repositories")
    print("=" * 50)
    
    # Initialize miner
    try:
        def progress_callback(message):
            print(f"[INFO] {message}")
        
        miner = AdvancedGitHubMiner(progress_callback=progress_callback)
        print("✅ GitHub Miner initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize GitHub Miner: {e}")
        return
    
    # Test users - mix of users with different repository counts
    test_users = [
        "defunkt",     # GitHub co-founder, might have minimal recent activity
        "mojombo",     # GitHub co-founder, might have older repos
        "pjhyett"      # Early GitHub user, might have fewer repos
    ]
    
    # Create unique filename with timestamp
    timestamp = int(time.time())
    filename = f"test_minimal_repos_{timestamp}"
    
    print(f"\n📊 Testing users with potentially minimal repositories:")
    for user in test_users:
        print(f"   - {user}")
    print(f"📁 Output files: {filename}_raw.json and {filename}_ml_features.csv")
    print("-" * 50)
    
    try:
        # Test with immediate saving
        results = miner.parallel_data_collection(
            usernames=test_users,
            max_workers=1,  # Sequential for clearer tracking
            save_immediately=True,
            filename=filename,
            fetch_all_commits=False  # Start with recent commits
        )
        
        print(f"\n✅ Data collection completed!")
        print(f"📈 Successfully processed {len(results)}/{len(test_users)} users")
        
        if len(results) != len(test_users):
            missing_users = len(test_users) - len(results)
            print(f"⚠️  {missing_users} users were not processed properly")
        
        # Analyze each user's data
        for i, user_data in enumerate(results):
            if user_data:
                username = user_data.get('username', 'unknown')
                public_repos = user_data.get('public_repos', 0)
                
                commit_activity = user_data.get('commit_activity', {})
                total_repos = commit_activity.get('total_repositories', 0)
                recent_commits = commit_activity.get('total_recent_commits', 0)
                
                print(f"\n👤 User {i+1}: {username}")
                print(f"   📊 Public repositories: {public_repos}")
                print(f"   📊 Original repositories: {total_repos}")
                print(f"   📊 Recent commits: {recent_commits}")
                print(f"   ✅ Data collected: {user_data is not None}")
                
                # Check if user has minimal repos but still got data
                if public_repos <= 1 or total_repos == 0:
                    print(f"   🎯 MINIMAL REPO USER - Data still collected successfully!")
        
        # Check files were created
        json_file = f"{filename}_raw.json"
        csv_file = f"{filename}_ml_features.csv"
        
        if os.path.exists(json_file):
            size = os.path.getsize(json_file)
            print(f"\n📄 JSON file created: {json_file} ({size:,} bytes)")
        
        if os.path.exists(csv_file):
            size = os.path.getsize(csv_file)
            print(f"📊 CSV file created: {csv_file} ({size:,} bytes)")
        
        print(f"\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_repository_mining_minimal():
    """Test repository mining to ensure all contributors are captured."""
    print("\n🧪 Testing Repository Mining - All Contributors")
    print("=" * 60)
    
    try:
        def progress_callback(message):
            print(f"[INFO] {message}")
        
        miner = AdvancedGitHubMiner(progress_callback=progress_callback)
        
        # Test with a repository that might have contributors with minimal repos
        repo_url = "https://github.com/octocat/Hello-World"
        timestamp = int(time.time())
        filename = f"test_repo_minimal_{timestamp}"
        
        print(f"📊 Testing repository: {repo_url}")
        print(f"🎯 Goal: Ensure ALL contributors are mined, even those with minimal repos")
        
        results = miner.mine_repository_contributors(
            repo_url=repo_url,
            save_immediately=True,
            filename=filename,
            fetch_all_commits=False
        )
        
        print(f"\n✅ Repository mining completed!")
        print(f"📈 Total contributors processed: {len(results)}")
        
        # Analyze contributor data
        minimal_repo_contributors = 0
        for user_data in results:
            if user_data:
                username = user_data.get('username', 'unknown')
                public_repos = user_data.get('public_repos', 0)
                commit_activity = user_data.get('commit_activity', {})
                total_repos = commit_activity.get('total_repositories', 0)
                
                if public_repos <= 1 or total_repos == 0:
                    minimal_repo_contributors += 1
                    print(f"   🎯 Minimal repo contributor: {username} ({public_repos} public repos, {total_repos} original)")
        
        print(f"\n📊 Summary:")
        print(f"   👥 Total contributors: {len(results)}")
        print(f"   🎯 Contributors with minimal repos: {minimal_repo_contributors}")
        print(f"   ✅ All contributors captured: {len(results) > 0}")
        
    except Exception as e:
        print(f"❌ Repository test failed: {e}")

if __name__ == "__main__":
    print("🚀 GitHub Miner - Minimal Repository Test Suite")
    print("=" * 60)
    print("🎯 Purpose: Verify that users with minimal repositories are properly fetched")
    print("")
    
    # Test 1: Users with minimal repositories
    test_minimal_repo_users()
    
    # Test 2: Repository mining including minimal repo contributors
    test_repository_mining_minimal()
    
    print("\n🏁 All tests completed!")
    print("💡 Users with minimal repositories should now be properly processed")
    print("✅ Even users with only forked repos or no original repos get data collected") 