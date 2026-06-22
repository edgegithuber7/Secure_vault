"""
vault_storage.py – Encrypted JSON vault storage per user.
Uses PBKDF2 + Fernet (AES-128-CBC) so the whole vault file is encrypted at rest.
"""

from __future__ import annotations

import base64
import csv
import io
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

VAULT_DIR = "vaults"
PBKDF2_ITERATIONS = 480_000


class WrongPasswordError(Exception):
    pass


class VaultStorage:
    def __init__(self, username: str, master_password: str):
        self.username = username
        os.makedirs(VAULT_DIR, exist_ok=True)
        self.vault_path = os.path.join(VAULT_DIR, f"{username}.vault")
        self.salt_path = os.path.join(VAULT_DIR, f"{username}.salt")
        self.fernet = self._get_fernet(master_password)
        self._data = self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_fernet(self, password: str) -> Fernet:
        if os.path.exists(self.salt_path):
            with open(self.salt_path, "rb") as f:
                salt = f.read()
        else:
            salt = os.urandom(16)
            with open(self.salt_path, "wb") as f:
                f.write(salt)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
        return Fernet(key)

    def _empty(self) -> dict:
        return {
            "version": "2.0",
            "items": [],
            "folders": ["Personal", "Work", "Finance", "Social"],
            "settings": {
                "auto_lock_minutes": 5,
                "clipboard_clear_seconds": 30,
                "confirm_delete": True,
                "default_sort": "name_asc",
                "list_density": "comfortable",
                "default_item_type": "login",
                "default_generator_length": 20,
                "default_generator_letters": True,
                "default_generator_numbers": True,
                "default_generator_special": True,
                "default_generator_exclude_ambiguous": False,
                "default_generator_passphrase_words": 4,
                "default_generator_passphrase_sep": "-",
                "default_generator_passphrase_cap": True,
                "default_generator_passphrase_num": True,
                "accent_color": "indigo",
                "theme": "dark",
            },
        }

    def _load(self) -> dict:
        if not os.path.exists(self.vault_path):
            return self._empty()
        with open(self.vault_path, "rb") as f:
            raw_enc = f.read()
        try:
            raw = self.fernet.decrypt(raw_enc)
        except InvalidToken as exc:
            raise WrongPasswordError("Master password is incorrect.") from exc
        return json.loads(raw.decode("utf-8"))

    # ------------------------------------------------------------------
    # Public persistence
    # ------------------------------------------------------------------

    def save(self) -> bool:
        raw = json.dumps(self._data, ensure_ascii=False).encode("utf-8")
        enc = self.fernet.encrypt(raw)
        with open(self.vault_path, "wb") as f:
            f.write(enc)
        return True

    # ------------------------------------------------------------------
    # Items CRUD
    # ------------------------------------------------------------------

    def all_items(self) -> list[dict]:
        return list(self._data["items"])

    def get_by_id(self, item_id: str) -> dict | None:
        for item in self._data["items"]:
            if item.get("id") == item_id:
                return item
        return None

    def add_item(self, item: dict) -> dict:
        if "id" not in item or not item["id"]:
            item["id"] = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item.setdefault("created", now)
        item.setdefault("last_edited", now)
        item.setdefault("favourite", False)
        item.setdefault("tags", [])
        item.setdefault("password_history", [])
        item.setdefault("folder", "")
        item.setdefault("item_type", "login")
        self._data["items"].append(item)
        self.save()
        return item

    def update_item(self, item_id: str, updates: dict) -> bool:
        for idx, item in enumerate(self._data["items"]):
            if item.get("id") == item_id:
                # Track password history
                old_pw = item.get("password", "")
                new_pw = updates.get("password", old_pw)
                if old_pw and new_pw != old_pw:
                    history: list = item.get("password_history", [])
                    history.insert(0, {"password": old_pw, "changed": datetime.now(timezone.utc).isoformat()})
                    updates["password_history"] = history[:10]
                updates["last_edited"] = datetime.now(timezone.utc).isoformat()
                self._data["items"][idx] = {**item, **updates}
                self.save()
                return True
        return False

    def delete_item(self, item_id: str) -> bool:
        before = len(self._data["items"])
        self._data["items"] = [i for i in self._data["items"] if i.get("id") != item_id]
        if len(self._data["items"]) < before:
            self.save()
            return True
        return False

    def toggle_favourite(self, item_id: str) -> bool | None:
        for item in self._data["items"]:
            if item.get("id") == item_id:
                item["favourite"] = not item.get("favourite", False)
                self.save()
                return item["favourite"]
        return None

    # ------------------------------------------------------------------
    # Filtering / search
    # ------------------------------------------------------------------

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for item in self._data["items"]:
            haystack = " ".join([
                item.get("item_name", ""),
                item.get("username", ""),
                item.get("website", ""),
                item.get("notes", ""),
                " ".join(item.get("tags", [])),
            ]).lower()
            if q in haystack:
                results.append(item)
        return results

    def by_type(self, item_type: str) -> list[dict]:
        return [i for i in self._data["items"] if i.get("item_type") == item_type]

    def by_folder(self, folder: str) -> list[dict]:
        return [i for i in self._data["items"] if i.get("folder") == folder]

    def favourites(self) -> list[dict]:
        return [i for i in self._data["items"] if i.get("favourite")]

    # ------------------------------------------------------------------
    # Folders
    # ------------------------------------------------------------------

    def get_folders(self) -> list[str]:
        return list(self._data.get("folders", []))

    def add_folder(self, name: str) -> bool:
        name = name.strip()
        if name and name not in self._data["folders"]:
            self._data["folders"].append(name)
            self.save()
            return True
        return False

    def rename_folder(self, old: str, new: str) -> bool:
        new = new.strip()
        if old not in self._data["folders"] or not new:
            return False
        idx = self._data["folders"].index(old)
        self._data["folders"][idx] = new
        for item in self._data["items"]:
            if item.get("folder") == old:
                item["folder"] = new
        self.save()
        return True

    def delete_folder(self, name: str) -> bool:
        if name not in self._data["folders"]:
            return False
        self._data["folders"].remove(name)
        for item in self._data["items"]:
            if item.get("folder") == name:
                item["folder"] = ""
        self.save()
        return True

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def get_settings(self) -> dict:
        return dict(self._data.get("settings", {}))

    def update_settings(self, updates: dict) -> None:
        self._data["settings"].update(updates)
        self.save()

    # ------------------------------------------------------------------
    # Health report
    # ------------------------------------------------------------------

    def vault_health(self) -> dict[str, Any]:
        from password_strength import PasswordStrength

        logins = self.by_type("login")
        passwords = [i.get("password", "") for i in logins if i.get("password")]

        weak: list[dict] = []
        reused: list[dict] = []
        old: list[dict] = []

        seen: dict[str, list[str]] = {}
        for item in logins:
            pw = item.get("password", "")
            if not pw:
                continue
            analysis = PasswordStrength.analyse(pw)
            if analysis["score"] < 50:
                weak.append({"id": item["id"], "name": item.get("item_name", ""), "score": analysis["score"]})
            seen.setdefault(pw, []).append(item.get("item_name", item["id"]))

        for pw, names in seen.items():
            if len(names) > 1:
                reused.extend({"password": pw, "name": n} for n in names)

        cutoff_days = 365
        now = datetime.now(timezone.utc)
        for item in logins:
            edited_str = item.get("last_edited", "")
            if edited_str:
                try:
                    edited = datetime.fromisoformat(edited_str)
                    if (now - edited).days > cutoff_days:
                        old.append({"id": item["id"], "name": item.get("item_name", "")})
                except ValueError:
                    pass

        total = len(logins)
        issues = len(weak) + len(reused) + len(old)
        score = max(0, 100 - int((issues / max(total, 1)) * 100))

        return {
            "total_logins": total,
            "total_items": len(self._data["items"]),
            "weak": weak,
            "reused": reused,
            "old": old,
            "overall_score": score,
        }

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def export_json(self) -> str:
        """Return a plaintext JSON export (unencrypted — for user download)."""
        export = {
            "exported": datetime.now(timezone.utc).isoformat(),
            "items": self._data["items"],
        }
        return json.dumps(export, indent=2, ensure_ascii=False)

    def export_csv(self) -> str:
        buf = io.StringIO()
        fieldnames = ["item_name", "username", "password", "website", "notes",
                      "item_type", "folder", "favourite", "tags"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in self._data["items"]:
            row = {k: item.get(k, "") for k in fieldnames}
            row["tags"] = ",".join(row["tags"]) if isinstance(row["tags"], list) else row["tags"]
            writer.writerow(row)
        return buf.getvalue()

    def duplicate_item(self, item_id: str) -> dict | None:
        item = self.get_by_id(item_id)
        if not item:
            return None
        import copy
        new_item = copy.deepcopy(item)
        new_item["id"] = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        new_item["created"] = now
        new_item["last_edited"] = now
        new_item["item_name"] = f"{new_item.get('item_name', '')} (Copy)"
        new_item["password_history"] = []
        self._data["items"].append(new_item)
        self.save()
        return new_item

    def recently_added(self, days: int = 7) -> list[dict]:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = []
        for item in self._data["items"]:
            created_str = item.get("created", "")
            if not created_str:
                continue
            try:
                created = datetime.fromisoformat(created_str)
                if created >= cutoff:
                    result.append(item)
            except ValueError:
                pass
        return sorted(result, key=lambda i: i.get("created", ""), reverse=True)

    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {"login": 0, "note": 0, "card": 0, "identity": 0}
        for item in self._data["items"]:
            t = item.get("item_type", "login")
            counts[t] = counts.get(t, 0) + 1
        return counts

    def import_csv(self, csv_text: str) -> int:
        reader = csv.DictReader(io.StringIO(csv_text))
        count = 0
        for row in reader:
            item = dict(row)
            item["tags"] = [t.strip() for t in item.get("tags", "").split(",") if t.strip()]
            item["favourite"] = str(item.get("favourite", "")).lower() in ("1", "true", "yes")
            self.add_item(item)
            count += 1
        return count
