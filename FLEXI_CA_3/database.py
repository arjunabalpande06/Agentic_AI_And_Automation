import sqlite3

DATABASE_NAME = "reminders.db"


def create_database():
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            email TEXT NOT NULL,
            task TEXT NOT NULL,
            deadline TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def add_reminder(student_name, email, task, deadline):
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO reminders
        (student_name, email, task, deadline)
        VALUES (?, ?, ?, ?)
    """, (student_name, email, task, deadline))

    connection.commit()
    connection.close()


def get_reminders():
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, student_name, email, task, deadline
        FROM reminders
        ORDER BY deadline
    """)

    data = cursor.fetchall()

    connection.close()

    return data


def delete_reminder(reminder_id):
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM reminders WHERE id = ?",
        (reminder_id,)
    )

    connection.commit()
    connection.close()