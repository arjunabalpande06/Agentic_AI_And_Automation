import gradio as gr
import json
import os
import asyncio
from datetime import datetime

try:
    from telegram_bot import send_telegram_message
    from database import load_deadlines, save_deadlines
except ImportError:
    from FLEXI_CA_3.telegram_bot import send_telegram_message
    from FLEXI_CA_3.database import load_deadlines, save_deadlines


# =========================================================
# LOAD CHAT ID
# =========================================================

def load_chat_id():
    # 1. Check environment variable (Vercel & cloud platforms)
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
            if item["completed"]
            else "⏳ Pending"
        )

        output += (
            f"### {item['id']}. "
            f"{item['assignment_name']}\n"
            f"**Student:** {item['student_name']}\n"
            f"**Subject:** {item['subject']}\n"
            f"**Deadline:** {item['deadline']}\n"
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


app_fastapi = app.app

if __name__ == "__main__":

    app.launch()