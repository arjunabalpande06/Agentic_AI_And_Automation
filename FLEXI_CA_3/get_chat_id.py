import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

base_dir = os.path.dirname(os.path.abspath(__file__))
for env_name in [".env", "example.env"]:
    env_path = os.path.join(base_dir, env_name)
    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)
load_dotenv(override=False)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN is not set in your .env file.")
    exit(1)


async def get_chat_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    chat_id = update.effective_chat.id

    print("Your Telegram Chat ID is:", chat_id)

    if update.message:
        await update.message.reply_text(
            f"👋 Hello! Your Telegram Chat ID is:\n`{chat_id}`",
            parse_mode="Markdown"
        )


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(
        filters.TEXT,
        get_chat_id
    )
)

print("Bot is running...")
print("Send a message to your Telegram bot.")

app.run_polling()