# AI-Suggestion Agent (v0.7.1-alpha)

<img alt="20260528_175036" src="https://github.com/user-attachments/assets/7f90513b-0b29-41e2-8471-055a00e8371c" />

`Qwen3.5-2B-UD-Q4_K_XL+` `Python 3.10+` `Bash 4.0+` `Zsh 5.0+` `OpenAI-compatible`

> ⚠️ **Alpha Release Notice:** This project is currently in active **Alpha** development and is subject to rapid, drastic architectural changes. Our core design goals are to maintain an extremely lightweight, minimal shell footprint while empowering your command line with high-performance local AI tool workflows.

An adaptive, local AI shell agent designed to conform completely to your workflow. By analyzing your terminal environment and learning your custom aliases, it intercepts command typos, syntax errors, or forgotten flags to seamlessly suggest the exact command you meant to run.

---

## Key Highlights & Features

* **Zero-Overhead, On-Demand Architecture:** Strictly **0% idle memory and CPU footprint**. The agent runs synchronously only for the millisecond you press `Enter` on a typo—no background pollers, timers, or daemons.
* **Sub-2ms Local Token Matching:** C-compiled Sørensen-Dice matrix set-intersections match jumbled or rephrased typos instantly, completely bypassing the local LLM.
* **Real-Time Context Injection (RAG):** Map standard terminal utilities or custom scripts as `[TOOL]` commands [3]. Your local LLM dynamically executes them, reads their raw outputs, and answers conversational system questions in **one single pass** [2].
* **Universal Configuration Mapper:** A single command (`ai --map`) to ingest `.bashrc`, `.zshrc`, `hyprland.conf`, `.lua` keybinds, or custom configurations, automatically generating semantic intents via your local LLM [3].
* **Interactive Suggestion Carousel:** If multiple local commands match a typo, cycle through your top 3 matches cleanly using your **Up** and **Down** arrow keys with high-contrast visual intent cues.
* **Bulletproof Offline Resilience:** If your local AI server is offline, your typo suggestions, custom aliases, and interactive teaching loops continue to work perfectly offline. Only conversational chat requests are blocked.

---

## Prerequisites & Requirements

* **Local LLM Server** providing an **OpenAI-compatible Chat Completions API** (e.g., `llama-server` [3], Ollama [2], LM Studio, or LocalAI [3]) running on `http://localhost:8080` (or your configured port [1]).
* **Python 3.10+**
* **Bash 4.0+** or **Zsh 5.0+**

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

### B. The Conversational Agent (On-Demand / Real-Time RAG)

```text
                         [ ai <conversational query> ]
                                      │
                                      ▼
                        [ 0ms TCP Handshake Check ] ──(Offline)──► [Exit 127]
                                      │ (Online)
                                      ▼
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
                         [ Local Conversational LLM ]
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

### 3. Ingest Your Configurations (`--map`)(Optional)

Use the high-speed Universal Configuration Mapper to automatically parse your system shortcuts and generate semantic intents via your local LLM [2, 3]:

**A. Map your terminal aliases:**
```bash
ai --map ~/.bashrc
```

**B. Map your desktop window manager keybinds:**
```bash
ai --map ~/.config/hypr/bindings.conf
```

---

## Core Commands & Configuration

The system manages its binary token matrix index (`ai-context.idx`) using an automated synchronization engine.

* **Auto-Compile on Change:** Whenever you manually open and edit `ai-context.txt` in your favorite text editor, the script automatically detects the file changes and recompiles your speed index in under 2ms on your very next execution.
* **Manual Compilation:** Force an index rebuild at any time:
  ```bash
  ai --compile
  ```
* **Interactive Teaching:** Register custom mappings directly from your terminal prompt:
  ```bash
  ai --teach
  ```

---

## Detailed Documentation
For deep dives into writing your own active system `[TOOL]` configurations, configuring dual-shell settings, or customizing prompt-engineering safety overrides, refer to the full **[documentation.md](documentation.md)**.


