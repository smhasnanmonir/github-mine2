# GitHub Miner - Refactored Version

A comprehensive tool for discovering and analyzing GitHub profiles with **advanced machine learning features**, **immediate data saving**, and **deep GitHub API analysis**.

## 🚀 What's New

The code has been **completely refactored** from a single 2650-line `main.py` file into a well-organized, modular structure with **immediate data preservation** and **comprehensive GitHub API mining**.

## 📊 **COMPREHENSIVE GITHUB ANALYSIS**

**NEW: We now mine 50+ advanced features** from the GitHub API that were previously missing:

### 🌐 **Social Network Analysis**
- **Followers & Following networks** (not just counts)
- **Mutual connections** discovery
- **Social influence scoring**
- **Collaboration patterns**
- **Network quality metrics**

### 📈 **Repository Portfolio Analysis**
- **Language distribution** with percentages
- **Repository maturity** and maintenance patterns
- **License preferences** across projects
- **Documentation quality** (README analysis)
- **Project collaboration** indicators
- **Repository size** and complexity metrics
- **Topic usage** patterns

### 🏆 **Contribution Quality Analysis**
- **Commit message quality** (conventional commits, length)
- **Pull request success rates** and patterns
- **Issue management** efficiency
- **Code review participation**
- **Testing patterns** and CI/CD adoption
- **Documentation contributions**

### 📅 **Advanced Temporal Analysis**
- **Coding time patterns** (timezone analysis)
- **Seasonal activity** patterns
- **Repository creation** trends over time
- **Maintenance consistency**

## 📁 New Project Structure

```
github_miner/
├── __init__.py              # Package initialization
├── config.py                # Configuration and constants  
├── discovery.py             # AutoProfileDiscovery class
├── miner.py                 # AdvancedGitHubMiner class (50+ features!)
├── gui.py                   # GitHubMinerGUI class
└── cli.py                   # Command-line interface

main_entry.py                # New main entry point
example_incremental_mining.py # Demo of immediate saving features
main.py                      # Original file (legacy)
requirements.txt             # Dependencies
```

## 🛠️ Usage

### GUI Mode (Default)
```bash
python main_entry.py
```

### CLI Mode  
```bash
# Automated profile discovery
python main_entry.py cli --token YOUR_TOKEN --mode trending --language python

# Repository contributor mining
python main_entry.py repo --token YOUR_TOKEN --repo-url https://github.com/owner/repo
```

### Programmatic Usage
```python
from github_miner import AdvancedGitHubMiner, AutoProfileDiscovery

# Traditional batch processing
discoverer = AutoProfileDiscovery("your_token")
users = discoverer.discover_trending_developers(language="python")

miner = AdvancedGitHubMiner("your_token") 
data = miner.parallel_data_collection(users)
miner.export_for_machine_learning(data, "output")

# NEW: Immediate saving (data saved after each user is processed)
data = miner.parallel_data_collection(
    users, 
    save_immediately=True, 
    filename="output"
)

# NEW: Repository mining with immediate saving
repo_data = miner.mine_repository_contributors(
    "https://github.com/owner/repo",
    save_immediately=True,
    filename="repo_output"
)
```

## 📊 **Data Features Extracted (50+ Features)**

### Basic Profile Data
- `followers`, `following`, `public_repos`, `created_at`, etc.

### **NEW: Social Network Features**
- `mutual_connections_count`, `social_influence_score`
- `follower_to_following_ratio`, `followers_sample_count`

### **NEW: Repository Portfolio Features**
- `primary_language`, `language_diversity`, `total_stars_received`
- `maintained_repos_ratio`, `documentation_score`, `avg_repo_size`
- `license_diversity`, `collaboration_repos_count`

### **NEW: Contribution Quality Features**  
- `conventional_commits_ratio`, `pr_merge_rate`, `issue_closure_rate`
- `avg_commit_message_length`, `testing_ratio`, `ci_adoption_ratio`
- `documentation_ratio`, `avg_changes_per_pr`

### Development Patterns
- `productivity_max_streak`, `total_commits`, `recent_active_days`
- `avg_commits_per_day`, `commit_comments_count`

## ⚡ Immediate Data Saving

**NEW FEATURE**: Data is now saved immediately after each user's data is collected!

### Benefits:
✅ **Data Preservation** - No data loss if process is interrupted  
✅ **Progress Monitoring** - See results as they're collected  
✅ **Fault Tolerance** - All processed data is preserved  
✅ **Memory Efficient** - No need to store all data in memory  

### How it works:
1. User data is collected one by one
2. **Immediately saved** to JSON and CSV files after each user
3. Files are continuously updated
4. If process stops, all collected data is preserved

### Example:
```python
# Profile mining with immediate saving
miner.parallel_data_collection(
    usernames=["user1", "user2", "user3"], 
    max_workers=2,
    save_immediately=True,
    filename="my_data"
)

# Repository mining with immediate saving  
miner.mine_repository_contributors(
    "https://github.com/owner/repo",
    save_immediately=True,
    filename="repo_data"
)
# Data is saved after each user/contributor is processed!
```

## 📦 Module Overview

- **config.py**: Global settings and constants
- **discovery.py**: Profile discovery strategies
- **miner.py**: Data mining and analysis + **immediate saving** + **50+ features**
- **gui.py**: Graphical user interface
- **cli.py**: Command-line interface

## 🎯 Key Benefits

✅ **Modular Architecture** - Each module has a single responsibility  
✅ **Easy Imports** - `from github_miner import AdvancedGitHubMiner`  
✅ **Better Testing** - Test individual components  
✅ **Maintainable** - Changes don't cascade  
✅ **Professional** - Proper Python package structure  
✅ **Data Safe** - **NEW: Immediate saving prevents data loss**  
✅ **Comprehensive** - **NEW: 50+ advanced GitHub features**  
✅ **ML Ready** - **Perfect for machine learning research**  

## 🔧 CLI Options

### Profile Discovery
Available modes: `trending`, `search`, `popular`, `active`, `organizations`, `comprehensive`

```bash
python main_entry.py cli \
    --token YOUR_TOKEN \
    --mode comprehensive \
    --language python,javascript \
    --max-users 50 \
    --output results
```

### Repository Mining
```bash
python main_entry.py repo \
    --token YOUR_TOKEN \
    --repo-url https://github.com/owner/repo \
    --output repo_results
```

Data will be saved immediately after each user to `results_TIMESTAMP_raw.json` and `results_TIMESTAMP_ml_features.csv`

## 🧪 Try the Demo

Run the immediate saving demo:
```bash
python example_incremental_mining.py
```

Choose from:
1. Multi-user immediate saving demo
2. Single user immediate saving  
3. **Repository contributors mining** (NEW!)

Try interrupting any process with Ctrl+C to see data preservation in action!

## 🔄 Migration from Old Version

**Old way** (batch processing):
```python
results = miner.parallel_data_collection(users)
miner.export_for_machine_learning(results, "output")
```

**New way** (immediate saving + comprehensive features):
```python
# Profile mining with 50+ features
results = miner.parallel_data_collection(
    users, 
    save_immediately=True, 
    filename="output"
)

# Repository mining (NEW!)
repo_results = miner.mine_repository_contributors(
    "https://github.com/owner/repo",
    save_immediately=True,
    filename="repo_output"
)
# Data is automatically saved after each user/contributor!
```

## 🧬 **Perfect for Machine Learning Research**

The GitHub Miner now extracts **50+ comprehensive features** perfect for:
- **Developer productivity** prediction
- **Repository success** modeling  
- **Collaboration pattern** analysis
- **Code quality** assessment
- **Social network** research
- **Career trajectory** analysis

The refactored GitHub Miner is now **research-grade** with **bulletproof data collection**! 🚀🧬 