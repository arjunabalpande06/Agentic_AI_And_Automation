import gradio as gr
import json
import os
import asyncio
from datetime import datetime

try:
    from telegram_bot import send_telegram_message
    from database import load_deadlines, save_deadlines
    from llm_service import parse_task_with_llm
except ImportError:
    from FLEXI_CA_3.telegram_bot import send_telegram_message
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
                with open(fpath, "r") as f:
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
# ADD ASSIGNMENT
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

        datetime.strptime(
            deadline,
            "%Y-%m-%d"
        )

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

    return (
        "✅ Assignment added successfully!\n\n"

        f"Student: {student_name}\n"
        f"Subject: {subject}\n"
        f"Assignment: {assignment_name}\n"
        f"Deadline: {deadline}\n"
        f"Reminder: {reminder_days} day(s) before"
    )


# =========================================================
# AI TASK & DEADLINE CREATION
# =========================================================

def create_ai_reminder(natural_input, student_name="Student", reminder_days=1):
    """
    Uses Groq LLM (openai/gpt-oss-120b) to extract structured deadline information
    from natural language and registers it with the existing task system.
    """
    if not natural_input or not natural_input.strip():
        return "⚠️ **Input required:** Please enter a task or deadline description in natural language."

    result = parse_task_with_llm(natural_input)

    if not result["success"]:
        if result.get("needs_clarification"):
            return (
                "⚠️ **More Information Needed**\n\n"
                f"{result['clarification_message']}\n\n"
                "_Tip: Please mention a specific date or time (e.g. 'on September 25 at 6 PM' or 'tomorrow at 5 PM')._"
            )
        return f"❌ **AI Assistant Error:** {result.get('error', 'Failed to process task.')}"

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
        status_note = "\n\n⚠️ *Note: Telegram Chat ID not found in .env. Reminder saved locally, but automated alerts require TELEGRAM_CHAT_ID.*"

    return (
        "### 🤖 AI Task & Deadline Created\n\n"
        f"**Task:** {task}\n\n"
        f"**Date:** {formatted_date}\n\n"
        f"**Time:** {formatted_time}\n\n"
        f"**Category:** {category}\n\n"
        "---\n"
        f"✅ **Saved as Assignment #{next_id}!** Reminding {reminder_days_val} day(s) before.{status_note}"
    )


# =========================================================
# VIEW ASSIGNMENTS
# =========================================================

def view_assignments():

    data = load_deadlines()

    if not data:

        return "📭 No assignments found."

    output = "## 📚 Your Assignments\n\n"

    for item in data:

        status = (
            "✅ Completed"
            if item.get("completed")
            else "⏳ Pending"
        )

        time_suffix = f" at {item['time']}" if item.get("time") else ""

        output += (
            f"### {item['id']}. "
            f"{item['assignment_name']}\n"
            f"**Student:** {item['student_name']}\n"
            f"**Subject / Category:** {item['subject']}\n"
            f"**Deadline:** {item['deadline']}{time_suffix}\n"
            f"**Status:** {status}\n\n"
        )

    return output


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

    return (
        f"✅ Assignment {assignment_id} "
        "marked as completed!"
    )


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

    return f"🗑️ Assignment {assignment_id} deleted successfully!"


# =========================================================
# SEND TEST TELEGRAM
# =========================================================

def test_telegram():

    chat_id = load_chat_id()

    if not chat_id:
        return "❌ Chat ID not found. Please add 'TELEGRAM_CHAT_ID=<your_id>' to the .env file."

    message = (
        "🔔 Student Deadline Reminder\n\n"
        "Hello! 👋\n\n"
        "This is a test notification.\n\n"
        "Your Telegram reminder system is working! ✅"
    )

    try:

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            loop.create_task(send_telegram_message(chat_id, message))
        else:
            asyncio.run(
                send_telegram_message(
                    chat_id,
                    message
                )
            )

        return "✅ Telegram message sent successfully!"

    except Exception as e:

        return f"❌ Telegram error: {str(e)}"


# =========================================================
# GRADIO INTERFACE
# =========================================================

with gr.Blocks(
    title="Student Deadline Reminder"
) as app:

    gr.Markdown(
        """
# 📚 Student Deadline Reminder Automation

Automatically receive assignment deadline reminders
through Telegram.
"""
    )

    # -----------------------------------------------------
    # AI TASK & DEADLINE ASSISTANT
    # -----------------------------------------------------

    with gr.Tab("🤖 AI Task & Deadline Assistant"):

        gr.Markdown(
            """
### 💡 Describe your task or deadline in natural language
Enter your assignment or deadline naturally, and the Groq LLM (`openai/gpt-oss-120b`) will automatically extract the date, time, and category and schedule your reminder.

**Examples:**
- *Remind me to submit my Python assignment on September 25 at 6 PM.*
- *I have a project presentation on September 28 at 10 AM.*
- *Remind me about my CA record submission tomorrow at 5 PM.*
"""
        )

        ai_input = gr.Textbox(
            label="Describe your task or deadline in natural language",
            placeholder="e.g. Remind me to submit my Python assignment on September 25 at 6 PM.",
            lines=3
        )

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
            "⚡ Create Reminder",
            variant="primary"
        )

        ai_output = gr.Markdown()

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
    # ADD ASSIGNMENT
    # -----------------------------------------------------

    with gr.Tab("➕ Add Assignment"):

        student_name = gr.Textbox(
            label="Student Name",
            placeholder="Enter student name"
        )

        subject = gr.Textbox(
            label="Subject",
            placeholder="Example: Python"
        )

        assignment_name = gr.Textbox(
            label="Assignment Name",
            placeholder="Example: Python Mini Project"
        )

        deadline = gr.Textbox(
            label="Deadline",
            placeholder="YYYY-MM-DD"
        )



        reminder_days = gr.Number(
            label="Remind me how many days before?",
            value=1,
            precision=0
        )

        add_button = gr.Button(
            "➕ Add Assignment"
        )

        add_output = gr.Markdown()

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
    # VIEW ASSIGNMENTS
    # -----------------------------------------------------

    with gr.Tab("📋 View Assignments"):

        view_button = gr.Button(
            "🔄 Refresh Assignments"
        )

        assignments_output = gr.Markdown()

        view_button.click(
            view_assignments,
            outputs=assignments_output
        )

    # -----------------------------------------------------
    # COMPLETE ASSIGNMENT
    # -----------------------------------------------------

    with gr.Tab("✅ Complete Assignment"):

        assignment_id = gr.Number(
            label="Assignment ID",
            precision=0
        )

        complete_button = gr.Button(
            "✅ Mark Completed"
        )

        complete_output = gr.Markdown()

        complete_button.click(
            mark_completed,
            inputs=assignment_id,
            outputs=complete_output
        )


    # -----------------------------------------------------
    # DELETE ASSIGNMENT
    # -----------------------------------------------------

    with gr.Tab("🗑️ Delete Assignment"):

        delete_id = gr.Number(
            label="Assignment ID",
            precision=0
        )

        delete_button = gr.Button(
            "🗑️ Delete Assignment"
        )

        delete_output = gr.Markdown()

        delete_button.click(
            delete_assignment,
            inputs=delete_id,
            outputs=delete_output
        )

if __name__ == "__main__":

    app.launch()