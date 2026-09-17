# 📚 Student Deadline Reminder Automation

A **Gradio-based web application** that helps students track assignment deadlines and receive automated reminders via **Telegram**.

---

## 🚀 Features

- ➕ **Add Assignments** — Store student name, subject, assignment name, deadline, and reminder preference
- 📋 **View Assignments** — List all assignments with their current status (Pending / Completed)
- ✅ **Mark as Completed** — Update an assignment's status by ID
- 🗑️ **Delete Assignments** — Remove assignments that are no longer needed
- 🔔 **Telegram Notifications** — Automatically sends deadline reminders directly to your Telegram chat
- 📅 **Flexible Reminder Days** — Choose how many days before the deadline you want to be reminded
- 🚨 **Same-day Alerts** — Sends an additional alert on the day the assignment is due

---

## 🗂️ Project Structure

```
FLEXI_CA_3_GRADIO/
│
├── app.py              # Main Gradio web application
├── reminder.py         # Deadline checker — sends Telegram reminders
├── telegram_bot.py     # Telegram bot helper (send messages)
├── get_chat_id.py      # Utility to find your Telegram Chat ID
├── database.py         # SQLite database utilities (alternate storage)
├── deadlines.json      # JSON file storing all assignments
├── Imp.txt             # Stores your Telegram Chat ID
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

---

## ⚙️ Setup & Installation

### 1. Clone / Download the Project

```bash
git clone <your-repo-url>
cd FLEXI_CA_3_GRADIO
```

### 2. Install Dependencies

```bash
pip install gradio python-telegram-bot
```

Or if a `requirements.txt` is populated:

```bash
pip install -r requirements.txt
```

### 3. Configure Your Telegram Bot

#### Step 1 — Create a Telegram Bot
1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the instructions
3. Copy the **Bot Token** you receive

#### Step 2 — Set the Bot Token

Open `telegram_bot.py` and replace the default token, **or** set it as an environment variable:

```bash
# Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN = "your_bot_token_here"

# Linux / macOS
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

#### Step 3 — Get Your Telegram Chat ID

Run the helper script and send any message to your bot on Telegram:

```bash
python get_chat_id.py
```

Your Chat ID will be printed in the terminal and replied by the bot.

#### Step 4 — Save Your Chat ID

Open `Imp.txt` and add your Chat ID in the following format:

```
Chat ID: 1234567890
```

---

## ▶️ Running the Application

### Launch the Gradio Web App

```bash
python app.py
```

The app will open in your browser at `http://127.0.0.1:7860`

### Run the Reminder Checker (Manually)

To check deadlines and send Telegram reminders:

```bash
python reminder.py
```

> **Tip:** Schedule `reminder.py` to run daily using **Task Scheduler** (Windows) or **cron** (Linux/macOS) for fully automated reminders.

---

## 🖥️ How to Use the App

### ➕ Add Assignment Tab
| Field | Description |
|---|---|
| Student Name | Name of the student |
| Subject | Course or subject name (e.g., Python) |
| Assignment Name | Title of the assignment |
| Deadline | Date in `YYYY-MM-DD` format (e.g., `2026-09-30`) |
| Remind X days before | Number of days before deadline to send a reminder |

Click **➕ Add Assignment** to save.

### 📋 View Assignments Tab
Click **🔄 Refresh Assignments** to see all saved assignments with their status.

### ✅ Complete Assignment Tab
Enter the **Assignment ID** and click **✅ Mark Completed** to update its status.

### 🗑️ Delete Assignment Tab
Enter the **Assignment ID** and click **🗑️ Delete Assignment** to permanently remove it.

---

## 🔔 How Reminders Work

The `reminder.py` script checks all assignments in `deadlines.json` each time it runs:

| Condition | Action |
|---|---|
| Days remaining == `reminder_days` | Sends a **reminder** Telegram message |
| Days remaining == `0` | Sends a **"Deadline Today!"** Telegram message |
| Assignment is completed | Skipped — no reminder sent |
| Reminder already sent | Skipped — no duplicate sent |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `gradio` | Web UI framework |
| `python-telegram-bot` | Telegram bot API integration |

---

## 🗄️ Data Storage

Assignments are stored in `deadlines.json` using the following structure:

```json
[
    {
        "id": 1,
        "student_name": "Alice",
        "subject": "Python",
        "assignment_name": "Mini Project",
        "deadline": "2026-09-30",
        "chat_id": "1234567890",
        "reminder_days": 2,
        "completed": false,
        "reminder_sent": false
    }
]
```

---

## 🔒 Security Note

> ⚠️ **Do not share your Bot Token publicly.** It is recommended to store it as an environment variable rather than hardcoding it in `telegram_bot.py`.

---

## 📅 Automating Daily Reminders

### Windows — Task Scheduler

1. Open **Task Scheduler** → Create Basic Task
2. Set trigger to **Daily**
3. Set action to run:
   ```
   python "C:\path\to\FLEXI_CA_3_GRADIO\reminder.py"
   ```

### Linux / macOS — Cron Job

```bash
crontab -e
# Add this line to run every day at 8:00 AM:
0 8 * * * python /path/to/FLEXI_CA_3_GRADIO/reminder.py
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `❌ Chat ID not found` | Add `Chat ID: <your_id>` to `Imp.txt` |
| `❌ Telegram error` | Check your Bot Token and internet connection |
| `❌ Invalid date format` | Use `YYYY-MM-DD` format (e.g., `2026-09-30`) |
| App won't start | Run `pip install gradio python-telegram-bot` |
| No reminders received | Run `python reminder.py` manually and check output |

---

## 👨‍💻 Author

Built as part of **FLEXI CA 3** — a student assignment deadline reminder system powered by Gradio and Telegram.
