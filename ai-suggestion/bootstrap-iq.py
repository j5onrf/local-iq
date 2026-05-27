#!/usr/bin/env python3
import sys
import re
import requests
import os

CONTEXT_FILE = os.path.expanduser("~/.config/hypr/scripts/ai/local-ai/ai-suggestion/ai-context.txt")

def main():
    if len(sys.argv) < 2:
        print("💡 Usage: python3 bootstrap-iq.py ~/.bashrc (or ~/.zshrc)")
        sys.exit(1)
        
    source_file = os.path.expanduser(sys.argv[1])
    if not os.path.exists(source_file):
        print(f"❌ Error: Configuration file not found at: {source_file}")
        sys.exit(1)
        
    try:
        with open(source_file, "r") as f:
            content = f.readlines()
            
        # Robust regex to capture standard aliases even with varying spaces or internal quotes
        alias_regex = re.compile(r"^alias\s+([a-zA-Z0-9_-]+)=['\"](.+?)['\"]")
        new_mappings = []
        
        print("\n⚡ Starting Local-IQ Bootstrap Engine...")
        print("Parsing shell config and generating semantic intents via local LLM...\n")
        
        for line in content:
            line = line.strip()
            # Skip comments, empty lines, or disabled settings
            if line.startswith("#") or not line:
                continue
                
            match = alias_regex.match(line)
            if match:
                alias_name = match.group(1)
                actual_cmd = match.group(2).strip()
                
                # Filter out system paths or structural logic lines that shouldn't be mapped
                if actual_cmd.startswith("[") or "source " in actual_cmd:
                    continue

                # Instruct the local server to extract 3 clean variations
                generation_prompt = (
                    f"<|im_start|>system\n"
                    f"You are a terminal analyzer. Given a Linux command, reply with exactly three brief, comma-separated natural phrases a human would say when they want to run it. "
                    f"Do not include the command name itself, explanations, or quotes. Example input: pacman -Syu | Example output: update system, upgrade packages, update everything\n<|im_end|>\n"
                    f"<|im_start|>user\n{actual_cmd}\n<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                
                try:
                    # Timeout protects against freezing if llama-server isn't running yet
                    res = requests.post("http://localhost:8080/completion", json={"prompt": generation_prompt, "stream": False}, timeout=6)
                    ai_phrases = res.json()["content"].strip()
                    
                    # Sanitation filters
                    ai_phrases = re.sub(r"<think>.*?</think>", "", ai_phrases, flags=re.DOTALL).strip()
                    ai_phrases = re.sub(r"['\"]", "", ai_phrases) # strip stray quotes
                    
                    intents = f"{alias_name}, {ai_phrases}"
                except Exception:
                    # Fail-safe gracefully defaults to just using the short alias name
                    intents = alias_name
                
                print(f"  → Processed: {actual_cmd} ---> {intents}")
                new_mappings.append(f"{actual_cmd} ---> {intents}\n")
                
        if not new_mappings:
            print("ℹ No valid shell aliases were found to convert.")
            sys.exit(0)
            
        # Append the processed block securely to the context structure
        with open(CONTEXT_FILE, "a") as f:
            f.write("\n# --- AUTO-BOOTSTRAP IMPORTED ALIASES ---\n")
            f.writelines(new_mappings)
            
        print(f"\n🎉 SUCCESS: Successfully created and appended {len(new_mappings)} robust structures to your context file!")
        
    except Exception as e:
        print(f"❌ Error during configuration conversion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[1;33m⚠️ Bootstrapping interrupted. Exiting safely.\033[0m")
        sys.exit(0)
