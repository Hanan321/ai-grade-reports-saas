"""Validation helpers for email delivery."""

from __future__ import annotations

import re


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: object) -> bool:
    """Return True when value looks like a usable email address."""

    if value is None:
        return False
    email = str(value).strip()
    return bool(email and EMAIL_PATTERN.match(email))
