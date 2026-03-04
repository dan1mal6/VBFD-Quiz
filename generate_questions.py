#!/usr/bin/env python3
"""
VBFD Exam Question Generator
Reads extracted documents and uses Claude API to generate quiz questions.
Output: questions_generated.js (same format as questions.js)
"""

import os
import json
import time
import re
from google import genai
from google.genai import types

# ── CONFIG ──────────────────────────────────────────────────────────────────
EXTRACTED_DIR = os.path.join(os.path.dirname(__file__), "extracted_content")
OUTPUT_FILE   = os.path.join(os.path.dirname(__file__), "questions_generated.js")
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "generate_progress.json")

# How many questions to request per document (Claude will generate up to this many)
QUESTIONS_PER_DOC = 8

# Max characters of document text to send to Claude (keep prompts manageable)
MAX_DOC_CHARS = 6000

# Delay between API calls (seconds) to avoid rate limits
API_DELAY = 1.5

# ── CATEGORY MAPPING ────────────────────────────────────────────────────────
# Maps filename keywords → quiz category
CATEGORY_MAP = [
    (["HR_Policies", "HR_Policy", "hr_policies", "3.01", "3.07", "3.09", "2.02",
      "Overtime", "Leave", "Injury_Leave", "Military_Leave", "Progressive_Discipline",
      "Standby", "Personnel"], "HR Policies"),

    (["FD_SOPs", "FD_SOP", "SOP", "sop", "New_SOPs", "5.", "6.", "7.", "8.", "9.",
      "Bomb_Threat", "Hose_Testing", "Vehicle_Maintenance", "Uniform", "Funeral",
      "Body_Armor", "Rotary_Wing", "Port_Authority", "News_Media", "Tuition",
      "Utility_Lift", "Operational_Bulletin"], "FD SOPs"),

    (["TEMS", "tems", "Triage", "Radio_Report", "Tactical", "EMS_SOP",
      "Clinical_Directive", "OMD", "pain_control", "Agitated"], "TEMS Protocols"),

    (["EMS_SOP", "EMS_SOPs", "EMS_Safe", "ems_sop"], "EMS SOPs"),

    (["Current_Events", "Announcement", "Operational_Bulletin", "Inclusion",
      "Diversity", "2026"], "Current Events"),

    (["Officer_1", "Chapter_", "chapter_", "Unit_", "unit_", "AFC_Officer",
      "Fire_Officer", "FIRE_OFFICER", "Practice_Exam", "Textbook"], "FD SOPs"),

    (["Captain", "captain", "Assessment_Center", "In_Basket", "Interview",
      "Promotional_Process", "Job_Description", "Bibliography"], "VBFD Overview"),

    (["VBFD", "vbfd", "Overview", "Study_Guide", "SOV", "COOP", "SBP"], "VBFD Overview"),
]

def classify_document(filename: str) -> str:
    """Assign a quiz category based on filename keywords."""
    for keywords, category in CATEGORY_MAP:
        for kw in keywords:
            if kw in filename:
                return category
    return "FD SOPs"  # default fallback

def load_progress() -> dict:
    """Load previously processed file list to allow resuming."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"processed": [], "questions": {}}

def save_progress(progress: dict):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def get_text_files() -> list[str]:
    """Return all .txt files in extracted_content, sorted."""
    files = [f for f in os.listdir(EXTRACTED_DIR) if f.endswith(".txt")
             and not f.startswith("_")]
    return sorted(files)

def read_document(filename: str) -> str:
    """Read and truncate a document to MAX_DOC_CHARS."""
    path = os.path.join(EXTRACTED_DIR, filename)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    # Truncate if needed
    if len(text) > MAX_DOC_CHARS:
        text = text[:MAX_DOC_CHARS] + "\n\n[...document truncated for length...]"
    return text.strip()

def generate_questions(client: genai.Client, doc_text: str,
                       category: str, filename: str) -> list[dict]:
    """Call Gemini API to generate quiz questions from document text."""

    system_prompt = """You are an expert exam question writer for the Virginia Beach Fire Department (VBFD) promotional exam prep system.

Your job is to generate high-quality quiz questions from training documents.
IMPORTANT: You MUST generate a mix of 3 different types of questions: 'multiple_choice', 'matching', and 'short_answer'.
Specifically, aim for about 70% multiple choice, 20% matching, and 10% short answer.
For this generation batch, if it's a long document, ensure at least one 'short_answer' and one 'matching' question is included.

Rules:
- Each question must be factually grounded in the provided document (ignoring administrative CFAI references or revision dates).
- Questions should test knowledge that a Fire Captain candidate would need to know.
- Return ONLY valid JSON — a single JSON array of question objects.

Format for 'multiple_choice':
{
  "type": "multiple_choice",
  "question": "Question text here?",
  "choices": ["Choice A", "Choice B", "Choice C", "Choice D"],
  "answer": 0, // 0-based index of correct choice
  "explanation": "Brief explanation."
}

Format for 'matching':
{
  "type": "matching",
  "question": "Match the following terms to their definitions:",
  "pairs": [
    {"term": "Term 1", "definition": "Definition 1"},
    {"term": "Term 2", "definition": "Definition 2"},
    {"term": "Term 3", "definition": "Definition 3"},
    {"term": "Term 4", "definition": "Definition 4"}
  ],
  "explanation": "Optional explanation."
}

Format for 'short_answer':
{
  "type": "short_answer",
  "question": "Prompt for the user to answer with a few words or sentences?",
  "correctAnswer": "The ideal complete answer.",
  "keywords": ["keyword1", "keyword2", "keyword3"], // Key terms expected in the answer
  "explanation": "Brief explanation."
}"""

    user_prompt = f"""Generate up to {QUESTIONS_PER_DOC} multiple choice quiz questions based on the following VBFD document.

Document category: {category}
Document source: {filename}

--- DOCUMENT START ---
{doc_text}
--- DOCUMENT END ---

Return a JSON array of question objects. If the document has insufficient testable content, return fewer questions or an empty array [].
Only return the JSON array, nothing else."""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        raw = response.text.strip()

        # Strip any accidental markdown code fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        questions = json.loads(raw)
        if not isinstance(questions, list):
            return []

        # Validate and clean each question
        valid = []
        for q in questions:
            if not isinstance(q, dict) or "type" not in q or "question" not in q:
                continue

            q_type = q["type"]
            q["explanation"] = q.get("explanation", "").strip()

            if q_type == "multiple_choice":
                if ("choices" in q and isinstance(q["choices"], list) and len(q["choices"]) >= 2
                        and "answer" in q and isinstance(q["answer"], int) and 0 <= q["answer"] < len(q["choices"])):
                    valid.append(q)

            elif q_type == "matching":
                if "pairs" in q and isinstance(q["pairs"], list) and len(q["pairs"]) >= 2:
                    valid.append(q)

            elif q_type == "short_answer":
                if "correctAnswer" in q and "keywords" in q and isinstance(q["keywords"], list):
                    valid.append(q)

        return valid

    except (json.JSONDecodeError, Exception) as e:
        print(f"    ⚠ Error generating questions: {e}")
        return []

def write_output(all_questions: dict[str, list]):
    """Write questions_generated.js in the same format as questions.js."""
    lines = ["// Auto-generated question bank — do not edit manually",
             "// Generated by generate_questions.py",
             f"// Total documents processed: see generate_progress.json",
             "",
             "const GENERATED_QUESTION_BANK = {",
             ""]

    categories = ["HR Policies", "FD SOPs", "TEMS Protocols",
                  "EMS SOPs", "VBFD Overview", "Current Events"]

    for cat in categories:
        questions = all_questions.get(cat, [])
        if not questions:
            continue
        # Escape category name for JS key
        cat_js = cat.replace('"', '\\"')
        lines.append(f'  "{cat_js}": [')
        for q in questions:
            q_type = q.get("type", "multiple_choice")
            question_escaped = q["question"].replace("\\", "\\\\").replace('"', '\\"')
            explanation_escaped = q.get("explanation", "").replace("\\", "\\\\").replace('"', '\\"')
            
            lines.append(f'    {{')
            lines.append(f'      type: "{q_type}",')
            lines.append(f'      question: "{question_escaped}",')
            
            if q_type == "multiple_choice":
                choices_js = json.dumps(q.get("choices", []), ensure_ascii=False)
                lines.append(f'      choices: {choices_js},')
                lines.append(f'      answer: {q.get("answer", 0)},')
            elif q_type == "matching":
                pairs_js = json.dumps(q.get("pairs", []), ensure_ascii=False)
                lines.append(f'      pairs: {pairs_js},')
            elif q_type == "short_answer":
                ca_escaped = q.get("correctAnswer", "").replace("\\", "\\\\").replace('"', '\\"')
                keywords_js = json.dumps(q.get("keywords", []), ensure_ascii=False)
                lines.append(f'      correctAnswer: "{ca_escaped}",')
                lines.append(f'      keywords: {keywords_js},')
                
            lines.append(f'      explanation: "{explanation_escaped}"')
            lines.append(f'    }},')
        lines.append(f'  ],')
        lines.append('')

    lines.append("};")
    lines.append("")
    lines.append("// Merge generated questions into main QUESTION_BANK if it exists")
    lines.append("if (typeof QUESTION_BANK !== 'undefined') {")
    lines.append("  for (const [cat, qs] of Object.entries(GENERATED_QUESTION_BANK)) {")
    lines.append("    if (!QUESTION_BANK[cat]) QUESTION_BANK[cat] = [];")
    lines.append("    QUESTION_BANK[cat].push(...qs);")
    lines.append("  }")
    lines.append("}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    # Check for API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set.")
        print("   Run: export GEMINI_API_KEY='your-key-here'")
        return

    client = genai.Client(api_key=api_key)

    # Load progress (allows resuming if interrupted)
    progress = load_progress()
    processed_set = set(progress["processed"])

    # Organize existing generated questions by category
    all_questions: dict[str, list] = {}
    for cat, qs in progress.get("questions", {}).items():
        all_questions[cat] = qs

    # Get all document files
    files = get_text_files()
    remaining = [f for f in files if f not in processed_set]

    print(f"📚 VBFD Question Generator")
    print(f"   Total documents: {len(files)}")
    print(f"   Already processed: {len(processed_set)}")
    print(f"   Remaining: {len(remaining)}")
    print(f"   Questions so far: {sum(len(v) for v in all_questions.values())}")
    print()

    if not remaining:
        print("✅ All documents already processed! Writing output...")
        write_output(all_questions)
        total = sum(len(v) for v in all_questions.values())
        print(f"✅ Done! {total} questions written to questions_generated.js")
        return

    for i, filename in enumerate(remaining, 1):
        category = classify_document(filename)
        print(f"[{i}/{len(remaining)}] {category} | {filename[:70]}...")

        doc_text = read_document(filename)
        if len(doc_text) < 100:
            print(f"    ⚠ Document too short, skipping.")
            progress["processed"].append(filename)
            save_progress(progress)
            continue

        questions = generate_questions(client, doc_text, category, filename)
        print(f"    ✓ Generated {len(questions)} questions")

        if category not in all_questions:
            all_questions[category] = []
        all_questions[category].extend(questions)

        # Save progress after every file
        progress["processed"].append(filename)
        progress["questions"] = all_questions
        save_progress(progress)

        # Write output file every 10 docs so you can preview progress
        if i % 10 == 0:
            write_output(all_questions)
            total = sum(len(v) for v in all_questions.values())
            print(f"\n    💾 Progress saved — {total} total questions so far\n")

        time.sleep(API_DELAY)

    # Final write
    write_output(all_questions)
    total = sum(len(v) for v in all_questions.values())
    print(f"\n✅ Complete! {total} questions written to questions_generated.js")
    print(f"   Breakdown:")
    for cat, qs in all_questions.items():
        print(f"   - {cat}: {len(qs)} questions")

if __name__ == "__main__":
    main()
