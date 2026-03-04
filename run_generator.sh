#!/bin/bash
# ─────────────────────────────────────────────────────────────
# VBFD Question Generator - Run Script
# Usage: ./run_generator.sh
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════════════╗"
echo "║       VBFD Question Generator                        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "Enter your Anthropic API key (from console.anthropic.com):"
  read -rs ANTHROPIC_API_KEY
  export ANTHROPIC_API_KEY
  echo "✓ API key set"
  echo ""
fi

# Run the generator
cd "$SCRIPT_DIR"
python3 generate_questions.py
