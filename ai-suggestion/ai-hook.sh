#!/usr/bin/env bash

# AI Suggestion v0.7.1 [j5onrf] [05-28-26]

# 1. Early-exit if shell is not interactive
[[ $- != *i* ]] && return

# 2. Define static path to Python backend script
_AI_SCRIPT_PATH="$HOME/.config/local-ai/ai-suggestion/alias-ai.py"

# 3. Static Path Audit: Exit silently if file is missing
[[ ! -f "$_AI_SCRIPT_PATH" ]] && return

# 4. Pre-cache absolute Python binary path to bypass PATH traversing
_AI_PYTHON_BIN=$(command -v python3 2>/dev/null || type -p python3 2>/dev/null || echo "python3")

ai_handle_missing() {
    # Normalize Zsh array indexing to 0-start (matching Bash) inside this scope
    [[ -n "$ZSH_VERSION" ]] && setopt local_options ksh_arrays

    local intent="$*"
    local raw_output cmd learn_key target_command key next_keys
    local is_new=false

    # Exit instantly if intent string is empty
    if [[ -z "$intent" ]]; then
        return 127
    fi

    # Invoke python via pre-cached binary
    raw_output="$($_AI_PYTHON_BIN "$_AI_SCRIPT_PATH" "$intent")"

    if [[ -z "$raw_output" || "$raw_output" == *"Command Not Found"* ]]; then
        cmd=""
    elif [[ "$raw_output" == "NEW_SUGGESTION:"* ]]; then
        is_new=true
        local payload="${raw_output#NEW_SUGGESTION:}"
        cmd="${payload%%--->*}"
        local discover_intent="${payload#*--->}"
    else
        cmd="$raw_output"
        local discover_intent="$intent"
    fi

    # Read multiline output into an array using native, high-speed shell methods
    local cmd_opts=()
    if [[ -n "$ZSH_VERSION" ]]; then
        cmd_opts=(${(f)raw_output})
    else
        mapfile -t cmd_opts <<< "$raw_output"
    fi

    # Sanitize & Filter: Ensure only well-formed, non-empty "intent|||cmd" mappings exist
    local clean_opts=()
    for opt in "${cmd_opts[@]}"; do
        if [[ "$opt" == *"|||"* && "$opt" != "|||"* ]]; then
            local check_cmd="${opt#*|||}"
            if [[ -n "$check_cmd" ]]; then
                clean_opts+=("$opt")
            fi
        fi
    done

    local num_opts=${#clean_opts[@]}
    local current_idx=0

    # ==============================================================================
    # 1. CYCLE OR SELECTION LOOP
    # ==============================================================================
    if (( num_opts > 0 )); then
        # Hide terminal cursor during interactive cycling to prevent flickering
        tput civis 2>/dev/null

        while true; do
            local current_entry="${clean_opts[$current_idx]}"
            # Split the entry into intent and command parts
            local current_intent="${current_entry%%|||*}"
            local current_cmd="${current_entry#*|||}"
            local display_idx=$((current_idx + 1))

            if [[ "$current_cmd" == "DANGER_FLAGGED:"* ]]; then
                cmd="${current_cmd#DANGER_FLAGGED:}"
                # Redraw line and print danger suggestion
                printf "\r\e[K\e[1;31m⚠️ WARNING: Potentially destructive suggestion detected!\e[0m"
                printf "\n\e[1;33mAI Suggestion (%d/%d):\e[0m \e[1;36m[%s]\e[0m %s" "$display_idx" "$num_opts" "$current_intent" "$cmd"
                printf "\nAre you absolutely sure you want to run this? (y/N): "
                
                tput cnorm 2>/dev/null # Restore cursor for confirmation prompt
                read -s -r -n 1 key
                echo # Newline
                
                if [[ ! "$key" =~ ^[Yy]$ ]]; then
                    echo "Aborted safely."
                    return 0
                fi
                eval "$cmd"
                return 0
            else
                cmd="$current_cmd"
                # Redraw line and print standard suggestion with high-contrast intent cues
                if (( num_opts > 1 )); then
                    printf "\r\e[K\e[1;32mAI Suggestion (%d/%d) [Up/Down]:\e[0m \e[1;36m[%s]\e[0m %s" "$display_idx" "$num_opts" "$current_intent" "$cmd"
                else
                    printf "\r\e[K\e[1;32mAI Suggestion:\e[0m \e[1;36m[%s]\e[0m %s" "$current_intent" "$cmd"
                fi
                
                # Inline action menu
                printf "\n[Enter] Execute / [t] Edit / [Any Key] Cancel: "
                
                # Read single character
                read -s -r -n 1 key

                # Detect Arrow Keys (Escape sequence checks)
                if [[ "$key" == $'\e' ]]; then
                    read -s -r -n 2 -t 0.05 next_keys 2>/dev/null
                    
                    if [[ "$next_keys" == "[A" ]]; then
                        # Up Arrow: Cycle backwards
                        current_idx=$(( (current_idx - 1 + num_opts) % num_opts ))
                        printf "\e[1A" # Move cursor back up to redraw correctly
                        continue
                    elif [[ "$next_keys" == "[B" ]]; then
                        # Down Arrow: Cycle forwards
                        current_idx=$(( (current_idx + 1) % num_opts ))
                        printf "\e[1A" # Move cursor back up to redraw correctly
                        continue
                    fi
                fi

                # Handle Selection Actions
                # Enter selected: Execute
                if [[ -z "$key" ]]; then
                    tput cnorm 2>/dev/null
                    echo # Clear prompt line
                    eval "$cmd"
                    return 0
                # 't' selected: Edit/Override
                elif [[ "$key" == "t" || "$key" == "T" ]]; then
                    tput cnorm 2>/dev/null
                    echo -e "\n\e[1;34mOverride suggestion. Enter your preferred command:\e[0m"
                    read -e -p "❯ " -i "$cmd" target_command

                    if [[ -n "$target_command" ]]; then
                        "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" --learn "$target_command" "$intent" > /dev/null
                        echo -e "\e[1;32m✓ Preferred mapping saved to local memory.\e[0m"
                        eval "$target_command"
                    else
                        echo "Cancelled. Nothing added."
                    fi
                    return 0
                # Any other key: Cancel
                else
                    tput cnorm 2>/dev/null
                    echo -e "\nCancelled."
                    return 0
                fi
            fi
        done
        tput cnorm 2>/dev/null
    fi

    # ==============================================================================
    # 2. TOTAL FAILURE: Drop to Manual Teach Loop
    # ==============================================================================
    echo -e "\e[1;33mℹ \"$intent\" is not mapping to a known automation.\e[0m"
    read -p "Would you like to teach the agent this custom phrase? (y/N): " -n 1 learn_key
    echo

    if [[ "$learn_key" =~ ^[Yy]$ ]]; then
        echo -e "\e[1;34mEnter the exact executable command this should map to:\e[0m"
        read -e -p "❯ " target_command

        if [[ -n "$target_command" ]]; then
            local learn_output
            learn_output="$($_AI_PYTHON_BIN "$_AI_SCRIPT_PATH" --learn "$target_command" "$intent")"
            
            if [[ "$learn_output" == "SUCCESS" ]]; then
                echo -e "\e[1;32m✓ Memory updated! Running command now...\e[0m"
                eval "$target_command"
                return 0
            else
                echo -e "\e[1;31m$learn_output\e[0m"
                return 1
            fi
        else
            echo "Cancelled. Nothing added to agent memory."
            return 0
        fi
    fi
    return 127
}

command_not_found_handle() {
    if [[ "$1" == --* ]]; then
        return 127
    fi

    ai_handle_missing "$*"
    return 0
}

# ==============================================================================
# 3. DIRECT CLI WRAPPER
# ==============================================================================
ai() {
    # Check if local llama-server is online on port 8080 (fails instantly if offline)
    if ! (echo > /dev/tcp/localhost/8080) >/dev/null 2>&1; then
        echo "bash: command not found: ai (Local AI server is offline)"
        return 127
    fi

    # Intercept manual compile and map parameters
    if [[ "$1" == "--compile" || "$1" == "--map" ]]; then
        "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" "$@"
        return 0
    fi

    # Explicit conversational chat mode
    if [[ "$1" == "--chat" ]]; then
        shift
        if [[ -n "$*" ]]; then
            "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" --talk "$*"
        else
            "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" --talk
        fi
        return 0
    fi

    # Manual training mode
    if [[ "$1" == "--teach" ]]; then
        echo -e "\e[1;34mEnter the custom phrase or typo you want to map:\e[0m"
        read -e -p "❯ " intent_to_teach
        if [[ -z "$intent_to_teach" ]]; then
            echo "Cancelled."
            return 0
        fi
        echo -e "\e[1;34mEnter the exact executable command this should map to:\e[0m"
        read -e -p "❯ " target_command
        if [[ -n "$target_command" ]]; then
            local learn_output
            learn_output="$($_AI_PYTHON_BIN "$_AI_SCRIPT_PATH" --learn "$target_command" "$intent_to_teach")"
            if [[ "$learn_output" == "SUCCESS" ]]; then
                echo -e "\e[1;32m✓ Memory updated! You can now use '$intent_to_teach'.\e[0m"
                return 0
            else
                echo -e "\e[1;31m$learn_output\e[0m"
                return 1
            fi
        else
            echo "Cancelled. Nothing added to agent memory."
            return 0
        fi
    fi

    # General fallback for arbitrary queries passed directly, e.g. `ai "how do I list files"`
    if [[ -n "$*" ]]; then
        "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" --talk "$*"
        return 0
    fi

    # Fallback directly into conversation loop if no arguments exist
    "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" --talk
}
