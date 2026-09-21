# 📚 Student Deadline Reminder Automation with AI Assistant

A modern, **Gradio-based web application** that helps students track assignment deadlines and receive automated reminders via **Telegram**, enhanced with an **LLM-based AI Task & Deadline Assistant** powered by **Groq API** (`openai/gpt-oss-120b`).

---

## 🚀 Features

- 🤖 **AI Task & Deadline Assistant** — Enter deadlines in natural language (e.g., *"Remind me to submit my Python assignment on September 25 at 6 PM"*), and the AI automatically extracts the task name, date, time, and category.
- ➕ **Manual Assignment Creation** — Store student name, subject, assignment name, deadline date, and reminder preferences.
- 📋 **View Assignments** — List all saved assignments with their deadline time and current status (Pending / Completed).
- ✅ **Mark as Completed** — Easily update an assignment's status by ID.
- 🗑️ **Delete Assignments** — Remove assignments that are no longer needed.
- 🔔 **Automated Telegram Notifications** — Automatically sends deadline alerts directly to your Telegram chat.
- 📅 **Flexible Reminder Days** — Choose how many days before the deadline you want to be reminded.
- 🚨 **Same-day Alerts** — Sends an additional alert on the day the assignment is due.

---

## 🗂️ Project Structure

```
FLEXI_CA_3/
│
├── app.py                 # Main Gradio web application (UI & integration)
├── llm_service.py         # Groq LLM service (openai/gpt-oss-120b natural language parser)
├── reminder.py            # Deadline checker — sends Telegram reminders
├── telegram_bot.py        # Telegram bot helper (send messages)
├── database.py            # JSON database utilities (load & save)
├── deadlines.json         # JSON file storing all assignments
├── get_chat_id.py         # Utility to find your Telegram Chat ID
├── test_telegram.py       # Helper to test Telegram notification delivery
├── test_llm_service.py    # Unit test suite for AI Task Assistant
├── requirements.txt       # Python dependencies
├── example.env            # Template for environment variables (.env)
└── README.md              # Project documentation
```

---

## ⚙️ Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/arjunabalpande06/Agentic_AI_And_Automation.git
cd Agentic_AI_And_Automation/FLEXI_CA_3
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

*(Dependencies include: `gradio`, `python-telegram-bot`, `python-dotenv`, `groq`)*

### 3. Configure Environment Variables (`.env`)

Create a `.env` file in the `FLEXI_CA_3` directory (copy from `example.env`):

```env
# Telegram Bot Token (from @BotFather on Telegram)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Telegram Chat ID (found via python get_chat_id.py)
TELEGRAM_CHAT_ID=your_chat_id_here

# Groq API Key (from https://console.groq.com/keys)
GROQ_API_KEY=your_groq_api_key_here
```

> 🔒 **Security Notice:** Never commit your actual `.env` file to version control. It is already ignored by `.gitignore`.

---

## ▶️ Running the Application

### 1. Launch the Gradio Web App

```bash
python app.py
```

The app will start locally and open in your browser at:
`http://127.0.0.1:7860`

### 2. Run the Telegram Reminder Checker

To check deadlines and send automated alerts for due assignments:

```bash
python reminder.py
```

> **Automating Daily Reminders:**
> - **Windows:** Set up a Task Scheduler job to run `python reminder.py` once every morning.
> - **Linux / macOS:** Add a cron job (`0 8 * * * python /path/to/reminder.py`).

---

## 🖥️ How to Use the App

### 🤖 1. AI Task & Deadline Assistant Tab (New!)
Enter deadlines in plain, natural English. The system calculates exact dates based on your PC's current time and extracts structured task details.

**Example Inputs:**
- *"Remind me to submit my Python assignment on September 25 at 6 PM."*
- *"I have a project presentation next Friday at 10 AM."*
- *"Remind me about my CA record submission tomorrow at 5 PM."*

Click **⚡ Create Reminder**. The AI extracts the task, calculates the deadline, and immediately registers it into your reminder system.

> 💡 **Smart Missing Info Handling:** If you omit the date or time (e.g., *"Remind me to submit my assignment"*), the AI assistant will prompt you for the missing details rather than guessing or hallucinating dates.

### ➕ 2. Add Assignment Tab
Manually enter:
- Student Name
- Subject
- Assignment Name
- Deadline (`YYYY-MM-DD`)
- Reminder Days Before

### 📋 3. View Assignments Tab
Click **🔄 Refresh Assignments** to view all scheduled deadlines, times, categories, and completion status.

### ✅ 4. Complete Assignment Tab
Enter the **Assignment ID** and click **✅ Mark Completed**.

### 🗑️ 5. Delete Assignment Tab
Enter the **Assignment ID** and click **🗑️ Delete Assignment**.

---

## 🧪 Running Unit Tests

Run the automated test suite for the LLM service and validation layer:

```bash
python -m unittest test_llm_service.py
```

---

## 🔔 How Telegram Reminders Work

Each time `reminder.py` runs:
| Condition | Action |
|---|---|
| Days remaining == `reminder_days` | Sends advance reminder to Telegram |
| Days remaining == `0` | Sends urgent **"🚨 DEADLINE TODAY!"** alert |
| Assignment marked completed | Skipped |
| Reminder already sent | Skipped (prevents duplicate spam) |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `gradio` | Interactive web user interface |
| `groq` | Official Groq Python SDK for LLM integration (`openai/gpt-oss-120b`) |
| `python-telegram-bot` | Telegram bot messaging integration |
| `python-dotenv` | Secure environment variable configuration |

---

## 👨‍💻 Author

Built as part of **FLEXI CA 3** — Student Deadline Reminder Automation powered by Gradio, Telegram, and Groq LLM.
