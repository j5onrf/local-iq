# media.py

<img alt="20260530_142040" src="https://github.com/user-attachments/assets/06c6a8b5-44f5-4267-a5e5-04c44f54b0bc" />
A simple, lightweight Terminal User Interface (TUI) media player controller and responsive audio visualizer built in Python. Inspired by the clean, minimal aesthetic of `cliamp`, it integrates seamlessly with `playerctl` to provide global media management directly inside your shell.

## media.sh
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

