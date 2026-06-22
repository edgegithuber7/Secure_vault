"""
Generator.py – Cryptographically secure password, passphrase, and username generator.
"""

from __future__ import annotations

import secrets
import string
from typing import List


class PasswordGenerator:
    _WORDS: List[str] = [
        "Swift", "Eagle", "Bold", "Lion", "River", "Storm", "Amber", "Frost",
        "Cedar", "Brave", "Coral", "Ember", "Flint", "Grove", "Haven", "Ivory",
        "Jade", "Kite", "Larch", "Maple", "Noble", "Opal", "Pearl", "Quest",
        "Ridge", "Sage", "Thorn", "Unity", "Valor", "Willow", "Xenon", "Yacht",
        "Zeal", "Blaze", "Cliff", "Dawn", "Echo", "Fern", "Gale", "Haze",
        "Iron", "Jewel", "Knox", "Lumen", "Mist", "Nova", "Orbit", "Pine",
    ]

    _ADJECTIVES: List[str] = [
        "swift", "bold", "brave", "calm", "dark", "eager", "fair", "glad",
        "happy", "keen", "kind", "lofty", "mild", "noble", "proud", "quick",
        "rare", "safe", "tall", "wise",
    ]

    _NOUNS: List[str] = [
        "wolf", "hawk", "bear", "fox", "deer", "owl", "crow", "lynx",
        "seal", "wren", "pike", "colt", "fawn", "toad", "moth", "gull",
        "koi", "ram", "puma", "ibis",
    ]

    def generate_password(
        self,
        length: int = 20,
        include_letters: bool = True,
        include_numbers: bool = True,
        include_special: bool = True,
        exclude_ambiguous: bool = False,
    ) -> str:
        if not any([include_letters, include_numbers, include_special]):
            include_letters = True

        ambiguous = "Il1O0"
        letters = string.ascii_letters
        digits = string.digits
        special = string.punctuation

        if exclude_ambiguous:
            letters = "".join(c for c in letters if c not in ambiguous)
            digits = "".join(c for c in digits if c not in ambiguous)
            special = "".join(c for c in special if c not in ambiguous)

        pool = ""
        required: list[str] = []

        if include_letters:
            pool += letters
            required.append(secrets.choice(letters))
        if include_numbers:
            pool += digits
            required.append(secrets.choice(digits))
        if include_special:
            pool += special
            required.append(secrets.choice(special))

        remaining = length - len(required)
        if remaining < 0:
            remaining = 0

        password_chars = required + [secrets.choice(pool) for _ in range(remaining)]

        # Shuffle without using random
        for i in range(len(password_chars) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

        return "".join(password_chars[:length])

    def generate_passphrase(
        self,
        word_count: int = 4,
        separator: str = "-",
        capitalise: bool = True,
        add_number: bool = True,
    ) -> str:
        words = [secrets.choice(self._WORDS) for _ in range(word_count)]
        if not capitalise:
            words = [w.lower() for w in words]
        phrase = separator.join(words)
        if add_number:
            phrase += separator + str(secrets.randbelow(90) + 10)
        return phrase

    def generate_username(self) -> str:
        adj = secrets.choice(self._ADJECTIVES)
        noun = secrets.choice(self._NOUNS)
        number = secrets.randbelow(900) + 100
        return f"{adj}{noun}{number}"
