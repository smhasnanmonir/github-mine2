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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global GitHub token
GITHUB_TOKEN = "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"

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
            repos = list(user.get_repos())
            
            # Filter out forks
            original_repos = [repo for repo in repos if not repo.fork]
            
            # Sort by different metrics
            by_stars = sorted(original_repos, key=lambda r: r.stargazers_count, reverse=True)[:limit]
            by_forks = sorted(original_repos, key=lambda r: r.forks_count, reverse=True)[:limit]
            by_size = sorted(original_repos, key=lambda r: r.size, reverse=True)[:limit]
            by_watchers = sorted(original_repos, key=lambda r: r.watchers_count, reverse=True)[:limit]
            by_recent = sorted(original_repos, key=lambda r: r.updated_at, reverse=True)[:limit]
            
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
                logging.warning("Skipping empty user_data")
                continue
            
            logging.info(f"Processing user: {user_data.get('username', 'Unknown')}")
            
            # Handle timezone-aware datetime from GitHub API
            created_at = user_data.get('created_at', datetime.now())
            if hasattr(created_at, 'tzinfo') and created_at.tzinfo is not None:
                created_at = created_at.replace(tzinfo=None)
            
            features = {
                'username': user_data.get('username'),
                'followers': user_data.get('followers', 0),
                'following': user_data.get('following', 0),
                'public_repos': user_data.get('public_repos', 0),
                'account_age_days': (datetime.now() - created_at).days,
                'public_gists': user_data.get('extended_user_data', {}).get('public_gists', 0),
                'org_count': len(user_data.get('extended_user_data', {}).get('organizations', [])),
                'starred_repo_count': len(user_data.get('extended_user_data', {}).get('starred_repos', [])),
                'watched_repo_count': len(user_data.get('extended_user_data', {}).get('watched_repos', [])),
                'event_count': len(user_data.get('extended_user_data', {}).get('events', []))
            }
            
            patterns = user_data.get('development_patterns', {})
            if patterns:
                features.update({
                    'total_commits': len(patterns.get('commit_frequency', [])),
                    'avg_commits_per_repo': np.mean([r.get('total_commits', 0) for r in patterns.get('repository_lifecycle', [])]) if patterns.get('repository_lifecycle') else 0,
                    'max_productivity_streak': patterns.get('productivity_streaks', {}).get('max_streak', 0),
                    'languages_used': len(patterns.get('language_evolution', {})),
                    'commit_comments_count': len(patterns.get('commit_comments', [])),
                    'issue_comments_count': len(patterns.get('issue_comments', [])),
                    'pr_reviews_count': len(patterns.get('pr_reviews', []))
                })
            
            # Add commit activity features
            commit_activity = user_data.get('commit_activity', {})
            if commit_activity:
                features.update({
                    'recent_commits_count': commit_activity.get('total_recent_commits', 0),
                    'recent_active_days': len(commit_activity.get('active_days', [])),
                    'avg_commits_per_active_day': commit_activity.get('avg_commits_per_day', 0),
                    'most_active_hour': max(commit_activity.get('commit_frequency_by_hour', {}).items(), key=lambda x: x[1])[0] if commit_activity.get('commit_frequency_by_hour') else 0,
                    'repositories_analyzed': commit_activity.get('repositories_analyzed', 0),
                    'total_original_repositories': commit_activity.get('total_repositories', 0)
                })
            
            # Add contribution activity features
            contribution_activity = user_data.get('contribution_activity', {})
            if contribution_activity:
                features.update({
                    'contribution_level': contribution_activity.get('contribution_level', 'Unknown'),
                    'recent_contributions_30_days': contribution_activity.get('recent_contributions_30_days', 0),
                    'activity_score': contribution_activity.get('activity_score', 0),
                    'repositories_contributed_to': contribution_activity.get('repositories_contributed_to', 0),
                    'issues_opened': contribution_activity.get('issues_opened', 0),
                    'issues_closed': contribution_activity.get('issues_closed', 0),
                    'pull_requests_opened': contribution_activity.get('pull_requests_opened', 0),
                    'pull_requests_merged': contribution_activity.get('pull_requests_merged', 0),
                    'recently_active_repositories': contribution_activity.get('recently_active_repositories', 0),
                    'contribution_total_stars': contribution_activity.get('total_stars_earned', 0),
                    'contribution_total_forks': contribution_activity.get('total_forks_earned', 0),
                    'event_types_count': len(contribution_activity.get('event_types', {}))
                })
            
            # Add language features
            language_data = user_data.get('language_percentages', {})
            if language_data:
                features.update({
                    'total_languages_used': language_data.get('total_languages', 0),
                    'primary_language': language_data.get('primary_language', ''),
                    'language_diversity': language_data.get('language_diversity_score', 0),
                    'top_language_percentage': list(language_data.get('language_percentages', {}).values())[0] if language_data.get('language_percentages') else 0
                })
            
            # Add top repositories features
            top_repos = user_data.get('top_repositories', {})
            if top_repos:
                features.update({
                    'total_original_repos': top_repos.get('total_original_repos', 0),
                    'total_stars_earned': top_repos.get('total_stars_earned', 0),
                    'total_forks_earned': top_repos.get('total_forks_earned', 0),
                    'avg_stars_per_repo': top_repos.get('total_stars_earned', 0) / max(top_repos.get('total_original_repos', 1), 1),
                    'most_starred_repo_stars': top_repos.get('by_stars', [{}])[0].get('stars', 0) if top_repos.get('by_stars') else 0
                })
            
            # Add interests features
            interests = user_data.get('interests', {})
            if interests:
                features.update({
                    'repository_topics_count': len(interests.get('repository_topics', {})),
                    'inferred_interests_count': len(interests.get('inferred_interests', [])),
                    'starred_topics_count': len(interests.get('starred_repo_topics', {})),
                    'organization_count': len(interests.get('organization_domains', []))
                })
            
            repos = user_data.get('repositories', [])
            if repos:
                # Use numpy with nan handling for empty arrays
                repo_stars = [r.get('stars', 0) for r in repos]
                repo_forks = [r.get('forks', 0) for r in repos]
                repo_sizes = [r.get('size', 0) for r in repos]
                
                features.update({
                    'avg_repo_stars': np.mean(repo_stars) if repo_stars else 0,
                    'avg_repo_forks': np.mean(repo_forks) if repo_forks else 0,
                    'avg_repo_size': np.mean(repo_sizes) if repo_sizes else 0,
                    'total_contributors': sum(len(r.get('contributor_network', {}).get('contributors', [])) for r in repos),
                    'avg_branches': np.mean([len(r.get('extended_repo_data', {}).get('branches', [])) for r in repos]) if repos else 0,
                    'avg_releases': np.mean([len(r.get('extended_repo_data', {}).get('releases', [])) for r in repos]) if repos else 0,
                    'avg_issues': np.mean([len(r.get('issues', [])) for r in repos]) if repos else 0,
                    'avg_resolution_time': np.mean([issue.get('resolution_time_hours', 0) for r in repos for issue in r.get('issues', []) if issue.get('resolution_time_hours')]) if any(r.get('issues', []) for r in repos) else 0
                })
            
            logging.info(f"Features extracted for {user_data.get('username')}: {len(features)} features")
            ml_features.append(features)
        
        if not ml_features:
            logging.error("No features extracted from dataset")
            raise ValueError("No valid features could be extracted from the dataset")
        
        logging.info(f"Creating DataFrame with {len(ml_features)} rows and {len(ml_features[0])} columns")
        df = pd.DataFrame(ml_features)
        
        # Export CSV
        csv_filename = f"{filename}_ml_features.csv"
        df.to_csv(csv_filename, index=False)
        logging.info(f"CSV file saved: {csv_filename} ({len(df)} rows, {len(df.columns)} columns)")
        
        # Export JSON
        json_filename = f"{filename}_raw.json"
        with open(json_filename, 'w') as f:
            json.dump(dataset, f, indent=2, default=str)
        logging.info(f"JSON file saved: {json_filename}")
        
        # Print summary
        print(f"Export Summary:")
        print(f"- CSV file: {csv_filename} ({len(df)} rows, {len(df.columns)} columns)")
        print(f"- JSON file: {json_filename}")
        print(f"- Features per user: {len(ml_features[0])}")
        
        logging.info(f"ML-ready dataset exported: {csv_filename}")
        logging.info(f"Raw dataset exported: {json_filename}")
    
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

class GitHubMinerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Profile Miner")
        self.stop_event = threading.Event()
        self.mining_thread = None
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Token input
        self.label_token = ttk.Label(self.main_frame, text="GitHub Token:")
        self.label_token.pack(pady=5)
        self.entry_token = ttk.Entry(self.main_frame, width=50, show="*")
        self.entry_token.pack(pady=5)
        
        # Profile URL input
        self.label_url = ttk.Label(self.main_frame, text="GitHub Profile URL:")
        self.label_url.pack(pady=5)
        self.entry_url = ttk.Entry(self.main_frame, width=50)
        self.entry_url.pack(pady=5)
        
        # Buttons frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(pady=10)
        
        self.mine_button = ttk.Button(self.button_frame, text="Mine Data", command=self.start_mining)
        self.mine_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="Stop Mining", command=self.stop_mining, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.set_token_button = ttk.Button(self.button_frame, text="Set Global Token", command=self.set_global_token)
        self.set_token_button.pack(side=tk.LEFT, padx=5)
        
        self.convert_button = ttk.Button(self.button_frame, text="Convert JSON to CSV", command=self.convert_json_to_csv)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        # Progress frame
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status text
        self.status_text = tk.Text(self.main_frame, height=10, width=50)
        self.status_text.pack(pady=10)
        
    def update_status(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def set_global_token(self):
        global GITHUB_TOKEN
        token = self.entry_token.get()
        if not token or token.strip() == "":
            messagebox.showerror("Error", "Token cannot be empty")
            return
        GITHUB_TOKEN = token
        messagebox.showinfo("Success", "Global token has been set!")
    
    def extract_username(self, url: str) -> str:
        url = url.strip()
        if not url:
            raise ValueError("Profile URL cannot be empty")
        pattern = r'github\.com/([a-zA-Z0-9-]+)'
        match = re.search(pattern, url)
        if not match:
            raise ValueError("Invalid GitHub profile URL")
        return match.group(1)
    
    def start_mining(self):
        self.stop_event.clear()  # Reset the stop event
        self.mine_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar.start()
        self.status_text.delete(1.0, tk.END)
        
        # Start mining in a separate thread
        self.mining_thread = threading.Thread(target=self.mining_profile)
        self.mining_thread.daemon = True
        self.mining_thread.start()
    
    def mining_profile(self):
        try:
            token = self.entry_token.get()
            profile_url = self.entry_url.get()
            
            username = self.extract_username(profile_url)
            self.update_status(f"Starting mining for user: {username}")
            
            if self.stop_event.is_set():
                return
            
            miner = AdvancedGitHubMiner(token, progress_callback=self.update_status, stop_event=self.stop_event)
            self.update_status("Collecting user data...")
            dataset = miner.parallel_data_collection([username], max_workers=1)
            
            if self.stop_event.is_set():
                self.update_status("Mining was stopped by user.")
                return
            
            if not dataset or dataset[0] is None:
                raise ValueError(f"No data collected for user: {username}")
            
            if self.stop_event.is_set():
                self.update_status("Mining was stopped by user.")
                return
            
            self.update_status("Exporting data...")
            timestamp = self.generate_timestamp()
            miner.export_for_machine_learning(dataset, f"github_data_{username}_{timestamp}")
            
            if not self.stop_event.is_set():
                self.update_status("Mining completed successfully!")
                messagebox.showinfo("Success", f"Data mined and exported for {username}!")
            
        except ValueError as e:
            if not self.stop_event.is_set():
                self.update_status(f"Error: {str(e)}")
                messagebox.showerror("Error", str(e))
        except Exception as e:
            if not self.stop_event.is_set():
                self.update_status(f"Unexpected error: {str(e)}")
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            self.progress_bar.stop()
            self.mine_button.config(state='normal')
            self.stop_button.config(state='disabled')

    def generate_timestamp(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def stop_mining(self):
        self.stop_event.set()
        self.stop_button.config(state='disabled')
        self.mine_button.config(state='disabled')
        self.progress_bar.stop()
        self.update_status("Mining stopped.")

    def convert_json_to_csv(self):
        """Convert a JSON file to CSV using file dialog."""
        try:
            from tkinter import filedialog
            
            # Ask user to select JSON file
            json_file_path = filedialog.askopenfilename(
                title="Select JSON file to convert",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not json_file_path:
                return  # User cancelled
            
            # Ask user where to save CSV
            csv_file_path = filedialog.asksaveasfilename(
                title="Save CSV file as",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialvalue=json_file_path.replace('.json', '_converted.csv')
            )
            
            if not csv_file_path:
                return  # User cancelled
            
            self.update_status(f"Converting {json_file_path} to CSV...")
            
            # Create miner instance for conversion
            token = self.entry_token.get() or GITHUB_TOKEN
            miner = AdvancedGitHubMiner(token)
            
            # Perform conversion
            result = miner.convert_json_to_csv(json_file_path, csv_file_path)
            
            self.update_status(f"Conversion completed: {result}")
            messagebox.showinfo("Success", f"JSON file converted to CSV successfully!\nSaved as: {result}")
            
        except Exception as e:
            self.update_status(f"Conversion error: {str(e)}")
            messagebox.showerror("Error", f"Failed to convert JSON to CSV: {e}")

def main():
    root = tk.Tk()
    app = GitHubMinerGUI(root)
    root.mainloop()

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
    main()
