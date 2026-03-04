#!/bin/bash
# ─────────────────────────────────────────────────────────────
# VBFD Quiz Updater
# Run this whenever you add new documents to Google Drive
# Usage: ./update_quiz.sh
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════╗"
echo "║           VBFD Quiz Updater                          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── STEP 1: Check for API key ────────────────────────────────
if [ -z "$GEMINI_API_KEY" ]; then
  echo "Enter your Gemini API key (from aistudio.google.com):"
  read -rs GEMINI_API_KEY
  export GEMINI_API_KEY
  echo "✓ API key set"
  echo ""
fi

# ── STEP 2: Extract new documents from Google Drive ──────────
echo "📂 Step 1/3: Extracting documents from Google Drive..."
python3 extract_drive.py
if [ $? -ne 0 ]; then
  echo "❌ Extraction failed. Check that extract_drive.py is working."
  exit 1
fi
echo "✓ Extraction complete"
echo ""

# ── STEP 3: Generate questions from new documents ────────────
echo "🤖 Step 2/3: Generating questions from new documents..."
echo "   (Only NEW documents will be processed — existing ones are skipped)"
python3 generate_questions.py
if [ $? -ne 0 ]; then
  echo "❌ Question generation failed."
  exit 1
fi
echo ""

# ── STEP 4: Push to GitHub ───────────────────────────────────
echo "🚀 Step 3/3: Pushing updates to GitHub..."
git add questions_generated.js
git commit -m "Updated question bank - $(date '+%B %d, %Y')"
git push
if [ $? -ne 0 ]; then
  echo "❌ Push to GitHub failed. Check your internet connection or token."
  exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✅ Done! Your quiz is updated and live.             ║"
echo "║  🌐 https://dan1mal6.github.io/VBFD-Quiz             ║"
echo "╚══════════════════════════════════════════════════════╝"
