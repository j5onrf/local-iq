# AI-Suggestion Agent (v0.7.3-alpha)

<img alt="20260528_175036" src="https://github.com/user-attachments/assets/7f90513b-0b29-41e2-8471-055a00e8371c" />

`Qwen-3.5-2b/3.6-35B-A3B+` `Gemini-3.1-Flash-Lite` `Python 3.10+` `Bash 4.0+` `OpenAI-Compatible API`

> ⚠️ **Alpha Release Notice:** This project is currently in active **Alpha** development and is subject to rapid, drastic changes. Our core design goals are to maintain an extremely lightweight, minimal shell footprint while empowering your command line with high-performance local/cloud AI tool workflows.

---

## Introduction

The **AI-Suggestion Agent** is an on-demand, local shell companion designed to conform to your keyboard habits with zero system overhead. It runs entirely on-demand, consuming **0% idle memory and 0% idle CPU** when your terminal is sitting idle [1]. 

When you type a command typo or unrecognized phrase, a high-speed C-compiled local token matrix corrects your input in under 2ms [1]. When you run conversational questions (using the `ai` prefix), the agent securely invokes your designated system tools, reads their terminal outputs, and streams context-aware answers using a local or cloud-based LLM (like Google Gemini) in a single inference pass [1, 2].

---

## Core Features

* **Zero-Background Footprint:** No background processes, timers, or daemons. Sourced synchronously only for the millisecond you execute a typo or query.
* **Instant Typo Correction (Local):** Local set-matrix calculations match and correct command typos locally, completely bypassing the LLM.
* **Active System Tools (RAG):** Map standard CLI commands or custom scripts as `[TOOL]` configurations [3]. Your LLM dynamically executes them, reads their raw outputs, and answers conversational system questions in a single pass [2].
* **Hybrid Local/Cloud Brains:** Runs privately on your local `llama-server`, or routes instantly to **Google Gemini** for rapid cloud execution with **0% local RAM/CPU overhead** [1, 2].
* **On-Demand Toggles:** Sourced directly in your active shell. Toggle Google Search Grounding (`ai --grounding [on|off]`) or Python Code Execution (`ai --code-exec [on|off]`) in real-time [3].
* **CLI System Monitor Dashboard:** Run `ai --status` or `ai --usage` to view real-time API transactions, prompt token costs, and local index metrics in a compact terminal card.

---

## Packaged Tools & TUI Integrations (`[TOOL]`)

The project is designed to be an infinitely extensible ecosystem of custom tools and Terminal User Interface (TUI) integrations. Included out-of-the-box and as template examples are:

### A. System Diagnostics & Management
* **`ai-system-diagnosis` (Real-Time System Doctor):** Inspects live CPU load, active memory metrics, disk space, and failed systemd units as simple key-value outputs, completely preventing model math hallucinations [4].
* **`update-inspector` (Pending Upgrades Analyzer):** Safely parses pending repository and AUR updates in memory, allowing your LLM to warn you about critical library dependencies or package keyring overrides before running upgrades [1.1.3].
* **`kill-ai-servers` (Resource Release Utility):** Instantly terminates background local AI inference servers to release system RAM back to your operating system on demand [1.1.3].

### B. Workspace Layouts & Workflow Profiles
* **`hyprstate` (Desktop State & Profile Setter):** Instantly configures your Hyprland workspace layouts on demand (such as `work`, `media`, or `clean`), cleanly launching, assigning, and moving background applications (Brave, Nautilus, editors) to their designated monitors and workspaces [1.1.2, 1.2.9].

### C. TUI & Utility Integrations
* **`basepage-tui` (RSS & Article Reader Integration):** Launches customized terminal user interfaces, feeds, and articles directly inside your active terminal window.
* **`ai-summary` (Text & Pipeline Summarizer):** Integrates with custom text, log, and code summarization engines to digest complex documents, fully compatible with the **Koko automated text-to-speech (TTS) read-aloud** feature for hands-free listening.

> **Extensibility:** You can easily wrap any custom shell script, Python routine, terminal utility, or third-party CLI tool into your context database to build your own personalized system assistant [3].

---

## System Architecture Overview

### A. The Typo Correction Loop (0% Idle CPU / Offline-Safe)

```text
                         [ Direct Shell Typo ]
                                   │
                                   ▼
                        [ Token Matrix Search ]
                       Sørensen-Dice Coefficient
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
       ( Match Found )                           ( No Match Found )
              │                                         │
              ▼                                         ▼
      [ Match Carousel ]                       [ Manual Teach Prompt ]
    Up/Down Arrow Selector                    "Would you like to teach...?"
              │                                         │
    ┌─────────┼─────────┐                     ┌─────────┴─────────┐
    ▼         ▼         ▼                     ▼                   ▼
[Enter]     [ t ]    [Any Key]             [  y  ]             [  n  ]
    │         │         │                     │                   │
    ▼         ▼         ▼                     ▼                   ▼
 Execute   Override   Cancel               Override             Cancel
   Cmd    Auto-Compile                     Auto-Compile
```

### B. The Conversational Agent (On-Demand / Hybrid Local-Cloud)

```text
                         [ ai <conversational query> ]
                                      │
                                      ▼
                   [ Cloud Mode Active? (Env Key check) ]
                                 /      \
                        (No Key)/        \(API Key Sourced)
                               /          \
            [ 0ms TCP Handshake Check ]    [ Standard Cloud Routing ]
             Port 8080 offline -> Exit      Bypasses local port checks
                               \          /
                                ▼        ▼
                           [ Tool-Intent Match? ]
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
                  ( Yes )                           ( No )
                     │                                 │
                     ▼                                 ▼
            [ Execute local tool ]              [ Standard Chat ]
            Inject Context (RAG)                 Generic Response
                     │                                 │
                     └────────────────┬────────────────┘
                                      │
                                      ▼
                        [ Local/Cloud OpenAI-API ]
                        (Streams Response to Shell)
```

---

## Installation & Setup

### 1. Install the Project Files

Choose one of the following commands to install the core scripts directly into your configuration directory:

**Option A: Universal Setup (No dependencies required)**

```bash
mkdir -p ~/.config/local-ai/ai-suggestion && \
curl -sL https://github.com/j5onrf/local-ai/tarball/main | \
tar -xzf - --wildcards --strip-components=2 -C ~/.config/local-ai/ai-suggestion "*/ai-suggestion"
```

**Option B: Using Node.js/npx**

```bash
mkdir -p ~/.config/local-ai && npx degit j5onrf/local-ai/ai-suggestion ~/.config/local-ai/ai-suggestion
```

### 2. Append the Hook to Your Shell Config

#### For Bash (`~/.bashrc`):
```bash
cat << 'EOF' >> ~/.bashrc

# AI-Suggestion Hook (Bash)
[ -f "$HOME/.config/local-ai/ai-suggestion/ai-hook.sh" ] && source "$HOME/.config/local-ai/ai-suggestion/ai-hook.sh"
EOF
```

Reload your shell:
```bash
source ~/.bashrc
```

*(Optional Cloud setup)*: Export your Gemini API key in your `.bashrc` to activate cloud routing instantly [1, 2]:
```bash
export GEMINI_API_KEY="AIzaSyYourGeminiKey"
```

---

## Core Commands & Configuration

The system manages its binary token matrix index (`ai-context.idx`) using an automated synchronization engine.

* **Auto-Compile on Change:** Whenever you manually open and edit `ai-context.txt` in your favorite text editor, the script automatically detects the file changes and recompiles your speed index in under 2ms on your very next execution.

* **Interactive Teaching:** Register custom mappings directly from your terminal prompt:
  ```bash
  ai --teach
  ```

---

## Detailed Documentation
For deep dives into writing your own active system `[TOOL]` configurations, configuring dual-shell settings, or customizing prompt-engineering safety overrides, refer to the full **[documentation.md](documentation.md)**.

---
