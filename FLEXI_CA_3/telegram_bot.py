import os
from telegram import Bot
from telegram.request import HTTPXRequest
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


def get_telegram_bot():
    bot_token = get_bot_token()
    if not bot_token:
        return None

    proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    request_client = HTTPXRequest(proxy=proxy) if proxy else None

    base_url = os.getenv("TELEGRAM_API_BASE_URL")
    if base_url:
        return Bot(token=bot_token, base_url=base_url, request=request_client)
    return Bot(token=bot_token, request=request_client)


async def send_telegram_message(chat_id, message):
    bot = get_telegram_bot()
    if not bot:
        print("Warning: TELEGRAM_BOT_TOKEN is not set. Message not sent.")
        return False

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message
        )
        return True
    except Exception as e:
        error_msg = str(e)
        if "ConnectError" in error_msg or "Connection reset" in error_msg:
            print("Telegram Connection Error: Your network/ISP or Wi-Fi is blocking access to api.telegram.org.")
            print("Tip: Try connecting to a Mobile Hotspot or using a VPN (e.g. Cloudflare 1.1.1.1 WARP).")
        else:
            print(f"Telegram error: {e}")
        raise e


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