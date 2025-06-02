"""
GitHub Profile Discovery Module.

This module contains the AutoProfileDiscovery class which provides various methods
for discovering GitHub profiles based on different criteria and strategies.
"""

from datetime import datetime, timedelta
from github import Github, GithubException
from typing import List, Dict, Optional
from .config import GITHUB_TOKEN, DEFAULT_DISCOVERY_LIMIT, DEFAULT_TOPIC_LIST


class AutoProfileDiscovery:
    """
    Automated GitHub profile discovery using various strategies.
    
    This class provides multiple methods to discover GitHub users:
    - Trending developers from popular repositories
    - Search-based discovery using specific criteria
    - Discovery from popular repositories in specific topics
    - Active developers discovery
    - Organization-based discovery
    - Comprehensive discovery combining multiple methods
    """
    
    def __init__(self, github_token: str = None):
        """
        Initialize the AutoProfileDiscovery instance.
        
        Args:
            github_token (str, optional): GitHub personal access token.
                                        If not provided, uses the global GITHUB_TOKEN.
        
        Raises:
            ValueError: If no GitHub token is provided or available.
        """
        self.token = github_token or GITHUB_TOKEN
        if not self.token:
            raise ValueError("GitHub token is required")
        self.github = Github(self.token)
        self.headers = {'Authorization': f'token {self.token}'}
    
    def discover_trending_developers(self, language: str = None, location: str = None, 
                                   limit: int = DEFAULT_DISCOVERY_LIMIT):
        """
        Discover developers from trending repositories.
        
        Args:
            language (str, optional): Programming language filter
            location (str, optional): Location filter
            limit (int): Maximum number of developers to discover
            
        Returns:
            List[str]: List of discovered GitHub usernames
        """
        try:
            discovered_users = set()
            
            # Search for trending repositories
            query_parts = []
            if language:
                query_parts.append(f"language:{language}")
            
            # Add date filter for recent activity (last 30 days)
            recent_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            query_parts.append(f"pushed:>{recent_date}")
            
            query = " ".join(query_parts) if query_parts else "stars:>100"
            
            print(f"Searching trending repositories with query: {query}")
            
            # Get trending repositories
            repos = self.github.search_repositories(query, sort="stars", order="desc")
            
            processed_repos = 0
            for repo in repos:
                if len(discovered_users) >= limit:
                    break
                
                try:
                    # Get repository owner
                    if repo.owner and repo.owner.type == "User":
                        if location:
                            user = self.github.get_user(repo.owner.login)
                            if user.location and location.lower() in user.location.lower():
                                discovered_users.add(repo.owner.login)
                        else:
                            discovered_users.add(repo.owner.login)
                    
                    # Get top contributors
                    try:
                        contributors = repo.get_contributors()
                        for contributor in list(contributors)[:5]:  # Top 5 contributors
                            if len(discovered_users) >= limit:
                                break
                            
                            if contributor.type == "User":
                                if location:
                                    try:
                                        user = self.github.get_user(contributor.login)
                                        if user.location and location.lower() in user.location.lower():
                                            discovered_users.add(contributor.login)
                                    except:
                                        pass
                                else:
                                    discovered_users.add(contributor.login)
                    except:
                        pass
                    
                    processed_repos += 1
                    if processed_repos >= 20:  # Limit API calls
                        break
                        
                except Exception as e:
                    print(f"Error processing repo {repo.full_name}: {e}")
                    continue
            
            print(f"Discovered {len(discovered_users)} developers from trending repositories")
            return list(discovered_users)[:limit]
            
        except Exception as e:
            print(f"Error discovering trending developers: {e}")
            return []
    
    def discover_by_search_criteria(self, criteria: dict, limit: int = DEFAULT_DISCOVERY_LIMIT):
        """
        Discover users based on search criteria.
        
        Args:
            criteria (dict): Search criteria including language, location, min_followers, etc.
            limit (int): Maximum number of users to discover
            
        Returns:
            List[str]: List of discovered GitHub usernames
        """
        try:
            query_parts = []
            
            # Build search query
            if criteria.get('language'):
                query_parts.append(f"language:{criteria['language']}")
            
            if criteria.get('location'):
                query_parts.append(f"location:{criteria['location']}")
            
            if criteria.get('min_followers'):
                query_parts.append(f"followers:>={criteria['min_followers']}")
            
            if criteria.get('min_repos'):
                query_parts.append(f"repos:>={criteria['min_repos']}")
            
            if criteria.get('company'):
                query_parts.append(f"company:{criteria['company']}")
            
            # Add type:user to search for users specifically
            query_parts.append("type:user")
            
            query = " ".join(query_parts)
            print(f"Searching users with query: {query}")
            
            users = self.github.search_users(query)
            discovered_users = []
            
            for user in users:
                if len(discovered_users) >= limit:
                    break
                discovered_users.append(user.login)
            
            print(f"Discovered {len(discovered_users)} users from search criteria")
            return discovered_users
            
        except Exception as e:
            print(f"Error discovering users by search: {e}")
            return []
    
    def discover_from_popular_repos(self, topics: list = None, limit: int = DEFAULT_DISCOVERY_LIMIT):
        """
        Discover developers from popular repositories in specific topics.
        
        Args:
            topics (list, optional): List of topics to search. Uses default topics if None.
            limit (int): Maximum number of developers to discover
            
        Returns:
            List[str]: List of discovered GitHub usernames
        """
        try:
            discovered_users = set()
            
            if not topics:
                topics = DEFAULT_TOPIC_LIST
            
            for topic in topics:
                if len(discovered_users) >= limit:
                    break
                
                try:
                    # Search for repositories with specific topics
                    query = f"topic:{topic} stars:>100"
                    repos = self.github.search_repositories(query, sort="stars", order="desc")
                    
                    processed = 0
                    for repo in repos:
                        if len(discovered_users) >= limit or processed >= 10:
                            break
                        
                        try:
                            # Add repository owner
                            if repo.owner and repo.owner.type == "User":
                                discovered_users.add(repo.owner.login)
                            
                            # Add top contributors
                            contributors = repo.get_contributors()
                            for contributor in list(contributors)[:3]:
                                if len(discovered_users) >= limit:
                                    break
                                if contributor.type == "User":
                                    discovered_users.add(contributor.login)
                            
                            processed += 1
                            
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"Error processing topic {topic}: {e}")
                    continue
            
            print(f"Discovered {len(discovered_users)} developers from popular repositories")
            return list(discovered_users)[:limit]
            
        except Exception as e:
            print(f"Error discovering from popular repos: {e}")
            return []
    
    def discover_active_developers(self, days_back: int = 7, limit: int = DEFAULT_DISCOVERY_LIMIT):
        """
        Discover recently active developers.
        
        Args:
            days_back (int): Number of days to look back for activity
            limit (int): Maximum number of developers to discover
            
        Returns:
            List[str]: List of discovered GitHub usernames
        """
        try:
            discovered_users = set()
            
            # Search for recently pushed repositories
            recent_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            query = f"pushed:>{recent_date} stars:>10"
            
            print(f"Searching for active developers in the last {days_back} days")
            
            repos = self.github.search_repositories(query, sort="updated", order="desc")
            
            processed_repos = 0
            for repo in repos:
                if len(discovered_users) >= limit:
                    break
                
                try:
                    # Get repository owner if it's a user
                    if repo.owner and repo.owner.type == "User":
                        discovered_users.add(repo.owner.login)
                    
                    # Get recent contributors
                    try:
                        contributors = repo.get_contributors()
                        for contributor in list(contributors)[:3]:
                            if len(discovered_users) >= limit:
                                break
                            if contributor.type == "User":
                                discovered_users.add(contributor.login)
                    except:
                        pass
                    
                    processed_repos += 1
                    if processed_repos >= 30:  # Limit API calls
                        break
                        
                except Exception as e:
                    continue
            
            print(f"Discovered {len(discovered_users)} active developers")
            return list(discovered_users)[:limit]
            
        except Exception as e:
            print(f"Error discovering active developers: {e}")
            return []
    
    def discover_by_organization(self, org_names: list, limit: int = DEFAULT_DISCOVERY_LIMIT):
        """
        Discover developers from specific organizations.
        
        Args:
            org_names (list): List of organization names to search
            limit (int): Maximum number of developers to discover
            
        Returns:
            List[str]: List of discovered GitHub usernames
        """
        try:
            discovered_users = set()
            
            for org_name in org_names:
                if len(discovered_users) >= limit:
                    break
                
                try:
                    org = self.github.get_organization(org_name)
                    members = org.get_members()
                    
                    for member in members:
                        if len(discovered_users) >= limit:
                            break
                        discovered_users.add(member.login)
                    
                except Exception as e:
                    print(f"Error accessing organization {org_name}: {e}")
                    continue
            
            print(f"Discovered {len(discovered_users)} developers from organizations")
            return list(discovered_users)[:limit]
            
        except Exception as e:
            print(f"Error discovering from organizations: {e}")
            return []
    
    def discover_comprehensive(self, preferences: dict = None, total_limit: int = 100):
        """
        Comprehensive discovery using multiple methods.
        
        Args:
            preferences (dict, optional): Discovery preferences and filters
            total_limit (int): Total number of users to discover across all methods
            
        Returns:
            List[str]: List of discovered GitHub usernames
        """
        try:
            all_discovered = set()
            methods_limit = total_limit // 4  # Distribute across 4 methods
            
            if not preferences:
                preferences = {}
            
            print("Starting comprehensive discovery...")
            
            # Method 1: Trending developers
            try:
                trending = self.discover_trending_developers(
                    language=preferences.get('language'),
                    location=preferences.get('location'),
                    limit=methods_limit
                )
                all_discovered.update(trending)
                print(f"Added {len(trending)} from trending developers")
            except Exception as e:
                print(f"Error in trending discovery: {e}")
            
            # Method 2: Search criteria
            try:
                search_criteria = {
                    'language': preferences.get('language'),
                    'location': preferences.get('location'),
                    'min_followers': preferences.get('min_followers', 10),
                    'min_repos': preferences.get('min_repos', 5)
                }
                search_users = self.discover_by_search_criteria(search_criteria, methods_limit)
                all_discovered.update(search_users)
                print(f"Added {len(search_users)} from search criteria")
            except Exception as e:
                print(f"Error in search discovery: {e}")
            
            # Method 3: Popular repositories
            try:
                popular_users = self.discover_from_popular_repos(
                    topics=preferences.get('topics'),
                    limit=methods_limit
                )
                all_discovered.update(popular_users)
                print(f"Added {len(popular_users)} from popular repositories")
            except Exception as e:
                print(f"Error in popular repos discovery: {e}")
            
            # Method 4: Active developers
            try:
                active_users = self.discover_active_developers(
                    days_back=preferences.get('activity_days', 7),
                    limit=methods_limit
                )
                all_discovered.update(active_users)
                print(f"Added {len(active_users)} from active developers")
            except Exception as e:
                print(f"Error in active discovery: {e}")
            
            result = list(all_discovered)[:total_limit]
            print(f"Comprehensive discovery completed: {len(result)} unique users found")
            return result
            
        except Exception as e:
            print(f"Error in comprehensive discovery: {e}")
            return [] 