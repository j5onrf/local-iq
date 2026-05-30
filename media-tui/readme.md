# media.py

<img alt="20260530_142040" src="https://github.com/user-attachments/assets/06c6a8b5-44f5-4267-a5e5-04c44f54b0bc" />
A simple, lightweight Terminal User Interface (TUI) media player controller and responsive audio visualizer built in Python. Inspired by the clean, minimal aesthetic of `cliamp`, it integrates seamlessly with `playerctl` to provide global media management directly inside your shell.

## media.sh media.lua
<img alt="20260530_153205" src="https://github.com/user-attachments/assets/5e0bfda4-5813-473c-a2ae-f50bc489f802" />
An ultra-lightweight, purely reactive inline media controller built in Bash. Designed to live directly inside your active shell stream without taking over the window, it uses playerctl and wpctl to provide zero-stutter playback and volume management at the tap of a key.

## Features

- **Universal Core Support:** Handles YouTube, YouTube Music, Spotify Web player instances, and local media streams (VLC, MPV, etc.) automatically.
- **Smart Browser Prioritization:** Automatically hunts and locks onto Chromium/Brave sessions first, falling back gracefully to Firefox and native media environments.
- **Failsafe Web Controls:** Leverages targeted hardware key injection (`xdotool`) to effortlessly resume stubborn or asleep sandboxed browser tabs (like Spotify Web) without programmatic failure.
- **5 Multi-Visualizer Modes:** Features real-time procedural and mathematical equalizer styles toggled dynamically with `[v]`:
  1. **Official Wave (Default):** Discrete high-contrast retro dot matrix outline wave layout.
  2. **Official Bars:** 10-Band EQ columns complete with smooth decay physics modeling.
  3. **Official Block:** Continuous, dense solid vertical audio spectrum wall.
  4. **Smooth Sine:** Fluid undulating mathematical wave landscape.
  5. **Pinnacle Peaks:** Isolated geometric accent peak shapes.
- **Resting Audio State:** Displays a pristine, low-profile resting wave profile matching your custom TUI backdrop when media tracks are paused.

---

## The Tools

### media.py
A simple, lightweight Terminal User Interface (TUI) media player controller and responsive audio visualizer built in Python. It provides an immersive, full-window layout featuring live, bouncing audio frequency bars—perfect for leaving open on a second monitor while listening to music.

### media.sh
An ultra-lightweight, purely reactive inline media controller built in Bash. Designed to live directly inside your active shell stream without taking over the window, it provides instant volume and track management at the tap of a key with zero background system overhead.

### media.lua
A blazing fast, native-efficiency inline media controller rewritten in Lua. Mirroring the inline design of the Bash version, it offers optimal string pattern matching and instant execution memory speeds, perfectly optimized to integrate with modern Lua-based desktop setups like Hyprland 0.55+.

---

## Comparison At A Glance

| Feature | `media.sh` | `media.lua` | `media.py` |
| :--- | :--- | :--- | :--- |
| **Interface Style** | Inline (2 Lines) | Inline (2 Lines) | Full TUI + Visualizer |
| **Language Runtime** | Bash (Native Shell) | Lua / LuaJIT | Python 3 |
| **Startup Speed** | Instant | Blazing Fast | Moderate |
| **Idle Resource Cost** | Absolute Zero | Absolute Zero | Low-to-Moderate |
| **Primary Focus** | Maximum Minimalism | Peak Efficiency | Visual Aesthetic |

---

## When to use which?

* **Use `media.py`** when you want to look at the screen—like opening a dedicated terminal tile to watch the audio spectrum visualizer bounce along to the beat.
* **Use `media.lua`** during your active daily workflow. It stays completely out of your way inside your command stream, uses zero idle resources, and fires with lightning-fast responsiveness.
* **Use `media.sh`** if you want a reliable tool that works out of the box on any machine with zero language environment dependencies.

## Requirements

Ensure your Linux system has the necessary backend tools installed:

```bash

# Arch Linux
sudo pacman -S playerctl xdotool

```

## Installation & Running

Clone your script repository or copy the code block into a destination folder, make it executable, and run it:

```bash
chmod +x media.py
./media.py
./media.sh

```

## Hotkeys

| Key | Action |
| --- | --- |
| `[Space]` / `[Enter]` | Play / Pause (Failsafe browser toggle) |
| `[v]` | Cycle through Visualizer Styles |
| `[n]` / `[➔]` | Skip to Next Track |
| `[p]` / `[⬅]` | Previous Track |
| `[+]` / `[=]` | Turn Volume Up (5% intervals) |
| `[-]` | Turn Volume Down (5% intervals) |
| `[q]` | Quit Program safely |

---
