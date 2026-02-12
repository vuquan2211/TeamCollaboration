# action_execution.py
import os
from datetime import datetime
import difflib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HISTORY_DIR = os.path.join(BASE_DIR, "history")
AUDIT_FILE = os.path.join(BASE_DIR, "audit_log.txt")


def capture_state(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def save_history(filename, before_text):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    base = os.path.splitext(os.path.basename(filename))[0]
    backup_path = os.path.join(HISTORY_DIR, f"{base}_{stamp}.txt")

    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(before_text)

    return backup_path


def generate_diff(before_text, after_text):
    before_lines = before_text.splitlines()
    after_lines = after_text.splitlines()

    diff_lines = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile="before",
        tofile="after",
        lineterm=""
    )

    diff_text = "\n".join(diff_lines)
    if diff_text.strip() == "":
        return "No changes."
    return diff_text


def create_audit_entry(user, filename, backup_path, diff_text):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = []
    entry.append("----- AUDIT ENTRY -----")
    entry.append(f"Time: {time_str}")
    entry.append(f"User: {user.get('login')}")
    entry.append(f"Role: {user.get('role')}")
    entry.append(f"File: {os.path.basename(filename)}")
    entry.append(f"Backup: {backup_path}")
    entry.append("Diff:")
    entry.append(diff_text)
    entry.append("-----------------------\n")

    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(entry))


def run_action_execution(user, filename):
    before_text = capture_state(filename)

    try:
        os.startfile(filename)
    except Exception:
        pass

    input("Edit the file in Notepad, save, then press ENTER here to continue...")

    after_text = capture_state(filename)

    if before_text == after_text:
        print("No changes detected. Nothing was updated.")
        return

    diff_text = generate_diff(before_text, after_text)
    backup_path = save_history(filename, before_text)
    create_audit_entry(user, filename, backup_path, diff_text)

    print(
        f"Saved. Updated by {user.get('login')} at "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
