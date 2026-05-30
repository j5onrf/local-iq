#!/usr/bin/env python3
# Universal Media Playback TUI v0.7.3

import sys
import os
import tty
import termios
import select
import subprocess
import shutil
import time
import math
import random

# Global state to mimic falling peak decay from vis_bars.go
NUM_BANDS = 10
BAND_WIDTH = 6 
current_heights = [0.0] * NUM_BANDS
peak_heights = [0.0] * NUM_BANDS

locked_player = None

def get_key_non_blocking():
    """Checks stdin for a keypress while terminal is in raw mode."""
    rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
    if rlist:
        ch = sys.stdin.read(1)
        if ch == '\033': 
            rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
            if rlist:
                ch += sys.stdin.read(2)
        return ch
    return None

def get_prioritized_player():
    """Finds all system players and prioritizes: Brave/Chromium -> Firefox -> Others."""
    global locked_player
    try:
        result = subprocess.run(["playerctl", "-l"], capture_output=True, text=True, check=True)
        players = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
    except subprocess.CalledProcessError:
        return None

    if not players:
        locked_player = None
        return None

    if locked_player and locked_player in players:
        return locked_player

    chromium_tier, firefox_tier, other_tier = [], [], []
    for p in players:
        p_low = p.lower()
        if "brave" in p_low or "chromium" in p_low:
            chromium_tier.append(p)
        elif "firefox" in p_low:
            firefox_tier.append(p)
        else:
            other_tier.append(p)

    sorted_players = chromium_tier + firefox_tier + other_tier
    
    for player in sorted_players:
        try:
            status = subprocess.run(["playerctl", f"--player={player}", "status"], capture_output=True, text=True).stdout.strip()
            if status == "Playing":
                locked_player = player
                return player
        except Exception:
            pass
            
    if sorted_players:
        locked_player = sorted_players[0]
        return sorted_players[0]
        
    return None

def run_pctl_for_player(player, args):
    """Safely runs playerctl metadata queries."""
    try:
        result = subprocess.run(["playerctl", f"--player={player}"] + args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def trigger_robust_toggle(player):
    """Failsafe play/pause logic using hardware keys to keep Spotify active."""
    if not player:
        return
    title = run_pctl_for_player(player, ["metadata", "title"]).lower()
    if "spotify" in player.lower() or "spotify" in title:
        if shutil.which("xdotool"):
            subprocess.run(["xdotool", "key", "XF86AudioPlay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    subprocess.run(["playerctl", f"--player={player}", "play-pause"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_system_volume():
    """Queries true system master volume using wpctl (preferred for PipeWire) or pactl fallback."""
    # Method A: Try wpctl (Native PipeWire/WirePlumber)
    if shutil.which("wpctl"):
        try:
            res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True)
            if res.returncode == 0:
                # Format is "Volume: 0.55" or "Volume: 0.55 [MUTED]"
                val_str = res.stdout.replace("Volume:", "").split()[0]
                return int(float(val_str) * 100)
        except Exception:
            pass

    # Method B: Fallback to pactl if wpctl errors out
    if shutil.which("pactl"):
        try:
            res = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True)
            if res.returncode == 0 and "Volume:" in res.stdout:
                parts = res.stdout.split()
                for p in parts:
                    if "%" in p:
                        return int(p.replace("%", ""))
        except Exception:
            pass

    # Method C: Ultimate player fallback
    global locked_player
    if locked_player:
        try:
            vol_str = run_pctl_for_player(locked_player, ["volume"])
            return int(float(vol_str) * 100) if vol_str else 100
        except Exception:
            pass
            
    return 100

def adjust_system_volume(direction="up"):
    """Adjusts hardware master slider using native wpctl steps or pactl alternate parsing."""
    wp_delta = "0.05+" if direction == "up" else "0.05-"
    pa_delta = "+5%" if direction == "up" else "-5%"  # Swapped sign position to fix pactl literal 5% bug

    if shutil.which("wpctl"):
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", wp_delta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    if shutil.which("pactl"):
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", pa_delta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    global locked_player
    if locked_player:
        pctl_delta = "0.05+" if direction == "up" else "0.05-"
        subprocess.run(["playerctl", f"--player={locked_player}", "volume", pctl_delta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def fmt_time(microseconds_or_seconds, is_micro=False):
    """Converts raw timestamps into clean MM:SS format strings."""
    try:
        total_seconds = float(microseconds_or_seconds)
        if is_micro:
            total_seconds /= 1_000_000
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError):
        return "00:00"

def generate_dynamic_cava(is_playing, ticks, style_mode):
    """Generates the visualizer line supporting all full styles from the cliamp architecture."""
    global current_heights, peak_heights
    num_columns = 60
    
    if not is_playing:
        return "⠂⠁⠂⠁⠤⠂⠁⠂⠁⠤⠂⠁⠂⠁⠤⠂⠁⠂⠁⠤⠂⠁⠂⠁⠤⠂⠁⠂⠁⠤⠂⠁⠂⠁⠤⠂⠁⠂⠁⠤⠂⠁⠂⠁⠤⠂⠁"

    standard_blocks = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    dense_blocks = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    peak_markers = [" ", " ", "⠂", "⠃", "⠆", "⠇", "⠦", "⠧", "⠷"]

    # --- Mode 0: Official GitHub vis_wave.go (Discrete Outline Wave) [DEFAULT] ---
    if style_mode == 0:
        t = ticks * 0.4
        visualizer_line = []
        for i in range(num_columns):
            wave = math.sin(t + i * 0.3) * math.cos(t * 0.4) * 3.5
            h_idx = int(max(0, min(len(peak_markers) - 1, 4 + wave)))
            char = peak_markers[h_idx] if h_idx > 1 else "⠂"
            if h_idx > 6:
                visualizer_line.append(f"\033[38;5;209m{char}\033[0m")
            elif h_idx > 3:
                visualizer_line.append(f"\033[38;5;110m{char}\033[0m")
            else:
                visualizer_line.append(f"\033[32m{char}\033[0m")
        return "".join(visualizer_line)

    # --- Mode 1: Official GitHub vis_bars.go (Channel Columns) ---
    elif style_mode == 1:
        visualizer_line = []
        for b in range(NUM_BANDS):
            target = random.uniform(1.0, 8.0) if random.random() > 0.15 else random.uniform(0.0, 3.0)
            current_heights[b] += (target - current_heights[b]) * 0.4
            h_idx = int(max(0, min(len(standard_blocks) - 1, current_heights[b])))
            chunk_char = standard_blocks[h_idx]
            colored_chunk = f"\033[32m{chunk_char * BAND_WIDTH}\033[0m"
            if h_idx > 6:
                colored_chunk = f"\033[38;5;209m{chunk_char * BAND_WIDTH}\033[0m"
            elif h_idx > 3:
                colored_chunk = f"\033[38;5;110m{chunk_char * BAND_WIDTH}\033[0m"
            visualizer_line.append(colored_chunk)
        return "".join(visualizer_line)

    # --- Mode 2: Official GitHub vis_block.go (Dense Solid Wall) ---
    elif style_mode == 2:
        t = ticks * 0.35
        visualizer_line = []
        for i in range(num_columns):
            wave1 = math.sin(t + i * 0.2) * 3.0
            wave2 = math.cos(t * 0.5 - i * 0.1) * 2.0
            h_idx = int(max(0, min(len(dense_blocks) - 1, 4 + wave1 + wave2)))
            if h_idx > 6:
                visualizer_line.append(f"\033[38;5;209m{dense_blocks[h_idx]}\033[0m")
            elif h_idx > 3:
                visualizer_line.append(f"\033[38;5;110m{dense_blocks[h_idx]}\033[0m")
            else:
                visualizer_line.append(f"\033[32m{dense_blocks[h_idx]}\033[0m")
        return "".join(visualizer_line)

    # --- Mode 3: Custom Smooth Sine Wave ---
    elif style_mode == 3:
        t = ticks * 0.35
        visualizer_line = []
        for i in range(num_columns):
            wave1 = math.sin(t + i * 0.25) * 3.5
            wave2 = math.cos(t * 0.6 - i * 0.15) * 2.5
            noise = random.uniform(-0.6, 0.6)
            h_idx = int(max(0, min(len(standard_blocks) - 1, 4 + wave1 + wave2 + noise)))
            if h_idx > 6:
                visualizer_line.append(f"\033[38;5;209m{standard_blocks[h_idx]}\033[0m")
            elif h_idx > 3:
                visualizer_line.append(f"\033[38;5;110m{standard_blocks[h_idx]}\033[0m")
            else:
                visualizer_line.append(f"\033[32m{standard_blocks[h_idx]}\033[0m")
        return "".join(visualizer_line)

    # --- Mode 4: Geometric Pinnacle Peaks ---
    else:
        peaks = [" ", " ", "░", "▒", "▓", "█", "▕", "▎", "▲"]
        t = ticks * 0.35
        visualizer_line = []
        for i in range(num_columns):
            wave = math.sin(t + i * 0.4) * math.cos(t * 0.5) * 4.0
            h_idx = int(max(0, min(len(peaks) - 1, 4 + wave)))
            if h_idx > 6:
                visualizer_line.append(f"\033[38;5;209m{peaks[h_idx]}\033[0m")
            elif h_idx > 3:
                visualizer_line.append(f"\033[38;5;110m{peaks[h_idx]}\033[0m")
            else:
                visualizer_line.append(f"\033[32m{peaks[h_idx]}\033[0m")
        return "".join(visualizer_line)

def run_media_control():
    """TUI loop rendering metadata frames and processing key configurations."""
    if not shutil.which("playerctl"):
        print("\033[1;31mError: 'playerctl' is required.\033[0m")
        return

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    sys.stdout.write("\033[?25l\033[H\033[J")
    sys.stdout.flush()

    last_mpris_check = 0.0
    ticks = 0
    visualizer_mode = 0  
    
    title, artist, status, pos_str, len_str = "", "", "", "", ""
    active_player = None
    is_playing = False

    mode_names = {0: "Official Wave", 1: "Official Bars", 2: "Official Block", 3: "Smooth Sine", 4: "Pinnacle Peaks"}

    try:
        tty.setraw(fd)

        while True:
            current_timestamp = time.time()
            ticks += 1
            
            if current_timestamp - last_mpris_check > 0.2:
                active_player = get_prioritized_player()
                if active_player:
                    title = run_pctl_for_player(active_player, ["metadata", "title"])
                    artist = run_pctl_for_player(active_player, ["metadata", "artist"])
                    status = run_pctl_for_player(active_player, ["status"])
                    pos_str = run_pctl_for_player(active_player, ["position"])
                    len_str = run_pctl_for_player(active_player, ["metadata", "mpris:length"])
                    is_playing = (status == "Playing")
                else:
                    title = ""
                last_mpris_check = current_timestamp

            sys.stdout.write("\033[H")
            sys.stdout.write("\r\033[1;32m C L I A M P\033[0m\033[K\r\n")

            if active_player and title:
                full_track = f"{artist} - {title}" if artist else title
                for word in [" - YouTube Music", " - YouTube", " - Spotify"]:
                    full_track = full_track.split(word)[0]
                clean_track = f"{full_track[:55]}..." if len(full_track) > 55 else full_track

                is_micro = False
                if len_str:
                    try:
                        is_micro = float(len_str) > 10000000
                    except ValueError:
                        pass

                time_current = fmt_time(pos_str, is_micro=False)
                if pos_str and is_micro:
                    time_current = fmt_time(float(pos_str) * 1000000, is_micro=True) if "." in pos_str else fmt_time(pos_str, is_micro=True)

                time_total = fmt_time(len_str, is_micro=is_micro) if len_str else "00:00"
                time_line = f"{time_current} / {time_total}"
                
                status_badge = "\033[1;45;30m Playing \033[0m" if is_playing else "\033[1;42;30m Paused \033[0m"

                sys.stdout.write(f"\r ♫ \033[38;5;209m{clean_track:<55}\033[0m\033[K\r\n")
                sys.stdout.write(f"\r {time_line:<45}{status_badge:>15}\033[K\r\n")
                sys.stdout.write(f"\r {generate_dynamic_cava(is_playing, ticks, visualizer_mode)}\033[K\r\n")

                progress_bar = "━" * 60
                if pos_str and len_str:
                    try:
                        p_val = float(pos_str)
                        l_val = float(len_str)
                        if is_micro:
                            l_val /= 1_000_000
                        pct = p_val / l_val if l_val > 0 else 0
                        filled = max(0, min(60, int(pct * 60)))
                        progress_bar = f"\033[38;5;209m{'━' * filled}\033[0m\033[90m{'━' * (60 - filled)}\033[0m"
                    except Exception:
                        pass
                sys.stdout.write(f"\r {progress_bar}\033[K\r\n\r\n")

                # Fetch real system volume level on every refresh frame
                vol_pct = get_system_volume()
                vol_pct = max(0, min(100, vol_pct)) 
                sys.stdout.write(f"\r \033[1mVOL\033[0m  [\033[32m{'━' * (vol_pct // 10)}{' ' * (10 - (vol_pct // 10))}\033[0m] {vol_pct}%\033[K\r\n")
                
                src_display = active_player.split('.')[0][:12]
                sys.stdout.write(f"\r \033[90mOUT Rate 44.1kHz  Resample 4/4  Src: {src_display}  Viz: {mode_names[visualizer_mode]}\033[0m\033[K\r\n")

            else:
                sys.stdout.write("\r ♫ \033[90mIdle\033[0m\033[K\r\n")
                sys.stdout.write("\r 00:00 / 00:00\033[K\r\n")
                sys.stdout.write(f"\r {generate_dynamic_cava(False, 0, 0)}\033[K\r\n")
                sys.stdout.write(f"\r \033[90m{'━' * 60}\033[0m\033[K\r\n\r\n")
                sys.stdout.write("\r \033[90m[ No active system media player detected ]\033[0m\033[K\r\n")
                sys.stdout.write("\r\033[K\r\n")

            # --- Bottom Playlist Split ---
            sys.stdout.write("\r\n\033[90m ── Playlist ──────────────────────────────────────────────────\033[0m\033[K\r\n")
            if active_player and title:
                sys.stdout.write(f"\r  \033[32m▶ 1. {clean_track[:50]:<50}\033[0m\033[K\r\n")
            else:
                sys.stdout.write("\r  \033[90m1. (Empty Queue)\033[0m\033[K\r\n")
                
            sys.stdout.write("\r\033[K\r\n")
            sys.stdout.write("\r \033[90m[Spc]▶⏸  [v]Toggle Style  [⇦⇨]Seek  [+/-]Vol  [n]Next  [q]Quit\033[0m\033[K\r\n")
            sys.stdout.flush()

            key = get_key_non_blocking()
            if key:
                if key == ' ' or key == '\r':
                    trigger_robust_toggle(active_player)
                elif key.lower() == 'v':
                    visualizer_mode = (visualizer_mode + 1) % 5
                elif key == '+' or key == '=':
                    adjust_system_volume("up")
                elif key == '-':
                    adjust_system_volume("down")
                elif active_player:
                    if key.lower() == 'n' or key == '\033[C':
                        subprocess.run(["playerctl", f"--player={active_player}", "next"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif key.lower() == 'p' or key == '\033[D':
                        subprocess.run(["playerctl", f"--player={active_player}", "previous"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif key.lower() == 'q':
                        break
                elif key.lower() == 'q':
                    break

            time.sleep(0.04)

    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[?25h\033[H\033[J")
        sys.stdout.flush()

if __name__ == "__main__":
    run_media_control()
