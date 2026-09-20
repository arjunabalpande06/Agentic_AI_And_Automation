import os
from telegram import Bot
from dotenv import load_dotenv

# Load local environment files if present
base_dir = os.path.dirname(os.path.abspath(__file__))
for env_name in [".env", "example.env"]:
    env_path = os.path.join(base_dir, env_name)
    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)
load_dotenv(override=False)


def get_bot_token():
    return os.getenv("TELEGRAM_BOT_TOKEN")


async def send_telegram_message(chat_id, message):
    bot_token = get_bot_token()
    if not bot_token:
        print("Warning: TELEGRAM_BOT_TOKEN is not set. Message not sent.")
        return False

    bot = Bot(token=bot_token)
    await bot.send_message(
        chat_id=chat_id,
        text=message
    )
    return True


async def send_test_message(chat_id):
    message = (
        "🔔 Student Deadline Reminder\n\n"
        "This is a test message.\n"
        "Your Telegram bot is working successfully! ✅"
    )
    return await send_telegram_message(
        chat_id,
        message
    )