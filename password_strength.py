"""
password_strength.py – Password entropy and quality analysis.
"""

from __future__ import annotations

import math
import re


class PasswordStrength:
    COMMON: frozenset[str] = frozenset({
        "password", "123456", "123456789", "qwerty", "abc123", "monkey",
        "1234567", "letmein", "trustno1", "dragon", "baseball", "iloveyou",
        "master", "sunshine", "ashley", "bailey", "passw0rd", "shadow",
        "123123", "654321", "superman", "qazwsx", "michael", "football",
        "admin", "welcome", "login", "hello", "charlie", "donald",
    })

    @staticmethod
    def analyse(password: str) -> dict:
        if not password:
            return {
                "score": 0, "level": "Very Weak", "colour": "#7f1d1d",
                "feedback": ["Enter a password."], "entropy": 0.0,
            }

        feedback: list[str] = []
        score = 0

        # --- Character set size ---
        pool = 0
        has_lower = bool(re.search(r"[a-z]", password))
        has_upper = bool(re.search(r"[A-Z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(re.search(r"[^a-zA-Z0-9]", password))

        if has_lower:
            pool += 26
        if has_upper:
            pool += 26
        if has_digit:
            pool += 10
        if has_special:
            pool += 32

        # --- Entropy ---
        entropy = math.log2(pool ** len(password)) if pool > 0 else 0.0
        score += min(30, int(entropy / 2))

        # --- Length bonus ---
        length = len(password)
        if length >= 8:
            score += 10
        if length >= 12:
            score += 10
        if length >= 16:
            score += 10
        if length >= 20:
            score += 10
        else:
            if length < 8:
                feedback.append("Use at least 8 characters.")
            elif length < 12:
                feedback.append("Consider using 12+ characters.")

        # --- Variety bonuses ---
        if has_lower and has_upper:
            score += 5
        elif not has_upper:
            feedback.append("Add uppercase letters.")
        if has_digit:
            score += 5
        else:
            feedback.append("Add numbers.")
        if has_special:
            score += 5
        else:
            feedback.append("Add special characters (!@#$%).")

        # --- Common password penalty ---
        if password.lower() in PasswordStrength.COMMON:
            score = max(0, score - 40)
            feedback.append("This is a commonly used password.")

        # --- Sequential characters ---
        sequences = 0
        for i in range(len(password) - 2):
            a, b, c = ord(password[i]), ord(password[i + 1]), ord(password[i + 2])
            if b - a == 1 and c - b == 1:
                sequences += 1
            elif a - b == 1 and b - c == 1:
                sequences += 1
        if sequences > 2:
            score = max(0, score - 10)
            feedback.append("Avoid sequential characters (abc, 123).")

        # --- Repeated characters ---
        repeats = len(re.findall(r"(.)\1{2,}", password))
        if repeats:
            score = max(0, score - 10)
            feedback.append("Avoid repeating characters.")

        score = min(100, score)

        if score < 20:
            level, colour = "Very Weak", "#7f1d1d"
        elif score < 40:
            level, colour = "Weak", "#ef4444"
        elif score < 60:
            level, colour = "Fair", "#f59e0b"
        elif score < 80:
            level, colour = "Strong", "#86efac"
        else:
            level, colour = "Very Strong", "#22c55e"

        if not feedback:
            feedback.append("Great password!")

        return {
            "score": score,
            "level": level,
            "colour": colour,
            "feedback": feedback,
            "entropy": round(entropy, 1),
        }
