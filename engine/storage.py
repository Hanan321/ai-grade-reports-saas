"""Simple local file storage helpers for school-mode persistence."""

from __future__ import annotations

from pathlib import Path


DATA_DIR = Path("data")
PARENT_CONTACTS_PATH = DATA_DIR / "parent_contacts.csv"
EMAIL_SETTINGS_PATH = DATA_DIR / "email_settings.json"


def ensure_data_dir() -> Path:
    """Create the local data directory when it does not exist."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR
