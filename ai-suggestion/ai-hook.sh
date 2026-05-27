#!/usr/bin/env bash

# AI Suggestion v0.6.6 [j5onrf] [05-26-26]

# 1. Early-exit if shell is not interactive
[[ $- != *i* ]] && return

# 2. Define static path to Python backend script
_AI_SCRIPT_PATH="$HOME/.config/local-ai/ai-suggestion/alias-ai.py"

# 3. Static Path Audit: Exit silently if file is missing (removes disk seeks during typos)
[[ ! -f "$_AI_SCRIPT_PATH" ]] && return

# 4. Pre-cache absolute Python binary path to bypass PATH traversing during typos
_AI_PYTHON_BIN=$(command -v python3 2>/dev/null || type -p python3 2>/dev/null || echo "python3")

ai_handle_missing() {
    local intent="$*"
    local raw_output cmd learn_key target_command key
    local is_new=false

    # Exit instantly if intent string is empty
    if [[ -z "$intent" ]]; then
        return 127
    fi

    # Invoke python via pre-cached binary and script paths (Fast!)
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

    # ==============================================================================
    # 1. MATCH OR DISCOVERY FOUND
    # ==============================================================================
    if [[ -n "$cmd" ]]; then
        if [[ "$cmd" == "DANGER_FLAGGED:"* ]]; then
            cmd="${cmd#DANGER_FLAGGED:}"
            echo -e "\e[1;31m⚠️ WARNING: Potentially destructive command detected!\e[0m"
            echo -e "\e[1;33mAI Suggestion:\e[0m $cmd"
            read -p "Are you absolutely sure you want to run this? (y/N): " -n 1 key
            echo
            if [[ ! "$key" =~ ^[Yy]$ ]]; then
                echo "Aborted safely."
                return 0
            fi
        else
            echo -e "\e[1;32mAI Suggestion:\e[0m $cmd"
            
            IFS= read -p "[Enter] Execute / [t] Edit / [Any Key] Cancel: " -s -n 1 key
            echo
            
            # [t] Edit/Train Route Interception
            if [[ "$key" =~ ^[Tt]$ ]]; then
                echo -e "\e[1;34mOverride suggestion. Enter your preferred command:\e[0m"
                read -e -p "❯ " -i "$cmd" target_command
                
                if [[ -n "$target_command" ]]; then
                    "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" --learn "$target_command" "$discover_intent" > /dev/null
                    echo -e "\e[1;32m✓ Preferred mapping saved to local memory.\e[0m"
                    eval "$target_command"
                else
                    echo "Cancelled. Nothing added."
                fi
                return 0
            fi

            # Handle Execute [Enter] or standard Cancel
            if [[ -z "$key" ]]; then
                if [ "$is_new" = true ]; then
                    "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" --learn "$cmd" "$discover_intent" > /dev/null
                    echo -e "\e[1;34m🧠 Added new translation to local memory.\e[0m"
                fi
                eval "$cmd"
            else
                echo "Cancelled."
            fi
            return 0
        fi
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
    # 1. Check if local server is online (port 8080)
    # If offline, instantly bypass the hook and let Bash output standard error (No Python executed)
    if ! (echo > /dev/tcp/localhost/8080) >/dev/null 2>&1; then
        return 127
    fi

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

    # Intercept manual compile parameter
    if [[ "$1" == "--compile" ]]; then
        "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" "$1"
        return 0
    fi

    # Intercept bootstrap parameter and execute bootstrap-iq.py directly
    if [[ "$1" == "--bootstrap" ]]; then
        local bootstrap_script="$HOME/.config/local-ai/ai-suggestion/bootstrap-iq.py"
        if [[ -f "$bootstrap_script" ]]; then
            # Automatically pass ~/.bashrc to the bootstrap script
            "$_AI_PYTHON_BIN" "$bootstrap_script" "$HOME/.bashrc"
        else
            # Fallback if bootstrap-iq.py is missing
            "$_AI_PYTHON_BIN" "$_AI_SCRIPT_PATH" "$1"
        fi
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
