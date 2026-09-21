import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# Ensure local .env files are loaded
base_dir = os.path.dirname(os.path.abspath(__file__))
for env_name in [".env", "example.env"]:
    env_path = os.path.join(base_dir, env_name)
    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)
load_dotenv(override=False)

GROQ_MODEL = "openai/gpt-oss-120b"


def get_groq_api_key():
    """Safely retrieves the Groq API key from environment variables or .env."""
    key = os.getenv("GROQ_API_KEY")
    if key and key.strip() and not key.startswith("your_"):
        return key.strip()

    # Fallback check directly in .env files without leaking
    for fname in [".env", "example.env"]:
        fpath = os.path.join(base_dir, fname) if not os.path.exists(fname) else fname
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GROQ_API_KEY="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val and not val.startswith("your_"):
                                return val
            except OSError:
                pass
    return None


def parse_task_with_llm(user_text: str, reference_datetime: datetime = None):
    """
    Parses natural language task description using Groq API and openai/gpt-oss-120b.

    Returns a dictionary with:
      - success (bool): True if parsing succeeded and all required fields are present
      - data (dict): parsed task details (task, date, time, category, description)
      - error (str or None): user-friendly error message if failed
      - needs_clarification (bool): True if date/time or task info was missing
      - clarification_message (str): prompt to user to provide missing information
    """
    if not user_text or not user_text.strip():
        return {
            "success": False,
            "data": None,
            "error": "Please enter a task or deadline description.",
            "needs_clarification": False,
            "clarification_message": "",
        }

    api_key = get_groq_api_key()
    if not api_key:
        return {
            "success": False,
            "data": None,
            "error": "Groq API key is not configured. Please add GROQ_API_KEY to your .env file.",
            "needs_clarification": False,
            "clarification_message": "",
        }

    try:
        from groq import Groq, AuthenticationError, RateLimitError, APIConnectionError, APITimeoutError
    except ImportError:
        return {
            "success": False,
            "data": None,
            "error": "The 'groq' package is not installed. Please run 'pip install -r requirements.txt'.",
            "needs_clarification": False,
            "clarification_message": "",
        }

    ref_dt = reference_datetime or datetime.now()
    current_datetime_str = ref_dt.strftime("%Y-%m-%d %H:%M")
    current_day_str = ref_dt.strftime("%A")
    current_year = ref_dt.strftime("%Y")

    system_prompt = f"""You are an intelligent AI Task and Deadline Assistant for a student task management system.
Your job is to understand natural language instructions and extract structured task details into valid JSON.

Current PC Context:
- Current Date and Time: {current_datetime_str}
- Current Day of the Week: {current_day_str}
- Current Year: {current_year}

Extraction Instructions:
1. "task": Concise, clean title for the assignment or task (e.g., "Submit Python assignment", "Project presentation").
2. "date": ISO format deadline date "YYYY-MM-DD".
   - Accurately resolve relative date expressions such as "today", "tomorrow", "next Monday", "next Friday", "September 25", etc. using the Current PC Context.
   - For weekday names like "next Friday", determine the exact date relative to {current_day_str} ({ref_dt.strftime('%Y-%m-%d')}).
   - For dates without a year (e.g. "September 25"), use current year {current_year} (or next year if passed).
3. "time": 24-hour format "HH:MM" (e.g., "18:00" for 6 PM, "10:00" for 10 AM, "18:30").
   - If time of day is explicitly specified, format as HH:MM.
   - If no specific time is mentioned but date is given, default to "23:59".
4. "category": Identify the appropriate category, e.g. "Assignment", "Project", "Presentation", "Quiz", "Exam", "CA Record", or "General".
5. "description": Any additional instructions or notes from the text, otherwise "".

STRICT MISSING INFORMATION & CLARIFICATION RULE:
- NEVER randomly invent, assume, or guess dates or times if the user has omitted them.
- If the user's input does NOT specify a deadline date (for example: "Remind me to submit my assignment", "I need to prepare for my test", "Remind me about the project"), you MUST NOT invent a date.
- In that case, set "needs_clarification": true and provide a friendly "clarification_message" explicitly asking for the missing date/time.
- If sufficient information is present, set "needs_clarification": false and "clarification_message": "".

Output Format:
You must return ONLY a single valid JSON object with these exact keys:
{{
  "task": "string",
  "date": "YYYY-MM-DD or empty string",
  "time": "HH:MM or empty string",
  "category": "string",
  "description": "string",
  "needs_clarification": boolean,
  "clarification_message": "string"
}}
"""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text.strip()}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500,
        )

        content = response.choices[0].message.content
        if not content:
            return {
                "success": False,
                "data": None,
                "error": "Received empty response from the Groq model.",
                "needs_clarification": False,
                "clarification_message": "",
            }

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Attempt to extract JSON substring if any markdown markers leaked
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": "Failed to parse model response into JSON.",
                    "needs_clarification": False,
                    "clarification_message": "",
                }

        # Check if model flagged clarification
        if parsed.get("needs_clarification"):
            clarification_msg = parsed.get("clarification_message") or (
                "Please provide the deadline date and time for this task."
            )
            return {
                "success": False,
                "data": parsed,
                "error": None,
                "needs_clarification": True,
                "clarification_message": clarification_msg,
            }

        # Validate essential fields
        task_name = (parsed.get("task") or "").strip()
        deadline_date = (parsed.get("date") or "").strip()
        deadline_time = (parsed.get("time") or "").strip()

        if not task_name:
            return {
                "success": False,
                "data": parsed,
                "error": None,
                "needs_clarification": True,
                "clarification_message": "Could not identify the task name. Please describe what task needs to be done.",
            }

        if not deadline_date:
            return {
                "success": False,
                "data": parsed,
                "error": None,
                "needs_clarification": True,
                "clarification_message": "Please specify the date for this task or deadline.",
            }

        # Validate date format YYYY-MM-DD
        try:
            datetime.strptime(deadline_date, "%Y-%m-%d")
        except ValueError:
            return {
                "success": False,
                "data": parsed,
                "error": f"Invalid date extracted ({deadline_date}). Please specify a valid date.",
                "needs_clarification": True,
                "clarification_message": "Please specify a clear date (e.g., September 25, tomorrow, next Monday).",
            }

        # Standardize time format HH:MM
        if not deadline_time:
            deadline_time = "23:59"
        else:
            # Validate HH:MM
            try:
                dt_time = datetime.strptime(deadline_time, "%H:%M")
                deadline_time = dt_time.strftime("%H:%M")
            except ValueError:
                # Try with AM/PM if model returned 12-hour format
                try:
                    dt_time = datetime.strptime(deadline_time, "%I:%M %p")
                    deadline_time = dt_time.strftime("%H:%M")
                except ValueError:
                    deadline_time = "23:59"

        result_data = {
            "task": task_name,
            "date": deadline_date,
            "time": deadline_time,
            "category": parsed.get("category") or "Assignment",
            "description": parsed.get("description") or "",
        }

        return {
            "success": True,
            "data": result_data,
            "error": None,
            "needs_clarification": False,
            "clarification_message": "",
        }

    except AuthenticationError:
        return {
            "success": False,
            "data": None,
            "error": "Groq Authentication Error: The provided GROQ_API_KEY is invalid. Please check your .env file.",
            "needs_clarification": False,
            "clarification_message": "",
        }
    except RateLimitError:
        return {
            "success": False,
            "data": None,
            "error": "Groq API Rate Limit reached. Please wait a moment and try again.",
            "needs_clarification": False,
            "clarification_message": "",
        }
    except (APIConnectionError, APITimeoutError) as e:
        return {
            "success": False,
            "data": None,
            "error": "Groq API connection/network timeout. Please check your internet connection.",
            "needs_clarification": False,
            "clarification_message": "",
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"An unexpected error occurred while communicating with the AI service: {type(e).__name__}",
            "needs_clarification": False,
            "clarification_message": "",
        }
