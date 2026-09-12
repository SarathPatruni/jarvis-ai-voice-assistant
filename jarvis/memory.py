import json
from pathlib import Path

MEMORY_FILE = Path(__file__).resolve().parent.parent / "conversation.json"


def load_conversations():
    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            return data
        return []
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        try:
            if MEMORY_FILE.exists():
                MEMORY_FILE.write_text("[]", encoding="utf-8")
        except OSError:
            pass
        return []


def save_conversation(user_command, jarvis_reply):
    try:
        history = load_conversations()
        history.append({
            "user": user_command,
            "jarvis": jarvis_reply,
        })
        with MEMORY_FILE.open("w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)
    except OSError:
        return False
    return True


def clear_conversations():
    try:
        with MEMORY_FILE.open("w", encoding="utf-8") as file:
            json.dump([], file, indent=4)
        return True
    except OSError:
        return False