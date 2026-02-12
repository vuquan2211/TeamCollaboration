# login.py
import json
import os
from authorization import show_group_files, open_group_file_with_permission

MAX_ATTEMPTS = 3
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "class_database.json")


def load_users():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["users"]


def authenticate(users, login, password):
    for user in users:
        if user["login"] == login and user["password"] == password:
            return user
    return None


def login():
    print("=== LOGIN ===")
    users = load_users()

    attempts = 0
    while attempts < MAX_ATTEMPTS:
        username = input("Enter login: ").strip()
        password = input("Enter password: ").strip()

        user = authenticate(users, username, password)

        if user:
            print("\nLogin successful!")
            print(f"Login: {user.get('login')}")
            print(f"Role: {user.get('role')}")
            print(f"Group: {user.get('group')}")

            selected_file = show_group_files(user)
            if selected_file:
                open_group_file_with_permission(user, selected_file)
            return

        attempts += 1
        print(f"Invalid login ({attempts}/{MAX_ATTEMPTS})\n")

    print("Too many failed attempts. Program terminated.")


if __name__ == "__main__":
    login()
