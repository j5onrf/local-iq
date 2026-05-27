#!/usr/bin/env python3

# AI Suggestion v0.6.6 [j5onrf] [05-26-26]

import sys
import re
import os
import json

CONTEXT_FILE = os.path.expanduser("~/.config/local-ai/ai-suggestion/ai-context.txt")
INDEX_FILE = os.path.expanduser("~/.config/local-ai/ai-suggestion/ai-context.idx")
DESTRUCTIVE_KEYWORDS = ["rm ", "dd ", "mkfs", "shred", "chmod -R 777", "> /dev/sda"]

# Pre-compile regex patterns to save execution time
TOKEN_RE = re.compile(r"[^\w\s]")

def sanitize_input(text):
    if not text:
        return ""
    return re.sub(r"[`$]", "", text).strip()

def tokenize(text):
    # Lowercase and replace non-alphanumeric with spaces using pre-compiled regex
    return [w for w in TOKEN_RE.sub(" ", text.lower()).split() if len(w) > 1]

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

def matrix_search(query, threshold=0.65):
    try:
        query_tokens = tokenize(query)
        if not query_tokens:
            return None
        with open(INDEX_FILE, "r") as f:
            index_data = json.load(f)
    except OSError:
        return None

    best_match, highest_score = None, 0.0
    
    # Pre-calculate set and length representations to save math operations in loop
    query_set = set(query_tokens)
    len_query = len(query_tokens)
    
    for entry in index_data:
        # C-implemented set intersection (much faster than a manual loop in Python)
        match_count = len(query_set.intersection(entry["tokens"]))
        if match_count == 0:
            continue
        score = (2.0 * match_count) / (len_query + len(entry["tokens"]))
        if score > highest_score:
            highest_score, best_match = score, entry["cmd"]
            
    return best_match if highest_score >= threshold else None

def check_danger(cmd):
    if not cmd:
        return cmd
    cmd_lower = cmd.lower()
    if any(kw in cmd_lower for kw in DESTRUCTIVE_KEYWORDS):
        return f"DANGER_FLAGGED:{cmd}"
    return cmd

# ==============================================================================
# ROUTING & EXECUTION
# ==============================================================================

# Manual Compile mode
if len(sys.argv) > 1 and sys.argv[1] == "--compile":
    if compile_vector_index():
        print("✓ Speed matrix index compiled successfully.")
        sys.exit(0)
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
        try:
            payload = {"messages": [{"role": "user", "content": query}], "stream": True}
            response = requests.post("http://localhost:8080/v1/chat/completions", json=payload, stream=True)
            first_chunk = True
            for chunk in response.iter_lines():
                if chunk:
                    decoded = chunk.decode("utf-8").replace("data: ", "")
                    if decoded == "[DONE]":
                        break
                    try:
                        content = json.loads(decoded)["choices"][0]["delta"].get("content", "")
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
                payload = {"messages": [{"role": "user", "content": query}], "stream": True}
                try:
                    response = requests.post("http://localhost:8080/v1/chat/completions", json=payload, stream=True)
                    first_chunk = True
                    for chunk in response.iter_lines():
                        if chunk:
                            decoded = chunk.decode("utf-8").replace("data: ", "")
                            if decoded == "[DONE]":
                                break
                            try:
                                content = json.loads(decoded)["choices"][0]["delta"].get("content", "")
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
    print(check_danger(matched_base))
    sys.exit(0)
else:
    print("Command Not Found")
    sys.exit(1)
