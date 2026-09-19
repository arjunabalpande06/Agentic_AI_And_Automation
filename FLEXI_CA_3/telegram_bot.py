import os
from telegram import Bot
from dotenv import load_dotenv


load_dotenv("example.env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def send_telegram_message(chat_id, message):

    bot = Bot(token=BOT_TOKEN)

    await bot.send_message(
        chat_id=chat_id,
        text=message
    )


async def send_test_message(chat_id):

    message = (
        "🔔 Student Deadline Reminder\n\n"
        "This is a test message.\n"
        "Your Telegram bot is working successfully! ✅"
    )

    await send_telegram_message(
        chat_id,
        message
    )