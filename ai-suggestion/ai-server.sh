#!/usr/bin/env bash

# Updated to use valid 2026 llama-server flags
llama-server \
  -m /home/j5/ollama_backup/Qwen3.5-2B-UD-Q4_K_XL.gguf \
  -c 8192 \
  -t 6 \
  -b 512 \
  --cache-type-k q4_0 \
  --cache-type-v q8_0 \
  --flash-attn on \
  --reasoning off \
  --reasoning-budget 0 \
  --context-shift \
  --jinja \
  --temp 1.0 \
  --top-p 1.0 \
  --top-k 20 \
  --min-p 0.0 \
  --presence-penalty 2.0 \
  --repeat-penalty 1.0 \
  --no-webui
