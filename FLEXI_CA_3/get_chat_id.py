import os
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


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