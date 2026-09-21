import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_FILE = os.path.join(BASE_DIR, "deadlines.json")


def get_data_file_path():
    """Returns path to the local deadlines.json file."""
    if os.path.exists("deadlines.json"):
        return "deadlines.json"
    return DEFAULT_DATA_FILE


def load_deadlines():
    """Loads deadlines from local deadlines.json file."""
    file_path = get_data_file_path()
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_deadlines(data):
    """Saves deadlines to local deadlines.json file."""
    file_path = get_data_file_path()
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        return True
    except OSError as e:
        print(f"File save error ({file_path}):", e)
        return False