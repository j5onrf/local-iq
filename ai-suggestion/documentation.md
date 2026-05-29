# AI-Suggestion Agent (v0.7.1-alpha) — Developer Documentation

An adaptive, local AI shell assistant designed to conform to your terminal environment. By leveraging a high-speed, local token-matrix cache alongside your local LLM, it corrects command typos, manages aliases, executes system tools, and answers conversational queries with zero background CPU overhead.

---

## 1. Architecture & Design Principles

The project operates under an on-demand execution model designed to protect terminal responsiveness:

* **Zero-Background Footprint:** No background daemons, cron-jobs, or continuous CPU-polling threads are used. Your shell experiences 0% idle RAM and 0% idle CPU overhead.
* **Dual-Layer Execution:** 
  * **Standard typos (direct shell inputs):** Bypasses the LLM completely. Typo errors are evaluated locally via a C-compiled set-intersection matrix in under 2ms.
  * **Conversational queries (using the `ai` prefix):** Run synchronously on-demand, connecting to your local LLM server and streaming responses directly to the terminal.
* **Offline Resilience:** If your local AI server is offline, your typo corrections, custom aliases, and interactive teaching loops continue to work locally and instantly. Only direct conversational LLM chat requests are safely blocked at the shell level.

---

## 2. Configuration & The Semantic Index

Your agent's brain is managed by a plain-text configuration master file.

* **Path:** `~/.config/local-ai/ai-suggestion/ai-context.txt`
* **Syntax:** `[command] ---> [intent1], [intent2], [intent3]`

*Example:*
```text
clear ---> cc, clear terminal, reset screen, wipe display
```

### Automatic Compilation on the Fly
You do not need to run manual compilation commands. Every time you interact with the agent, the Python script compares modification timestamps (`getmtime`) of your files. If the plain-text configuration has been modified, it silently rebuilds your minified, high-speed binary lookup index (`ai-context.idx`) in under 2ms before executing.

### Optional Manual Compilation
If you want to explicitly force a rebuild of the speed index for diagnostic or sanity checks, run:
```bash
ai --compile
```

---

## 3. Interactive CLI Training Loops

You can train your agent's memory directly from your terminal session in three ways:

### A. The Direct Correction Loop
If you type an unmapped command or typo (such as `sb`), the shell hook intercepts it and prompts:
```text
ℹ "sb" is not mapping to a known automation.
Would you like to teach the agent this custom phrase? (y/N)
```
Pressing `y` prompts you for the exact executable command this should map to, automatically building, appending, and compiling the new association.

### B. Manual Training Command
To manually register a custom alias or shortcut at any time without triggering a typo, run:
```bash
ai --teach
```
This launches a CLI prompt asking you for your custom natural phrase and the exact terminal command it should map to, writing it cleanly to your database.

### C. Suggestion Overriding
If the agent suggests an existing command but you want to edit or override it on the fly, press **`t`** during the selection prompt:
* This launches an interactive line editor (such as `read -e` in Bash or `vared` in Zsh) allowing you to override the command string, saving the new preference permanently to memory [2].

---

## 4. Active System Tools (`[TOOL]` Prefixing)

You can turn any standard Linux command, package, binary, or custom script into an AI tool by prefixing the command with `[TOOL]` in your `ai-context.txt` [3]:

*Example:*
```text
[TOOL] df -h / ---> check my nvme drive, is my hard drive full, show disk space
```

### Local Context-Injected RAG (Retrieval-Augmented Generation)
1. You ask: `ai "how much space is on my nvme drive?"`
2. The local matrix search instantly matches the intent to `[TOOL] df -h /` (0ms delay).
3. Python executes `df -h /` behind the scenes, capturing your physical hard drive table in under 2ms [2].
4. Python injects that raw text output directly into your LLM's system prompt [2].
5. The local LLM reads the raw data and formulates a real-time response: *"Your drive is currently using 49% of its space, leaving 237GB free."* [2]

> **Security Note:** This is highly secure because you define exactly what commands are safe to run, completely removing any risk of the AI hallucinating or executing destructive commands on your system.

---

## 5. Universal Configuration Mapper (`--map`)

To easily populate your configuration master database, you can automatically ingest and map your existing system shortcuts, terminal aliases, and desktop keybindings:

```bash
ai --map /path/to/config_file
```

### Supported Formats & Parsing Engine:
* **Shell Aliases (`.bashrc` / `.zshrc`):** Parses `alias name='command'` and maps `command ---> name, run command via name`.
* **Legacy Hyprland Keybinds (`.conf`):** Parses `bind = ..., exec, command` and maps `command ---> trigger_key, run command` [1.1.2, 1.2.9].
* **Modern Hyprland 0.55+ Keybinds (`.lua`):** Parses native Lua `hl.bind("keys", hl.dsp.exec_cmd("command"))` structures, automatically resolving variable concatenations (like converting `mainMod .. " + Q"` into a clean `"SUPER + Q"` intent) [1.1.4, 1.1.5, 1.4.3].
* **Neovim Lua Keymaps (`*.lua`):** Parses Neovim `keymap.set` and `api.nvim_set_keymap` structures [2].
* **WezTerm Lua Keymaps (`*.lua`):** Parses WezTerm key/mods action launch configurations [2].
* **Direct Context Merges (`.txt`):** Parses direct `--->` configurations, allowing you to instantly merge or combine other context files into your master database.

### Smart GUI/Redirection Detection
During the mapping import phase, the engine automatically checks if the key trigger looks like a graphical/desktop binder (e.g., contains triggers like `F2`, `Print`, `Super`, `Ctrl`, or `Alt`) [1.1.2]. 
* If it is a GUI binder, it automatically appends **` >/dev/null 2>&1`** to the mapped command [3]. This prevents verbose graphical debug logs from polluting your terminal when executing.
* If it is a standard shell alias (like `alias x='yay -Syu'`), it leaves it raw so you can see the terminal output.

---

## 6. Mathematical Optimizations

The system is designed to scale to thousands of custom mappings while maintaining a minimal shell footprint:

### A. Conversational-Resilient Stop Words
In search index engines, common grammatical connector words (like `what`, `is`, `it`, `do`, `any`, `I`, `have`, `the`, `a`) are called **"Stop Words"** [2]. Because these words carry no actual action, including them in your intent database causes completely unrelated commands (like `date` and `hyprctl clients`) to collide on generic English sentence structures [2].

To solve this, the Python script's `tokenize()` function automatically filters out a pre-compiled set of common English stop words [2]. For example:
* `"what about rain in the next few days?"` and `"is it going to rain?"` both compress down to exactly: **`["rain"]`** under the hood. 

This completely immunizes your database against structural grammar collisions, allowing you to write natural, conversational sentences while ensuring your matrix search targets only the specific, relevant keywords [2].

### B. High-Contrast Category Tags (Resource Isolation)
Small, local models can occasionally experience "cross-talk" hallucinations when parsing space-separated, adjacent numerical lines (for example, misinterpreting a `49%` disk space metric as your active RAM usage).

To prevent this, the active diagnostics tool `ai-system-diagnosis` prefixes each performance category with high-contrast, brackets tags (such as `[SYSTEM]`, `[CPU_HOGS]`, `[MEMORY]`, and `[STORAGE]`) [4]. This keeps your metrics isolated, allowing lightweight models to analyze your CPU, RAM, and disk specs with absolute precision [4].

---

## 7. Suggestion Carousel & Visual Cues

* **Multi-Contender Carousel:** If your terminal query matches more than one local intent, the CLI suggestion prompt displays a cycle index:
  ```text
  AI Suggestion (1/2) [Up/Down]: ...
  ```
  Pressing the **Up** and **Down** arrow keys allows you to cycle through your top 3 highest-probability matches cleanly.
* **Visual Intent Headers:** To quickly identify long, complex command strings on your screen, the carousel displays your matched intent in bold-cyan brackets right before the executable command:
  ```text
  AI Suggestion (1/2) [Up/Down]: [spotify music] -> uwsm app -- brave-origin...
  ```


