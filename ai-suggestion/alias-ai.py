#!/usr/bin/env python3
# AI Suggestion v0.7.1 [j5onrf] [05-28-26]

import sys
import re
import os
import json

CONTEXT_FILE = os.path.expanduser("~/.config/local-ai/ai-suggestion/ai-context.txt")
INDEX_FILE = os.path.expanduser("~/.config/local-ai/ai-suggestion/ai-context.idx")
DESTRUCTIVE_KEYWORDS = ["rm ", "dd ", "mkfs", "shred", "chmod -R 777", "> /dev/sda"]

# Pre-compile regex patterns to save execution time
TOKEN_RE = re.compile(r"[^\w\s]")

# Standard English stop-words to prevent grammatical collisions (0ms memory overhead)
STOP_WORDS = {
    "is", "what", "it", "do", "any", "i", "have", "the", "a", "an", "on", "to", 
    "for", "me", "you", "my", "your", "we", "us", "show", "get", "run", "check",
    "please", "can", "could", "would", "tell", "find", "list", "are", "about", 
    "in", "next", "few", "days", "going", "soon", "anytime", "day", "week"
}

def sanitize_input(text):
    if not text:
        return ""
    return re.sub(r"[`$]", "", text).strip()

def tokenize(text):
    # Lowercase and replace non-alphanumeric with spaces using pre-compiled regex
    raw_tokens = [w for w in TOKEN_RE.sub(" ", text.lower()).split() if len(w) > 1]
    # Filter out common stop-words to keep the matching strictly keyword-focused
    return [t for w in raw_tokens if (t := w) not in STOP_WORDS]

def compile_vector_index():
    if not os.path.exists(CONTEXT_FILE):
        return False
    with open(CONTEXT_FILE, "r") as f:
        lines = f.read().splitlines()
    index_data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "----->" in line or "--->" not in line:
            continue
        cmd_side, intents_side = line.split("--->", 1)
        intents = [i.strip() for i in intents_side.split(",")]
        for intent in intents:
            tokens = tokenize(intent)
            if tokens:
                index_data.append({"cmd": cmd_side.strip(), "intent": intent, "tokens": tokens})
    # Write as a minified, single-line JSON to optimize read operations
    with open(INDEX_FILE, "w") as f:
        json.dump(index_data, f)
    return True

# Highly efficient EAFP file timestamp check (minimizes syscall overhead)
try:
    mtime_ctx = os.path.getmtime(CONTEXT_FILE)
    try:
        mtime_idx = os.path.getmtime(INDEX_FILE)
        if mtime_ctx > mtime_idx:
            compile_vector_index()
    except OSError:
        compile_vector_index()
except OSError:
    pass

def check_danger(cmd):
    if not cmd:
        return cmd
    cmd_lower = cmd.lower()
    if any(kw in cmd_lower for kw in DESTRUCTIVE_KEYWORDS):
        return f"DANGER_FLAGGED:{cmd}"
    return cmd

def matrix_search(query, threshold=0.50): # Lowered slightly to capture close alternative candidates
    try:
        query_tokens = tokenize(query)
        if not query_tokens:
            return None
        with open(INDEX_FILE, "r") as f:
            index_data = json.load(f)
    except OSError:
        return None

    query_set = set(query_tokens)
    len_query = len(query_tokens)
    
    # Correctly initialize the candidates list
    candidates = []
    
    for entry in index_data:
        match_count = len(query_set.intersection(entry["tokens"]))
        if match_count == 0:
            continue
        score = (2.0 * match_count) / (len_query + len(entry["tokens"]))
        if score >= threshold:
            candidates.append((score, entry["cmd"], entry["intent"]))
            
    # Sort candidates by score descending
    candidates.sort(reverse=True, key=lambda x: x[0])
    
    # Extract up to 3 unique command contenders with their matching intents
    seen = set()
    top_entries = []
    for score, cmd, intent in candidates:
        if cmd not in seen:
            seen.add(cmd)
            # Evaluate danger flag on the command
            danger_cmd = check_danger(cmd)
            top_entries.append(f"{intent}|||{danger_cmd}")
            if len(top_entries) == 3:
                break
                
    return "\n".join(top_entries) if top_entries else None

def parse_universal_file(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return []

    new_mappings = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("--"):
            continue
        
        # 1. Parse direct ---> context format (for merging external context files)
        if "--->" in line and not line.startswith("----->"):
            cmd_side, intents_side = line.split("--->", 1)
            new_mappings.append((cmd_side.strip(), intents_side.strip(), True))
            continue

        # 2. Parse Bash/Zsh Aliases
        alias_match = re.match(r"^alias\s+(\w+)\s*=\s*(.*)", line)
        if alias_match:
            trigger = alias_match.group(1).strip()
            cmd_part = alias_match.group(2).strip().strip("'\"")
            new_mappings.append((cmd_part, trigger, False))
            continue

        # 3. Parse Hyprland Legacy Binds (.conf)
        if line.startswith("bind") and "exec," in line:
            try:
                left_side, cmd_part = line.split("exec,", 1)
                cmd_part = cmd_part.strip().strip("'\"")
                parts = [p.strip() for p in left_side.split(",")]
                trigger_key = ""
                for p in reversed(parts):
                    clean_p = p.replace("bind", "").replace("=", "").strip()
                    if clean_p:
                        trigger_key = clean_p
                        break
                if cmd_part:
                    new_mappings.append((cmd_part, trigger_key, False))
            except Exception:
                pass
            continue

        # 4. Parse Hyprland 0.55+ Modern Lua Binds (.lua)
        # e.g., hl.bind("SUPER + SHIFT + Q", hl.dsp.exec_cmd("firefox"))
        if "hl.bind" in line and "hl.dsp.exec_cmd" in line:
            try:
                cmd_match = re.search(r"hl\.dsp\.exec_cmd\(\s*\[*['\"]*(.*?)['\"]*\]*\s*\)", line)
                key_match = re.search(r"hl\.bind\(\s*\[*['\"]*(.*?)['\"]*\]*\s*,", line)
                if cmd_match and key_match:
                    cmd_part = cmd_match.group(1).strip().strip("'\"")
                    trigger_key = key_match.group(1).strip().strip("'\"")
                    # Clean up Lua variable concatenations (e.g., mainMod .. " + F" -> SUPER + F)
                    trigger_key = trigger_key.replace("mainMod ..", "SUPER").replace("mainMod", "SUPER")
                    trigger_key = trigger_key.replace("..", "+").replace("\"", "").replace("'", "").strip()
                    trigger_key = re.sub(r"\s+", " ", trigger_key)
                    if cmd_part:
                        new_mappings.append((cmd_part, trigger_key, False))
            except Exception:
                pass
            continue

        # 5. Parse Neovim Lua Keymaps
        if "keymap.set" in line or "api.nvim_set_keymap" in line:
            try:
                quoted_strings = re.findall(r"['\"](.*?)['\"]", line)
                if len(quoted_strings) >= 3:
                    trigger = quoted_strings[1]
                    cmd_part = quoted_strings[2]
                    if trigger and cmd_part and not cmd_part.startswith(":") and not cmd_part.startswith("<"):
                        new_mappings.append((cmd_part, trigger, False))
                    elif cmd_part.startswith(":"):
                        new_mappings.append((f"nvim {cmd_part}", trigger, False))
            except Exception:
                pass
            continue

        # 6. Parse WezTerm / Lua config binds
        if "SpawnCommand" in line and "args" in line:
            try:
                key_match = re.search(r"key\s*=\s*['\"](.*?)['\"]", line)
                args_match = re.search(r"args\s*=\s*\{\s*['\"](.*?)['\"]", line)
                if key_match and args_match:
                    trigger = key_match.group(1).strip()
                    cmd_part = args_match.group(1).strip()
                    new_mappings.append((cmd_part, trigger, False))
            except Exception:
                pass
            continue
            
    return new_mappings

def generate_intents_for_cmd(cmd, trigger):
    # Safe fallback if LLM is offline
    default_intents = f"launch {trigger}, run {cmd.split()[0]} via {trigger}" if trigger else f"run {cmd.split()[0]}"
    import requests
    try:
        prompt = f"Generate 3 natural language intents (phrases) a user would type into a terminal to trigger this command: '{cmd}'. Output ONLY the phrases separated by commas. No explanations, no numbering, no formatting."
        payload = {
            "messages": [
                {"role": "system", "content": "You are a strict terminal command to intent translator. Output only comma-separated phrases."},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        response = requests.post("http://localhost:8080/v1/chat/completions", json=payload, timeout=4)
        if response.status_code == 200:
            ans = response.json()["choices"][0]["message"]["content"].strip()
            ans = re.sub(r"^\d+\.\s*", "", ans)
            if ans and len(ans) < 150:
                return f"{ans}, {default_intents}"
    except Exception:
        pass
    return default_intents

# ==============================================================================
# ROUTING & EXECUTION
# ==============================================================================

# Manual Compile mode
if len(sys.argv) > 1 and sys.argv[1] == "--compile":
    if compile_vector_index():
        print("✓ Speed matrix index compiled successfully.")
        sys.exit(0)
    sys.exit(1)

# Map bindings and aliases configuration mode (Universal Parser)
if len(sys.argv) > 1 and sys.argv[1] == "--map":
    if len(sys.argv) < 3:
        print("Error: Please specify the path to your config file.")
        print("Usage: ai --map /path/to/file")
        sys.exit(1)
    file_path = sys.argv[2]
    mappings = parse_universal_file(file_path)
    if not mappings:
        print("No valid configurations (aliases, keybinds, or mappings) found or file could not be read.")
        sys.exit(1)
        
    print(f"⚡ Starting Universal Configuration Mapper... Found {len(mappings)} entry candidates.")
    successful = 0
    try:
        os.makedirs(os.path.dirname(CONTEXT_FILE), exist_ok=True)
        with open(CONTEXT_FILE, "a") as f:
            for cmd, trigger, is_pre_mapped in mappings:
                if is_pre_mapped:
                    print(f"  → Merging mapping: {cmd} ---> {trigger}")
                    f.write(f"\n{cmd} ---> {trigger}")
                    successful += 1
                else:
                    # Clean trailing redirects if they already exist
                    cmd_write = cmd
                    # Detect if key trigger looks like a desktop/GUI binder
                    is_gui_bind = trigger and any(k in trigger.lower() for k in ["f", "print", "ctrl", "alt", "super", "shift", "mod"])
                    if is_gui_bind and not cmd_write.endswith(">/dev/null 2>&1") and not cmd_write.startswith("alias"):
                        cmd_write = f"{cmd_write} >/dev/null 2>&1"
                        
                    print(f"  → Mapping command: {cmd_write}")
                    intents = generate_intents_for_cmd(cmd_write, trigger)
                    f.write(f"\n{cmd_write} ---> {intents}")
                    successful += 1
        compile_vector_index()
        print(f"✓ Successfully mapped {successful} items to ai-context.txt and recompiled index!")
        sys.exit(0)
    except Exception as e:
        print(f"Error writing to context: {str(e)}")
        sys.exit(1)

# Teach Mode (Supports both CLI Quick-add and Editor mode)
if len(sys.argv) > 1 and (sys.argv[1] == "--teach" or sys.argv[1] == "--learn"):
    if len(sys.argv) >= 4:
        # Quick-add mode (ai --teach "command" "intent")
        cmd_to_learn = sys.argv[2]
        intent_to_learn = sys.argv[3]
        try:
            os.makedirs(os.path.dirname(CONTEXT_FILE), exist_ok=True)
            with open(CONTEXT_FILE, "a") as f:
                f.write(f"\n{cmd_to_learn} ---> {intent_to_learn}")
            compile_vector_index()
            print("SUCCESS")
            sys.exit(0)
        except Exception:
            pass
    sys.exit(1)

# Handle interactive chat mode flag or direct conversational queries
if len(sys.argv) > 1 and sys.argv[1] == "--talk":
    # Lazy-load requests library only when active network chat is needed
    import requests
    if len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        
        # 1. Run a local matrix check to see if query maps to a [TOOL]
        system_context = ""
        tool_match = matrix_search(query)
        if tool_match:
            first_match = tool_match.split("\n")[0]
            if "|||" in first_match:
                intent, cmd = first_match.split("|||", 1)
                if cmd.startswith("[TOOL]"):
                    tool_cmd = cmd.replace("[TOOL]", "").strip()
                    # Lazy-load subprocess only when executing a local tool
                    import subprocess
                    try:
                        output = subprocess.check_output(tool_cmd, shell=True, text=True, timeout=2).strip()
                        # Clean confirmation for silent GUI tools
                        if not output:
                            output = "Action executed successfully."
                        system_context = f"The output of the local system tool '{tool_cmd}' is:\n{output}\n"
                    except Exception as e:
                        system_context = f"Failed to run local tool '{tool_cmd}': {str(e)}\n"

        # 2. Compile conversational assistant system prompt
        system_prompt = "You are a helpful, conversational local AI shell assistant. Answer the user's questions clearly, concisely, and directly."
        if system_context:
            system_prompt += f"\n\n# Real-time System Context\nUse the following real-time data to answer the user's request:\n{system_context}"

        try:
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                "stream": True
            }
            response = requests.post("http://localhost:8080/v1/chat/completions", json=payload, stream=True)
            first_chunk = True
            for chunk in response.iter_lines():
                if not chunk:
                    continue
                decoded = chunk.decode("utf-8").replace("data: ", "").strip()
                if decoded == "[DONE]":
                    break
                try:
                    data = json.loads(decoded)
                    content = data["choices"][0]["delta"].get("content", "")
                    if content:
                        if first_chunk:
                            print("\033[1;32mAI: \033[0m", end="", flush=True)
                            first_chunk = False
                        print(content, end="", flush=True)
                except Exception:
                    pass
            print()
        except requests.exceptions.RequestException:
            print("\033[1;31mError: Local AI server is offline. Please start your server.\033[0m")
        except KeyboardInterrupt:
            print("\n\033[1;33mInterrupted.\033[0m")
        sys.exit(0)
    else:
        print("\033[1;34m💬 Local AI Conversation Mode. Ctrl+C to quit.\033[0m\n")
        try:
            while True:
                query = input("❯ ")
                if not query.strip():
                    continue

                # 1. Run a local matrix check inside the interactive chat loop
                system_context = ""
                tool_match = matrix_search(query)
                if tool_match:
                    first_match = tool_match.split("\n")[0]
                    if "|||" in first_match:
                        intent, cmd = first_match.split("|||", 1)
                        if cmd.startswith("[TOOL]"):
                            tool_cmd = cmd.replace("[TOOL]", "").strip()
                            # Lazy-load subprocess only when executing a local tool
                            import subprocess
                            try:
                                output = subprocess.check_output(tool_cmd, shell=True, text=True, timeout=2).strip()
                                # Clean confirmation for silent GUI tools
                                if not output:
                                    output = "Action executed successfully."
                                system_context = f"The output of the local system tool '{tool_cmd}' is:\n{output}\n"
                            except Exception as e:
                                system_context = f"Failed to run local tool '{tool_cmd}': {str(e)}\n"

                # 2. Compile conversational assistant system prompt
                system_prompt = "You are a helpful, conversational local AI shell assistant. Answer the user's questions clearly, concisely, and directly."
                if system_context:
                    system_prompt += f"\n\n# Real-time System Context\nUse the following real-time data to answer the user's request:\n{system_context}"

                payload = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "stream": True
                }
                try:
                    response = requests.post("http://localhost:8080/v1/chat/completions", json=payload, stream=True)
                    first_chunk = True
                    for chunk in response.iter_lines():
                        if not chunk:
                            continue
                        decoded = chunk.decode("utf-8").replace("data: ", "").strip()
                        if decoded == "[DONE]":
                            break
                        try:
                            data = json.loads(decoded)
                            content = data["choices"][0]["delta"].get("content", "")
                            if content:
                                if first_chunk:
                                    print("\033[1;32mAI: \033[0m", end="", flush=True)
                                    first_chunk = False
                                print(content, end="", flush=True)
                        except Exception:
                            pass
                    print("\n")
                except requests.exceptions.RequestException:
                    print("\033[1;31mError: Local AI server is offline. Please start your server.\033[0m\n")
        except KeyboardInterrupt:
            print("\n\033[1;33mExiting conversation.\033[0m")
            sys.exit(0)

# ==============================================================================
# INPUT PROCESSING (Direct shell typo lookup only)
# ==============================================================================
user_input = sanitize_input(" ".join(sys.argv[1:])) if len(sys.argv) > 1 else ""
if not user_input or sys.argv[1].startswith("--"):
    sys.exit(0)

# Matrix Search (Automation/Commands)
matched_base = matrix_search(user_input)
if matched_base:
    # Clean any [TOOL] prefixes out before sending the suggestions to the shell hook
    lines = matched_base.split("\n")
    out_lines = []
    for line in lines:
        intent, cmd = line.split("|||", 1)
        if cmd.startswith("[TOOL]"):
            cmd = cmd.replace("[TOOL]", "").strip()
        out_lines.append(f"{intent}|||{cmd}")
    print("\n".join(out_lines))
    sys.exit(0)
else:
    print("Command Not Found") # <--- FIXED THIS TYPO HERE!
    sys.exit(1)
