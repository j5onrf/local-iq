# AI-Suggestion Agent (v0.6.6)


<img alt="20260526_173110" src="https://github.com/user-attachments/assets/e322df2e-5711-47d1-a2f0-e23de19755af" />


`Qwen3.5-2B-UD-Q4_K_XL.gguf+` `Python 3.10+` `Bash 4.0+`

An adaptive, local AI shell agent designed to conform completely to your workflow. By analyzing your terminal environment and learning your custom aliases, it intercepts command typos, syntax errors, or forgotten flags to seamlessly suggest the exact command you meant to run.

---
## System Architecture Overview

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
     [ Suggestion Menu ]                      [ Manual Teach Prompt ]
   [Enter] / [t] / [Cancel]                 "Would you like to teach...?"
             │                                         │
   ┌─────────┼─────────┐                     ┌─────────┴─────────┐
   ▼         ▼         ▼                     ▼                   ▼
[Enter]    [ t ]    [Any Key]             [  y  ]             [  n  ]
   │         │         │                     │                   │
   ▼         ▼         ▼                     ▼                   ▼
Execute   Override   Cancel               Override             Cancel
  Cmd   Auto-Compile                    Auto-Compile
```

```text
                     [ ai <conversational query> ]
                                  │
                                  ▼
                     [ Local Conversational LLM ]
                     (Streams Response to Shell)
```

1. **Layer 1 (Local Matrix Search):** Checks shell typos directly against your `ai-context.txt` baseline. It calculates mathematical overlap weights using the **Sørensen-Dice Coefficient** [1]. Rephrased or jumbled inputs match instantly (~3–5ms latency) while completely bypassing the LLM.
2. **Zero-LLM Fallback (Interactive Teach Loop):** If a typo has no local mapping, the shell hook bypasses the LLM to protect system performance and eliminate translation lag. It drops instantly to a manual teach prompt, allowing you to bind the custom phrase to its command and auto-compile it directly from your shell.
3. **Layer 2 (Conversational Local LLM):** Executed exclusively when invoking the `ai` command prefix (e.g., `ai --chat` or `ai "what is 2 + 45"`). It establishes a direct streaming session with your local `llama-server` to provide natural language answers.


## Installation & Setup

### 1. Install the Project Files

Choose one of the following commands to install the core scripts directly into your configuration directory:

**Option A: Universal Setup (No dependencies required)**

```bash
mkdir -p ~/.config/local-ai/ai-suggestion && curl -sL https://github.com/j5onrf/local-ai/tarball/main | tar -xzf - --strip-components=2 -C ~/.config/local-ai/ai-suggestion "*/ai-suggestion"
```

**Option B: Using Node.js/npx**

```bash
mkdir -p ~/.config/local-ai && npx degit j5onrf/local-ai/ai-suggestion ~/.config/local-ai/ai-suggestion
```

### 2. Append to `.bashrc`

Add the background hook process to your environment so the suggestion engine is always active when a new terminal initializes:

```bash
cat << 'EOF' >> ~/.bashrc

# AI-Suggestion Hook
if [ -f "$HOME/.config/local-ai/ai-suggestion/ai-hook.sh" ]; then
    source "$HOME/.config/local-ai/ai-suggestion/ai-hook.sh"
fi
EOF
```

### 3. Build the AI Context Cache (`--bootstrap`)

To seed the agent with your current environment profile and baseline system knowledge, initialize the engine via the CLI wrapper:

```bash
ai --bootstrap
```

This parses your active shell aliases and generates your central `ai-context.txt` configuration master.

> ⚠️ **Important Note for Smaller Models:** Smaller local models can occasionally struggle to structure the initial bootstrap execution perfectly. After running your bootstrap step, always open and inspect your `ai-context.txt` file to ensure it compiled cleanly and accurately.

---

## Core Commands & Compilation

The system manages its high-speed binary token matrix index (`ai-context.idx`) seamlessly using an automated synchronization engine, completely eliminating the need for manual upkeep.

### Automatic Compilation on the Fly
If you manually open, edit, clean, or strip lines from `ai-context.txt` using your preferred text editor (such as VS Code, Vim, or Nano), you do not need to run any manual commands afterward. 

The next time you type any command or interact with the agent, the system automatically detects that the configuration file was modified and rebuilds your high-speed binary lookup index (`ai-context.idx`) in under 2ms before executing.

### Optional Manual Compilation
If you want to explicitly force a rebuild of the speed index (for diagnostic verification or sanity checks), you can run:

```bash
ai --compile
```

This manually parses your configuration file, builds the optimized mathematical table, and prints a success confirmation to your terminal.

---

## Configuration (`ai-context.txt`)

The `ai-context.txt` file is the master command center for the agent's knowledge base.

* **Manual Control:** Because your context file belongs entirely to your system and your specific customizations, you can manually open and edit this file at any time to explicitly instruct the AI on workflows, scripts, or specific behaviors you want it to prioritize.
* **Automated Training:** Any correction rules or adjustments you input via the `[t] Edit` loop are safely written to this file with zero formatting gaps or artifacts, ensuring the terminal environment adapts to your operational habits permanently.

---

### References
[1] Sørensen, T. J. (1948). "A method of establishing groups of equal amplitude in plant sociology based on similarity of species content." *Kongelige Danske Videnskabernes Selskab*, 5(4), 1–34.
```
