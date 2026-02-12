# authorization.py
import os
import json
import subprocess
from datetime import datetime, date
from action_execution import run_action_execution

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AUDIT_FILE = os.path.join(BASE_DIR, "audit_log.txt")
DUE_DATES_FILE = os.path.join(BASE_DIR, "due_dates.json")
DB_FILE = os.path.join(BASE_DIR, "class_database.json")

RED = "\033[31m"
GRAY = "\033[90m"
RESET = "\033[0m"


def _get_group_number_from_filename(filename):
    return int(filename.replace("group", "").replace(".txt", ""))


def _normalize_group_value(group_value):
    try:
        return int(float(group_value))
    except Exception:
        return None


def _load_users_from_db(path=DB_FILE):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("users", [])


def _open_database_file(path=DB_FILE):
    try:
        os.startfile(path)
    except Exception:
        try:
            subprocess.Popen(["notepad.exe", path])
        except Exception:
            print("Open this file manually:", path)


def _print_class_roster():
    users = _load_users_from_db(DB_FILE)

    instructors = [
        u.get("login") for u in users
        if str(u.get("role", "")).strip().lower() == "instructor"
    ]

    group_map = {}
    for u in users:
        role = str(u.get("role", "")).strip().lower()
        if role != "student":
            continue
        g = _normalize_group_value(u.get("group"))
        if g is None:
            continue
        group_map.setdefault(g, []).append(u.get("login"))

    print("\nInstructor:")
    for name in sorted([x for x in instructors if x]):
        print("    " + str(name))

    for g in sorted(group_map.keys()):
        print(f"\nGroup{g}:")
        for name in sorted([x for x in group_map[g] if x]):
            print("    " + str(name))


def _parse_due_date(due_str):
    if not due_str or str(due_str).upper() in ["TBD", "N/A"]:
        return None
    s = str(due_str).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _days_left(due_str):
    d = _parse_due_date(due_str)
    if not d:
        return None
    return (d - date.today()).days


def _due_status(due_str):
    left = _days_left(due_str)
    if left is None:
        return "NORMAL", ""
    if left < 0:
        return "CLOSED", "(closed)"
    if left <= 7:
        if left == 0:
            return "SOON", "(due today)"
        if left == 1:
            return "SOON", "(1 day left)"
        return "SOON", f"({left} days left)"
    return "NORMAL", ""


def _load_due_dates(path=DUE_DATES_FILE):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _parse_audit_log(audit_path=AUDIT_FILE):
    if not os.path.exists(audit_path):
        return {}

    last_updates = {}
    current = {}

    def commit():
        raw_fname = current.get("file")
        tstr = current.get("time")
        user = current.get("user")
        if not (raw_fname and tstr and user):
            return

        fname = os.path.basename(str(raw_fname).strip())

        try:
            t = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return

        if fname not in last_updates or t > last_updates[fname][1]:
            last_updates[fname] = (user, t, tstr)

    with open(audit_path, "r", encoding="utf-8") as f:
        for line in map(str.strip, f):
            if line == "----- AUDIT ENTRY -----":
                current = {}
            elif line == "-----------------------":
                commit()
                current = {}
            elif line.startswith("Time:"):
                current["time"] = line.replace("Time:", "").strip()
            elif line.startswith("User:"):
                current["user"] = line.replace("User:", "").strip()
            elif line.startswith("File:"):
                raw_file = line.replace("File:", "").strip()
                current["file"] = os.path.basename(raw_file)

    commit()
    return {k: (v[0], v[2]) for k, v in last_updates.items()}


def show_group_files(user):
    role = str(user.get("role", "")).strip().lower()

    if role == "admin":
        _print_class_roster()
        choice = input("\nDo you want to edit group membership now? (y/n): ").strip().lower()
        if choice == "y":
            _open_database_file(DB_FILE)
        return None

    group_files = []
    for f in os.listdir(BASE_DIR):
        if f.startswith("group") and f.endswith(".txt"):
            if f.replace("group", "").replace(".txt", "").isdigit():
                group_files.append(f)

    group_files.sort(key=_get_group_number_from_filename)

    last_info = _parse_audit_log(AUDIT_FILE)
    due_dates = _load_due_dates(DUE_DATES_FILE)

    print("\nAvailable Group Files:\n")
    print(
        f"{'No':<4}"
        f"{'File':<16}"
        f"{'Group':<10}"
        f"{'Last Updated By':<18}"
        f"{'Last Updated At':<20}"
        f"{'Due Date'}"
    )
    print("-" * 100)

    status_map = {}

    for i, filename in enumerate(group_files, start=1):
        group_name = f"Group{_get_group_number_from_filename(filename)}"
        last_user, last_time = last_info.get(filename, ("N/A", "N/A"))
        due_date = due_dates.get(filename, "TBD")

        status, extra = _due_status(due_date)
        status_map[i] = status

        d = _parse_due_date(due_date)
        if d:
            due_display = d.strftime("%Y-%m-%d")
        else:
            due_display = str(due_date)

        if status in ["SOON", "CLOSED"] and extra:
            due_display = f"{due_display} {extra}"

        row = (
            f"{i:<4}"
            f"{filename:<16}"
            f"{group_name:<10}"
            f"{last_user:<18}"
            f"{last_time:<20}"
            f"{due_display:<30}"
        )

        if status == "SOON":
            print(RED + row + RESET)
        elif status == "CLOSED":
            print(GRAY + row + RESET)
        else:
            print(row)

    if not group_files:
        return None

    while True:
        choice = input("\nSelect a file number to work with: ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(group_files):
                return group_files[idx - 1], status_map[idx]
        print("Invalid selection.")


def open_group_file_with_permission(user, selection):
    filename, status = selection
    role = str(user.get("role", "")).strip().lower()
    user_group = _normalize_group_value(user.get("group"))
    file_group = _get_group_number_from_filename(filename)

    closed = (status == "CLOSED")

    if role == "instructor":
        mode = "FULL"
    elif closed:
        mode = "VIEW"
    elif role == "student" and user_group == file_group:
        mode = "FULL"
    else:
        mode = "VIEW"

    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        print("File not found.")
        return

    print("\n" + "-" * 50)
    print("OPENING FILE:", filename)
    print("MODE:", "EDIT" if mode == "FULL" else "VIEW ONLY")
    print("-" * 50)

    with open(path, "r", encoding="utf-8") as f:
        print(f.read())

    if closed:
        print(RED + "\nProject is closed." + RESET)

    if closed and role != "instructor":
        return

    if mode == "FULL":
        run_action_execution(user, path)
    else:
        print("You don't have permission to edit this file.")


def authorize_and_open(user):
    result = show_group_files(user)
    if result:
        open_group_file_with_permission(user, result)
