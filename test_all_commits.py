#!/usr/bin/env python3
"""
Test script to demonstrate fetching all commits vs recent commits functionality.
"""

import os
import sys
import time
from github_miner import AdvancedGitHubMiner

def test_recent_vs_all_commits():
    """Compare recent commits vs all commits functionality."""
    print("🧪 Testing Recent vs All Commits Functionality")
    print("=" * 60)
    
    # Initialize miner
    try:
        def progress_callback(message):
            print(f"[INFO] {message}")
        
        miner = AdvancedGitHubMiner(progress_callback=progress_callback)
        print("✅ GitHub Miner initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize GitHub Miner: {e}")
        return
    
    # Test with a user likely to have many commits
    test_user = "octocat"  # GitHub's mascot account
    
    # Create unique filename with timestamp
    timestamp = int(time.time())
    
    print(f"\n📊 Comparing recent vs all commits for user: {test_user}")
    print("-" * 60)
    
    try:
        # Test 1: Recent commits only (default behavior)
        print("\n🔍 TEST 1: Fetching RECENT commits only")
        print("-" * 40)
        
        recent_filename = f"test_recent_commits_{timestamp}"
        recent_results = miner.parallel_data_collection(
            usernames=[test_user],
            max_workers=1,
            save_immediately=True,
            filename=recent_filename,
            fetch_all_commits=False  # Recent commits only
        )
        
        # Test 2: All commits
        print("\n🔍 TEST 2: Fetching ALL commits")
        print("-" * 40)
        
        all_filename = f"test_all_commits_{timestamp}"
        all_results = miner.parallel_data_collection(
            usernames=[test_user],
            max_workers=1,
            save_immediately=True,
            filename=all_filename,
            fetch_all_commits=True  # All commits
        )
        
        # Compare results
        print("\n📊 COMPARISON RESULTS")
        print("=" * 50)
        
        if recent_results and all_results:
            recent_data = recent_results[0]
            all_data = all_results[0]
            
            recent_activity = recent_data.get('commit_activity', {})
            all_activity = all_data.get('commit_activity', {})
            
            print(f"👤 User: {test_user}")
            print(f"📅 Recent commits mode:")
            print(f"   📊 Total recent commits: {recent_activity.get('total_recent_commits', 0)}")
            print(f"   📝 Recent commits array length: {len(recent_activity.get('recent_commits', []))}")
            print(f"   🔧 Fetch mode: {recent_activity.get('fetch_mode', 'unknown')}")
            
            print(f"\n📅 All commits mode:")
            print(f"   📊 Total commits (all time): {all_activity.get('total_commits', 0)}")
            print(f"   📊 Recent commits (for comparison): {all_activity.get('total_recent_commits', 0)}")
            print(f"   📝 Recent commits stored (max 50): {len(all_activity.get('recent_commits', []))}")
            print(f"   🔧 Fetch mode: {all_activity.get('fetch_mode', 'unknown')}")
            
            # Show ratio
            total_commits = all_activity.get('total_commits', 0)
            recent_commits = all_activity.get('total_recent_commits', 0)
            if total_commits > 0:
                ratio = (recent_commits / total_commits) * 100
                print(f"\n📈 Analysis:")
                print(f"   🔢 Recent commits are {ratio:.1f}% of all commits")
                print(f"   📆 All-time commit history: {total_commits} commits")
            
            # Show sample commits from recent commits array (limited to 50)
            recent_commits_array = all_activity.get('recent_commits', [])
            if recent_commits_array:
                print(f"\n📋 Sample from recent commits (showing first 3 of {len(recent_commits_array)} stored):")
                for i, commit in enumerate(recent_commits_array[:3]):
                    date = commit.get('date', 'unknown')
                    repo = commit.get('repo', 'unknown')
                    message = commit.get('message', 'No message')[:50]
                    print(f"   {i+1}. [{date}] {repo}: {message}...")
            
            # File size comparison
            recent_json = f"{recent_filename}_raw.json"
            all_json = f"{all_filename}_raw.json"
            
            if os.path.exists(recent_json) and os.path.exists(all_json):
                recent_size = os.path.getsize(recent_json)
                all_size = os.path.getsize(all_json)
                print(f"\n📁 File size comparison:")
                print(f"   📄 Recent commits JSON: {recent_size:,} bytes")
                print(f"   📄 All commits JSON: {all_size:,} bytes")
                if recent_size > 0:
                    size_ratio = all_size / recent_size
                    print(f"   📊 All commits file is {size_ratio:.1f}x larger")
        
        print(f"\n🎉 Test completed successfully!")
        print(f"💾 Both datasets saved with immediate saving functionality")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_repository_all_commits():
    """Test repository mining with all commits."""
    print("\n🧪 Testing Repository Mining with All Commits")
    print("=" * 60)
    
    try:
        def progress_callback(message):
            print(f"[INFO] {message}")
        
        miner = AdvancedGitHubMiner(progress_callback=progress_callback)
        
        # Test with a small repository
        repo_url = "https://github.com/octocat/Hello-World"
        timestamp = int(time.time())
        filename = f"test_repo_all_commits_{timestamp}"
        
        print(f"📊 Testing repository mining with ALL commits")
        print(f"🔗 Repository: {repo_url}")
        print(f"📁 Output: {filename}_*.json/csv")
        
        results = miner.mine_repository_contributors(
            repo_url=repo_url,
            save_immediately=True,
            filename=filename,
            fetch_all_commits=True  # NEW: Fetch all commits
        )
        
        print(f"\n✅ Repository mining completed!")
        print(f"📈 Processed {len(results)} contributors")
        
        # Show sample data from first contributor
        if results:
            first_contributor = results[0]
            commit_activity = first_contributor.get('commit_activity', {})
            
            print(f"\n🔍 Sample data for '{first_contributor['username']}':")
            print(f"   📊 Total commits (all time): {commit_activity.get('total_commits', 0)}")
            print(f"   📊 Recent commits: {commit_activity.get('total_recent_commits', 0)}")
            print(f"   📝 Recent commits stored (max 50): {len(commit_activity.get('recent_commits', []))}")
            print(f"   🔧 Fetch mode: {commit_activity.get('fetch_mode', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Repository test failed: {e}")

def demonstrate_usage():
    """Show example usage patterns."""
    print("\n💡 Usage Examples")
    print("=" * 30)
    
    print("📝 Python code examples:")
    print("""
# Fetch recent commits (default behavior)
miner.parallel_data_collection(
    usernames=['user1', 'user2'],
    save_immediately=True,
    filename='recent_data',
    fetch_all_commits=False  # or omit (default)
)

# Count ALL commits but store only recent commit details (max 50)
miner.parallel_data_collection(
    usernames=['user1', 'user2'],
    save_immediately=True,
    filename='all_data',
    fetch_all_commits=True  # NEW: Counts all commits, stores max 50 recent
)

# Repository mining with all commits counting
miner.mine_repository_contributors(
    repo_url='https://github.com/owner/repo',
    save_immediately=True,
    filename='repo_all_commits',
    fetch_all_commits=True  # NEW: Counts all, stores max 50 recent
)
""")

if __name__ == "__main__":
    print("🚀 GitHub Miner - All Commits Test Suite")
    print("=" * 60)
    
    # Test 1: Recent vs All commits comparison
    test_recent_vs_all_commits()
    
    # Test 2: Repository mining with all commits
    test_repository_all_commits()
    
    # Show usage examples
    demonstrate_usage()
    
    print("\n🏁 All tests completed!")
    print("💡 You can now count ALL commits or just analyze recent commits")
    print("📊 All commits mode: Counts total commits but stores max 50 recent commit details")
    print("⚡ Memory efficient: No large arrays of all commit data stored") 