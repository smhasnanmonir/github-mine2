"""
GitHub Data Mining Module.

This module contains the AdvancedGitHubMiner class which provides comprehensive
data mining capabilities for GitHub profiles and repositories.
"""

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

from .config import GITHUB_TOKEN, DEFAULT_COMMIT_ANALYSIS_DAYS, DEFAULT_TOP_REPOS_LIMIT


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
            # Test the token by getting user info
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
                    # Note: This is a placeholder for actual archive processing
                    # In a real implementation, you would download and process the .gz file
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
            
            # Process user's repositories (limit to first 10 for performance)
            for repo in repos[:10]:
                if self.stop_event and self.stop_event.is_set():
                    break
                    
                try:
                    if repo.fork:
                        logging.info(f"Skipping fork: {repo.name} for user {username}")
                        continue
                    
                    # Analyze commits
                    commits = list(repo.get_commits(author=username))
                    commit_dates = [commit.commit.author.date for commit in commits]
                    patterns['commit_frequency'].extend(commit_dates)
                    
                    # Analyze commit timing
                    for date in commit_dates:
                        patterns['commit_timing']['hours'].append(date.hour)
                        patterns['commit_timing']['days'].append(date.weekday())
                    
                    # Repository lifecycle analysis
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
                    
                    # Language evolution
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
                    
                    # Analyze commit comments (limit for performance)
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
                    
                    # Analyze issue comments
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
                    
                    # Analyze PR reviews
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
            
            # Calculate productivity streaks
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
                    
                    # Collect comments
                    try:
                        comments = issue.get_comments()
                        for comment in comments:
                            issue_info['comments'].append({
                                'user': comment.user.login if comment.user else None,
                                'body': comment.body,
                                'created_at': comment.created_at
                            })
                    except GithubException as e:
                        logging.warning(f"Error fetching comments for issue {issue.number}: {e}")
                    
                    issue_data.append(issue_info)
                    
            except GithubException as e:
                logging.warning(f"No issues found for {repo_owner}/{repo_name}: {e}")
            
            return issue_data
        except GithubException as e:
            logging.error(f"Error collecting issue sentiment data for {repo_owner}/{repo_name}: {e}")
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
                extended_data['starred_repos'] = [
                    {'full_name': repo.full_name, 'stars': repo.stargazers_count} 
                    for repo in starred[:10]
                ]
            except GithubException as e:
                logging.warning(f"Error fetching starred repos for {username}: {e}")
            
            try:
                watched = user.get_watched()
                extended_data['watched_repos'] = [
                    {'full_name': repo.full_name, 'watchers': repo.watchers_count} 
                    for repo in watched[:10]
                ]
            except GithubException as e:
                logging.warning(f"Error fetching watched repos for {username}: {e}")
            
            try:
                gists = user.get_gists()
                extended_data['gists'] = [
                    {'id': gist.id, 'description': gist.description, 'created_at': gist.created_at} 
                    for gist in gists[:10]
                ]
            except GithubException as e:
                logging.warning(f"Error fetching gists for {username}: {e}")
            
            try:
                orgs = user.get_orgs()
                extended_data['organizations'] = [
                    {'login': org.login, 'description': org.description} 
                    for org in orgs
                ]
            except GithubException as e:
                logging.warning(f"Error fetching organizations for {username}: {e}")
            
            try:
                events = user.get_events()
                extended_data['events'] = [
                    {'type': event.type, 'repo': event.repo.name, 'created_at': event.created_at} 
                    for event in events[:50]
                ]
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
                extended_data['branches'] = [
                    {'name': branch.name, 'protected': branch.protected} 
                    for branch in branches[:10]
                ]
            except GithubException as e:
                logging.warning(f"Error fetching branches for {repo_owner}/{repo_name}: {e}")
            
            try:
                releases = repo.get_releases()
                extended_data['releases'] = [
                    {'tag_name': release.tag_name, 'created_at': release.created_at} 
                    for release in releases[:10]
                ]
            except GithubException as e:
                logging.warning(f"Error fetching releases for {repo_owner}/{repo_name}: {e}")
            
            try:
                tags = repo.get_tags()
                extended_data['tags'] = [
                    {'name': tag.name, 'commit_sha': tag.commit.sha} 
                    for tag in tags[:10]
                ]
            except GithubException as e:
                logging.warning(f"Error fetching tags for {repo_owner}/{repo_name}: {e}")
            
            try:
                stats = repo.get_stats_commit_activity()
                if stats:
                    extended_data['commit_stats'] = [
                        {'week': stat.week, 'total': stat.total} 
                        for stat in stats
                    ]
            except GithubException as e:
                logging.warning(f"Error fetching commit stats for {repo_owner}/{repo_name}: {e}")
            
            try:
                code_freq = repo.get_stats_code_frequency()
                if code_freq:
                    extended_data['code_frequency'] = [
                        {'week': stat.week, 'additions': stat.additions, 'deletions': stat.deletions} 
                        for stat in code_freq
                    ]
            except GithubException as e:
                logging.warning(f"Error fetching code frequency for {repo_owner}/{repo_name}: {e}")
            
            try:
                forks = repo.get_forks()
                extended_data['forks_history'] = [
                    {'owner': fork.owner.login, 'created_at': fork.created_at} 
                    for fork in forks[:10]
                ]
            except GithubException as e:
                logging.warning(f"Error fetching forks for {repo_owner}/{repo_name}: {e}")
            
            return extended_data
        except GithubException as e:
            logging.error(f"Error collecting extended repo data for {repo_owner}/{repo_name}: {e}")
            return {}

    def parallel_data_collection(self, usernames: List[str], max_workers: int = 5, save_immediately: bool = False, filename: str = None, fetch_all_commits: bool = False) -> List[Dict]:

        if save_immediately and not filename:
            raise ValueError("filename is required when save_immediately=True")
        
        def collect_single_user(username):
            """Collect comprehensive data for a single user."""
            try:
                if self.progress_callback:
                    commit_mode = "all commits" if fetch_all_commits else "recent commits"
                    self.progress_callback(f"Starting data collection ({commit_mode}) for {username}")
                
                user_data = self.collect_single_user(username, fetch_all_commits=fetch_all_commits)
                
                # Save immediately after collection if requested
                if save_immediately and user_data:
                    self.append_single_user_to_export(user_data, filename)
                    if self.progress_callback:
                        self.progress_callback(f"Data for {username} collected and saved immediately")
                
                return user_data
            except Exception as e:
                logging.error(f"Error collecting data for {username}: {e}")
                if self.progress_callback:
                    self.progress_callback(f"Failed to collect data for {username}: {e}")
                return None
        
        results = []
        successful_count = 0
        failed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_username = {
                executor.submit(collect_single_user, username): username 
                for username in usernames
            }
            
            # Process completed tasks
            for future in as_completed(future_to_username):
                username = future_to_username[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        successful_count += 1
                        if self.progress_callback:
                            self.progress_callback(f"✓ Completed {username} - Progress: {successful_count + failed_count}/{len(usernames)} ({successful_count} successful, {failed_count} failed)")
                    else:
                        failed_count += 1
                        if self.progress_callback:
                            self.progress_callback(f"✗ Failed {username} - Progress: {successful_count + failed_count}/{len(usernames)} ({successful_count} successful, {failed_count} failed)")
                except Exception as e:
                    failed_count += 1
                    logging.error(f"Error processing {username}: {e}")
                    if self.progress_callback:
                        self.progress_callback(f"✗ Error processing {username}: {e}")
                        self.progress_callback(f"Progress: {successful_count + failed_count}/{len(usernames)} ({successful_count} successful, {failed_count} failed)")
        
        if save_immediately and self.progress_callback:
            self.progress_callback(f"All data collection completed! {successful_count}/{len(usernames)} users successfully processed and saved")
        
        return results

    def collect_single_user(self, username: str, fetch_all_commits: bool = False) -> Dict:

        try:
            if self.stop_event and self.stop_event.is_set():
                return None
            
            logging.info(f"Starting data collection for user: {username}")
            user = self.github.get_user(username)
            
            # Basic user data - always collect this
            user_data = {
                'username': username,
                'followers': user.followers,
                'following': user.following,
                'public_repos': user.public_repos,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
            }
            
            logging.info(f"User {username}: {user.public_repos} public repos, {user.followers} followers")
            
            # Extended user data - with error handling
            try:
                if self.progress_callback:
                    self.progress_callback(f"Collecting extended data for {username}")
                user_data['extended_user_data'] = self.collect_extended_user_data(username)
            except Exception as e:
                logging.warning(f"Failed to collect extended data for {username}: {e}")
                user_data['extended_user_data'] = {}
            
            # Development patterns - with error handling
            try:
                if self.progress_callback:
                    self.progress_callback(f"Analyzing development patterns for {username}")
                user_data['development_patterns'] = self.analyze_development_patterns(username)
            except Exception as e:
                logging.warning(f"Failed to analyze development patterns for {username}: {e}")
                user_data['development_patterns'] = {}
            
            # Commit activity (with optional all commits fetch) - with error handling
            try:
                commit_mode = "all commits" if fetch_all_commits else "recent commits"
                if self.progress_callback:
                    self.progress_callback(f"Analyzing commit activity ({commit_mode}) for {username}")
                user_data['commit_activity'] = self.analyze_commit_activity(username, fetch_all_commits=fetch_all_commits)
            except Exception as e:
                logging.warning(f"Failed to analyze commit activity for {username}: {e}")
                user_data['commit_activity'] = {
                    'total_commits': 0 if fetch_all_commits else 0,
                    'total_recent_commits': 0,
                    'active_days': [],
                    'commit_frequency_by_day': {},
                    'commit_frequency_by_hour': {},
                    'recent_commits': [],
                    'most_active_repo': None,
                    'commit_streaks': [],
                    'avg_commits_per_day': 0,
                    'repositories_analyzed': 0,
                    'total_repositories': 0,
                    'fetch_mode': 'all' if fetch_all_commits else 'recent'
                }
            
            # NEW: Social network analysis - with error handling
            try:
                if self.progress_callback:
                    self.progress_callback(f"Analyzing social network for {username}")
                user_data['social_network'] = self.collect_social_network_data(username)
            except Exception as e:
                logging.warning(f"Failed to analyze social network for {username}: {e}")
                user_data['social_network'] = {}
            
            # NEW: Repository portfolio analysis - with error handling
            try:
                if self.progress_callback:
                    self.progress_callback(f"Analyzing repository portfolio for {username}")
                user_data['repository_portfolio'] = self.analyze_repository_portfolio(username)
            except Exception as e:
                logging.warning(f"Failed to analyze repository portfolio for {username}: {e}")
                user_data['repository_portfolio'] = {}
            
            # NEW: Contribution quality analysis - with error handling
            try:
                if self.progress_callback:
                    self.progress_callback(f"Analyzing contribution quality for {username}")
                user_data['contribution_quality'] = self.analyze_contribution_quality(username)
            except Exception as e:
                logging.warning(f"Failed to analyze contribution quality for {username}: {e}")
                user_data['contribution_quality'] = {}
            
            logging.info(f"Successfully collected data for user: {username}")
            return user_data
            
        except Exception as e:
            logging.error(f"Error collecting single user data for {username}: {e}")
            return None

    def analyze_commit_activity(self, username: str, days: int = DEFAULT_COMMIT_ANALYSIS_DAYS, fetch_all_commits: bool = False) -> Dict:

        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            if self.stop_event and self.stop_event.is_set():
                return {
                    'total_commits': 0 if fetch_all_commits else 0,
                    'total_recent_commits': 0,
                    'active_days': [],
                    'commit_frequency_by_day': {},
                    'commit_frequency_by_hour': {},
                    'recent_commits': [],
                    'most_active_repo': None,
                    'commit_streaks': [],
                    'avg_commits_per_day': 0,
                    'repositories_analyzed': 0,
                    'total_repositories': 0,
                    'fetch_mode': 'all' if fetch_all_commits else 'recent'
                }
            
            user = self.github.get_user(username)
            repos = list(user.get_repos())
            
            # Use timezone-naive datetime to avoid issues
            cutoff_date = datetime.now() - timedelta(days=days)
            
            activity_data = {
                'total_commits': 0 if fetch_all_commits else 0,
                'total_recent_commits': 0,
                'active_days': set(),
                'commit_frequency_by_day': {},
                'commit_frequency_by_hour': {},
                'recent_commits': [],  # Limited to 50 commits max
                'most_active_repo': None,
                'commit_streaks': [],
                'avg_commits_per_day': 0,
                'repositories_analyzed': 0,
                'total_repositories': len([r for r in repos if not r.fork]),
                'fetch_mode': 'all' if fetch_all_commits else 'recent'
            }
            
            repo_commit_counts = {}
            
            # Filter out forks and get only user's original repos
            original_repos = [repo for repo in repos if not repo.fork]
            
            # If user has no original repositories, still return valid structure with their basic info
            if not original_repos:
                logging.info(f"User {username} has no original repositories (only forks or no repos), returning basic activity data")
                activity_data['active_days'] = list(activity_data['active_days'])
                return activity_data
            
            # Limit repositories to analyze (more when fetching all commits to get comprehensive data)
            repo_limit = 25 if fetch_all_commits else 15
            
            for repo in original_repos[:repo_limit]:
                try:
                    if self.stop_event and self.stop_event.is_set():
                        break
                    
                    activity_data['repositories_analyzed'] += 1
                    logging.info(f"Analyzing commits for repo: {repo.name} ({'counting all commits' if fetch_all_commits else 'recent commits'})")
                    
                    # Try different approaches to get commits
                    commits = []
                    
                    if fetch_all_commits:
                        # Fetch ALL commits but only count them, don't store data
                        try:
                            # Method 1: Get all commits by author (no date filter)
                            all_commits = list(repo.get_commits(author=username))
                            commits = all_commits  # Use all for counting
                            logging.info(f"Found {len(all_commits)} total commits in {repo.name}")
                        except GithubException as e:
                            logging.warning(f"Failed to get all commits for {repo.name}: {e}")
                            try:
                                # Fallback: Get commits without author filter and filter manually
                                all_commits = list(repo.get_commits())
                                commits = [c for c in all_commits if c.author and c.author.login == username]
                            except GithubException as e2:
                                logging.warning(f"Fallback failed for {repo.name}: {e2}")
                                continue
                    else:
                        # Fetch RECENT commits only (existing logic)
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
                            repo_commits += 1
                            
                            # Convert to naive datetime for consistency
                            if commit_date.tzinfo:
                                commit_date = commit_date.replace(tzinfo=None)
                            
                            # Count all commits if fetch_all_commits is True
                            if fetch_all_commits:
                                activity_data['total_commits'] += 1
                            
                            # Always count recent commits for comparison
                            if commit_date >= cutoff_date:
                                activity_data['total_recent_commits'] += 1
                                
                                # Only store recent commit details and limit to 50
                                if len(activity_data['recent_commits']) < 50:
                                    day_key = commit_date.strftime('%Y-%m-%d')
                                    hour_key = str(commit_date.hour)
                                    
                                    activity_data['active_days'].add(day_key)
                                    
                                    # Track daily frequency
                                    if day_key not in activity_data['commit_frequency_by_day']:
                                        activity_data['commit_frequency_by_day'][day_key] = 0
                                    activity_data['commit_frequency_by_day'][day_key] += 1
                                    
                                    # Track hourly frequency
                                    if hour_key not in activity_data['commit_frequency_by_hour']:
                                        activity_data['commit_frequency_by_hour'][hour_key] = 0
                                    activity_data['commit_frequency_by_hour'][hour_key] += 1
                                    
                                    # Store commit details (limited to 50 recent commits)
                                    commit_details = {
                                        'repo': repo.name,
                                        'sha': commit.sha,
                                        'message': commit.commit.message[:200],  # Truncate message
                                        'date': commit_date,
                                        'stats': {
                                            'additions': commit.stats.additions if commit.stats else 0,
                                            'deletions': commit.stats.deletions if commit.stats else 0,
                                            'total': commit.stats.total if commit.stats else 0
                                        }
                                    }
                                    
                                    activity_data['recent_commits'].append(commit_details)
                            
                        except Exception as e:
                            logging.warning(f"Error processing commit in {repo.name}: {e}")
                            continue
                    
                    repo_commit_counts[repo.name] = repo_commits
                    
                    if fetch_all_commits:
                        logging.info(f"Counted {repo_commits} total commits from {repo.name}")
                    
                except Exception as e:
                    logging.error(f"Error analyzing repository {repo.name}: {e}")
                    continue
            
            # Determine most active repository
            if repo_commit_counts:
                activity_data['most_active_repo'] = max(repo_commit_counts, key=repo_commit_counts.get)
            
            # Calculate average commits per day based on recent commits data
            total_days = len(activity_data['active_days'])
            if total_days > 0:
                activity_data['avg_commits_per_day'] = activity_data['total_recent_commits'] / total_days
            
            # Convert active_days set to list for JSON serialization
            activity_data['active_days'] = list(activity_data['active_days'])
            
            if fetch_all_commits:
                logging.info(f"Completed analysis for {username}: {activity_data['total_commits']} total commits, {activity_data['total_recent_commits']} recent commits (stored {len(activity_data['recent_commits'])} recent commit details)")
            else:
                logging.info(f"Completed analysis for {username}: {activity_data['total_recent_commits']} recent commits (stored {len(activity_data['recent_commits'])} commit details)")
            
            return activity_data
            
        except GithubException as e:
            logging.error(f"Error analyzing commit activity for {username}: {e}")
            return {
                'total_commits': 0 if fetch_all_commits else 0,
                'total_recent_commits': 0,
                'active_days': [],
                'commit_frequency_by_day': {},
                'commit_frequency_by_hour': {},
                'recent_commits': [],
                'most_active_repo': None,
                'commit_streaks': [],
                'avg_commits_per_day': 0,
                'repositories_analyzed': 0,
                'total_repositories': 0,
                'fetch_mode': 'all' if fetch_all_commits else 'recent'
            }

    def append_single_user_to_export(self, user_data: Dict, filename: str):

        if not user_data:
            logging.warning("No user data to append")
            return
        
        try:
            # Append to JSON file
            json_filename = f"{filename}_raw.json"
            self._append_to_json_file(user_data, json_filename)
            
            # Append to CSV file
            csv_filename = f"{filename}_ml_features.csv"
            flattened_data = self._flatten_user_data(user_data)
            self._append_to_csv_file(flattened_data, csv_filename)
            
            logging.info(f"Appended data for user {user_data.get('username', 'unknown')} to {json_filename} and {csv_filename}")
            
        except Exception as e:
            logging.error(f"Error appending user data: {e}")
            import traceback
            traceback.print_exc()
    
    def _append_to_json_file(self, user_data: Dict, json_filename: str):
        """
        Append user data to JSON file in streaming fashion.
        
        Args:
            user_data (Dict): User data to append
            json_filename (str): JSON filename
        """
        import os
        
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # Check if file exists and has content
        file_exists = os.path.exists(json_filename) and os.path.getsize(json_filename) > 0
        
        if not file_exists:
            # Create new file with opening bracket
            with open(json_filename, 'w', encoding='utf-8') as f:
                f.write('[\n')
                json.dump(user_data, f, indent=2, default=datetime_handler, ensure_ascii=False)
                f.write('\n]')
        else:
            # Read existing file and append new data
            with open(json_filename, 'r+', encoding='utf-8') as f:
                # Go to end of file and move back to find the closing bracket
                f.seek(0, 2)  # Go to end
                file_size = f.tell()
                
                if file_size > 2:
                    # Move back to find the closing bracket
                    f.seek(file_size - 2)
                    last_chars = f.read()
                    
                    if ']' in last_chars:
                        # Position before the closing bracket
                        f.seek(file_size - 2)
                        f.write(',\n')
                        json.dump(user_data, f, indent=2, default=datetime_handler, ensure_ascii=False)
                        f.write('\n]')
                    else:
                        # File might be corrupted, append safely
                        f.write(',\n')
                        json.dump(user_data, f, indent=2, default=datetime_handler, ensure_ascii=False)
                        f.write('\n]')
    
    def _append_to_csv_file(self, flattened_data: Dict, csv_filename: str):
        """
        Append flattened user data to CSV file.
        
        Args:
            flattened_data (Dict): Flattened user data
            csv_filename (str): CSV filename
        """
        import os
        
        df = pd.DataFrame([flattened_data])
        
        # Check if file exists
        file_exists = os.path.exists(csv_filename)
        
        if not file_exists:
            # Create new file with headers
            df.to_csv(csv_filename, index=False, encoding='utf-8')
        else:
            # Append without headers
            df.to_csv(csv_filename, mode='a', header=False, index=False, encoding='utf-8')
    
    def export_for_machine_learning(self, dataset: List[Dict], filename: str):
        """
        Export collected data in machine learning ready format.
        
        Args:
            dataset (List[Dict]): List of user data dictionaries
            filename (str): Base filename for output files
        """
        if not dataset:
            logging.warning("No data to export")
            return
        
        try:
            # Save raw JSON data
            json_filename = f"{filename}_raw.json"
            
            def datetime_handler(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, default=datetime_handler, ensure_ascii=False)
            
            # Flatten data for CSV export
            flattened_data = []
            for user_data in dataset:
                flattened_user = self._flatten_user_data(user_data)
                flattened_data.append(flattened_user)
            
            # Create DataFrame and save as CSV
            if flattened_data:
                df = pd.DataFrame(flattened_data)
                csv_filename = f"{filename}_ml_features.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                logging.info(f"Exported {len(flattened_data)} records to {csv_filename}")
                logging.info(f"Raw data saved to {json_filename}")
                logging.info(f"Features extracted: {list(df.columns)}")
                return csv_filename
            else:
                logging.warning("No flattened data to export")
                
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            import traceback
            traceback.print_exc()

    def _flatten_user_data(self, user_data: Dict) -> Dict:
        """
        Flatten nested user data for machine learning export.
        
        Args:
            user_data (Dict): User data dictionary
            
        Returns:
            Dict: Flattened user data
        """
        flattened = {
            # Basic user info
            'username': user_data.get('username', ''),
            'followers': user_data.get('followers', 0),
            'following': user_data.get('following', 0),
            'public_repos': user_data.get('public_repos', 0),
            'created_at': user_data.get('created_at', ''),
        }
        
        # Extended user data
        extended = user_data.get('extended_user_data', {})
        flattened.update({
            'public_gists': extended.get('public_gists', 0),
            'starred_repos_count': len(extended.get('starred_repos', [])),
            'watched_repos_count': len(extended.get('watched_repos', [])),
            'organizations_count': len(extended.get('organizations', [])),
            'events_count': len(extended.get('events', [])),
            'has_email': bool(extended.get('email')),
            'has_location': bool(extended.get('location')),
            'has_bio': bool(extended.get('bio')),
            'has_company': bool(extended.get('company')),
            'has_blog': bool(extended.get('blog')),
            'is_hireable': extended.get('hireable', False)
        })
        
        # Development patterns
        patterns = user_data.get('development_patterns', {})
        flattened.update({
            'total_commits': len(patterns.get('commit_frequency', [])),
            'productivity_max_streak': patterns.get('productivity_streaks', {}).get('max_streak', 0),
            'productivity_active_days': patterns.get('productivity_streaks', {}).get('total_active_days', 0),
            'commit_comments_count': len(patterns.get('commit_comments', [])),
            'issue_comments_count': len(patterns.get('issue_comments', [])),
            'pr_reviews_count': len(patterns.get('pr_reviews', []))
        })
        
        # Commit activity
        commit_activity = user_data.get('commit_activity', {})
        flattened.update({
            'total_commits': commit_activity.get('total_commits', 0),  # Count only (no data stored)
            'recent_commits_total': commit_activity.get('total_recent_commits', 0),
            'recent_active_days': len(commit_activity.get('active_days', [])),
            'avg_commits_per_day': commit_activity.get('avg_commits_per_day', 0),
            'repositories_analyzed': commit_activity.get('repositories_analyzed', 0),
            'recent_commits': commit_activity.get('recent_commits', []),  # Limited to 50 max
            'fetch_mode': commit_activity.get('fetch_mode', 'recent')
        })
        
        # NEW: Social network features
        social = user_data.get('social_network', {})
        flattened.update({
            'followers_sample_count': len(social.get('followers_list', [])),
            'following_sample_count': len(social.get('following_list', [])),
            'mutual_connections_count': len(social.get('mutual_connections', [])),
            'follower_to_following_ratio': social.get('follower_to_following_ratio', 0),
            'social_influence_score': social.get('social_influence_score', 0)
        })
        
        # NEW: Repository portfolio features
        portfolio = user_data.get('repository_portfolio', {})
        flattened.update({
            'total_repositories': portfolio.get('total_repositories', 0),
            'original_repos': portfolio.get('original_repos', 0),
            'forked_repos': portfolio.get('forked_repos', 0),
            'primary_language': max(portfolio.get('language_distribution', {}).items(), key=lambda x: x[1])[0] if portfolio.get('language_distribution') else '',
            'language_diversity': len(portfolio.get('language_distribution', {})),
            'avg_repo_size': sum(r['size_kb'] for r in portfolio.get('repository_sizes', [])) / len(portfolio.get('repository_sizes', [])) if portfolio.get('repository_sizes') else 0,
            'total_stars_received': sum(r['stars'] for r in portfolio.get('repository_sizes', [])),
            'total_forks_received': sum(r['forks'] for r in portfolio.get('repository_sizes', [])),
            'license_diversity': len(portfolio.get('license_preferences', {})),
            'topics_used_count': len(portfolio.get('topics_used', {})),
            'collaboration_repos_count': len(portfolio.get('collaboration_repos', [])),
            'maintained_repos_ratio': portfolio.get('maintenance_patterns', {}).get('maintenance_ratio', 0),
            'avg_repo_age_days': portfolio.get('maintenance_patterns', {}).get('avg_repo_age_days', 0),
            'documentation_score': portfolio.get('readme_analysis', {}).get('documentation_score', 0),
            'avg_readme_length': portfolio.get('readme_analysis', {}).get('avg_readme_length', 0)
        })
        
        # NEW: Contribution quality features
        quality = user_data.get('contribution_quality', {})
        commit_analysis = quality.get('commit_message_analysis', {})
        pr_analysis = quality.get('pull_request_patterns', {})
        issue_analysis = quality.get('issue_management', {})
        
        flattened.update({
            'avg_commit_message_length': commit_analysis.get('avg_message_length', 0),
            'conventional_commits_ratio': commit_analysis.get('conventional_commits_ratio', 0),
            'multiline_commits_ratio': commit_analysis.get('multiline_commits_ratio', 0),
            'pr_merge_rate': pr_analysis.get('merge_rate', 0),
            'avg_comments_per_pr': pr_analysis.get('avg_comments_per_pr', 0),
            'avg_changes_per_pr': pr_analysis.get('avg_changes_per_pr', 0),
            'issue_closure_rate': issue_analysis.get('closure_rate', 0),
            'avg_issue_description_length': issue_analysis.get('avg_issue_description_length', 0),
            'documentation_ratio': quality.get('documentation_contributions', {}).get('documentation_ratio', 0),
            'testing_ratio': quality.get('testing_patterns', {}).get('testing_ratio', 0),
            'ci_adoption_ratio': quality.get('ci_cd_adoption', {}).get('ci_adoption_ratio', 0)
        })
        
        return flattened 

    def mine_repository_contributors(self, repo_url: str, save_immediately: bool = False, filename: str = None, fetch_all_commits: bool = False) -> List[Dict]:
        """
        Mine repository contributors and optionally save data immediately.
        
        Args:
            repo_url (str): GitHub repository URL (e.g., "https://github.com/owner/repo")
            save_immediately (bool): If True, save data immediately after each contributor is processed
            filename (str): Base filename for immediate saving (required if save_immediately=True)
            fetch_all_commits (bool): If True, fetch all commits instead of just recent commits
            
        Returns:
            List[Dict]: List of contributor data
            
        Raises:
            ValueError: If repo_url is invalid or filename is required but not provided
        """
        if save_immediately and not filename:
            raise ValueError("filename is required when save_immediately=True")
        
        try:
            # Extract owner and repo name from URL
            repo_owner, repo_name = self._extract_repo_info(repo_url)
            
            if self.progress_callback:
                self.progress_callback(f"Getting contributors for {repo_owner}/{repo_name}")
            
            repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            
            # Get repository contributors
            contributors = list(repo.get_contributors())
            contributor_usernames = [contributor.login for contributor in contributors if contributor.type == "User"]
            
            if self.progress_callback:
                self.progress_callback(f"Found {len(contributor_usernames)} contributors: {', '.join(contributor_usernames[:10])}")
                if len(contributor_usernames) > 10:
                    self.progress_callback(f"... and {len(contributor_usernames) - 10} more")
            
            if not contributor_usernames:
                if self.progress_callback:
                    self.progress_callback("No contributors found for this repository")
                return []
            
            # Mine contributor data using parallel collection with optional immediate saving
            commit_mode = "all commits" if fetch_all_commits else "recent commits"
            if self.progress_callback:
                self.progress_callback(f"Starting to mine data ({commit_mode}) for {len(contributor_usernames)} contributors...")
            
            results = self.parallel_data_collection(
                contributor_usernames,
                max_workers=2,  # Keep low to avoid rate limits
                save_immediately=save_immediately,
                filename=filename,
                fetch_all_commits=fetch_all_commits
            )
            
            if self.progress_callback:
                self.progress_callback(f"Repository mining completed! {len(results)}/{len(contributor_usernames)} contributors processed")
            
            return results
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"Error mining repository contributors: {e}")
            logging.error(f"Error mining repository contributors from {repo_url}: {e}")
            raise
    
    def _extract_repo_info(self, repo_url: str) -> tuple:
        """
        Extract owner and repository name from GitHub repository URL.
        
        Args:
            repo_url (str): GitHub repository URL
            
        Returns:
            tuple: (owner, repo_name)
            
        Raises:
            ValueError: If URL is invalid or empty
        """
        import re
        
        repo_url = repo_url.strip()
        if not repo_url:
            raise ValueError("Repository URL cannot be empty")
        
        # Pattern to match GitHub repository URLs
        patterns = [
            r'github\.com/([a-zA-Z0-9\-._]+)/([a-zA-Z0-9\-._]+)',  # https://github.com/owner/repo
            r'github\.com/([a-zA-Z0-9\-._]+)/([a-zA-Z0-9\-._]+)\.git',  # https://github.com/owner/repo.git
        ]
        
        for pattern in patterns:
            match = re.search(pattern, repo_url)
            if match:
                owner = match.group(1)
                repo_name = match.group(2)
                # Remove common suffixes
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                return owner, repo_name
        
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}") 

    def collect_social_network_data(self, username: str) -> Dict:
        """
        Collect social network and collaboration data.
        
        Args:
            username (str): GitHub username to analyze
            
        Returns:
            Dict: Social network analysis data
        """
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            user = self.github.get_user(username)
            social_data = {
                'followers_list': [],
                'following_list': [],
                'mutual_connections': [],
                'follower_to_following_ratio': 0,
                'social_influence_score': 0,
                'collaboration_network': [],
                'mentorship_indicators': {},
                'cross_org_collaborations': []
            }
            
            # Get followers and following (limited to avoid rate limits)
            try:
                followers = list(user.get_followers()[:50])  # Limit to 50
                social_data['followers_list'] = [
                    {
                        'login': follower.login,
                        'followers': follower.followers,
                        'public_repos': follower.public_repos,
                        'created_at': follower.created_at
                    } for follower in followers
                ]
                
                following = list(user.get_following()[:50])  # Limit to 50
                social_data['following_list'] = [
                    {
                        'login': follow.login,
                        'followers': follow.followers,
                        'public_repos': follow.public_repos,
                        'created_at': follow.created_at
                    } for follow in following
                ]
                
                # Calculate mutual connections
                follower_logins = set(f.login for f in followers)
                following_logins = set(f.login for f in following)
                mutual = follower_logins.intersection(following_logins)
                social_data['mutual_connections'] = list(mutual)
                
                # Calculate ratios
                if user.following > 0:
                    social_data['follower_to_following_ratio'] = user.followers / user.following
                
                # Social influence score (simple heuristic)
                social_data['social_influence_score'] = (
                    user.followers * 0.6 + 
                    user.public_repos * 0.3 + 
                    len(mutual) * 0.1
                )
                
            except GithubException as e:
                logging.warning(f"Error fetching social network for {username}: {e}")
            
            return social_data
            
        except GithubException as e:
            logging.error(f"Error collecting social network data for {username}: {e}")
            return {}
    
    def analyze_repository_portfolio(self, username: str) -> Dict:
        """
        Analyze user's repository portfolio in detail.
        
        Args:
            username (str): GitHub username to analyze
            
        Returns:
            Dict: Repository portfolio analysis
        """
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            user = self.github.get_user(username)
            repos = list(user.get_repos())
            
            portfolio_data = {
                'total_repositories': len(repos),
                'original_repos': 0,
                'forked_repos': 0,
                'language_distribution': {},
                'repository_sizes': [],
                'license_preferences': {},
                'topics_used': {},
                'repo_creation_pattern': {},
                'readme_analysis': {},
                'collaboration_repos': [],
                'maintenance_patterns': {},
                'repository_maturity': []
            }
            
            total_size = 0
            languages_bytes = {}
            license_counts = {}
            topics_counts = {}
            creation_years = {}
            readme_lengths = []
            collaborative_repos = []
            
            for repo in repos[:20]:  # Limit to avoid rate limits
                try:
                    if repo.fork:
                        portfolio_data['forked_repos'] += 1
                    else:
                        portfolio_data['original_repos'] += 1
                    
                    # Repository size
                    if repo.size:
                        total_size += repo.size
                        portfolio_data['repository_sizes'].append({
                            'name': repo.name,
                            'size_kb': repo.size,
                            'stars': repo.stargazers_count,
                            'forks': repo.forks_count
                        })
                    
                    # Languages
                    try:
                        languages = repo.get_languages()
                        for lang, bytes_count in languages.items():
                            languages_bytes[lang] = languages_bytes.get(lang, 0) + bytes_count
                    except:
                        pass
                    
                    # License analysis
                    if repo.license:
                        license_name = repo.license.name
                        license_counts[license_name] = license_counts.get(license_name, 0) + 1
                    
                    # Topics
                    topics = repo.get_topics()
                    for topic in topics:
                        topics_counts[topic] = topics_counts.get(topic, 0) + 1
                    
                    # Creation pattern
                    year = repo.created_at.year
                    creation_years[year] = creation_years.get(year, 0) + 1
                    
                    # README analysis
                    try:
                        readme = repo.get_readme()
                        readme_content = readme.decoded_content.decode('utf-8')
                        readme_lengths.append({
                            'repo': repo.name,
                            'readme_length': len(readme_content),
                            'has_badges': '[![' in readme_content or '![' in readme_content,
                            'has_sections': '##' in readme_content or '#' in readme_content
                        })
                    except:
                        readme_lengths.append({
                            'repo': repo.name,
                            'readme_length': 0,
                            'has_badges': False,
                            'has_sections': False
                        })
                    
                    # Collaboration indicators
                    if repo.forks_count > 0 or repo.stargazers_count > 5:
                        collaborative_repos.append({
                            'name': repo.name,
                            'forks': repo.forks_count,
                            'stars': repo.stargazers_count,
                            'watchers': repo.watchers_count,
                            'contributors_count': repo.get_contributors().totalCount if hasattr(repo.get_contributors(), 'totalCount') else 0
                        })
                    
                    # Repository maturity
                    days_old = (datetime.now() - repo.created_at.replace(tzinfo=None)).days
                    last_push_days = (datetime.now() - repo.pushed_at.replace(tzinfo=None)).days if repo.pushed_at else 9999
                    
                    portfolio_data['repository_maturity'].append({
                        'name': repo.name,
                        'age_days': days_old,
                        'days_since_last_push': last_push_days,
                        'commits_count': repo.get_commits().totalCount if hasattr(repo.get_commits(), 'totalCount') else 0,
                        'is_maintained': last_push_days < 30
                    })
                    
                except Exception as e:
                    logging.warning(f"Error analyzing repo {repo.name}: {e}")
                    continue
            
            # Process collected data
            total_bytes = sum(languages_bytes.values())
            if total_bytes > 0:
                portfolio_data['language_distribution'] = {
                    lang: (bytes_count / total_bytes) * 100 
                    for lang, bytes_count in languages_bytes.items()
                }
            
            portfolio_data['license_preferences'] = license_counts
            portfolio_data['topics_used'] = topics_counts
            portfolio_data['repo_creation_pattern'] = creation_years
            portfolio_data['collaboration_repos'] = collaborative_repos
            portfolio_data['readme_analysis'] = {
                'avg_readme_length': sum(r['readme_length'] for r in readme_lengths) / len(readme_lengths) if readme_lengths else 0,
                'repos_with_badges': sum(1 for r in readme_lengths if r['has_badges']),
                'repos_with_sections': sum(1 for r in readme_lengths if r['has_sections']),
                'documentation_score': len([r for r in readme_lengths if r['readme_length'] > 500]) / len(readme_lengths) if readme_lengths else 0
            }
            
            # Maintenance patterns
            maintained_repos = [r for r in portfolio_data['repository_maturity'] if r['is_maintained']]
            portfolio_data['maintenance_patterns'] = {
                'maintained_repos_count': len(maintained_repos),
                'maintenance_ratio': len(maintained_repos) / len(portfolio_data['repository_maturity']) if portfolio_data['repository_maturity'] else 0,
                'avg_repo_age_days': sum(r['age_days'] for r in portfolio_data['repository_maturity']) / len(portfolio_data['repository_maturity']) if portfolio_data['repository_maturity'] else 0
            }
            
            return portfolio_data
            
        except GithubException as e:
            logging.error(f"Error analyzing repository portfolio for {username}: {e}")
            return {}
    
    def analyze_contribution_quality(self, username: str) -> Dict:
        """
        Analyze the quality and patterns of user contributions.
        
        Args:
            username (str): GitHub username to analyze
            
        Returns:
            Dict: Contribution quality analysis
        """
        if not username:
            raise ValueError("username cannot be empty")
        
        try:
            user = self.github.get_user(username)
            repos = list(user.get_repos())
            
            quality_data = {
                'commit_message_analysis': {},
                'pull_request_patterns': {},
                'issue_management': {},
                'code_review_participation': {},
                'documentation_contributions': {},
                'testing_patterns': {},
                'ci_cd_adoption': {}
            }
            
            commit_messages = []
            pr_data = []
            issue_data = []
            doc_contributions = 0
            test_contributions = 0
            ci_files = 0
            
            for repo in repos[:10]:  # Limit to avoid rate limits
                try:
                    if repo.fork:
                        continue
                    
                    # Analyze commits
                    commits = list(repo.get_commits(author=username)[:20])
                    for commit in commits:
                        message = commit.commit.message
                        commit_messages.append({
                            'message': message,
                            'length': len(message),
                            'has_type': any(prefix in message.lower() for prefix in ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:']),
                            'lines_count': len(message.split('\n')),
                            'repo': repo.name
                        })
                    
                    # Analyze pull requests
                    try:
                        prs = list(repo.get_pulls(creator=username, state='all')[:10])
                        for pr in prs:
                            pr_data.append({
                                'state': pr.state,
                                'merged': pr.merged,
                                'comments': pr.comments,
                                'review_comments': pr.review_comments,
                                'commits': pr.commits,
                                'additions': pr.additions,
                                'deletions': pr.deletions,
                                'changed_files': pr.changed_files,
                                'repo': repo.name
                            })
                    except:
                        pass
                    
                    # Analyze issues
                    try:
                        issues = list(repo.get_issues(creator=username, state='all')[:10])
                        for issue in issues:
                            issue_data.append({
                                'state': issue.state,
                                'comments': issue.comments,
                                'labels_count': len(issue.labels),
                                'body_length': len(issue.body) if issue.body else 0,
                                'repo': repo.name
                            })
                    except:
                        pass
                    
                    # Check for documentation files
                    try:
                        contents = repo.get_contents("")
                        for content in contents:
                            if content.type == "file":
                                filename = content.name.lower()
                                if any(doc_pattern in filename for doc_pattern in ['readme', 'doc', 'wiki', 'guide', 'tutorial']):
                                    doc_contributions += 1
                                elif any(test_pattern in filename for test_pattern in ['test', 'spec']):
                                    test_contributions += 1
                                elif filename in ['.github/workflows', '.travis.yml', '.circleci', 'jenkinsfile', '.gitlab-ci.yml']:
                                    ci_files += 1
                    except:
                        pass
                    
                except Exception as e:
                    logging.warning(f"Error analyzing contributions in {repo.name}: {e}")
                    continue
            
            # Process commit message analysis
            if commit_messages:
                quality_data['commit_message_analysis'] = {
                    'total_commits': len(commit_messages),
                    'avg_message_length': sum(c['length'] for c in commit_messages) / len(commit_messages),
                    'conventional_commits_ratio': sum(1 for c in commit_messages if c['has_type']) / len(commit_messages),
                    'multiline_commits_ratio': sum(1 for c in commit_messages if c['lines_count'] > 1) / len(commit_messages)
                }
            
            # Process PR patterns
            if pr_data:
                merged_prs = [pr for pr in pr_data if pr['merged']]
                quality_data['pull_request_patterns'] = {
                    'total_prs': len(pr_data),
                    'merge_rate': len(merged_prs) / len(pr_data),
                    'avg_comments_per_pr': sum(pr['comments'] for pr in pr_data) / len(pr_data),
                    'avg_changes_per_pr': sum(pr['additions'] + pr['deletions'] for pr in pr_data) / len(pr_data),
                    'avg_files_per_pr': sum(pr['changed_files'] for pr in pr_data) / len(pr_data)
                }
            
            # Process issue management
            if issue_data:
                closed_issues = [issue for issue in issue_data if issue['state'] == 'closed']
                quality_data['issue_management'] = {
                    'total_issues': len(issue_data),
                    'closure_rate': len(closed_issues) / len(issue_data),
                    'avg_labels_per_issue': sum(issue['labels_count'] for issue in issue_data) / len(issue_data),
                    'avg_issue_description_length': sum(issue['body_length'] for issue in issue_data) / len(issue_data)
                }
            
            # Documentation and testing
            quality_data['documentation_contributions'] = {
                'doc_files_count': doc_contributions,
                'documentation_ratio': doc_contributions / len(repos) if repos else 0
            }
            
            quality_data['testing_patterns'] = {
                'test_files_count': test_contributions,
                'testing_ratio': test_contributions / len(repos) if repos else 0
            }
            
            quality_data['ci_cd_adoption'] = {
                'ci_files_count': ci_files,
                'ci_adoption_ratio': ci_files / len(repos) if repos else 0
            }
            
            return quality_data
            
        except GithubException as e:
            logging.error(f"Error analyzing contribution quality for {username}: {e}")
            return {} 