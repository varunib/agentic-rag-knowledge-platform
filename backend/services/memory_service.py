import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_FILE = os.path.join(BASE_DIR, "data", "memory.json")

print("Memory file path:", MEMORY_FILE)


def _load_memory():
    print("Loading memory...")

    if not os.path.exists(MEMORY_FILE):
        print("Memory file not found.")
        return {}

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        print("Loaded:", data)
        return data


def _save_memory(memory):
    print("Saving:", memory)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)

    print("Saved successfully.")


def save_message(session_id, role, content):

    print("save_message called")

    memory = _load_memory()

    if session_id not in memory:
        memory[session_id] = []

    memory[session_id].append(
        {
            "role": role,
            "content": content,
        }
    )

    _save_memory(memory)


def get_memory(session_id):

    memory = _load_memory()

    return memory.get(session_id, [])


def clear_memory(session_id):

    memory = _load_memory()

    memory[session_id] = []

    _save_memory(memory)