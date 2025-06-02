# GitHub Miner - Refactored Version

A comprehensive tool for discovering and analyzing GitHub profiles with machine learning features and **immediate data saving**.

## 🚀 What's New

The code has been **completely refactored** from a single 2650-line `main.py` file into a well-organized, modular structure with **immediate data preservation**.

## 📁 New Project Structure

```
github_miner/
├── __init__.py              # Package initialization
├── config.py                # Configuration and constants  
├── discovery.py             # AutoProfileDiscovery class
├── miner.py                 # AdvancedGitHubMiner class (with immediate saving)
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
- **miner.py**: Data mining and analysis + **immediate saving**
- **gui.py**: Graphical user interface
- **cli.py**: Command-line interface

## 🎯 Key Benefits

✅ **Modular Architecture** - Each module has a single responsibility  
✅ **Easy Imports** - `from github_miner import AdvancedGitHubMiner`  
✅ **Better Testing** - Test individual components  
✅ **Maintainable** - Changes don't cascade  
✅ **Professional** - Proper Python package structure  
✅ **Data Safe** - **NEW: Immediate saving prevents data loss**  

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

**New way** (immediate saving):
```python
# Profile mining
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

The refactored GitHub Miner is now production-ready with **bulletproof data collection**! 🚀 