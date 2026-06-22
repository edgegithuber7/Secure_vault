"""
Vault_details.py – ItemDetails dataclass with serialisation helpers.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

ITEM_TYPES: dict[str, str] = {
    "login": "Login",
    "note": "Secure Note",
    "card": "Card",
    "identity": "Identity",
}

TYPE_ICONS: dict[str, str] = {
    "login": "🔑",
    "note": "📝",
    "card": "💳",
    "identity": "👤",
}


class ItemDetails:
    def __init__(
        self,
        item_name: str = "",
        username: str = "",
        password: str = "",
        website: str = "",
        notes: str = "",
        last_edited: str = "",
        expiry: str = "",
        password_history: list | None = None,
        item_id: str = "",
        item_type: str = "login",
        folder: str = "",
        favourite: bool = False,
        tags: list | None = None,
        # Card fields
        card_number: str = "",
        card_holder: str = "",
        card_expiry_date: str = "",
        card_cvv: str = "",
        card_brand: str = "",
        # Identity fields
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        phone: str = "",
        address: str = "",
        created: str = "",
    ):
        self.item_id = item_id or str(uuid.uuid4())
        self.item_name = item_name
        self.username = username
        self.password = password
        self.website = website
        self.notes = notes
        self.last_edited = last_edited or datetime.now(timezone.utc).isoformat()
        self.created = created or self.last_edited
        self.expiry = expiry
        self.password_history: list = password_history or []
        self.item_type = item_type if item_type in ITEM_TYPES else "login"
        self.folder = folder
        self.favourite = favourite
        self.tags: list = tags or []
        # Card
        self.card_number = card_number
        self.card_holder = card_holder
        self.card_expiry_date = card_expiry_date
        self.card_cvv = card_cvv
        self.card_brand = card_brand
        # Identity
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.address = address

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "id": self.item_id,
            "item_name": self.item_name,
            "username": self.username,
            "password": self.password,
            "website": self.website,
            "notes": self.notes,
            "last_edited": self.last_edited,
            "created": self.created,
            "expiry": self.expiry,
            "password_history": self.password_history,
            "item_type": self.item_type,
            "folder": self.folder,
            "favourite": self.favourite,
            "tags": self.tags,
            "card_number": self.card_number,
            "card_holder": self.card_holder,
            "card_expiry_date": self.card_expiry_date,
            "card_cvv": self.card_cvv,
            "card_brand": self.card_brand,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ItemDetails":
        return cls(
            item_name=d.get("item_name", ""),
            username=d.get("username", ""),
            password=d.get("password", ""),
            website=d.get("website", ""),
            notes=d.get("notes", ""),
            last_edited=d.get("last_edited", ""),
            created=d.get("created", ""),
            expiry=d.get("expiry", ""),
            password_history=d.get("password_history", []),
            item_id=d.get("id", ""),
            item_type=d.get("item_type", "login"),
            folder=d.get("folder", ""),
            favourite=d.get("favourite", False),
            tags=d.get("tags", []),
            card_number=d.get("card_number", ""),
            card_holder=d.get("card_holder", ""),
            card_expiry_date=d.get("card_expiry_date", ""),
            card_cvv=d.get("card_cvv", ""),
            card_brand=d.get("card_brand", ""),
            first_name=d.get("first_name", ""),
            last_name=d.get("last_name", ""),
            email=d.get("email", ""),
            phone=d.get("phone", ""),
            address=d.get("address", ""),
        )

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def display_name(self) -> str:
        return self.item_name or self.username or "(Unnamed)"

    def type_icon(self) -> str:
        return TYPE_ICONS.get(self.item_type, "🔑")

    def is_expired(self) -> bool:
        if not self.expiry:
            return False
        try:
            exp = datetime.fromisoformat(self.expiry)
            return exp < datetime.now(timezone.utc)
        except ValueError:
            return False

    def subtitle(self) -> str:
        if self.item_type == "login":
            return self.username or self.website
        if self.item_type == "card":
            masked = f"**** {self.card_number[-4:]}" if len(self.card_number) >= 4 else self.card_number
            return masked or self.card_holder
        if self.item_type == "identity":
            return f"{self.first_name} {self.last_name}".strip()
        return "Secure Note"
