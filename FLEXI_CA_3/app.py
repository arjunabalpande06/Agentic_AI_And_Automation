import gradio as gr
import json
import os
import asyncio
from datetime import datetime

try:
    from telegram_bot import send_telegram_message, send_test_message
    from database import load_deadlines, save_deadlines
    from llm_service import parse_task_with_llm
except ImportError:
    from FLEXI_CA_3.telegram_bot import send_telegram_message, send_test_message
    from FLEXI_CA_3.database import load_deadlines, save_deadlines
    from FLEXI_CA_3.llm_service import parse_task_with_llm


# =========================================================
# LOAD CHAT ID
# =========================================================

def load_chat_id():
    # 1. Check environment variable
    env_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if env_chat_id and env_chat_id.strip():
        return env_chat_id.strip()

    # 2. Local file fallbacks
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for fname in [".env", "example.env", "Imp.txt"]:
        fpath = os.path.join(base_dir, fname) if not os.path.exists(fname) else fname
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("TELEGRAM_CHAT_ID="):
                            val = line.split("=", 1)[1].strip()
                            if val:
                                return val
                        elif line.startswith("Chat ID:"):
                            val = line.split(":", 1)[1].strip()
                            if val:
                                return val
            except OSError:
                pass

    return None


# =========================================================
# ADD ASSIGNMENT (MANUAL)
# =========================================================

def add_assignment(
    student_name,
    subject,
    assignment_name,
    deadline,
    reminder_days
):
    chat_id = load_chat_id()

    if not chat_id:
        return "❌ Chat ID not found. Please add 'TELEGRAM_CHAT_ID=<your_id>' to the .env file."

    if not student_name:
        return "❌ Please enter student name."

    if not subject:
        return "❌ Please enter subject."

    if not assignment_name:
        return "❌ Please enter assignment name."

    if not deadline:
        return "❌ Please enter deadline."

    try:
        datetime.strptime(deadline, "%Y-%m-%d")
    except ValueError:
        return (
            "❌ Invalid date format.\n\n"
            "Use:\n"
            "YYYY-MM-DD\n\n"
            "Example:\n"
            "2026-09-10"
        )

    data = load_deadlines()

    try:
        reminder_days_val = int(reminder_days) if reminder_days is not None else 1
    except (ValueError, TypeError):
        reminder_days_val = 1

    next_id = max([item["id"] for item in data if "id" in item], default=0) + 1

    new_assignment = {
        "id": next_id,
        "student_name": student_name,
        "subject": subject,
        "assignment_name": assignment_name,
        "deadline": deadline,
        "chat_id": str(chat_id),
        "reminder_days": reminder_days_val,
        "completed": False,
        "reminder_sent": False
    }

    data.append(new_assignment)
    save_deadlines(data)

    return f"""
    <div class="result-card success-card">
        <div class="result-header">
            <span class="badge-success">✓ Assignment Added</span>
            <span class="badge-id">ID: #{next_id}</span>
        </div>
        <div class="result-grid">
            <div class="result-item"><span class="result-label">Student</span><span class="result-value">{student_name}</span></div>
            <div class="result-item"><span class="result-label">Subject</span><span class="result-value">{subject}</span></div>
            <div class="result-item"><span class="result-label">Assignment</span><span class="result-value">{assignment_name}</span></div>
            <div class="result-item"><span class="result-label">Deadline</span><span class="result-value">📅 {deadline}</span></div>
        </div>
        <div class="result-footer">
            <span class="status-dot-pulse"></span>
            <span>Reminder will trigger <strong>{reminder_days_val} day(s)</strong> before deadline via Telegram.</span>
        </div>
    </div>
    """


# =========================================================
# AI TASK & DEADLINE CREATION
# =========================================================

def create_ai_reminder(natural_input, student_name="Student", reminder_days=1):
    """
    Uses Groq LLM (openai/gpt-oss-120b) to extract structured deadline information
    from natural language and registers it with the existing task system.
    """
    if not natural_input or not natural_input.strip():
        return """
        <div class="result-card warning-card">
            <div class="result-header"><span class="badge-warn">⚠️ Input Required</span></div>
            <p style="margin: 6px 0 0 0; color: #cbd5e1;">Please enter a task or deadline description in natural language.</p>
        </div>
        """

    result = parse_task_with_llm(natural_input)

    if not result["success"]:
        if result.get("needs_clarification"):
            return f"""
            <div class="result-card warning-card">
                <div class="result-header"><span class="badge-warn">⚠️ More Details Needed</span></div>
                <p style="margin: 8px 0 6px 0; color: #f8fafc; font-size: 1rem;">{result['clarification_message']}</p>
                <p style="margin: 0; font-size: 0.85rem; color: #94a3b8;"><em>Tip: Mention a specific date or time (e.g., 'on September 25 at 6 PM' or 'tomorrow at 5 PM').</em></p>
            </div>
            """
        return f"""
        <div class="result-card error-card">
            <div class="result-header"><span class="badge-error">❌ AI Assistant Error</span></div>
            <p style="margin: 8px 0 0 0; color: #fca5a5;">{result.get('error', 'Failed to process task.')}</p>
        </div>
        """

    data = result["data"]
    task = data.get("task", "Assignment")
    date_str = data.get("date", "")
    time_str = data.get("time", "23:59")
    category = data.get("category", "Assignment")
    description = data.get("description", "")

    # Format human-friendly date and time
    try:
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt_obj.strftime("%d %B %Y")
    except ValueError:
        formatted_date = date_str

    try:
        t_obj = datetime.strptime(time_str, "%H:%M")
        formatted_time = t_obj.strftime("%I:%M %p").lstrip("0")
    except ValueError:
        formatted_time = time_str

    # Register into existing task storage
    chat_id = load_chat_id()
    deadlines = load_deadlines()

    try:
        reminder_days_val = int(reminder_days) if reminder_days is not None else 1
    except (ValueError, TypeError):
        reminder_days_val = 1

    next_id = max([item["id"] for item in deadlines if "id" in item], default=0) + 1
    student_val = student_name.strip() if student_name and student_name.strip() else "Student"

    new_assignment = {
        "id": next_id,
        "student_name": student_val,
        "subject": category,
        "assignment_name": task,
        "deadline": date_str,
        "time": time_str,
        "category": category,
        "description": description,
        "chat_id": str(chat_id) if chat_id else "",
        "reminder_days": reminder_days_val,
        "completed": False,
        "reminder_sent": False
    }

    deadlines.append(new_assignment)
    save_deadlines(deadlines)

    status_note = ""
    if not chat_id:
        status_note = '<div style="margin-top: 10px; color: #fbbf24; font-size: 0.85rem;">⚠️ <em>Note: Telegram Chat ID not found in .env. Saved locally, but automated alerts require TELEGRAM_CHAT_ID.</em></div>'

    return f"""
    <div class="result-card success-card">
        <div class="result-header">
            <span class="badge-success">✓ Scheduled & Saved</span>
            <span class="badge-id">Saved as Assignment #{next_id}</span>
        </div>
        <div class="result-grid">
            <div class="result-item">
                <span class="result-label">Task</span>
                <span class="result-value task-highlight">{task}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Date</span>
                <span class="result-value date-highlight">📅 {formatted_date}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Time</span>
                <span class="result-value time-highlight">⏰ {formatted_time}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Category</span>
                <span class="result-value cat-highlight">🏷️ {category}</span>
            </div>
        </div>
        <div class="result-footer">
            <span class="status-dot-pulse"></span>
            <span>Saved as Assignment #{next_id}! Reminding <strong>{reminder_days_val} day(s)</strong> before deadline via Telegram.</span>
        </div>
        {status_note}
    </div>
    """


# =========================================================
# VIEW ASSIGNMENTS
# =========================================================

def view_assignments():
    data = load_deadlines()

    if not data:
        return """
        <div class="empty-container">
            <div class="empty-icon">📭</div>
            <h3 class="empty-title">No assignments scheduled</h3>
            <p class="empty-desc">Create your first reminder using the AI Assistant or Add Assignment tab!</p>
        </div>
        """

    cards = '<div class="cards-grid">'

    for item in data:
        is_done = item.get("completed", False)
        status_class = "card-completed" if is_done else "card-pending"
        status_label = "Completed" if is_done else "Pending"
        status_icon = "✓" if is_done else "⏳"
        time_badge = f'<span class="time-pill">⏰ {item["time"]}</span>' if item.get("time") else ""
        category = item.get("category") or item.get("subject") or "Assignment"

        cards += f"""
        <div class="assignment-card {status_class}">
            <div class="card-top">
                <span class="category-badge">🏷️ {category}</span>
                <span class="status-badge {status_class}">
                    <span class="status-dot"></span> {status_icon} {status_label}
                </span>
            </div>
            <h3 class="card-title">{item.get('assignment_name', 'Untitled')}</h3>
            <div class="card-info-list">
                <div class="info-row">
                    <span class="info-label">👤 Student</span>
                    <span class="info-val">{item.get('student_name', 'Student')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">📚 Subject</span>
                    <span class="info-val">{item.get('subject', 'General')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">📅 Deadline</span>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span class="info-val deadline-text">{item.get('deadline', '')}</span>
                        {time_badge}
                    </div>
                </div>
                <div class="info-row">
                    <span class="info-label">🔔 Reminder</span>
                    <span class="info-val">{item.get('reminder_days', 1)} day(s) before</span>
                </div>
            </div>
            <div class="card-bottom">
                <span class="id-tag">ID: #{item.get('id', '?')}</span>
            </div>
        </div>
        """

    cards += "</div>"
    return cards


# =========================================================
# MARK COMPLETED
# =========================================================

def mark_completed(assignment_id):
    data = load_deadlines()

    try:
        assignment_id = int(assignment_id)
    except (ValueError, TypeError):
        return "❌ Enter a valid assignment ID."

    found = False
    for item in data:
        if item["id"] == assignment_id:
            item["completed"] = True
            found = True
            break

    if not found:
        return "❌ Assignment ID not found."

    save_deadlines(data)
    return f"""
    <div class="result-card success-card">
        <div class="result-header"><span class="badge-success">✓ Status Updated</span></div>
        <p style="margin: 6px 0 0 0; color: #f8fafc; font-size: 1rem;">Assignment <strong>#{assignment_id}</strong> marked as completed! 🎉</p>
    </div>
    """


# =========================================================
# DELETE ASSIGNMENT
# =========================================================

def delete_assignment(assignment_id):
    data = load_deadlines()

    try:
        assignment_id = int(assignment_id)
    except (ValueError, TypeError):
        return "❌ Enter a valid assignment ID."

    original_len = len(data)
    data = [item for item in data if item["id"] != assignment_id]

    if len(data) == original_len:
        return "❌ Assignment ID not found."

    save_deadlines(data)
    return f"""
    <div class="result-card error-card">
        <div class="result-header"><span class="badge-error">🗑️ Assignment Deleted</span></div>
        <p style="margin: 6px 0 0 0; color: #f8fafc; font-size: 1rem;">Assignment <strong>#{assignment_id}</strong> was successfully removed.</p>
    </div>
    """


# =========================================================
# CUSTOM CSS DESIGN SYSTEM
# =========================================================

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap');

:root {
    --primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
    --secondary-gradient: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
    --dark-bg: #090d16;
    --card-bg: rgba(15, 23, 42, 0.7);
    --border-color: rgba(255, 255, 255, 0.08);
}

body, .gradio-container {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: radial-gradient(circle at 10% 15%, rgba(99, 102, 241, 0.15) 0%, transparent 45%),
                radial-gradient(circle at 90% 85%, rgba(236, 72, 153, 0.12) 0%, transparent 45%),
                radial-gradient(circle at 50% 50%, rgba(6, 182, 212, 0.08) 0%, transparent 60%),
                var(--dark-bg) !important;
    color: #f8fafc !important;
    max-width: 1160px !important;
    margin: 0 auto !important;
    padding: 24px 16px !important;
}

/* Header Section */
.hero-header {
    text-align: center;
    padding: 28px 20px 20px 20px;
    margin-bottom: 24px;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid var(--border-color);
    border-radius: 24px;
    backdrop-filter: blur(16px);
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.35);
    border-radius: 9999px;
    color: #a5b4fc;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 14px;
}

.pulsing-green-dot {
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 10px #10b981;
    animation: livePulse 2s infinite ease-in-out;
}

@keyframes livePulse {
    0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.hero-title {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #ffffff 20%, #c7d2fe 60%, #f472b6 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    margin: 0 0 8px 0 !important;
    letter-spacing: -0.02em;
}

.hero-subtitle {
    color: #94a3b8 !important;
    font-size: 1.05rem !important;
    max-width: 650px;
    margin: 0 auto !important;
    line-height: 1.5;
}

/* Tabs Styling */
.tabs {
    background: transparent !important;
}

.tab-nav {
    display: flex !important;
    gap: 8px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    padding-bottom: 4px !important;
    margin-bottom: 20px !important;
}

.tab-nav button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #94a3b8 !important;
    background: rgba(15, 23, 42, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px 12px 0 0 !important;
    padding: 10px 20px !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.tab-nav button:hover {
    color: #ffffff !important;
    background: rgba(99, 102, 241, 0.15) !important;
}

.tab-nav button.selected {
    color: #ffffff !important;
    background: linear-gradient(180deg, rgba(99, 102, 241, 0.25) 0%, rgba(15, 23, 42, 0.6) 100%) !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
    border-bottom: 2px solid #818cf8 !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.15) !important;
}

/* Inputs & Form Elements */
input, textarea, select {
    background: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 14px !important;
    color: #f8fafc !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 12px 16px !important;
    transition: all 0.2s ease !important;
}

input:focus, textarea:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
    outline: none !important;
    background: rgba(15, 23, 42, 0.95) !important;
}

/* Buttons */
button.primary-action-btn, button.primary, .primary-action-btn {
    background: var(--primary-gradient) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 13px 28px !important;
    cursor: pointer !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    letter-spacing: 0.02em;
}

button.primary-action-btn:hover, button.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 30px rgba(236, 72, 153, 0.45) !important;
}

button.primary-action-btn:active, button.primary:active {
    transform: translateY(0) !important;
}

/* Quick Prompt Chip Buttons */
.chip-btn {
    background: rgba(30, 41, 59, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 9999px !important;
    color: #cbd5e1 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.chip-btn:hover {
    background: rgba(99, 102, 241, 0.25) !important;
    border-color: #818cf8 !important;
    color: #ffffff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25) !important;
}

/* Result Card Component */
.result-card {
    border-radius: 18px;
    padding: 22px;
    margin-top: 14px;
    backdrop-filter: blur(16px);
    animation: slideFadeIn 0.3s ease-out;
}

@keyframes slideFadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.success-card {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(236, 72, 153, 0.12) 100%);
    border: 1px solid rgba(168, 85, 247, 0.4);
    box-shadow: 0 12px 35px rgba(99, 102, 241, 0.2);
}

.warning-card {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.4);
    box-shadow: 0 8px 25px rgba(245, 158, 11, 0.15);
}

.error-card {
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.4);
    box-shadow: 0 8px 25px rgba(239, 68, 68, 0.15);
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}

.badge-success {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid #10b981;
    color: #34d399;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.badge-warn {
    background: rgba(245, 158, 11, 0.2);
    border: 1px solid #f59e0b;
    color: #fbbf24;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.badge-error {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid #ef4444;
    color: #f87171;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.badge-id {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #cbd5e1;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 600;
}

.result-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 16px;
    border-radius: 14px;
}

.result-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.result-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    color: #94a3b8;
    font-weight: 700;
    letter-spacing: 0.05em;
}

.result-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f8fafc;
}

.task-highlight { color: #ffffff; }
.date-highlight { color: #38bdf8; }
.time-highlight { color: #f472b6; }
.cat-highlight { color: #a78bfa; }

.result-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 14px;
    font-size: 0.88rem;
    color: #cbd5e1;
}

.status-dot-pulse {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 10px #10b981;
    display: inline-block;
}

/* Assignments Grid & Cards */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
    margin-top: 10px;
}

.assignment-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid var(--border-color);
    border-radius: 18px;
    padding: 20px;
    backdrop-filter: blur(12px);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.assignment-card:hover {
    transform: translateY(-4px);
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 14px 35px rgba(0, 0, 0, 0.4);
}

.card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.category-badge {
    background: rgba(99, 102, 241, 0.18);
    border: 1px solid rgba(99, 102, 241, 0.35);
    color: #a5b4fc;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 9999px;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
}

.status-badge.card-completed {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
}

.status-badge.card-pending {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    color: #fbbf24;
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
}

.card-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0 0 14px 0;
    line-height: 1.35;
}

.card-info-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 0.88rem;
    color: #94a3b8;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.info-label {
    color: #64748b;
    font-weight: 600;
    font-size: 0.82rem;
}

.info-val {
    color: #e2e8f0;
    font-weight: 600;
}

.deadline-text {
    color: #38bdf8 !important;
}

.time-pill {
    background: rgba(236, 72, 153, 0.18);
    border: 1px solid rgba(236, 72, 153, 0.35);
    color: #f472b6;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
}

.card-bottom {
    display: flex;
    justify-content: flex-end;
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.id-tag {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 700;
}

/* Empty State */
.empty-container {
    text-align: center;
    padding: 48px 20px;
    background: rgba(15, 23, 42, 0.5);
    border: 2px dashed rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    margin-top: 10px;
}

.empty-icon {
    font-size: 3rem;
    margin-bottom: 10px;
}

.empty-title {
    color: #f8fafc;
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0 0 6px 0;
}

.empty-desc {
    color: #94a3b8;
    margin: 0;
    font-size: 0.95rem;
}
"""


# =========================================================
# GRADIO INTERFACE
# =========================================================

with gr.Blocks(
    title="Student Deadline Reminder Automation"
) as app:

    # Hero Header Banner & Global Styles
    gr.HTML(
        f"""
        <style>
        {CUSTOM_CSS}
        </style>
        <div class="hero-header">
            <div class="hero-badge">
                <span class="pulsing-green-dot"></span>
                <span>AI Automation & Deadline Tracker</span>
                <span style="opacity: 0.5;">•</span>
                <span style="color: #c084fc;">Groq openai/gpt-oss-120b</span>
            </div>
            <h1 class="hero-title">Student Deadline Assistant</h1>
            <p class="hero-subtitle">Convert natural language thoughts into scheduled deadlines with automated Telegram notifications.</p>
        </div>
        """
    )

    # -----------------------------------------------------
    # 🤖 AI TASK & DEADLINE ASSISTANT
    # -----------------------------------------------------
    with gr.Tab("🤖 AI Task & Deadline Assistant"):

        gr.Markdown(
            """
### 💡 Describe your task or deadline in natural language
Type what you need to do naturally, and the Groq LLM will extract the task name, date, time, and category automatically.
"""
        )

        ai_input = gr.Textbox(
            label="Describe your task or deadline in natural language",
            placeholder="e.g. Remind me to submit my Machine Learning lab report tomorrow at 5 PM.",
            lines=3
        )

        # Quick Suggestion Chips
        gr.Markdown("<div style='font-size: 0.8rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-top: 4px;'>⚡ Quick Try Prompts (Click to fill):</div>")
        with gr.Row():
            chip1 = gr.Button("📌 ML Lab Report tomorrow at 5 PM", elem_classes=["chip-btn"])
            chip2 = gr.Button("🚀 Python Project on September 25 at 6 PM", elem_classes=["chip-btn"])
            chip3 = gr.Button("📊 Project Presentation next Friday at 10 AM", elem_classes=["chip-btn"])

        chip1.click(lambda: "Remind me to submit my Machine Learning lab report tomorrow at 5 PM.", outputs=ai_input)
        chip2.click(lambda: "Remind me to submit my Python assignment on September 25 at 6 PM.", outputs=ai_input)
        chip3.click(lambda: "I have a project presentation next Friday at 10 AM.", outputs=ai_input)

        with gr.Row():
            ai_student_name = gr.Textbox(
                label="Student Name",
                value="Student",
                placeholder="Enter your name"
            )
            ai_reminder_days = gr.Number(
                label="Remind me how many days before?",
                value=1,
                precision=0
            )

        ai_create_button = gr.Button(
            "⚡ Create & Schedule Reminder",
            variant="primary",
            elem_classes=["primary-action-btn"]
        )

        ai_output = gr.HTML()

        ai_create_button.click(
            create_ai_reminder,
            inputs=[
                ai_input,
                ai_student_name,
                ai_reminder_days
            ],
            outputs=ai_output
        )

    # -----------------------------------------------------
    # ➕ ADD ASSIGNMENT (MANUAL)
    # -----------------------------------------------------
    with gr.Tab("➕ Add Assignment"):
        gr.Markdown("### 📝 Manually Schedule an Assignment")

        with gr.Row():
            student_name = gr.Textbox(
                label="Student Name",
                placeholder="e.g. Rahul"
            )
            subject = gr.Textbox(
                label="Subject",
                placeholder="e.g. Machine Learning"
            )

        with gr.Row():
            assignment_name = gr.Textbox(
                label="Assignment Name",
                placeholder="e.g. Lab Report 3"
            )
            deadline = gr.Textbox(
                label="Deadline Date",
                placeholder="YYYY-MM-DD (e.g. 2026-09-30)"
            )

        reminder_days = gr.Number(
            label="Remind me how many days before?",
            value=1,
            precision=0
        )

        add_button = gr.Button(
            "➕ Add Assignment",
            variant="primary",
            elem_classes=["primary-action-btn"]
        )

        add_output = gr.HTML()

        add_button.click(
            add_assignment,
            inputs=[
                student_name,
                subject,
                assignment_name,
                deadline,
                reminder_days
            ],
            outputs=add_output
        )

    # -----------------------------------------------------
    # 📋 VIEW ASSIGNMENTS
    # -----------------------------------------------------
    with gr.Tab("📋 View Assignments"):
        with gr.Row():
            gr.Markdown("### 📚 Your Scheduled Assignments")
            view_button = gr.Button(
                "🔄 Refresh Assignments",
                elem_classes=["chip-btn"]
            )

        assignments_output = gr.HTML(value=view_assignments)

        view_button.click(
            view_assignments,
            outputs=assignments_output
        )

    # -----------------------------------------------------
    # ✅ COMPLETE ASSIGNMENT
    # -----------------------------------------------------
    with gr.Tab("✅ Complete Assignment"):
        gr.Markdown("### Mark an Assignment as Done")

        assignment_id = gr.Number(
            label="Assignment ID",
            precision=0
        )

        complete_button = gr.Button(
            "✅ Mark as Completed",
            variant="primary",
            elem_classes=["primary-action-btn"]
        )

        complete_output = gr.HTML()

        complete_button.click(
            mark_completed,
            inputs=assignment_id,
            outputs=complete_output
        )

    # -----------------------------------------------------
    # 🗑️ DELETE ASSIGNMENT
    # -----------------------------------------------------
    with gr.Tab("🗑️ Delete Assignment"):
        gr.Markdown("### Remove an Assignment")

        delete_id = gr.Number(
            label="Assignment ID",
            precision=0
        )

        delete_button = gr.Button(
            "🗑️ Delete Assignment",
            variant="stop"
        )

        delete_output = gr.HTML()

        delete_button.click(
            delete_assignment,
            inputs=delete_id,
            outputs=delete_output
        )


if __name__ == "__main__":
    app.launch()