# VBFD Quiz App - Claude Instructions

## What This Project Is
A promotional exam prep quiz app for Virginia Beach Fire Department (VBFD) Captain candidates.
Live at: https://dan1mal6.github.io/VBFD-Quiz
GitHub: https://github.com/dan1mal6/VBFD-Quiz

## Project Location
/Users/danfernandez/Library/CloudStorage/GoogleDrive-hello@asklucy.us/My Drive/Promotional Exam Prep Center/quiz-app

## Key Files
- index.html — the quiz web app
- questions.js — original question bank (115 questions)
- questions_part1_hr.js — HR questions (100 questions)
- src/data/hr_policies_questions.js — HR policy questions (165 questions)
- questions_generated.js — AI-generated questions (3700+ questions, DO NOT manually edit)
- generate_questions.py — generates questions using Gemini API
- extract_drive.py — extracts text from Google Drive documents
- update_quiz.sh — runs full update pipeline
- extracted_content/ — 500+ extracted text files from Google Drive

## Quiz Categories
- HR Policies
- FD SOPs
- TEMS Protocols
- EMS SOPs
- VBFD Overview
- Current Events

## Question Types Supported
- multiple_choice (choices[], answer index, explanation)
- matching (pairs[] with term/definition)
- short_answer (correctAnswer, keywords[], explanation)

## API Keys Needed
- GEMINI_API_KEY — from aistudio.google.com (used by generate_questions.py)
- GitHub token — stored in git remote URL (dan1mal6)

## How to Update the Quiz (Monthly)
When the user says "update the quiz" or "add new documents", do this:

1. Ask the user if they have added new files to Google Drive already
2. Run extraction to pull new docs:
   cd to quiz-app folder, run: python3 extract_drive.py
3. Run question generator (only processes NEW files, skips already done):
   run: ./run_generator.sh (will ask for GEMINI_API_KEY if not set)
4. Push to GitHub:
   git add questions_generated.js
   git commit -m "Updated question bank - [current month/year]"
   git push
5. Confirm live site updated at https://dan1mal6.github.io/VBFD-Quiz

## Important Notes
- generate_progress.json tracks which files have been processed — DO NOT delete unless doing a full regeneration
- The quiz runs 100% client-side — no server needed
- GitHub Pages auto-deploys when main branch is pushed (takes 2-3 min)
- WordPress embed uses an iframe pointing to the GitHub Pages URL
- questions_generated.js auto-merges into QUESTION_BANK via JS at bottom of file
- Generator uses Gemini 2.5 Flash model
- To do a FULL regeneration from scratch: delete generate_progress.json first
