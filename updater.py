"""
updater.py – Background update checker.

Fetches the latest GitHub Release tag and compares it against APP_VERSION.
Runs in a QThread so it never blocks the UI.  Emits update_available(str)
with the new version string when a newer release is found.
"""

from __future__ import annotations

import urllib.request
import urllib.error
import json

from PySide6.QtCore import QThread, Signal

APP_VERSION = "1.0.0"
RELEASES_URL = (
    "https://api.github.com/repos/edgegithuber7/Secure_vault/releases/latest"
)


def _parse_version(tag: str) -> tuple[int, ...]:
    """'v1.2.3' or '1.2.3'  →  (1, 2, 3)"""
    tag = tag.lstrip("v")
    try:
        return tuple(int(x) for x in tag.split("."))
    except ValueError:
        return (0,)


class UpdateChecker(QThread):
    """Fires update_available(new_version_str) when a newer release exists."""

    update_available = Signal(str)

    def run(self) -> None:
        try:
            req = urllib.request.Request(
                RELEASES_URL,
                headers={"User-Agent": f"SecureVault/{APP_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())

            tag: str = data.get("tag_name", "")
            if not tag:
                return

            if _parse_version(tag) > _parse_version(APP_VERSION):
                self.update_available.emit(tag.lstrip("v"))

        except Exception:
            pass   # silently ignore network errors, rate limits, etc.
