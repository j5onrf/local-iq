# basepage

A minimal, text-focused terminal dashboard and feed reader. It aggregates your favorite subreddits, standard RSS, and Atom feeds into a single lightweight, keyboard-driven interface.

Designed to run completely sandboxed in your alternate screen buffer to keep your primary terminal scrollback clean.

## Features

* **Universal Feed Parser**: Supports Reddit subreddits, standard Atom (like Arch Linux News), and RSS 2.0 (like Hacker News) out of the box.
* **Auto-Discovery Private Redirects**: Automatically fetches, verifies, and routes Reddit links through active [Redlib](https://github.com/redlib-org/redlib) private front-end instances to prevent trackable redirects.
* **Alternate Screen Sandboxing**: Runs inside the terminal's alternate screen buffer (`?1049h`), leaving your terminal exactly as it was when you exit.
* **Hacker News Integration**: Intercepts HN selections to immediately open the native discussion thread in your default browser instead of blank self-text pages.
* **Background Sync**: Launches an invisible background worker on boot to pre-cache your feeds and sorting states, keeping the UI fast.
* **Dynamic Menu & Configuration**: Customize and scale your dashboard simply by adding new entries to a single configuration dictionary inside the script.

## Quick Start

### 1. Requirements
* **Python 3.11+**
* An internet connection (for initial feed fetching and Redlib instance validation).

### 2. Installation
Clone this repository or download the script directly:

```bash
mkdir -p ~/.config/local-ai/basepage-tui/
wget -O ~/.config/local-ai/basepage-tui/basepage.py https://raw.githubusercontent.com/yourusername/basepage/main/basepage.py
chmod +x ~/.config/local-ai/basepage-tui/basepage.py
```

### 3. Usage
Run the script to launch the dashboard:
```bash
python3 ~/.config/local-ai/basepage-tui/basepage.py
```

## Adding Custom Feeds

You can add any RSS, Atom, or Reddit feed by modifying the `FEEDS` dictionary at the top of the `basepage.py` script:

```python
FEEDS = {
    "r/hyprland": {"type": "reddit", "subreddit": "hyprland"},
    "r/unixporn": {"type": "reddit", "subreddit": "unixporn"},
    "Arch Linux News": {"type": "custom", "url": "https://archlinux.org/feeds/news/"},
    "Hacker News": {"type": "custom", "url": "https://news.ycombinator.com/rss"},
    "Your Custom Feed": {"type": "custom", "url": "https://example.com/feed.xml"}
}
```

## Navigation & Controls

### Main Controller Grid
* `↑` / `↓` : Navigate options
* `Enter` : Select option / Open Feed

### Index Page
* `↑` / `↓` : Scroll entries
* `←` / `→` : Change page (15 items per page)
* `Enter` : Open deep text reader
* `o` : Open link in default browser (using Redlib redirects for Reddit)
* `q` : Exit back to Main Controller Grid

### Text Reader
* `↑` / `↓` : Scroll text body
* `o` : Open link in browser
* `q` / `Enter` : Close reader and return to index

