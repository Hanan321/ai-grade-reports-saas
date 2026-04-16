"""Persistent email settings stored in a local JSON file."""

from __future__ import annotations

import json
from pathlib import Path

from engine.storage import EMAIL_SETTINGS_PATH, ensure_data_dir


EMAIL_SETTING_FIELDS = (
    "host",
    "port",
    "sender",
    "username",
    "password",
    "use_tls",
    "use_ssl",
    "test_email",
)

DEFAULT_EMAIL_SETTINGS: dict[str, str] = {
    "host": "",
    "port": "587",
    "sender": "",
    "username": "",
    "password": "",
    "use_tls": "true",
    "use_ssl": "false",
    "test_email": "",
}


def load_email_settings(path: Path = EMAIL_SETTINGS_PATH) -> dict[str, str]:
    """Load persisted email settings, returning defaults when missing or incomplete."""

    if not path.exists():
        return DEFAULT_EMAIL_SETTINGS.copy()

    try:
        raw_settings = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return DEFAULT_EMAIL_SETTINGS.copy()

    settings = DEFAULT_EMAIL_SETTINGS.copy()
    for field in EMAIL_SETTING_FIELDS:
        settings[field] = str(raw_settings.get(field, settings[field])).strip()
    return settings


def save_email_settings(settings: dict[str, object], path: Path = EMAIL_SETTINGS_PATH) -> None:
    """Persist email settings to a local JSON file."""

    ensure_data_dir()
    cleaned = DEFAULT_EMAIL_SETTINGS.copy()
    for field in EMAIL_SETTING_FIELDS:
        value = settings.get(field, cleaned[field])
        if field in {"use_tls", "use_ssl"} and isinstance(value, bool):
            cleaned[field] = "true" if value else "false"
        else:
            cleaned[field] = str(value).strip()
    path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")


def email_settings_exist(path: Path = EMAIL_SETTINGS_PATH) -> bool:
    """Return True when the email settings file exists."""

    return path.exists()
