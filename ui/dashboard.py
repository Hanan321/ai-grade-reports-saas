"""School-mode dashboard UI."""

from __future__ import annotations

import streamlit as st

from config.default_config import AppConfig
from engine.email_settings import email_settings_exist, load_email_settings
from engine.parent_contacts import load_saved_parent_contacts, saved_contacts_to_recipient_contacts
from engine.storage import EMAIL_SETTINGS_PATH, PARENT_CONTACTS_PATH


def _set_school_nav(page: str) -> None:
    """Switch the school-mode sidebar navigation on the next rerun."""

    st.session_state.school_nav = page


def render_school_dashboard(app_config: AppConfig) -> None:
    """Render a small school admin dashboard."""

    st.subheader("Dashboard")
    st.caption("Manage persistent school setup and then generate parent-ready reports.")

    contacts = load_saved_parent_contacts()
    recipients = saved_contacts_to_recipient_contacts(contacts)
    email_settings = load_email_settings()

    metric_cols = st.columns(3)
    metric_cols[0].metric("Saved Students", len(contacts))
    metric_cols[1].metric("Parent Emails", len(recipients))
    metric_cols[2].metric("Email Settings", "Saved" if email_settings_exist() else "Missing")

    st.markdown("**Quick Actions**")
    action_cols = st.columns(3)
    action_cols[0].button(
        "Go To Upload",
        use_container_width=True,
        on_click=_set_school_nav,
        args=("Upload & Reports",),
    )
    action_cols[1].button(
        "Manage Parent Contacts",
        use_container_width=True,
        on_click=_set_school_nav,
        args=("Parent Contacts",),
    )
    action_cols[2].button(
        "Email Settings",
        use_container_width=True,
        on_click=_set_school_nav,
        args=("Email Settings",),
    )

    st.markdown("**Storage**")
    st.write(f"Parent contacts: `{PARENT_CONTACTS_PATH}`")
    st.write(f"Email settings: `{EMAIL_SETTINGS_PATH}`")

    if not email_settings["host"] or not email_settings["sender"]:
        st.warning("Email settings are incomplete. Open Email Settings before sending reports.")

    if contacts.empty:
        st.info("No parent contacts saved yet. Open Parent Contacts to add students and parents.")

    st.caption(
        f"Active school mode: {app_config.branding.school_name or app_config.branding.app_name}"
    )
