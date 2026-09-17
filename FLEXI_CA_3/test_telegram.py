import os
import asyncio
from telegram_bot import send_test_message


CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


asyncio.run(
    send_test_message(CHAT_ID)
)

print("Test message sent!")