import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import re
from github import Github, GithubException
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Dict, Optional
import logging
import numpy as np
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import threading
import argparse
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global GitHub token (can be set via GUI or environment variable)
GITHUB_TOKEN = ""

class AutoProfileDiscovery:
    def __init__(self, github_token: str = None):
        self.token = github_token or GITHUB_TOKEN
        if not self.token:
            raise ValueError("GitHub token is required")
        self.github = Github(self.token)
        self.headers = {'Authorization': f'token {self.token}'}
    
    def discover_trending_developers(self, language: str = None, location: str = None, limit: int = 50):
        """Discover developers from trending repositories."""
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
    
    def discover_by_search_criteria(self, criteria: dict, limit: int = 50):
        """Discover users based on search criteria."""
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
    
    def discover_from_popular_repos(self, topics: list = None, limit: int = 50):
        """Discover developers from popular repositories in specific topics."""
        try:
            discovered_users = set()
            
            if not topics:
                topics = ['machine-learning', 'web-development', 'mobile', 'data-science', 
                         'artificial-intelligence', 'blockchain', 'devops', 'frontend', 'backend']
            
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
    
    def discover_active_developers(self, days_back: int = 7, limit: int = 50):
        """Discover recently active developers."""
        try:
            discovered_users = set()
            
            # Search for recently updated repositories
            recent_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            query = f"pushed:>{recent_date} stars:>10"
            repos = self.github.search_repositories(query, sort="updated", order="desc")
            
            processed = 0
            for repo in repos:
                if len(discovered_users) >= limit or processed >= 30:
                    break
                
                try:
                    # Add repository owner if recently active
                    if repo.owner and repo.owner.type == "User":
                        discovered_users.add(repo.owner.login)
                    
                    # Get recent commits to find active contributors
                    commits = repo.get_commits(since=datetime.now() - timedelta(days=days_back))
                    for commit in list(commits)[:5]:
                        if len(discovered_users) >= limit:
                            break
                        if commit.author and commit.author.type == "User":
                            discovered_users.add(commit.author.login)
                    
                    processed += 1
                    
                except Exception as e:
                    continue
            
            print(f"Discovered {len(discovered_users)} recently active developers")
            return list(discovered_users)[:limit]
            
        except Exception as e:
            print(f"Error discovering active developers: {e}")
            return []
    
    def discover_by_organization(self, org_names: list, limit: int = 50):
        """Discover developers from specific organizations."""
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
                    print(f"Error processing organization {org_name}: {e}")
                    continue
            
            print(f"Discovered {len(discovered_users)} developers from organizations")
            return list(discovered_users)[:limit]
            
        except Exception as e:
            print(f"Error discovering from organizations: {e}")
            return []
    
    def discover_comprehensive(self, preferences: dict = None, total_limit: int = 100):
        """Comprehensive discovery using multiple methods."""
        if not preferences:
            preferences = {
                'languages': ['python', 'javascript', 'java', 'go', 'rust'],
                'topics': ['machine-learning', 'web-development', 'mobile'],
                'min_followers': 50,
                'include_trending': True,
                'include_active': True,
                'days_back': 7
            }
        
        all_discovered = set()
        per_method_limit = total_limit // 4  # Divide among methods
        
        try:
            # Method 1: Trending developers
            if preferences.get('include_trending', True):
                for lang in preferences.get('languages', ['python'])[:2]:
                    trending = self.discover_trending_developers(
                        language=lang, 
                        limit=per_method_limit // 2
                    )
                    all_discovered.update(trending)
                    if len(all_discovered) >= total_limit:
                        break
            
            # Method 2: Search-based discovery
            if len(all_discovered) < total_limit:
                search_criteria = {
                    'min_followers': preferences.get('min_followers', 50),
                    'min_repos': preferences.get('min_repos', 5)
                }
                
                for lang in preferences.get('languages', ['python'])[:2]:
                    search_criteria['language'] = lang
                    search_users = self.discover_by_search_criteria(
                        search_criteria, 
                        limit=per_method_limit // 2
                    )
                    all_discovered.update(search_users)
                    if len(all_discovered) >= total_limit:
                        break
            
            # Method 3: Popular repositories
            if len(all_discovered) < total_limit:
                popular = self.discover_from_popular_repos(
                    topics=preferences.get('topics'),
                    limit=per_method_limit
                )
                all_discovered.update(popular)
            
            # Method 4: Recently active developers
            if len(all_discovered) < total_limit and preferences.get('include_active', True):
                active = self.discover_active_developers(
                    days_back=preferences.get('days_back', 7),
                    limit=per_method_limit
                )
                all_discovered.update(active)
            
            final_list = list(all_discovered)[:total_limit]
            print(f"Comprehensive discovery completed: {len(final_list)} unique developers found")
            
            return final_list
            
        except Exception as e:
            print(f"Error in comprehensive discovery: {e}")
            return list(all_discovered)[:total_limit]

class AdvancedGitHubMiner:
    def __init__(self, github_token: str = None, progress_callback=None, stop_event=None):
        if github_token is None:
            github_token = GITHUB_TOKEN
            
        if not github_token or github_token.strip() == "":
            raise ValueError("Invalid or empty GitHub token provided")
        self.token = github_token
        self.progress_callback = progress_callback
        self.stop_event = stop_event
        try:
            self.github = Github(github_token)
            self.github.get_user().login
        except GithubException as e:
            raise ValueError(f"Invalid GitHub token: {e}")
        self.headers = {'Authorization': f'token {github_token}'}
        
    def mine_github_archive(self, date_range: tuple, event_types: List[str] = None):
        if not isinstance(date_range, tuple) or len(date_range) != 2:
            raise ValueError("date_range must be a tuple of (start_date, end_date)")
        try:
            start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
            end_date = datetime.strptime(date_range[1], '%Y-%m-%d')
            if start_date > end_date:
                raise ValueError("start_date cannot be later than end_date")
        except ValueError as e:
            raise ValueError(f"Invalid date format in date_range: {e}")
        
        if event_types is None:
            event_types = ['PushEvent', 'PullRequestEvent', 'IssuesEvent', 'CreateEvent']
        
        events_data = []
        current_date = start_date
        while current_date <= end_date:
            for hour in range(24):
                date_str = current_date.strftime('%Y-%m-%d')
                url = f"https://data.gharchive.org/{date_str}-{hour}.json.gz"
                try:
                    logging.info(f"Processing: {url}")
                except Exception as e:
                    logging.error(f"Error processing {url}: {e}")
                    continue
            current_date += timedelta(days=1)
        
        return events_data
    
    def get_contributor_network(self, repo_owner: str, repo_name: str) -> Dict:
        if not repo_owner or not repo_name:
            raise ValueError("repo_owner and repo_name cannot be empty")
        
        try:
            repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            contributor_data = []
            
            try:
                contributors = repo.get_contributors()
                for contributor in contributors:
                    contrib_info = {
                        'login': contributor.login,
                        'contributions': contributor.contributions,
                        'followers': contributor.followers,
                        'following': contributor.following,
                        'public_repos': contributor.public_repos
                    }
                    contributor_data.append(contrib_info)
            except GithubException as e:
                logging.warning(f"No contributors found for {repo_owner}/{repo_name}: {e}")
            
            collaboration_data = []
            try:
                pull_requests = repo.get_pulls(state='all')
                for pr in pull_requests:
                    if pr.user and pr.merged_by and pr.user.login != pr.merged_by.login:
                        collaboration_data.append({
                            'author': pr.user.login,
                            'merger': pr.merged_by.login,
                            'created_at': pr.created_at,
                            'merged_at': pr.merged_at
                        })
            except GithubException as e:
                logging.warning(f"No pull requests found for {repo_owner}/{repo_name}: {e}")
            
            return {
                'contributors': contributor_data,
                'collaborations': collaboration_data
            }
        except GithubException as e:
            logging.error(f"Error getting contributor network for {repo_owner}/{repo_name}: {e}")
            return {}
    
    def analyze_development_patterns(self, username: str) -> Dict:
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            user = self.github.get_user(username)
            repos = list(user.get_repos())
            
            patterns = {
                'commit_frequency': [],
                'commit_timing': {'hours': [], 'days': []},
                'repository_lifecycle': [],
                'language_evolution': {},
                'productivity_streaks': {},
                'commit_comments': [],
                'issue_comments': [],
                'pr_reviews': []
            }
            
            for repo in repos[:10]:
                try:
                    if repo.fork:
                        logging.info(f"Skipping fork: {repo.name} for user {username}")
                        continue
                    
                    commits = list(repo.get_commits(author=username))
                    commit_dates = [commit.commit.author.date for commit in commits]
                    patterns['commit_frequency'].extend(commit_dates)
                    
                    for date in commit_dates:
                        patterns['commit_timing']['hours'].append(date.hour)
                        patterns['commit_timing']['days'].append(date.weekday())
                    
                    if commit_dates:
                        first_commit = min(commit_dates)
                        last_commit = max(commit_dates)
                        lifecycle_days = (last_commit - first_commit).days
                        patterns['repository_lifecycle'].append({
                            'repo_name': repo.name,
                            'lifecycle_days': lifecycle_days,
                            'total_commits': len(commits),
                            'commits_per_day': len(commits) / max(lifecycle_days, 1)
                        })
                    
                    languages = repo.get_languages()
                    repo_date = repo.created_at
                    for lang, bytes_count in languages.items():
                        if lang not in patterns['language_evolution']:
                            patterns['language_evolution'][lang] = []
                        patterns['language_evolution'][lang].append({
                            'date': repo_date,
                            'bytes': bytes_count,
                            'repo': repo.name
                        })
                    
                    for commit in commits[:50]:
                        try:
                            comments = commit.get_comments()
                            for comment in comments:
                                if comment.user and comment.user.login == username:
                                    patterns['commit_comments'].append({
                                        'repo': repo.name,
                                        'commit_sha': commit.sha,
                                        'comment_body': comment.body,
                                        'created_at': comment.created_at
                                    })
                        except GithubException as e:
                            logging.warning(f"Error fetching commit comments for {repo.name}: {e}")
                    
                    try:
                        issues = repo.get_issues(creator=username, state='all')
                        for issue in issues[:50]:
                            comments = issue.get_comments()
                            for comment in comments:
                                if comment.user and comment.user.login == username:
                                    patterns['issue_comments'].append({
                                        'repo': repo.name,
                                        'issue_number': issue.number,
                                        'comment_body': comment.body,
                                        'created_at': comment.created_at
                                    })
                    except GithubException as e:
                        logging.warning(f"Error fetching issues for {repo.name}: {e}")
                    
                    try:
                        prs = repo.get_pulls(state='all')
                        for pr in prs[:50]:
                            reviews = pr.get_reviews()
                            for review in reviews:
                                if review.user and review.user.login == username:
                                    patterns['pr_reviews'].append({
                                        'repo': repo.name,
                                        'pr_number': pr.number,
                                        'review_state': review.state,
                                        'review_body': review.body,
                                        'submitted_at': review.submitted_at
                                    })
                    except GithubException as e:
                        logging.warning(f"Error fetching pull requests for {repo.name}: {e}")
                
                except Exception as e:
                    logging.error(f"Error processing repository {repo.name} for user {username}: {e}")
                    continue
            
            if patterns['commit_frequency']:
                sorted_dates = sorted(set(date.date() for date in patterns['commit_frequency']))
                current_streak = 1
                max_streak = 1
                for i in range(1, len(sorted_dates)):
                    if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                        current_streak += 1
                        max_streak = max(max_streak, current_streak)
                    else:
                        current_streak = 1
                patterns['productivity_streaks'] = {
                    'max_streak': max_streak,
                    'total_active_days': len(sorted_dates)
                }
            
            return patterns
        except GithubException as e:
            logging.error(f"Error analyzing development patterns for {username}: {e}")
            return {}
    
    def collect_issue_sentiment_data(self, repo_owner: str, repo_name: str) -> List[Dict]:
        if not repo_owner or not repo_name:
            raise ValueError("repo_owner and repo_name cannot be empty")
        
        try:
            repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            issue_data = []
            
            try:
                issues = repo.get_issues(state='all')
                for issue in issues:
                    issue_info = {
                        'number': issue.number,
                        'title': issue.title,
                        'body': issue.body or '',
                        'state': issue.state,
                        'created_at': issue.created_at,
                        'closed_at': issue.closed_at,
                        'user': issue.user.login if issue.user else None,
                        'labels': [label.name for label in issue.labels],
                        'comments_count': issue.comments,
                        'comments': [],
                        'resolution_time_hours': None
                    }
                    if issue.closed_at:
                        issue_info['resolution_time_hours'] = (issue.closed_at - issue.created_at).total_seconds() / 3600
                    
                    try:
                        comments = issue.get_comments()
                        for comment in comments:
                            issue_info['comments'].append({
                                'user': comment.user.login if comment.user else None,
                                'body': comment.body,
                                'created_at': comment.created_at
                            })
                    except GithubException as e:
                        logging.warning(f"Error fetching comments for issue {issue.number} in {repo_owner}/{repo_name}: {e}")
                    
                    issue_data.append(issue_info)
            except GithubException as e:
                logging.warning(f"No issues found for {repo_owner}/{repo_name}: {e}")
            
            return issue_data
        except GithubException as e:
            logging.error(f"Error collecting issue data for {repo_owner}/{repo_name}: {e}")
            return []
    
    def collect_extended_user_data(self, username: str) -> Dict:
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            user = self.github.get_user(username)
            extended_data = {
                'email': user.email,
                'location': user.location,
                'bio': user.bio,
                'company': user.company,
                'blog': user.blog,
                'twitter_username': user.twitter_username,
                'hireable': user.hireable,
                'public_gists': user.public_gists,
                'avatar_url': user.avatar_url,
                'starred_repos': [],
                'watched_repos': [],
                'gists': [],
                'organizations': [],
                'events': []
            }
            
            try:
                starred = user.get_starred()
                extended_data['starred_repos'] = [{'full_name': repo.full_name, 'stars': repo.stargazers_count} for repo in starred[:10]]
            except GithubException as e:
                logging.warning(f"Error fetching starred repos for {username}: {e}")
            
            try:
                watched = user.get_watched()
                extended_data['watched_repos'] = [{'full_name': repo.full_name, 'watchers': repo.watchers_count} for repo in watched[:10]]
            except GithubException as e:
                logging.warning(f"Error fetching watched repos for {username}: {e}")
            
            try:
                gists = user.get_gists()
                extended_data['gists'] = [{'id': gist.id, 'description': gist.description, 'created_at': gist.created_at} for gist in gists[:10]]
            except GithubException as e:
                logging.warning(f"Error fetching gists for {username}: {e}")
            
            try:
                orgs = user.get_orgs()
                extended_data['organizations'] = [{'login': org.login, 'description': org.description} for org in orgs]
            except GithubException as e:
                logging.warning(f"Error fetching organizations for {username}: {e}")
            
            try:
                events = user.get_events()
                extended_data['events'] = [{'type': event.type, 'repo': event.repo.name, 'created_at': event.created_at} for event in events[:50]]
            except GithubException as e:
                logging.warning(f"Error fetching events for {username}: {e}")
            
            return extended_data
        except GithubException as e:
            logging.error(f"Error collecting extended user data for {username}: {e}")
            return {}
    
    def collect_extended_repo_data(self, repo_owner: str, repo_name: str) -> Dict:
        if not repo_owner or not repo_name:
            raise ValueError("repo_owner and repo_name cannot be empty")
        
        try:
            repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            extended_data = {
                'branches': [],
                'releases': [],
                'tags': [],
                'commit_stats': [],
                'code_frequency': [],
                'topics': repo.get_topics(),
                'license': repo.license.name if repo.license else None,
                'forks_history': []
            }
            
            try:
                branches = repo.get_branches()
                extended_data['branches'] = [{'name': branch.name, 'protected': branch.protected} for branch in branches[:10]]
            except GithubException as e:
                logging.warning(f"Error fetching branches for {repo_owner}/{repo_name}: {e}")
            
            try:
                releases = repo.get_releases()
                extended_data['releases'] = [{'tag_name': release.tag_name, 'created_at': release.created_at} for release in releases[:10]]
            except GithubException as e:
                logging.warning(f"Error fetching releases for {repo_owner}/{repo_name}: {e}")
            
            try:
                tags = repo.get_tags()
                extended_data['tags'] = [{'name': tag.name, 'commit_sha': tag.commit.sha} for tag in tags[:10]]
            except GithubException as e:
                logging.warning(f"Error fetching tags for {repo_owner}/{repo_name}: {e}")
            
            try:
                stats = repo.get_stats_commit_activity()
                if stats:
                    extended_data['commit_stats'] = [{'week': stat.week, 'total': stat.total} for stat in stats]
            except GithubException as e:
                logging.warning(f"Error fetching commit stats for {repo_owner}/{repo_name}: {e}")
            
            try:
                code_freq = repo.get_stats_code_frequency()
                if code_freq:
                    extended_data['code_frequency'] = [{'week': stat.week, 'additions': stat.additions, 'deletions': stat.deletions} for stat in code_freq]
            except GithubException as e:
                logging.warning(f"Error fetching code frequency for {repo_owner}/{repo_name}: {e}")
            
            try:
                forks = repo.get_forks()
                extended_data['forks_history'] = [{'owner': fork.owner.login, 'created_at': fork.created_at} for fork in forks[:10]]
            except GithubException as e:
                logging.warning(f"Error fetching forks for {repo_owner}/{repo_name}: {e}")
            
            return extended_data
        except GithubException as e:
            logging.error(f"Error collecting extended repo data for {repo_owner}/{repo_name}: {e}")
            return {}
    
    def analyze_commit_activity(self, username: str, days: int = 90) -> Dict:
        """Analyze recent commit activity for a user."""
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            if self.stop_event and self.stop_event.is_set():
                return {}
            
            user = self.github.get_user(username)
            repos = list(user.get_repos())
            
            # Use timezone-naive datetime to avoid issues
            cutoff_date = datetime.now() - timedelta(days=days)
            
            activity_data = {
                'total_recent_commits': 0,
                'active_days': set(),
                'commit_frequency_by_day': {},
                'commit_frequency_by_hour': {},
                'recent_commits': [],
                'most_active_repo': None,
                'commit_streaks': [],
                'avg_commits_per_day': 0,
                'repositories_analyzed': 0,
                'total_repositories': len([r for r in repos if not r.fork])
            }
            
            repo_commit_counts = {}
            
            # Filter out forks and get only user's original repos
            original_repos = [repo for repo in repos if not repo.fork]
            
            for repo in original_repos[:15]:  # Limit to avoid rate limits
                try:
                    if self.stop_event and self.stop_event.is_set():
                        break
                    
                    activity_data['repositories_analyzed'] += 1
                    logging.info(f"Analyzing commits for repo: {repo.name}")
                    
                    # Try different approaches to get commits
                    commits = []
                    try:
                        # Method 1: Get commits by author since cutoff date
                        commits = list(repo.get_commits(author=username, since=cutoff_date))
                    except GithubException as e:
                        logging.warning(f"Method 1 failed for {repo.name}: {e}")
                        try:
                            # Method 2: Get recent commits and filter by author
                            all_commits = list(repo.get_commits(since=cutoff_date))
                            commits = [c for c in all_commits if c.author and c.author.login == username]
                        except GithubException as e2:
                            logging.warning(f"Method 2 failed for {repo.name}: {e2}")
                            try:
                                # Method 3: Get commits without date filter and filter manually
                                recent_commits = list(repo.get_commits()[:50])  # Get last 50 commits
                                commits = []
                                for c in recent_commits:
                                    if c.author and c.author.login == username:
                                        commit_date = c.commit.author.date
                                        if commit_date.tzinfo:
                                            commit_date = commit_date.replace(tzinfo=None)
                                        if commit_date >= cutoff_date:
                                            commits.append(c)
                            except GithubException as e3:
                                logging.warning(f"Method 3 failed for {repo.name}: {e3}")
                                continue
                    
                    repo_commits = 0
                    
                    for commit in commits:
                        try:
                            commit_date = commit.commit.author.date
                            activity_data['total_recent_commits'] += 1
                            repo_commits += 1
                            
                            # Convert to naive datetime for consistency
                            if commit_date.tzinfo:
                                commit_date = commit_date.replace(tzinfo=None)
                            
                            day_key = commit_date.strftime('%Y-%m-%d')
                            hour_key = str(commit_date.hour)
                            
                            activity_data['active_days'].add(day_key)
                            activity_data['commit_frequency_by_day'][day_key] = activity_data['commit_frequency_by_day'].get(day_key, 0) + 1
                            activity_data['commit_frequency_by_hour'][hour_key] = activity_data['commit_frequency_by_hour'].get(hour_key, 0) + 1
                            
                            # Get commit stats safely
                            additions = 0
                            deletions = 0
                            try:
                                if commit.stats:
                                    additions = commit.stats.additions
                                    deletions = commit.stats.deletions
                            except:
                                pass
                            
                            activity_data['recent_commits'].append({
                                'repo': repo.name,
                                'sha': commit.sha,
                                'message': commit.commit.message[:100] if commit.commit.message else "",
                                'date': commit_date,
                                'additions': additions,
                                'deletions': deletions
                            })
                        except Exception as e:
                            logging.warning(f"Error processing commit {commit.sha}: {e}")
                            continue
                    
                    repo_commit_counts[repo.name] = repo_commits
                    logging.info(f"Found {repo_commits} commits in {repo.name}")
                    
                except GithubException as e:
                    logging.warning(f"Error getting commits for repo {repo.name}: {e}")
                    continue
                except Exception as e:
                    logging.error(f"Unexpected error analyzing repo {repo.name}: {e}")
                    continue
            
            # Find most active repository
            if repo_commit_counts:
                activity_data['most_active_repo'] = max(repo_commit_counts, key=repo_commit_counts.get)
            
            # Calculate average commits per day
            if activity_data['active_days']:
                activity_data['avg_commits_per_day'] = activity_data['total_recent_commits'] / len(activity_data['active_days'])
            
            # Convert set to list for JSON serialization
            activity_data['active_days'] = list(activity_data['active_days'])
            
            logging.info(f"Commit activity analysis complete: {activity_data['total_recent_commits']} commits found")
            return activity_data
            
        except GithubException as e:
            logging.error(f"Error analyzing commit activity for {username}: {e}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error in commit activity analysis for {username}: {e}")
            return {}
    
    def analyze_contribution_activity(self, username: str) -> Dict:
        """Analyze overall contribution activity and patterns for a user."""
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            if self.stop_event and self.stop_event.is_set():
                return {}
            
            user = self.github.get_user(username)
            
            contribution_data = {
                'contribution_years': [],
                'total_contributions': 0,
                'current_streak': 0,
                'longest_streak': 0,
                'contribution_level': 'Unknown',
                'public_contributions': 0,
                'private_contributions': 0,
                'issues_opened': 0,
                'issues_closed': 0,
                'pull_requests_opened': 0,
                'pull_requests_merged': 0,
                'repositories_contributed_to': 0,
                'followers_gained_recently': 0,
                'following_activity': 0
            }
            
            # Get user's events for contribution analysis
            try:
                events = list(user.get_events()[:100])  # Get recent 100 events
                contribution_data['recent_events_count'] = len(events)
                
                # Analyze different types of events
                event_types = {}
                recent_contributions = 0
                repositories_set = set()
                
                for event in events:
                    try:
                        if self.stop_event and self.stop_event.is_set():
                            break
                        
                        event_type = event.type
                        event_types[event_type] = event_types.get(event_type, 0) + 1
                        
                        # Count recent contributions (last 30 days)
                        event_date = event.created_at
                        if event_date.tzinfo:
                            event_date = event_date.replace(tzinfo=None)
                        
                        if (datetime.now() - event_date).days <= 30:
                            recent_contributions += 1
                        
                        # Track repositories contributed to
                        if hasattr(event, 'repo') and event.repo:
                            repositories_set.add(event.repo.full_name)
                        
                        # Specific event analysis
                        if event_type == 'IssuesEvent':
                            if hasattr(event, 'payload') and event.payload.get('action') == 'opened':
                                contribution_data['issues_opened'] += 1
                            elif hasattr(event, 'payload') and event.payload.get('action') == 'closed':
                                contribution_data['issues_closed'] += 1
                        
                        elif event_type == 'PullRequestEvent':
                            if hasattr(event, 'payload') and event.payload.get('action') == 'opened':
                                contribution_data['pull_requests_opened'] += 1
                            elif hasattr(event, 'payload') and event.payload.get('action') == 'closed':
                                contribution_data['pull_requests_merged'] += 1
                        
                        elif event_type == 'PushEvent':
                            contribution_data['public_contributions'] += 1
                    
                    except Exception as e:
                        logging.warning(f"Error processing event: {e}")
                        continue
                
                contribution_data['event_types'] = event_types
                contribution_data['recent_contributions_30_days'] = recent_contributions
                contribution_data['repositories_contributed_to'] = len(repositories_set)
                
            except GithubException as e:
                logging.warning(f"Error getting events for {username}: {e}")
            
            # Analyze user's repositories for contribution patterns
            try:
                repos = list(user.get_repos())
                original_repos = [repo for repo in repos if not repo.fork]
                
                contribution_data['total_repositories'] = len(repos)
                contribution_data['original_repositories'] = len(original_repos)
                contribution_data['forked_repositories'] = len(repos) - len(original_repos)
                
                # Calculate total stars and forks earned
                total_stars = sum(repo.stargazers_count for repo in original_repos)
                total_forks = sum(repo.forks_count for repo in original_repos)
                total_watchers = sum(repo.watchers_count for repo in original_repos)
                
                contribution_data['total_stars_earned'] = total_stars
                contribution_data['total_forks_earned'] = total_forks
                contribution_data['total_watchers_earned'] = total_watchers
                
                # Analyze repository activity patterns
                recent_repos = [repo for repo in original_repos if (datetime.now() - repo.updated_at.replace(tzinfo=None) if repo.updated_at.tzinfo else repo.updated_at).days <= 90]
                contribution_data['recently_active_repositories'] = len(recent_repos)
                
                # Calculate contribution level based on activity
                if total_stars > 1000 or len(original_repos) > 50:
                    contribution_data['contribution_level'] = 'High'
                elif total_stars > 100 or len(original_repos) > 20:
                    contribution_data['contribution_level'] = 'Medium'
                elif total_stars > 10 or len(original_repos) > 5:
                    contribution_data['contribution_level'] = 'Low'
                else:
                    contribution_data['contribution_level'] = 'Beginner'
                
            except GithubException as e:
                logging.warning(f"Error analyzing repositories for {username}: {e}")
            
            # Get user's starred repositories for interest analysis
            try:
                starred_repos = list(user.get_starred()[:20])  # Get first 20 starred repos
                contribution_data['starred_repositories_count'] = len(starred_repos)
                
                # Analyze starred repositories' languages
                starred_languages = {}
                for starred_repo in starred_repos:
                    if starred_repo.language:
                        starred_languages[starred_repo.language] = starred_languages.get(starred_repo.language, 0) + 1
                
                contribution_data['starred_languages'] = starred_languages
                
            except GithubException as e:
                logging.warning(f"Error getting starred repositories for {username}: {e}")
            
            # Calculate activity score
            activity_score = 0
            activity_score += contribution_data.get('recent_contributions_30_days', 0) * 2
            activity_score += contribution_data.get('total_stars_earned', 0) * 0.1
            activity_score += contribution_data.get('original_repositories', 0) * 5
            activity_score += contribution_data.get('repositories_contributed_to', 0) * 3
            
            contribution_data['activity_score'] = round(activity_score, 2)
            
            logging.info(f"Contribution activity analysis complete for {username}")
            return contribution_data
            
        except GithubException as e:
            logging.error(f"Error analyzing contribution activity for {username}: {e}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error in contribution activity analysis for {username}: {e}")
            return {}
    
    def analyze_language_percentages(self, username: str) -> Dict:
        """Analyze language distribution across user's repositories."""
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            if self.stop_event and self.stop_event.is_set():
                return {}
            
            user = self.github.get_user(username)
            repos = list(user.get_repos())
            
            language_data = {}
            total_bytes = 0
            
            for repo in repos:
                try:
                    if self.stop_event and self.stop_event.is_set():
                        break
                    
                    if repo.fork:
                        continue
                    
                    languages = repo.get_languages()
                    for lang, bytes_count in languages.items():
                        language_data[lang] = language_data.get(lang, 0) + bytes_count
                        total_bytes += bytes_count
                        
                except GithubException as e:
                    logging.warning(f"Error getting languages for repo {repo.name}: {e}")
                    continue
            
            # Calculate percentages
            language_percentages = {}
            if total_bytes > 0:
                for lang, bytes_count in language_data.items():
                    language_percentages[lang] = round((bytes_count / total_bytes) * 100, 2)
            
            # Sort by percentage
            sorted_languages = dict(sorted(language_percentages.items(), key=lambda x: x[1], reverse=True))
            
            return {
                'language_percentages': sorted_languages,
                'total_languages': len(sorted_languages),
                'primary_language': list(sorted_languages.keys())[0] if sorted_languages else None,
                'language_diversity_score': len(sorted_languages)  # Simple diversity metric
            }
            
        except GithubException as e:
            logging.error(f"Error analyzing language percentages for {username}: {e}")
            return {}
    
    def get_top_repositories(self, username: str, limit: int = 10) -> Dict:
        """Get user's top repositories by various metrics."""
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            if self.stop_event and self.stop_event.is_set():
                return {}
            
            user = self.github.get_user(username)
            all_repos = list(user.get_repos())
            
            # Filter out forks
            original_repos = [repo for repo in all_repos if not repo.fork]
            
            if not original_repos:
                return {
                    'by_stars': [],
                    'by_forks': [],
                    'by_size': [],
                    'by_watchers': [],
                    'by_recent_activity': [],
                    'total_original_repos': 0,
                    'total_stars_earned': 0,
                    'total_forks_earned': 0
                }
            
            # Adjust limit based on available repositories
            actual_limit = min(limit, len(original_repos))
            
            # Sort by different metrics
            by_stars = sorted(original_repos, key=lambda r: r.stargazers_count, reverse=True)[:actual_limit]
            by_forks = sorted(original_repos, key=lambda r: r.forks_count, reverse=True)[:actual_limit]
            by_size = sorted(original_repos, key=lambda r: r.size, reverse=True)[:actual_limit]
            by_watchers = sorted(original_repos, key=lambda r: r.watchers_count, reverse=True)[:actual_limit]
            by_recent = sorted(original_repos, key=lambda r: r.updated_at, reverse=True)[:actual_limit]
            
            def repo_info(repo):
                return {
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'watchers': repo.watchers_count,
                    'language': repo.language,
                    'size': repo.size,
                    'created_at': repo.created_at,
                    'updated_at': repo.updated_at,
                    'topics': repo.get_topics()
                }
            
            return {
                'by_stars': [repo_info(repo) for repo in by_stars],
                'by_forks': [repo_info(repo) for repo in by_forks],
                'by_size': [repo_info(repo) for repo in by_size],
                'by_watchers': [repo_info(repo) for repo in by_watchers],
                'by_recent_activity': [repo_info(repo) for repo in by_recent],
                'total_original_repos': len(original_repos),
                'total_stars_earned': sum(repo.stargazers_count for repo in original_repos),
                'total_forks_earned': sum(repo.forks_count for repo in original_repos)
            }
            
        except GithubException as e:
            logging.error(f"Error getting top repositories for {username}: {e}")
            return {}
    
    def analyze_interests(self, username: str) -> Dict:
        """Analyze user interests based on repositories, topics, and activity."""
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            if self.stop_event and self.stop_event.is_set():
                return {}
            
            user = self.github.get_user(username)
            repos = list(user.get_repos())
            
            interests_data = {
                'repository_topics': {},
                'language_interests': {},
                'description_keywords': {},
                'starred_repo_topics': {},
                'organization_domains': [],
                'inferred_interests': []
            }
            
            # Analyze repository topics and descriptions
            for repo in repos:
                try:
                    if self.stop_event and self.stop_event.is_set():
                        break
                    
                    if repo.fork:
                        continue
                    
                    # Repository topics
                    topics = repo.get_topics()
                    for topic in topics:
                        interests_data['repository_topics'][topic] = interests_data['repository_topics'].get(topic, 0) + 1
                    
                    # Language interests
                    if repo.language:
                        interests_data['language_interests'][repo.language] = interests_data['language_interests'].get(repo.language, 0) + 1
                    
                    # Keywords from descriptions
                    if repo.description:
                        # Simple keyword extraction (can be improved with NLP)
                        words = re.findall(r'\b\w+\b', repo.description.lower())
                        tech_keywords = ['api', 'web', 'mobile', 'data', 'machine', 'learning', 'ai', 'cloud', 'database', 'frontend', 'backend', 'devops', 'security', 'blockchain', 'iot', 'game', 'bot', 'cli', 'library', 'framework', 'tool', 'automation', 'testing', 'monitoring']
                        for word in words:
                            if word in tech_keywords and len(word) > 2:
                                interests_data['description_keywords'][word] = interests_data['description_keywords'].get(word, 0) + 1
                    
                except GithubException as e:
                    logging.warning(f"Error analyzing repo {repo.name}: {e}")
                    continue
            
            # Analyze starred repositories (limited to avoid rate limits)
            try:
                starred_repos = user.get_starred()
                starred_count = 0
                for starred_repo in starred_repos:
                    if starred_count >= 50:  # Limit to avoid rate limits
                        break
                    
                    topics = starred_repo.get_topics()
                    for topic in topics:
                        interests_data['starred_repo_topics'][topic] = interests_data['starred_repo_topics'].get(topic, 0) + 1
                    starred_count += 1
                    
            except GithubException as e:
                logging.warning(f"Error analyzing starred repos for {username}: {e}")
            
            # Analyze organizations
            try:
                orgs = user.get_orgs()
                for org in orgs:
                    if org.company:
                        interests_data['organization_domains'].append(org.company)
                        
            except GithubException as e:
                logging.warning(f"Error analyzing organizations for {username}: {e}")
            
            # Generate inferred interests based on frequency
            all_topics = {}
            all_topics.update(interests_data['repository_topics'])
            all_topics.update(interests_data['starred_repo_topics'])
            all_topics.update(interests_data['description_keywords'])
            
            # Sort by frequency and take top interests
            sorted_interests = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)
            interests_data['inferred_interests'] = [interest for interest, count in sorted_interests[:20]]
            
            return interests_data
            
        except GithubException as e:
            logging.error(f"Error analyzing interests for {username}: {e}")
            return {}
    
    def parallel_data_collection(self, usernames: List[str], max_workers: int = 5) -> List[Dict]:
        if not usernames:
            raise ValueError("usernames list cannot be empty")
        if not all(isinstance(u, str) and u.strip() for u in usernames):
            raise ValueError("All usernames must be non-empty strings")
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        
        def collect_single_user(username):
            try:
                if self.stop_event and self.stop_event.is_set():
                    return None
                
                if self.progress_callback:
                    self.progress_callback(f"Collecting data for: {username}")
                user = self.github.get_user(username)
                
                if self.stop_event and self.stop_event.is_set():
                    return None
                
                if self.progress_callback:
                    self.progress_callback(f"Collecting extended user data for: {username}")
                extended_data = self.collect_extended_user_data(username)
                
                if self.stop_event and self.stop_event.is_set():
                    return None
                
                if self.progress_callback:
                    self.progress_callback(f"Analyzing development patterns for: {username}")
                development_patterns = self.analyze_development_patterns(username)
                
                if self.stop_event and self.stop_event.is_set():
                    return None
                
                if self.progress_callback:
                    self.progress_callback(f"Analyzing commit activity for: {username}")
                commit_activity = self.analyze_commit_activity(username)
                
                if self.stop_event and self.stop_event.is_set():
                    return None
                
                if self.progress_callback:
                    self.progress_callback(f"Analyzing contribution activity for: {username}")
                contribution_activity = self.analyze_contribution_activity(username)
                
                if self.stop_event and self.stop_event.is_set():
                    return None
                
                if self.progress_callback:
                    self.progress_callback(f"Analyzing language distribution for: {username}")
                language_percentages = self.analyze_language_percentages(username)
                
                if self.stop_event and self.stop_event.is_set():
                    return None
                
                if self.progress_callback:
                    self.progress_callback(f"Getting top repositories for: {username}")
                top_repositories = self.get_top_repositories(username)
                
                if self.stop_event and self.stop_event.is_set():
                    return None
                
                if self.progress_callback:
                    self.progress_callback(f"Analyzing interests for: {username}")
                interests = self.analyze_interests(username)
                
                user_data = {
                    'username': username,
                    'name': user.name,
                    'followers': user.followers,
                    'following': user.following,
                    'public_repos': user.public_repos,
                    'created_at': user.created_at,
                    'extended_user_data': extended_data,
                    'development_patterns': development_patterns,
                    'commit_activity': commit_activity,
                    'contribution_activity': contribution_activity,
                    'language_percentages': language_percentages,
                    'top_repositories': top_repositories,
                    'interests': interests
                }
                
                if self.progress_callback:
                    self.progress_callback(f"Analyzing repositories for: {username}")
                
                repos = list(user.get_repos())[:5]
                if not repos:
                    logging.info(f"No repositories found for user: {username}")
                    user_data['repositories'] = []
                    return user_data
                
                logging.info(f"Found {len(repos)} repositories for user: {username}")
                repo_details = []
                for i, repo in enumerate(repos):
                    try:
                        if self.progress_callback:
                            self.progress_callback(f"Processing repository {i+1}/{len(repos)}: {repo.name}")
                        if repo.fork:
                            logging.info(f"Skipping fork: {repo.name} for user {username}")
                            continue
                        
                        repo_info = {
                            'name': repo.name,
                            'stars': repo.stargazers_count,
                            'forks': repo.forks_count,
                            'language': repo.language,
                            'size': repo.size,
                            'contributor_network': self.get_contributor_network(username, repo.name),
                            'issues': self.collect_issue_sentiment_data(username, repo.name),
                            'extended_repo_data': self.collect_extended_repo_data(username, repo.name)
                        }
                        repo_details.append(repo_info)
                    except Exception as e:
                        logging.error(f"Error processing repository {repo.name} for user {username}: {e}")
                        continue
                
                user_data['repositories'] = repo_details
                return user_data
            except GithubException as e:
                if self.progress_callback:
                    self.progress_callback(f"Error collecting data for {username}: {e}")
                logging.error(f"GitHub error collecting data for {username}: {e}")
                return None
            except Exception as e:
                if self.progress_callback:
                    self.progress_callback(f"Unexpected error for user {username}: {e}")
                logging.error(f"Unexpected error for user {username}: {e}")
                return None
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_username = {executor.submit(collect_single_user, username): username 
                                 for username in usernames}
            for future in as_completed(future_to_username):
                username = future_to_username[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    if self.progress_callback:
                        self.progress_callback(f"Error processing {username}: {e}")
                    logging.error(f"Error processing {username}: {e}")
        
        return results
    
    def export_for_machine_learning(self, dataset: List[Dict], filename: str):
        if not dataset:
            raise ValueError("dataset cannot be empty")
        if not filename or not filename.strip():
            raise ValueError("filename cannot be empty")
        
        ml_features = []
        for user_data in dataset:
            if not user_data:
                continue
            
            # Basic user features
            features = {
                'username': user_data.get('username'),
                'name': user_data.get('name'),
                'followers': user_data.get('followers', 0),
                'following': user_data.get('following', 0),
                'public_repos': user_data.get('public_repos', 0),
                'account_age_days': 0,  # Initialize with 0
                'mined_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Safely calculate account age
            try:
                created_at = user_data.get('created_at')
                if created_at:
                    # Convert string to datetime if needed
                    if isinstance(created_at, str):
                        created_at = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
                    
                    # Convert to naive datetime
                    if created_at.tzinfo:
                        created_at = created_at.replace(tzinfo=None)
                    
                    # Get current time as naive datetime
                    current_time = datetime.now()
                    
                    # Calculate age
                    features['account_age_days'] = (current_time - created_at).days
            except Exception as e:
                logging.warning(f"Error calculating account age: {e}")
                features['account_age_days'] = 0
            
            # Extended user data
            extended_data = user_data.get('extended_user_data', {})
            features.update({
                'email': extended_data.get('email'),
                'location': extended_data.get('location'),
                'bio': extended_data.get('bio'),
                'company': extended_data.get('company'),
                'blog': extended_data.get('blog'),
                'twitter_username': extended_data.get('twitter_username'),
                'hireable': extended_data.get('hireable'),
                'public_gists': extended_data.get('public_gists', 0),
                'avatar_url': extended_data.get('avatar_url'),
                'starred_repo_count': len(extended_data.get('starred_repos', [])),
                'watched_repo_count': len(extended_data.get('watched_repos', [])),
                'gist_count': len(extended_data.get('gists', [])),
                'organization_count': len(extended_data.get('organizations', [])),
                'event_count': len(extended_data.get('events', []))
            })
            
            # Development patterns
            patterns = user_data.get('development_patterns', {})
            if patterns:
                features.update({
                    'total_commits': len(patterns.get('commit_frequency', [])),
                    'avg_commits_per_repo': np.mean([r.get('total_commits', 0) for r in patterns.get('repository_lifecycle', [])]) if patterns.get('repository_lifecycle') else 0,
                    'max_productivity_streak': patterns.get('productivity_streaks', {}).get('max_streak', 0),
                    'total_active_days': patterns.get('productivity_streaks', {}).get('total_active_days', 0),
                    'languages_used': len(patterns.get('language_evolution', {})),
                    'commit_comments_count': len(patterns.get('commit_comments', [])),
                    'issue_comments_count': len(patterns.get('issue_comments', [])),
                    'pr_reviews_count': len(patterns.get('pr_reviews', []))
                })
                
                # Add language evolution data
                for lang, data in patterns.get('language_evolution', {}).items():
                    features[f'language_{lang}_bytes'] = sum(item.get('bytes', 0) for item in data)
                    features[f'language_{lang}_repos'] = len(data)
            
            # Repository data
            repos = user_data.get('repositories', [])
            if repos:
                features.update({
                    'total_repos_analyzed': len(repos),
                    'avg_repo_stars': np.mean([r.get('stars', 0) for r in repos]),
                    'avg_repo_forks': np.mean([r.get('forks', 0) for r in repos]),
                    'avg_repo_size': np.mean([r.get('size', 0) for r in repos]),
                    'total_contributors': sum(len(r.get('contributor_network', {}).get('contributors', [])) for r in repos),
                    'avg_branches': np.mean([len(r.get('extended_repo_data', {}).get('branches', [])) for r in repos]),
                    'avg_releases': np.mean([len(r.get('extended_repo_data', {}).get('releases', [])) for r in repos]),
                    'avg_tags': np.mean([len(r.get('extended_repo_data', {}).get('tags', [])) for r in repos]),
                    'avg_issues': np.mean([len(r.get('issues', [])) for r in repos]),
                    'avg_resolution_time': np.mean([issue.get('resolution_time_hours', 0) for r in repos for issue in r.get('issues', []) if issue.get('resolution_time_hours')])
                })
                
                # Add repository complexity metrics
                complexity_metrics = {
                    'avg_lines_of_code': 0,
                    'avg_comment_ratio': 0,
                    'avg_function_count': 0,
                    'avg_class_count': 0,
                    'avg_file_count': 0
                }
                
                for repo in repos:
                    complexity = repo.get('complexity', {})
                    if complexity:
                        complexity_metrics['avg_lines_of_code'] += complexity.get('lines_of_code', 0)
                        complexity_metrics['avg_comment_ratio'] += complexity.get('comment_ratio', 0)
                        complexity_metrics['avg_function_count'] += complexity.get('function_count', 0)
                        complexity_metrics['avg_class_count'] += complexity.get('class_count', 0)
                        complexity_metrics['avg_file_count'] += complexity.get('file_count', 0)
                
                if len(repos) > 0:
                    for key in complexity_metrics:
                        complexity_metrics[key] /= len(repos)
                
                features.update(complexity_metrics)
                
                # Add repository-specific data
                for i, repo in enumerate(repos):
                    repo_name = repo.get('name', f'repo_{i}')
                    features.update({
                        f'{repo_name}_stars': repo.get('stars', 0),
                        f'{repo_name}_forks': repo.get('forks', 0),
                        f'{repo_name}_size': repo.get('size', 0),
                        f'{repo_name}_language': repo.get('language'),
                        f'{repo_name}_contributors': len(repo.get('contributor_network', {}).get('contributors', [])),
                        f'{repo_name}_issues': len(repo.get('issues', [])),
                        f'{repo_name}_branches': len(repo.get('extended_repo_data', {}).get('branches', [])),
                        f'{repo_name}_releases': len(repo.get('extended_repo_data', {}).get('releases', [])),
                        f'{repo_name}_tags': len(repo.get('extended_repo_data', {}).get('tags', []))
                    })
            
            ml_features.append(features)
        
        # Convert to DataFrame and handle any non-serializable values
        df = pd.DataFrame(ml_features)
        for col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
        
        # Append to CSV file
        csv_file = "github_data_ml_features.csv"
        if os.path.exists(csv_file):
            df.to_csv(csv_file, mode='a', header=False, index=False)
        else:
            df.to_csv(csv_file, index=False)
        
        # Append to JSON file
        json_file = "github_data_raw.json"
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []
        
        # Convert datetime objects to strings before JSON serialization
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%dT%H:%M:%SZ')
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        existing_data.extend(dataset)
        
        with open(json_file, 'w') as f:
            json.dump(existing_data, f, indent=2, default=datetime_handler)
        
        print(f"Data appended to: {csv_file} and {json_file}")
    
    def convert_json_to_csv(self, json_file_path: str, output_csv_path: str = None) -> str:
        """Convert a JSON file containing GitHub user data to CSV format."""
        try:
            # Load JSON data
            with open(json_file_path, 'r') as f:
                dataset = json.load(f)
            
            if not dataset:
                raise ValueError("JSON file is empty or invalid")
            
            # Generate output filename if not provided
            if output_csv_path is None:
                base_name = json_file_path.replace('.json', '')
                output_csv_path = f"{base_name}_converted.csv"
            
            # Use the existing export function to convert
            temp_filename = json_file_path.replace('.json', '').replace('_raw', '')
            self.export_for_machine_learning(dataset, temp_filename + "_converted")
            
            logging.info(f"JSON to CSV conversion completed: {output_csv_path}")
            return output_csv_path
            
        except Exception as e:
            logging.error(f"Error converting JSON to CSV: {e}")
            raise
    
    def mine_repository_contributors(self, repo_url: str) -> List[Dict]:
        """Mine data for all contributors of a repository."""
        if not repo_url:
            raise ValueError("Repository URL cannot be empty")
            
        # Extract owner and repo name from URL
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, repo_url)
        if not match:
            raise ValueError("Invalid GitHub repository URL")
            
        owner, repo_name = match.groups()
        
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            contributors = list(repo.get_contributors())
            
            if self.progress_callback:
                self.progress_callback(f"Found {len(contributors)} contributors in {owner}/{repo_name}")
            
            # Collect usernames of all contributors
            usernames = [contrib.login for contrib in contributors]
            
            # Use parallel_data_collection to get data for all contributors
            results = []
            for username in usernames:
                try:
                    if self.progress_callback:
                        self.progress_callback(f"Collecting data for: {username}")
                    
                    # Collect data for single user
                    user_data = self.collect_single_user(username)
                    if user_data:
                        results.append(user_data)
                        
                except Exception as e:
                    if self.progress_callback:
                        self.progress_callback(f"Error collecting data for {username}: {str(e)}")
                    logging.error(f"Error collecting data for {username}: {e}")
                    continue
            
            return results
            
        except GithubException as e:
            raise ValueError(f"Error accessing repository: {e}")
    
    def collect_single_user(self, username: str) -> Dict:
        """Collect data for a single user."""
        try:
            if self.stop_event and self.stop_event.is_set():
                return None
            
            user = self.github.get_user(username)
            
            if self.progress_callback:
                self.progress_callback(f"Collecting extended user data for: {username}")
            extended_data = self.collect_extended_user_data(username)
            
            if self.stop_event and self.stop_event.is_set():
                return None
            
            if self.progress_callback:
                self.progress_callback(f"Analyzing development patterns for: {username}")
            development_patterns = self.analyze_development_patterns(username)
            
            if self.stop_event and self.stop_event.is_set():
                return None
            
            if self.progress_callback:
                self.progress_callback(f"Analyzing commit activity for: {username}")
            commit_activity = self.analyze_commit_activity(username)
            
            if self.stop_event and self.stop_event.is_set():
                return None
            
            if self.progress_callback:
                self.progress_callback(f"Analyzing contribution activity for: {username}")
            contribution_activity = self.analyze_contribution_activity(username)
            
            if self.stop_event and self.stop_event.is_set():
                return None
            
            if self.progress_callback:
                self.progress_callback(f"Analyzing language distribution for: {username}")
            language_percentages = self.analyze_language_percentages(username)
            
            if self.stop_event and self.stop_event.is_set():
                return None
            
            if self.progress_callback:
                self.progress_callback(f"Getting top repositories for: {username}")
            top_repositories = self.get_top_repositories(username)
            
            if self.stop_event and self.stop_event.is_set():
                return None
            
            if self.progress_callback:
                self.progress_callback(f"Analyzing interests for: {username}")
            interests = self.analyze_interests(username)
            
            user_data = {
                'username': username,
                'name': user.name,
                'followers': user.followers,
                'following': user.following,
                'public_repos': user.public_repos,
                'created_at': user.created_at,
                'extended_user_data': extended_data,
                'development_patterns': development_patterns,
                'commit_activity': commit_activity,
                'contribution_activity': contribution_activity,
                'language_percentages': language_percentages,
                'top_repositories': top_repositories,
                'interests': interests
            }
            
            if self.progress_callback:
                self.progress_callback(f"Analyzing repositories for: {username}")
            
            # Get all repositories and filter out forks
            all_repos = list(user.get_repos())
            original_repos = [repo for repo in all_repos if not repo.fork]
            
            if not original_repos:
                logging.info(f"No original repositories found for user: {username}")
                user_data['repositories'] = []
                return user_data
            
            # Take up to 5 repositories, or all if less than 5
            repos_to_analyze = original_repos[:min(5, len(original_repos))]
            logging.info(f"Found {len(repos_to_analyze)} repositories to analyze for user: {username}")
            
            repo_details = []
            for i, repo in enumerate(repos_to_analyze):
                try:
                    if self.progress_callback:
                        self.progress_callback(f"Processing repository {i+1}/{len(repos_to_analyze)}: {repo.name}")
                    
                    repo_info = {
                        'name': repo.name,
                        'stars': repo.stargazers_count,
                        'forks': repo.forks_count,
                        'language': repo.language,
                        'size': repo.size,
                        'contributor_network': self.get_contributor_network(username, repo.name),
                        'issues': self.collect_issue_sentiment_data(username, repo.name),
                        'extended_repo_data': self.collect_extended_repo_data(username, repo.name)
                    }
                    repo_details.append(repo_info)
                except Exception as e:
                    logging.error(f"Error processing repository {repo.name} for user {username}: {e}")
                    continue
            
            user_data['repositories'] = repo_details
            return user_data
            
        except GithubException as e:
            if self.progress_callback:
                self.progress_callback(f"GitHub error collecting data for {username}: {e}")
            logging.error(f"GitHub error collecting data for {username}: {e}")
            return None
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"Unexpected error for user {username}: {e}")
            logging.error(f"Unexpected error for user {username}: {e}")
            return None

class GitHubMinerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Profile Miner")
        self.stop_event = threading.Event()
        self.mining_thread = None
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create tabs
        self.profile_tab = ttk.Frame(self.notebook)
        self.repo_tab = ttk.Frame(self.notebook)
        self.auto_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.profile_tab, text="Profile Mining")
        self.notebook.add(self.repo_tab, text="Repository Mining")
        self.notebook.add(self.auto_tab, text="Auto Discovery")
        
        # Setup each tab
        self.setup_profile_tab()
        self.setup_repo_tab()
        self.setup_auto_discovery_tab()
        
        # Progress frame (shared between tabs)
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status text (shared between tabs)
        self.status_text = tk.Text(self.main_frame, height=10, width=80)
        self.status_text.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Control buttons (shared)
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(pady=5)
        
        self.stop_button = ttk.Button(self.control_frame, text="Stop Mining", command=self.stop_mining, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(self.control_frame, text="Clear Log", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=5)
    
    def setup_profile_tab(self):
        # Token input
        self.label_token = ttk.Label(self.profile_tab, text="GitHub Token:")
        self.label_token.pack(pady=5)
        self.entry_token = ttk.Entry(self.profile_tab, width=50, show="*")
        self.entry_token.pack(pady=5)
        
        # Profile URL input
        self.label_url = ttk.Label(self.profile_tab, text="GitHub Profile URL:")
        self.label_url.pack(pady=5)
        self.entry_url = ttk.Entry(self.profile_tab, width=50)
        self.entry_url.pack(pady=5)
        
        # Buttons frame
        self.button_frame = ttk.Frame(self.profile_tab)
        self.button_frame.pack(pady=10)
        
        self.mine_button = ttk.Button(self.button_frame, text="Mine Profile", command=self.start_profile_mining)
        self.mine_button.pack(side=tk.LEFT, padx=5)
        
        self.set_token_button = ttk.Button(self.button_frame, text="Set Global Token", command=self.set_global_token)
        self.set_token_button.pack(side=tk.LEFT, padx=5)
    
    def setup_repo_tab(self):
        # Token input
        self.repo_label_token = ttk.Label(self.repo_tab, text="GitHub Token:")
        self.repo_label_token.pack(pady=5)
        self.repo_entry_token = ttk.Entry(self.repo_tab, width=50, show="*")
        self.repo_entry_token.pack(pady=5)
        
        # Repository URL input
        self.repo_label_url = ttk.Label(self.repo_tab, text="GitHub Repository URL:")
        self.repo_label_url.pack(pady=5)
        self.repo_entry_url = ttk.Entry(self.repo_tab, width=50)
        self.repo_entry_url.pack(pady=5)
        
        # Buttons frame
        self.repo_button_frame = ttk.Frame(self.repo_tab)
        self.repo_button_frame.pack(pady=10)
        
        self.mine_repo_button = ttk.Button(self.repo_button_frame, text="Mine Contributors", command=self.start_repo_mining)
        self.mine_repo_button.pack(side=tk.LEFT, padx=5)
        
        self.set_repo_token_button = ttk.Button(self.repo_button_frame, text="Set Global Token", command=self.set_global_token)
        self.set_repo_token_button.pack(side=tk.LEFT, padx=5)
    
    def setup_auto_discovery_tab(self):
        # Token input for auto discovery
        token_frame = ttk.Frame(self.auto_tab)
        token_frame.pack(fill=tk.X, pady=5)
        ttk.Label(token_frame, text="GitHub Token:").pack(side=tk.LEFT)
        self.auto_token_entry = ttk.Entry(token_frame, width=40, show="*")
        self.auto_token_entry.pack(side=tk.LEFT, padx=5)
        
        # Quick Discovery Options
        quick_frame = ttk.LabelFrame(self.auto_tab, text="Quick Discovery", padding="10")
        quick_frame.pack(fill=tk.X, pady=5)
        
        quick_buttons = ttk.Frame(quick_frame)
        quick_buttons.pack()
        
        ttk.Button(quick_buttons, text="Discover Python Developers", 
                  command=lambda: self.start_auto_discovery("python_devs")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_buttons, text="Discover JS Developers", 
                  command=lambda: self.start_auto_discovery("js_devs")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_buttons, text="Discover ML/AI Experts", 
                  command=lambda: self.start_auto_discovery("ml_experts")).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_buttons, text="Discover Trending Developers", 
                  command=lambda: self.start_auto_discovery("trending")).pack(side=tk.LEFT, padx=5)
        
        # Custom Discovery Options
        custom_frame = ttk.LabelFrame(self.auto_tab, text="Custom Discovery", padding="10")
        custom_frame.pack(fill=tk.X, pady=5)
        
        # Discovery method selection
        method_frame = ttk.Frame(custom_frame)
        method_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(method_frame, text="Discovery Method:").pack(side=tk.LEFT)
        self.discovery_method = ttk.Combobox(method_frame, values=[
            "Comprehensive (All Methods)",
            "Trending Repositories", 
            "Search Criteria",
            "Popular Topics",
            "Recently Active",
            "From Organizations"
        ], state="readonly", width=25)
        self.discovery_method.set("Comprehensive (All Methods)")
        self.discovery_method.pack(side=tk.LEFT, padx=5)
        
        # Parameters grid
        params_frame = ttk.Frame(custom_frame)
        params_frame.pack(fill=tk.X, pady=5)
        
        # Left column
        left_params = ttk.Frame(params_frame)
        left_params.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_params, text="Languages (comma-separated):").pack(anchor=tk.W)
        self.languages_entry = ttk.Entry(left_params, width=30)
        self.languages_entry.insert(0, "python,javascript,java")
        self.languages_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(left_params, text="Topics (comma-separated):").pack(anchor=tk.W)
        self.topics_entry = ttk.Entry(left_params, width=30)
        self.topics_entry.insert(0, "machine-learning,web-development,mobile")
        self.topics_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(left_params, text="Location:").pack(anchor=tk.W)
        self.location_entry = ttk.Entry(left_params, width=30)
        self.location_entry.pack(fill=tk.X, pady=2)
        
        # Right column
        right_params = ttk.Frame(params_frame)
        right_params.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        ttk.Label(right_params, text="Min Followers:").pack(anchor=tk.W)
        self.min_followers_entry = ttk.Entry(right_params, width=20)
        self.min_followers_entry.insert(0, "50")
        self.min_followers_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(right_params, text="Min Repositories:").pack(anchor=tk.W)
        self.min_repos_entry = ttk.Entry(right_params, width=20)
        self.min_repos_entry.insert(0, "5")
        self.min_repos_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(right_params, text="Max Users to Discover:").pack(anchor=tk.W)
        self.max_users_entry = ttk.Entry(right_params, width=20)
        self.max_users_entry.insert(0, "100")
        self.max_users_entry.pack(fill=tk.X, pady=2)
        
        # Organizations input
        org_frame = ttk.Frame(custom_frame)
        org_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(org_frame, text="Organizations (for org discovery):").pack(anchor=tk.W)
        self.orgs_entry = ttk.Entry(org_frame, width=50)
        self.orgs_entry.insert(0, "google,microsoft,facebook,netflix,uber")
        self.orgs_entry.pack(fill=tk.X, pady=2)
        
        # Custom discovery button
        ttk.Button(custom_frame, text="Start Custom Discovery", 
                  command=self.start_custom_discovery).pack(pady=10)
        
        # Advanced Options
        advanced_frame = ttk.LabelFrame(self.auto_tab, text="Advanced Options", padding="10")
        advanced_frame.pack(fill=tk.X, pady=5)
        
        adv_grid = ttk.Frame(advanced_frame)
        adv_grid.pack()
        
        ttk.Label(adv_grid, text="Days back for activity:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.days_back_entry = ttk.Entry(adv_grid, width=10)
        self.days_back_entry.insert(0, "7")
        self.days_back_entry.grid(row=0, column=1, padx=5)
        
        self.include_trending_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(adv_grid, text="Include Trending", variable=self.include_trending_var).grid(row=0, column=2, padx=10)
        
        self.include_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(adv_grid, text="Include Recently Active", variable=self.include_active_var).grid(row=0, column=3, padx=10)
    
    def start_auto_discovery(self, discovery_type):
        """Start predefined auto discovery."""
        self.stop_event.clear()
        self.stop_button.config(state='normal')
        self.progress_bar.start()
        self.update_status(f"Starting {discovery_type} auto discovery...")
        
        # Start discovery in a separate thread
        self.mining_thread = threading.Thread(
            target=self.auto_discovery_worker, 
            args=(discovery_type,)
        )
        self.mining_thread.daemon = True
        self.mining_thread.start()
    
    def start_custom_discovery(self):
        """Start custom auto discovery based on user parameters."""
        self.stop_event.clear()
        self.stop_button.config(state='normal')
        self.progress_bar.start()
        self.update_status("Starting custom auto discovery...")
        
        # Gather parameters
        params = self.get_discovery_parameters()
        
        # Start discovery in a separate thread
        self.mining_thread = threading.Thread(
            target=self.custom_discovery_worker, 
            args=(params,)
        )
        self.mining_thread.daemon = True
        self.mining_thread.start()
    
    def get_discovery_parameters(self):
        """Get discovery parameters from GUI."""
        return {
            'method': self.discovery_method.get(),
            'languages': [lang.strip() for lang in self.languages_entry.get().split(',') if lang.strip()],
            'topics': [topic.strip() for topic in self.topics_entry.get().split(',') if topic.strip()],
            'location': self.location_entry.get().strip(),
            'min_followers': int(self.min_followers_entry.get() or 0),
            'min_repos': int(self.min_repos_entry.get() or 0),
            'max_users': int(self.max_users_entry.get() or 100),
            'organizations': [org.strip() for org in self.orgs_entry.get().split(',') if org.strip()],
            'days_back': int(self.days_back_entry.get() or 7),
            'include_trending': self.include_trending_var.get(),
            'include_active': self.include_active_var.get()
        }
    
    def auto_discovery_worker(self, discovery_type):
        """Worker for predefined auto discovery."""
        try:
            token = self.auto_token_entry.get() or self.entry_token.get() or GITHUB_TOKEN
            if not token:
                raise ValueError("GitHub token is required")
            
            discoverer = AutoProfileDiscovery(token)
            
            # Predefined discovery strategies
            strategies = {
                "python_devs": {
                    'languages': ['python'],
                    'topics': ['machine-learning', 'data-science', 'web-development'],
                    'min_followers': 100,
                    'include_trending': True,
                    'include_active': True
                },
                "js_devs": {
                    'languages': ['javascript'],
                    'topics': ['web-development', 'frontend', 'nodejs'],
                    'min_followers': 100,
                    'include_trending': True,
                    'include_active': True
                },
                "ml_experts": {
                    'languages': ['python', 'r'],
                    'topics': ['machine-learning', 'artificial-intelligence', 'data-science'],
                    'min_followers': 200,
                    'include_trending': True,
                    'include_active': True
                },
                "trending": {
                    'languages': ['python', 'javascript', 'java', 'go'],
                    'topics': ['trending'],
                    'min_followers': 50,
                    'include_trending': True,
                    'include_active': True
                }
            }
            
            if discovery_type in strategies:
                preferences = strategies[discovery_type]
                self.update_status(f"Discovering profiles using {discovery_type} strategy...")
                
                discovered_users = discoverer.discover_comprehensive(preferences, total_limit=100)
                
                if discovered_users and not self.stop_event.is_set():
                    self.update_status(f"Found {len(discovered_users)} profiles. Starting mining...")
                    self.mine_discovered_users(discovered_users, f"auto_{discovery_type}")
                else:
                    self.update_status("No profiles discovered or operation was stopped.")
            
        except Exception as e:
            if not self.stop_event.is_set():
                self.update_status(f"Auto discovery error: {str(e)}")
                messagebox.showerror("Error", f"Auto discovery failed: {e}")
        finally:
            self.progress_bar.stop()
            self.stop_button.config(state='disabled')
    
    def custom_discovery_worker(self, params):
        """Worker for custom auto discovery."""
        try:
            token = self.auto_token_entry.get() or self.entry_token.get() or GITHUB_TOKEN
            if not token:
                raise ValueError("GitHub token is required")
            
            discoverer = AutoProfileDiscovery(token)
            discovered_users = []
            
            method = params['method']
            
            if method == "Comprehensive (All Methods)":
                preferences = {
                    'languages': params['languages'],
                    'topics': params['topics'],
                    'min_followers': params['min_followers'],
                    'min_repos': params['min_repos'],
                    'include_trending': params['include_trending'],
                    'include_active': params['include_active'],
                    'days_back': params['days_back']
                }
                discovered_users = discoverer.discover_comprehensive(preferences, params['max_users'])
                
            elif method == "Trending Repositories":
                for lang in params['languages'][:3]:  # Limit to avoid rate limits
                    users = discoverer.discover_trending_developers(
                        language=lang, 
                        location=params['location'] if params['location'] else None,
                        limit=params['max_users'] // len(params['languages'])
                    )
                    discovered_users.extend(users)
                    
            elif method == "Search Criteria":
                criteria = {
                    'min_followers': params['min_followers'],
                    'min_repos': params['min_repos']
                }
                if params['location']:
                    criteria['location'] = params['location']
                
                for lang in params['languages'][:3]:
                    criteria['language'] = lang
                    users = discoverer.discover_by_search_criteria(criteria, params['max_users'] // len(params['languages']))
                    discovered_users.extend(users)
                    
            elif method == "Popular Topics":
                discovered_users = discoverer.discover_from_popular_repos(params['topics'], params['max_users'])
                
            elif method == "Recently Active":
                discovered_users = discoverer.discover_active_developers(params['days_back'], params['max_users'])
                
            elif method == "From Organizations":
                discovered_users = discoverer.discover_by_organization(params['organizations'], params['max_users'])
            
            # Remove duplicates
            discovered_users = list(set(discovered_users))[:params['max_users']]
            
            if discovered_users and not self.stop_event.is_set():
                self.update_status(f"Found {len(discovered_users)} profiles. Starting mining...")
                self.mine_discovered_users(discovered_users, "custom_discovery")
            else:
                self.update_status("No profiles discovered or operation was stopped.")
                
        except Exception as e:
            if not self.stop_event.is_set():
                self.update_status(f"Custom discovery error: {str(e)}")
                messagebox.showerror("Error", f"Custom discovery failed: {e}")
        finally:
            self.progress_bar.stop()
            self.stop_button.config(state='disabled')
    
    def mine_discovered_users(self, usernames, output_prefix):
        """Mine data for discovered users."""
        try:
            token = self.auto_token_entry.get() or self.entry_token.get() or GITHUB_TOKEN
            
            def progress_callback(message):
                self.update_status(message)
            
            miner = AdvancedGitHubMiner(token, progress_callback=progress_callback)
            
            # Process in smaller batches to avoid rate limits
            batch_size = 3
            all_results = []
            
            for i in range(0, len(usernames), batch_size):
                if self.stop_event.is_set():
                    break
                    
                batch = usernames[i:i + batch_size]
                self.update_status(f"Processing batch {i//batch_size + 1}/{(len(usernames) + batch_size - 1)//batch_size}: {', '.join(batch)}")
                
                try:
                    batch_results = miner.parallel_data_collection(batch, max_workers=2)
                    all_results.extend(batch_results)
                    
                    # Save intermediate results
                    if batch_results:
                        miner.export_for_machine_learning(batch_results, "github_data")
                        self.update_status(f"Batch {i//batch_size + 1} completed and saved")
                    
                    # Rate limiting delay
                    if i + batch_size < len(usernames) and not self.stop_event.is_set():
                        self.update_status("Waiting 30 seconds to avoid rate limits...")
                        for _ in range(30):
                            if self.stop_event.is_set():
                                break
                            time.sleep(1)
                        
                except Exception as e:
                    self.update_status(f"Error processing batch {i//batch_size + 1}: {e}")
                    continue
            
            if all_results and not self.stop_event.is_set():
                self.update_status(f"Auto discovery and mining completed!")
                self.update_status(f"Total users processed: {len(all_results)}/{len(usernames)}")
                self.update_status(f"Success rate: {len(all_results)/len(usernames)*100:.1f}%")
                
                messagebox.showinfo("Success", 
                    f"Auto discovery completed!\n"
                    f"Discovered: {len(usernames)} profiles\n"
                    f"Successfully mined: {len(all_results)} profiles")
            elif not self.stop_event.is_set():
                self.update_status("No data was successfully collected")
                
        except Exception as e:
            if not self.stop_event.is_set():
                self.update_status(f"Mining error: {str(e)}")
                messagebox.showerror("Error", f"Mining failed: {e}")
    
    def stop_mining(self):
        """Stop the current mining operation."""
        self.stop_event.set()
        self.stop_button.config(state='disabled')
        self.progress_bar.stop()
        self.update_status("Mining stopped by user.")
    
    def clear_log(self):
        """Clear the status log."""
        self.status_text.delete(1.0, tk.END)
    
    def update_status(self, message):
        """Update the status text with a new message."""
        self.status_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def set_global_token(self):
        global GITHUB_TOKEN
        token = self.entry_token.get() or self.repo_entry_token.get()
        if not token or token.strip() == "":
            messagebox.showerror("Error", "Token cannot be empty")
            return
        GITHUB_TOKEN = token
        messagebox.showinfo("Success", "Global token has been set!")
    
    def start_profile_mining(self):
        self.mine_button.config(state='disabled')
        self.progress_bar.start()
        self.status_text.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self.mine_profile)
        thread.daemon = True
        thread.start()
    
    def start_repo_mining(self):
        self.mine_repo_button.config(state='disabled')
        self.progress_bar.start()
        self.status_text.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self.mine_repository)
        thread.daemon = True
        thread.start()
    
    def mine_profile(self):
        try:
            token = self.entry_token.get()
            profile_url = self.entry_url.get()
            
            username = self.extract_username(profile_url)
            self.update_status(f"Starting mining for user: {username}")
            
            miner = AdvancedGitHubMiner(token, progress_callback=self.update_status)
            self.update_status("Collecting user data...")
            dataset = miner.parallel_data_collection([username], max_workers=1)
            
            if not dataset or dataset[0] is None:
                raise ValueError(f"No data collected for user: {username}")
            
            self.update_status("Exporting data...")
            miner.export_for_machine_learning(dataset, "github_data")
            
            self.update_status("Mining completed successfully!")
            messagebox.showinfo("Success", f"Data mined and exported for {username}!")
            
        except ValueError as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        except Exception as e:
            self.update_status(f"Unexpected error: {str(e)}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            self.progress_bar.stop()
            self.mine_button.config(state='normal')
    
    def mine_repository(self):
        try:
            token = self.repo_entry_token.get()
            repo_url = self.repo_entry_url.get()
            
            self.update_status(f"Starting mining for repository: {repo_url}")
            
            miner = AdvancedGitHubMiner(token, progress_callback=self.update_status)
            self.update_status("Collecting contributor data...")
            dataset = miner.mine_repository_contributors(repo_url)
            
            if not dataset:
                raise ValueError("No contributor data collected")
            
            self.update_status(f"Found data for {len(dataset)} contributors")
            self.update_status("Exporting data...")
            miner.export_for_machine_learning(dataset, "github_data")
            
            self.update_status("Mining completed successfully!")
            messagebox.showinfo("Success", f"Data mined and exported for {len(dataset)} contributors!")
            
        except ValueError as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        except Exception as e:
            self.update_status(f"Unexpected error: {str(e)}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            self.progress_bar.stop()
            self.mine_repo_button.config(state='normal')
    
    def extract_username(self, url: str) -> str:
        url = url.strip()
        if not url:
            raise ValueError("Profile URL cannot be empty")
        pattern = r'github\.com/([a-zA-Z0-9-]+)'
        match = re.search(pattern, url)
        if not match:
            raise ValueError("Invalid GitHub profile URL")
        return match.group(1)

def main():
    root = tk.Tk()
    app = GitHubMinerGUI(root)
    root.mainloop()

def cli_auto_discovery():
    """Command line interface for automated discovery and mining."""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub Developer Analyzer - Automated Discovery & Mining')
    parser.add_argument('--token', required=True, help='GitHub API token')
    parser.add_argument('--mode', choices=['quick', 'custom', 'comprehensive'], required=True, 
                       help='Discovery mode: quick, custom, or comprehensive')
    
    # Quick mode arguments
    parser.add_argument('--strategy', choices=['python_devs', 'js_devs', 'ml_experts', 'trending'], 
                       help='Quick strategy (for quick mode)')
    
    # Custom mode arguments
    parser.add_argument('--method', choices=['trending', 'search', 'topics', 'active', 'orgs'], 
                       help='Discovery method (for custom mode)')
    parser.add_argument('--languages', help='Comma-separated languages (e.g., python,javascript)')
    parser.add_argument('--topics', help='Comma-separated topics (e.g., machine-learning,web-development)')
    parser.add_argument('--location', help='Location filter')
    parser.add_argument('--min-followers', type=int, default=50, help='Minimum followers')
    parser.add_argument('--min-repos', type=int, default=5, help='Minimum repositories')
    parser.add_argument('--organizations', help='Comma-separated organization names')
    parser.add_argument('--days-back', type=int, default=7, help='Days back for activity search')
    
    # General arguments
    parser.add_argument('--max-users', type=int, default=100, help='Maximum users to discover and mine')
    parser.add_argument('--output', default='auto_discovery', help='Output file prefix')
    parser.add_argument('--batch-size', type=int, default=3, help='Batch size for processing')
    
    args = parser.parse_args()
    
    try:
        print(f"Starting automated GitHub profile discovery and mining...")
        print(f"Mode: {args.mode}")
        print(f"Max users: {args.max_users}")
        print(f"Output prefix: {args.output}")
        print("-" * 50)
        
        # Initialize discoverer
        discoverer = AutoProfileDiscovery(args.token)
        discovered_users = []
        
        if args.mode == 'quick':
            if not args.strategy:
                print("Error: --strategy is required for quick mode")
                return
            
            strategies = {
                'python_devs': {
                    'languages': ['python'],
                    'topics': ['machine-learning', 'data-science', 'web-development'],
                    'min_followers': 100,
                    'include_trending': True,
                    'include_active': True
                },
                'js_devs': {
                    'languages': ['javascript'],
                    'topics': ['web-development', 'frontend', 'nodejs'],
                    'min_followers': 100,
                    'include_trending': True,
                    'include_active': True
                },
                'ml_experts': {
                    'languages': ['python', 'r'],
                    'topics': ['machine-learning', 'artificial-intelligence', 'data-science'],
                    'min_followers': 200,
                    'include_trending': True,
                    'include_active': True
                },
                'trending': {
                    'languages': ['python', 'javascript', 'java', 'go'],
                    'topics': ['trending'],
                    'min_followers': 50,
                    'include_trending': True,
                    'include_active': True
                }
            }
            
            preferences = strategies[args.strategy]
            print(f"Using quick strategy: {args.strategy}")
            discovered_users = discoverer.discover_comprehensive(preferences, args.max_users)
            
        elif args.mode == 'custom':
            if not args.method:
                print("Error: --method is required for custom mode")
                return
            
            print(f"Using custom method: {args.method}")
            
            if args.method == 'trending':
                languages = args.languages.split(',') if args.languages else ['python']
                for lang in languages[:3]:
                    users = discoverer.discover_trending_developers(
                        language=lang.strip(), 
                        location=args.location,
                        limit=args.max_users // len(languages)
                    )
                    discovered_users.extend(users)
                    
            elif args.method == 'search':
                criteria = {
                    'min_followers': args.min_followers,
                    'min_repos': args.min_repos
                }
                if args.location:
                    criteria['location'] = args.location
                
                languages = args.languages.split(',') if args.languages else ['python']
                for lang in languages[:3]:
                    criteria['language'] = lang.strip()
                    users = discoverer.discover_by_search_criteria(criteria, args.max_users // len(languages))
                    discovered_users.extend(users)
                    
            elif args.method == 'topics':
                topics = args.topics.split(',') if args.topics else ['machine-learning', 'web-development']
                discovered_users = discoverer.discover_from_popular_repos([t.strip() for t in topics], args.max_users)
                
            elif args.method == 'active':
                discovered_users = discoverer.discover_active_developers(args.days_back, args.max_users)
                
            elif args.method == 'orgs':
                if not args.organizations:
                    print("Error: --organizations is required for orgs method")
                    return
                orgs = [org.strip() for org in args.organizations.split(',')]
                discovered_users = discoverer.discover_by_organization(orgs, args.max_users)
            
        elif args.mode == 'comprehensive':
            preferences = {
                'languages': args.languages.split(',') if args.languages else ['python', 'javascript', 'java'],
                'topics': args.topics.split(',') if args.topics else ['machine-learning', 'web-development', 'mobile'],
                'min_followers': args.min_followers,
                'min_repos': args.min_repos,
                'include_trending': True,
                'include_active': True,
                'days_back': args.days_back
            }
            print("Using comprehensive discovery (all methods)")
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
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
        miner = AdvancedGitHubMiner(args.token, progress_callback=progress_callback)
        
        # Process in batches
        batch_size = args.batch_size
        all_results = []
        
        for i in range(0, len(discovered_users), batch_size):
            batch = discovered_users[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(discovered_users) + batch_size - 1) // batch_size
            
            print(f"\nProcessing batch {batch_num}/{total_batches}: {', '.join(batch)}")
            
            try:
                batch_results = miner.parallel_data_collection(batch, max_workers=2)
                all_results.extend(batch_results)
                
                # Save intermediate results
                if batch_results:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    intermediate_file = f"{args.output}_batch_{batch_num}_{timestamp}"
                    miner.export_for_machine_learning(batch_results, intermediate_file)
                    print(f"Batch {batch_num} completed and saved as {intermediate_file}")
                
                # Rate limiting delay
                if i + batch_size < len(discovered_users):
                    print("Waiting 30 seconds to avoid rate limits...")
                    time.sleep(30)
                    
            except Exception as e:
                print(f"Error processing batch {batch_num}: {e}")
                continue
        
        # Export final combined results
        if all_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_file = f"{args.output}_final_{timestamp}"
            miner.export_for_machine_learning(all_results, final_file)
            
            print(f"\n" + "=" * 50)
            print(f"AUTOMATED DISCOVERY AND MINING COMPLETED!")
            print(f"=" * 50)
            print(f"Users discovered: {len(discovered_users)}")
            print(f"Users successfully mined: {len(all_results)}")
            print(f"Success rate: {len(all_results)/len(discovered_users)*100:.1f}%")
            print(f"Final output files:")
            print(f"  - CSV: {final_file}_ml_features.csv")
            print(f"  - JSON: {final_file}_raw.json")
            print(f"Total features per user: {len(all_results[0].keys()) if all_results else 0}")
            
        else:
            print("No data was successfully collected")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_json_to_csv_conversion(json_file_path: str):
    """Standalone function to test JSON to CSV conversion."""
    try:
        print(f"Testing JSON to CSV conversion for: {json_file_path}")
        miner = AdvancedGitHubMiner()
        result = miner.convert_json_to_csv(json_file_path)
        print(f"Conversion successful: {result}")
        return result
    except Exception as e:
        print(f"Conversion failed: {e}")
        return None

def debug_export_function(dataset_file: str = None):
    """Debug function to test the export functionality."""
    try:
        if dataset_file:
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
                    'repository_lifecycle': [{'total_commits': 10}],
                    'productivity_streaks': {'max_streak': 5},
                    'language_evolution': {'Python': 1000, 'JavaScript': 500},
                    'commit_comments': [],
                    'issue_comments': [],
                    'pr_reviews': []
                },
                'commit_activity': {
                    'total_recent_commits': 15,
                    'active_days': ['2024-01-01', '2024-01-02'],
                    'avg_commits_per_day': 7.5,
                    'commit_frequency_by_hour': {'9': 5, '14': 10},
                    'repositories_analyzed': 3,
                    'total_repositories': 25
                },
                'contribution_activity': {
                    'contribution_level': 'Medium',
                    'recent_contributions_30_days': 20,
                    'activity_score': 75.5,
                    'repositories_contributed_to': 8,
                    'issues_opened': 3,
                    'issues_closed': 2,
                    'pull_requests_opened': 4,
                    'pull_requests_merged': 3,
                    'recently_active_repositories': 5,
                    'total_stars_earned': 150,
                    'total_forks_earned': 25,
                    'event_types': {'PushEvent': 10, 'IssuesEvent': 5}
                },
                'language_percentages': {
                    'language_percentages': {'Python': 60.5, 'JavaScript': 30.2, 'HTML': 9.3},
                    'total_languages': 3,
                    'primary_language': 'Python',
                    'language_diversity_score': 3
                },
                'top_repositories': {
                    'total_original_repos': 25,
                    'total_stars_earned': 150,
                    'total_forks_earned': 25,
                    'by_stars': [{'stars': 50}]
                },
                'interests': {
                    'repository_topics': {'machine-learning': 3, 'web-development': 2},
                    'inferred_interests': ['python', 'ai', 'web'],
                    'starred_repo_topics': {'data-science': 5},
                    'organization_domains': ['company1', 'company2']
                },
                'repositories': [
                    {
                        'stars': 50,
                        'forks': 10,
                        'size': 1000,
                        'contributor_network': {'contributors': ['user1', 'user2']},
                        'extended_repo_data': {'branches': ['main'], 'releases': []},
                        'issues': []
                    }
                ]
            }]
        
        print("Testing export function with sample/loaded data...")
        miner = AdvancedGitHubMiner()
        miner.export_for_machine_learning(dataset, "debug_test")
        print("Export test completed successfully!")
        
    except Exception as e:
        print(f"Debug export failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    # Check if running in CLI mode (has command line arguments)
    if len(sys.argv) > 1:
        # Check if it's the auto-discovery CLI
        if '--mode' in sys.argv:
            cli_auto_discovery()
        else:
            # Run GUI with any other arguments (backward compatibility)
            main()
    else:
        # Run GUI if no arguments
        main()