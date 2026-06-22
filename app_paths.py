"""
app_paths.py – Platform-aware paths for user data.

When running as a PyInstaller bundle the working directory is unreliable,
so vaults/ and users.txt must live in the OS app-data folder, not next to
the executable.
"""

from __future__ import annotations

import os
import platform

_SYSTEM = platform.system()


def get_data_dir() -> str:
    if _SYSTEM == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif _SYSTEM == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    path = os.path.join(base, "SecureVault")
    os.makedirs(path, exist_ok=True)
    return path


DATA_DIR   = get_data_dir()
VAULT_DIR  = os.path.join(DATA_DIR, "vaults")
USERS_FILE = os.path.join(DATA_DIR, "users.txt")
