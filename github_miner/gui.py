"""
Graphical User Interface Module for GitHub Miner.

This module provides a comprehensive GUI for GitHub profile discovery and mining
with support for profile mining, repository mining, and automated discovery.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import re
from datetime import datetime

from .discovery import AutoProfileDiscovery
from .miner import AdvancedGitHubMiner
from .config import GITHUB_TOKEN, set_github_token


class GitHubMinerGUI:
    """
    Main GUI class for GitHub Miner application.
    
    Provides a tabbed interface with the following features:
    - Profile Mining: Mine individual GitHub profiles
    - Repository Mining: Mine repository contributors
    - Auto Discovery: Automated profile discovery with various strategies
    """
    
    def __init__(self, root):
        """
        Initialize the GUI application.
        
        Args:
            root: Tkinter root window
        """
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
        
        self.stop_button = ttk.Button(self.control_frame, text="Stop Mining", 
                                     command=self.stop_mining, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(self.control_frame, text="Clear Log", 
                                      command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=5)
    
    def setup_profile_tab(self):
        """Setup the Profile Mining tab."""
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
        
        self.mine_button = ttk.Button(self.button_frame, text="Mine Profile", 
                                     command=self.start_profile_mining)
        self.mine_button.pack(side=tk.LEFT, padx=5)
        
        self.set_token_button = ttk.Button(self.button_frame, text="Set Global Token", 
                                          command=self.set_global_token)
        self.set_token_button.pack(side=tk.LEFT, padx=5)
    
    def setup_repo_tab(self):
        """Setup the Repository Mining tab."""
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
        
        self.mine_repo_button = ttk.Button(self.repo_button_frame, text="Mine Contributors", 
                                          command=self.start_repo_mining)
        self.mine_repo_button.pack(side=tk.LEFT, padx=5)
        
        self.set_repo_token_button = ttk.Button(self.repo_button_frame, text="Set Global Token", 
                                               command=self.set_global_token)
        self.set_repo_token_button.pack(side=tk.LEFT, padx=5)
    
    def setup_auto_discovery_tab(self):
        """Setup the Auto Discovery tab."""
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
        ttk.Checkbutton(adv_grid, text="Include Trending", 
                       variable=self.include_trending_var).grid(row=0, column=2, padx=10)
        
        self.include_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(adv_grid, text="Include Recently Active", 
                       variable=self.include_active_var).grid(row=0, column=3, padx=10)
    
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
                    users = discoverer.discover_by_search_criteria(criteria, 
                                                                  params['max_users'] // len(params['languages']))
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
        """Mine data for discovered users with immediate saving after each user."""
        try:
            token = self.auto_token_entry.get() or self.entry_token.get() or GITHUB_TOKEN
            
            def progress_callback(message):
                self.update_status(message)
            
            miner = AdvancedGitHubMiner(token, progress_callback=progress_callback, stop_event=self.stop_event)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{output_prefix}_{timestamp}"
            
            self.update_status(f"Starting data collection for {len(usernames)} users...")
            self.update_status(f"Data will be saved immediately after each user is processed")
            self.update_status(f"Files: {filename}_raw.json and {filename}_ml_features.csv")
            
            # Use immediate saving with the standard parallel_data_collection method
            all_results = miner.parallel_data_collection(
                usernames, 
                max_workers=2,  # Keep it low to avoid rate limits
                save_immediately=True,
                filename=filename
            )
            
            if all_results and not self.stop_event.is_set():
                self.update_status(f"Auto discovery and mining completed!")
                self.update_status(f"Total users processed: {len(all_results)}/{len(usernames)}")
                self.update_status(f"Success rate: {len(all_results)/len(usernames)*100:.1f}%")
                self.update_status(f"Final files: {filename}_raw.json and {filename}_ml_features.csv")
                
                messagebox.showinfo("Success", 
                    f"Auto discovery completed!\n"
                    f"Discovered: {len(usernames)} profiles\n"
                    f"Successfully mined: {len(all_results)} profiles\n"
                    f"Data saved immediately after each user to:\n"
                    f"- {filename}_raw.json\n"
                    f"- {filename}_ml_features.csv")
            elif not self.stop_event.is_set():
                self.update_status("No data was successfully collected")
            else:
                self.update_status("Operation was stopped by user")
                
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
        """Set the global GitHub token."""
        token = self.entry_token.get() or self.repo_entry_token.get()
        if not token or token.strip() == "":
            messagebox.showerror("Error", "Token cannot be empty")
            return
        set_github_token(token)
        messagebox.showinfo("Success", "Global token has been set!")
    
    def start_profile_mining(self):
        """Start profile mining in a separate thread."""
        self.mine_button.config(state='disabled')
        self.progress_bar.start()
        self.status_text.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self.mine_profile)
        thread.daemon = True
        thread.start()
    
    def start_repo_mining(self):
        """Start repository mining in a separate thread."""
        self.mine_repo_button.config(state='disabled')
        self.progress_bar.start()
        self.status_text.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self.mine_repository)
        thread.daemon = True
        thread.start()
    
    def mine_profile(self):
        """Mine a single GitHub profile with immediate saving."""
        try:
            token = self.entry_token.get()
            profile_url = self.entry_url.get()
            
            username = self.extract_username(profile_url)
            self.update_status(f"Starting mining for user: {username}")
            
            miner = AdvancedGitHubMiner(token, progress_callback=self.update_status)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"profile_{username}_{timestamp}"
            
            self.update_status("Collecting user data with immediate saving...")
            
            # Use immediate saving with standard parallel_data_collection
            dataset = miner.parallel_data_collection(
                [username], 
                max_workers=1,
                save_immediately=True,
                filename=filename
            )
            
            if not dataset or dataset[0] is None:
                raise ValueError(f"No data collected for user: {username}")
            
            self.update_status("Mining completed successfully!")
            self.update_status(f"Data saved to {filename}_raw.json and {filename}_ml_features.csv")
            
            messagebox.showinfo("Success", 
                f"Data mined and exported for {username}!\n"
                f"Files saved:\n"
                f"- {filename}_raw.json\n"
                f"- {filename}_ml_features.csv")
            
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
        """Mine repository contributors with immediate saving."""
        try:
            token = self.repo_entry_token.get()
            repo_url = self.repo_entry_url.get()
            
            if not token or not repo_url:
                raise ValueError("Both GitHub token and repository URL are required")
            
            self.update_status(f"Starting mining for repository: {repo_url}")
            
            miner = AdvancedGitHubMiner(token, progress_callback=self.update_status, stop_event=self.stop_event)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            filename = f"repo_{repo_name}_{timestamp}"
            
            self.update_status("Collecting repository contributor data with immediate saving...")
            self.update_status(f"Data will be saved immediately after each contributor is processed")
            self.update_status(f"Files: {filename}_raw.json and {filename}_ml_features.csv")
            
            # Mine repository contributors with immediate saving
            dataset = miner.mine_repository_contributors(
                repo_url,
                save_immediately=True,
                filename=filename
            )
            
            if not dataset:
                self.update_status("No contributor data was collected")
                messagebox.showwarning("Warning", "No contributor data was collected from this repository")
            else:
                self.update_status("Repository mining completed successfully!")
                self.update_status(f"Data saved to {filename}_raw.json and {filename}_ml_features.csv")
                
                messagebox.showinfo("Success", 
                    f"Repository mining completed!\n"
                    f"Contributors processed: {len(dataset)}\n"
                    f"Data saved immediately after each contributor to:\n"
                    f"- {filename}_raw.json\n"
                    f"- {filename}_ml_features.csv")
            
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
        """
        Extract GitHub username from a profile URL.
        
        Args:
            url (str): GitHub profile URL
            
        Returns:
            str: Extracted username
            
        Raises:
            ValueError: If URL is invalid or empty
        """
        url = url.strip()
        if not url:
            raise ValueError("Profile URL cannot be empty")
        
        pattern = r'github\.com/([a-zA-Z0-9-]+)'
        match = re.search(pattern, url)
        if not match:
            raise ValueError("Invalid GitHub profile URL")
        
        return match.group(1)


def create_gui():
    """
    Create and run the GitHub Miner GUI application.
    
    Returns:
        None
    """
    root = tk.Tk()
    app = GitHubMinerGUI(root)
    root.mainloop() 