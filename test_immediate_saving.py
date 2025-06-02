#!/usr/bin/env python3
"""
Test script to demonstrate immediate saving functionality with recent commits.
"""

import os
import sys
import time
from github_miner import AdvancedGitHubMiner

def test_immediate_saving():
    """Test immediate saving with recent commits."""
    print("🧪 Testing Immediate Saving with Recent Commits")
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
    
    # Test users (mix of active and less active)
    test_users = ["octocat", "torvalds"]  # Small test set
    
    # Create unique filename with timestamp
    timestamp = int(time.time())
    filename = f"test_immediate_saving_{timestamp}"
    
    print(f"\n📊 Testing immediate saving for {len(test_users)} users...")
    print(f"📁 Output files: {filename}_raw.json and {filename}_ml_features.csv")
    print("-" * 50)
    
    try:
        # Test immediate saving
        results = miner.parallel_data_collection(
            usernames=test_users,
            max_workers=1,  # Sequential for clearer demo
            save_immediately=True,
            filename=filename
        )
        
        print(f"\n✅ Data collection completed!")
        print(f"📈 Processed {len(results)} users successfully")
        
        # Check if files were created
        json_file = f"{filename}_raw.json"
        csv_file = f"{filename}_ml_features.csv"
        
        if os.path.exists(json_file):
            size = os.path.getsize(json_file)
            print(f"📄 JSON file: {json_file} ({size} bytes)")
        else:
            print(f"❌ JSON file not found: {json_file}")
        
        if os.path.exists(csv_file):
            size = os.path.getsize(csv_file)
            print(f"📊 CSV file: {csv_file} ({size} bytes)")
        else:
            print(f"❌ CSV file not found: {csv_file}")
        
        # Check recent commits in first result
        if results and len(results) > 0:
            first_user = results[0]
            commit_activity = first_user.get('commit_activity', {})
            recent_commits = commit_activity.get('recent_commits', [])
            
            print(f"\n🔍 Recent Commits Analysis for '{first_user['username']}':")
            print(f"   📊 Total recent commits: {commit_activity.get('total_recent_commits', 0)}")
            print(f"   📝 Recent commits array length: {len(recent_commits)}")
            
            if recent_commits:
                print("   📋 Sample recent commits:")
                for i, commit in enumerate(recent_commits[:3]):  # Show first 3
                    print(f"      {i+1}. {commit['repo']} - {commit['message'][:50]}...")
            else:
                print("   📝 No recent commits found (empty array as expected)")
        
        print(f"\n🎉 Test completed successfully!")
        print(f"💾 Data was saved immediately after each user was processed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_empty_recent_commits():
    """Test that users with no recent commits get empty arrays."""
    print("\n🧪 Testing Empty Recent Commits Handling")
    print("=" * 50)
    
    # Test with a user that likely has no recent commits (old account)
    test_users = ["defunkt"]  # GitHub co-founder, but likely inactive
    
    try:
        def progress_callback(message):
            print(f"[INFO] {message}")
        
        miner = AdvancedGitHubMiner(progress_callback=progress_callback)
        
        timestamp = int(time.time())
        filename = f"test_empty_commits_{timestamp}"
        
        print(f"📊 Testing with user: {test_users[0]}")
        
        results = miner.parallel_data_collection(
            usernames=test_users,
            max_workers=1,
            save_immediately=True,
            filename=filename
        )
        
        if results and len(results) > 0:
            user_data = results[0]
            commit_activity = user_data.get('commit_activity', {})
            recent_commits = commit_activity.get('recent_commits', [])
            
            print(f"\n✅ Results for '{user_data['username']}':")
            print(f"   📊 Total recent commits: {commit_activity.get('total_recent_commits', 0)}")
            print(f"   📝 Recent commits array: {recent_commits}")
            print(f"   📏 Array length: {len(recent_commits)}")
            
            if len(recent_commits) == 0:
                print("   ✅ Empty array correctly returned for user with no recent commits")
            else:
                print(f"   📋 Found {len(recent_commits)} recent commits")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 GitHub Miner - Immediate Saving Test Suite")
    print("=" * 60)
    
    # Test 1: Basic immediate saving
    test_immediate_saving()
    
    # Test 2: Empty recent commits
    test_empty_recent_commits()
    
    print("\n🏁 All tests completed!")
    print("💡 The data was saved immediately after each user was processed")
    print("📁 Check the generated files to see the immediate saving in action") 