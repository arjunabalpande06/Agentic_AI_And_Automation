import json
import os
import asyncio

from datetime import datetime, date

from telegram_bot import send_telegram_message


DATA_FILE = "deadlines.json"


def load_deadlines():

    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_deadlines(data):

    with open(DATA_FILE, "w") as file:
        json.dump(
            data,
            file,
            indent=4
        )


async def check_deadlines():

    data = load_deadlines()

    today = date.today()

    changed = False

    for item in data:

        # Skip completed assignments
        if item.get("completed", False):
            continue

        deadline = datetime.strptime(
            item["deadline"],
            "%Y-%m-%d"
        ).date()

        days_remaining = (
            deadline - today
        ).days

        reminder_days = item.get("reminder_days", 1)

        # -------------------------------------------------
        # SEND REMINDER (before deadline)
        # -------------------------------------------------

        if days_remaining == reminder_days and reminder_days > 0 and not item.get("reminder_sent", False):

            message = (
                "🔔 ASSIGNMENT REMINDER\n\n"

                f"Hello {item['student_name']}! 👋\n\n"

                f"📚 Subject: {item['subject']}\n"
                f"📝 Assignment: "
                f"{item['assignment_name']}\n\n"

                f"📅 Deadline: "
                f"{item['deadline']}\n\n"

                f"⏰ Only {days_remaining} "
                f"day(s) remaining!\n\n"

                "Don't forget to submit your "
                "assignment. 💪"
            )

            try:

                await send_telegram_message(
                    item["chat_id"],
                    message
                )

                print(
                    f"Reminder sent for "
                    f"{item['assignment_name']}"
                )

                item["reminder_sent"] = True

                changed = True

            except Exception as e:

                print(
                    "Telegram error:",
                    e
                )

        # -------------------------------------------------
        # DEADLINE TODAY
        # -------------------------------------------------

        elif days_remaining == 0 and not item.get("today_reminder_sent", False):

            message = (
                "🚨 DEADLINE TODAY!\n\n"

                f"Hello {item['student_name']}!\n\n"

                f"📝 Assignment: "
                f"{item['assignment_name']}\n"

                f"📚 Subject: "
                f"{item['subject']}\n\n"

                "⚠️ Your assignment is due TODAY!\n\n"

                "Please submit it before the deadline."
            )

            try:

                await send_telegram_message(
                    item["chat_id"],
                    message
                )

                print(
                    f"Deadline reminder sent for "
                    f"{item['assignment_name']}"
                )

                item["today_reminder_sent"] = True

                changed = True

            except Exception as e:

                print(
                    "Telegram error:",
                    e
                )

    if changed:

        save_deadlines(data)


if __name__ == "__main__":

    asyncio.run(
        check_deadlines()
    )