import os
import asyncio
from telegram_bot import send_test_message


CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not CHAT_ID:
    print("❌ Error: TELEGRAM_CHAT_ID is not set in .env file.")
    exit(1)

asyncio.run(
    send_test_message(CHAT_ID)
)

print("Test message sent successfully!")