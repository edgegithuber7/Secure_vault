"""
Authentication.py – bcrypt-based user registration and login.
"""

from __future__ import annotations

import bcrypt

from app_paths import USERS_FILE


def check_cridentials(self, username: str, password: str) -> bool:
    try:
        with open(USERS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",", 1)
                if len(parts) != 2:
                    continue
                stored_user, stored_hash = parts[0], parts[1].encode()
                if stored_user == username:
                    return bcrypt.checkpw(password.encode(), stored_hash)
        return False
    except FileNotFoundError:
        return False


def register_user(username: str, password: str) -> bool:
    """Register a new user. Returns False if the username already exists."""
    username = username.strip()
    if not username or not password:
        return False
    try:
        with open(USERS_FILE, "r") as f:
            for line in f:
                if line.split(",", 1)[0] == username:
                    return False
    except FileNotFoundError:
        pass
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with open(USERS_FILE, "a") as f:
        f.write(f"{username},{hashed}\n")
    return True


def user_exists(username: str) -> bool:
    try:
        with open(USERS_FILE, "r") as f:
            for line in f:
                if line.split(",", 1)[0] == username.strip():
                    return True
    except FileNotFoundError:
        pass
    return False
