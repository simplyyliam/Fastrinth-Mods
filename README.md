# 🚀 Modrinth Mod Downloader

> Your automated shopping assistant for Minecraft mods - because manually downloading 180+ mods is a special kind of torture.

## What's This All About?

Ever tried to set up a modded Minecraft server or client with dozens (or hundreds) of mods? You know the drill: search for each mod, find the right version for your Minecraft version and mod loader, click download, wait, repeat 180 times. Your wrist hurts, your soul hurts, and you've only done 23 mods.

This tool is your escape hatch. Give it a list of mod names, and it'll handle the rest - searching, version matching, downloading, and even skipping mods you already have.

## The Brain Food: Core Concepts

### 🎯 The Search Problem: Finding Needles in a Digital Haystack

When you search for "Sodium" on Modrinth, you're not just typing into a box - you're querying an API (Application Programming Interface). Think of an API like a restaurant menu: you don't go into the kitchen and make your own food; you ask the waiter (the API) for what you want, and the kitchen (Modrinth's servers) delivers it.

```python
def search_mod(self, mod_name: str) -> Optional[Dict]:
    response = self.session.get(
        f"{self.config.api_base_url}/search",
        params={"query": mod_name},
        timeout=10
    )
```

This code is literally asking Modrinth: "Hey, got any mods matching this name?" The `timeout=10` is your patience limit - if Modrinth takes more than 10 seconds to respond, we bail out.

### 🔄 Retry Logic: The Persistent Friend

The internet is a fickle beast. Servers hiccup, connections drop, and sometimes APIs just... don't feel like responding. That's where retry logic comes in:

```python
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
```

Imagine you're knocking on a friend's door, but they don't answer immediately. Do you give up? No! You knock again, maybe wait a bit longer this time. The `backoff_factor` is that "wait a bit longer" part - it's exponential, so:
- 1st retry: wait 1 second
- 2nd retry: wait 2 seconds
- 3rd retry: wait 4 seconds

The `status_forcelist` tells us WHEN to retry. A `429` means "slow down, you're knocking too fast!" A `500` means "our kitchen is on fire, try again later."

### 🎮 Version Compatibility: The Minecraft Tetris

Not every mod works with every Minecraft version or mod loader. It's like trying to fit a PlayStation 5 game into a Nintendo Switch - wrong hardware, wrong generation, no bueno.

```python
compatible_versions = [
    version for version in versions
    if (self.config.loader in version["loaders"] and 
        self.config.game_version in version["game_versions"])
]
```

This is a **list comprehension** (Python's fancy way of filtering lists). Read it like: "Give me all versions where BOTH the loader matches (Fabric/Forge) AND the game version matches (1.21.11)."

Think of it as a bouncer at a club checking two IDs: one for your age (game version) and one for your membership (loader type). Both need to check out, or you're not getting in.

### 🏗️ Object-Oriented Design: Building with LEGO Blocks

This code uses **classes** - reusable blueprints for creating objects. We have two main classes:

#### `ModrinthConfig` - The Settings Manager
Like a control panel for a spaceship. It holds all your preferences:
- Where to save mods
- What loader you're using (Fabric/Forge)
- What Minecraft version you're targeting

#### `ModrinthDownloader` - The Worker Bee
This does the heavy lifting. It:
- Searches for mods
- Checks compatibility
- Downloads files
- Tracks what succeeded or failed

**Why split them?** Separation of concerns. The config doesn't need to know HOW to download, and the downloader doesn't need to worry about WHERE the config came from. They each have one job, and they do it well.

```python
config = ModrinthConfig(save_directory="mods", loader="fabric")
downloader = ModrinthDownloader(config)
```

It's like building with LEGO: you make separate pieces (config, downloader) and snap them together to build something complex.

### 📦 Sessions: Keeping Your Connection Warm

```python
self.session = self._create_session()
```

A **session** in HTTP is like keeping a phone line open instead of dialing every time you want to talk. It:
- Reuses the same connection (faster!)
- Maintains cookies/headers (if needed)
- Applies your retry strategy automatically

Without sessions, every API call would be like introducing yourself to the same person 180 times. Awkward and slow.

### 🎓 Type Hints: Documentation That Runs

```python
def search_mod(self, mod_name: str) -> Optional[Dict]:
```

Those `: str` and `-> Optional[Dict]` bits are **type hints**. They're like road signs for your code:
- `mod_name: str` means "this should be text"
- `-> Optional[Dict]` means "I'll return a dictionary, or maybe None if things go wrong"

They don't enforce anything (Python is chill like that), but they help:
- Your IDE catch mistakes before you run the code
- Other developers understand what to pass in
- Your future self remember what you were thinking

### 🪵 Logging: Your Code's Diary

```python
self.logger.info(f"Downloading '{file_name}'...")
```

**Logging** beats `print()` statements because:
- You can control verbosity (INFO, WARNING, ERROR)
- Timestamps are automatic
- You can route logs to files, not just the console
- It's the difference between scribbled notes and a proper journal

## How to Use This Thing

### Prerequisites

```bash
pip install requests
```

That's it. Seriously. Just the `requests` library for HTTP calls.

### Basic Usage

1. **Edit the config** in the `main()` function:

```python
config = ModrinthConfig(
    save_directory="mods",      # Where to save downloaded mods
    loader="fabric",             # or "forge"
    game_version="1.21.11"       # Your Minecraft version
)
```

2. **Add your mod list**:

```python
mod_names = [
    "Sodium",
    "Lithium",
    "Iris Shaders",
    # ... add more
]
```

3. **Run it**:

```bash
python modrinth_mod_downloader.py
```

4. **Grab coffee** ☕ while it works.

### What Happens Under the Hood

```
For each mod:
  1. Search Modrinth API by name
  2. Get the mod's "slug" (unique identifier)
  3. Fetch all versions for that mod
  4. Filter versions by loader + game version
  5. Pick the latest compatible version
  6. Check if already downloaded (skip if yes)
  7. Download the .jar file
  8. Save to your mods folder
  9. Log success/failure
```

## Architecture: The 10,000 Foot View

```
┌─────────────────┐
│  ModrinthConfig │  ← Settings storage
└────────┬────────┘
         │
         │ passed to
         ↓
┌─────────────────────┐
│ ModrinthDownloader  │  ← Does all the work
├─────────────────────┤
│ - search_mod()      │  ← Searches API
│ - get_compatible_   │  ← Filters versions
│   version()         │
│ - download_mod()    │  ← Gets the file
│ - print_summary()   │  ← Shows results
└─────────────────────┘
```

## Cool Features You Might Miss

### 🛡️ Already Downloaded? Skip It.

```python
if self.is_mod_downloaded(file_name):
    self.logger.info(f"'{file_name}' already exists. Skipping download.")
    return True
```

Run the script twice? No worries. It checks what you already have and skips re-downloading. Saves bandwidth and time.

### 📊 Summary Report

At the end, you get a nice summary:
```
==================================================
DOWNLOAD SUMMARY
==================================================
Total mods processed: 180
Successfully downloaded: 175
Failed: 5

Failed mods:
  - Some-Obscure-Mod
  - Another-Missing-Mod
```

### 🎯 Pathlib Over String Manipulation

```python
file_path = self.config.save_directory / file_name
```

Modern Python uses `pathlib` for file paths. That `/` operator joins paths intelligently - no more worrying about Windows backslashes vs. Unix forward slashes.

## Common Gotchas

### "No compatible versions found"

The mod might not be available for your loader or game version. Double-check:
- Is it Fabric-only but you're using Forge?
- Are you on 1.21.11 but the mod only supports 1.20.x?

### "Failed to search for mod"

Could be:
- Internet connection issues
- Modrinth API is down
- You're rate-limited (too many requests too fast)

The retry logic will help, but if Modrinth is down, nothing will work.

### "Download keeps failing"

Some mods are HUGE. The default timeout is 30 seconds. If you're on slow internet, bump it up:

```python
response = self.session.get(file_url, timeout=60)  # 60 seconds
```

## Extending This Code

Want to add features? Here are some ideas:

### 1. **GUI Interface**
Wrap this in Tkinter or PyQt for a drag-and-drop mod manager.

### 2. **Dependency Resolution**
Some mods require other mods (like how Sodium Extra needs Sodium). Parse the mod's dependencies and auto-download them.

### 3. **Update Checker**
Compare downloaded mods against latest versions and show which are outdated.

### 4. **Multi-threading**
Download multiple mods simultaneously instead of one-by-one. (Use `concurrent.futures` or `asyncio`).

## The Philosophy

This code embodies a few programming principles:

- **DRY (Don't Repeat Yourself)**: Functions encapsulate repeated logic
- **Single Responsibility**: Each method does ONE thing well
- **Fail Gracefully**: Errors are logged, not crashed
- **User-Friendly**: Clear logging and summaries

## License

Do whatever you want with this code. It's yours now. Build something cool. 🚀

## Questions?

The code is pretty self-documenting, but if something's unclear, read through the docstrings (the `"""triple-quoted"""` strings under each function). They explain what each function does, what it expects, and what it returns.

Happy modding! 🎮
