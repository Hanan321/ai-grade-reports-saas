"""Streamlit UI for persistent school email settings."""

from __future__ import annotations

import streamlit as st

from engine.email_settings import load_email_settings, save_email_settings
from engine.storage import EMAIL_SETTINGS_PATH
from utils.email_validators import is_valid_email


def render_email_settings_section() -> None:
    """Render persistent SMTP settings for school mode."""

    st.subheader("Email Settings")
    st.caption(
        "Save SMTP settings for school mode so report sending can reuse them after refresh. "
        "Settings are stored locally in the data folder."
    )
    st.caption(f"Settings file: `{EMAIL_SETTINGS_PATH}`")

    settings = load_email_settings()
    with st.form("email_settings_form"):
        col1, col2 = st.columns([2, 1])
        host = col1.text_input("SMTP host", value=settings["host"], placeholder="smtp.gmail.com")
        port = col2.text_input("SMTP port", value=settings["port"] or "587")
        sender = st.text_input("Sender email", value=settings["sender"], placeholder="teacher@example.com")
        username = st.text_input("SMTP username", value=settings["username"], placeholder="teacher@example.com")
        password = st.text_input("SMTP password or app password", value=settings["password"], type="password")
        test_email = st.text_input("Test/admin email", value=settings["test_email"], placeholder="you@example.com")
        security = st.selectbox(
            "SMTP security",
            options=["STARTTLS", "SSL", "None"],
            index=_security_index(settings),
        )

        submitted = st.form_submit_button("Save Email Settings")

    if not submitted:
        return

    errors = _validate_settings(host, port, sender, test_email)
    if errors:
        for error in errors:
            st.error(error)
        return

    save_email_settings(
        {
            "host": host,
            "port": port,
            "sender": sender,
            "username": username,
            "password": password,
            "use_tls": "true" if security == "STARTTLS" else "false",
            "use_ssl": "true" if security == "SSL" else "false",
            "test_email": test_email,
        }
    )
    st.success("Email settings saved.")


def _security_index(settings: dict[str, str]) -> int:
    if settings["use_ssl"].lower() in {"1", "true", "yes", "on"}:
        return 1
    if settings["use_tls"].lower() in {"1", "true", "yes", "on"}:
        return 0
    return 2


def _validate_settings(host: str, port: str, sender: str, test_email: str) -> list[str]:
    errors: list[str] = []
    if not host.strip():
        errors.append("SMTP host is required.")
    if not sender.strip() or not is_valid_email(sender):
        errors.append("Sender email must be valid.")
    if test_email.strip() and not is_valid_email(test_email):
        errors.append("Test/admin email must be valid when provided.")
    try:
        int(port)
    except ValueError:
        errors.append("SMTP port must be a number.")
    return errors
