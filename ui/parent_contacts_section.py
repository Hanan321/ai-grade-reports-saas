"""Streamlit UI for manually managing saved parent contacts."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from engine.parent_contacts import (
    SAVED_PARENT_CONTACTS_PATH,
    delete_parent_contact,
    load_saved_parent_contacts,
    save_parent_contacts,
    upsert_parent_contact,
)


def render_parent_contacts_section() -> None:
    """Render manual parent contact entry and management controls."""

    st.subheader("Manage Parent Contacts")
    st.caption(
        "Add or update saved parent contacts here. These saved contacts are reused for "
        "report matching and take priority over uploaded CSV contacts."
    )
    st.caption(f"Saved contacts file: `{SAVED_PARENT_CONTACTS_PATH}`")

    contacts = load_saved_parent_contacts()
    _render_contact_form(contacts)
    contacts = load_saved_parent_contacts()

    st.markdown("**Saved Parent Contacts**")
    if contacts.empty:
        st.info("No saved parent contacts yet. Add one with the form above.")
    else:
        st.dataframe(contacts, use_container_width=True)
        _render_delete_contact(contacts)


def _render_contact_form(contacts: pd.DataFrame) -> None:
    st.markdown("**Add Or Update Contact**")
    with st.form("parent_contact_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        student_id = col1.text_input("Student ID", placeholder="Optional, but preferred")
        student_name = col2.text_input("Student name")
        parent_email = col1.text_input("Parent email")
        parent_name = col2.text_input("Parent name", placeholder="Optional")

        submitted = st.form_submit_button("Save Parent Contact")

    if not submitted:
        return

    updated_contacts, action, messages = upsert_parent_contact(
        contacts,
        student_id=student_id,
        student_name=student_name,
        parent_email=parent_email,
        parent_name=parent_name,
    )

    if action == "error":
        for message in messages:
            st.error(message)
        return

    save_parent_contacts(updated_contacts)
    if action == "updated":
        st.success("Parent contact updated.")
    else:
        st.success("Parent contact saved.")

    warning_messages = [message for message in messages if "recommended" in message]
    for message in warning_messages:
        st.warning(message)
    st.rerun()


def _render_delete_contact(contacts: pd.DataFrame) -> None:
    st.markdown("**Delete Contact**")
    contact_options = [
        _contact_option_label(index, row)
        for index, row in contacts.reset_index(drop=True).iterrows()
    ]
    selected_label = st.selectbox(
        "Choose a saved contact to delete",
        options=["Select a contact", *contact_options],
    )

    if selected_label == "Select a contact":
        return

    selected_index = contact_options.index(selected_label)
    selected_row = contacts.reset_index(drop=True).iloc[selected_index]
    if st.button("Delete Selected Contact"):
        updated_contacts, deleted = delete_parent_contact(
            contacts,
            student_id=selected_row["student_id"],
            student_name=selected_row["student_name"],
        )
        if deleted:
            save_parent_contacts(updated_contacts)
            st.success("Parent contact deleted.")
            st.rerun()
        else:
            st.error("Could not find that contact to delete.")


def _contact_option_label(index: int, row: pd.Series) -> str:
    student_id = str(row["student_id"]).strip() or "no ID"
    student_name = str(row["student_name"]).strip() or "Unnamed student"
    parent_email = str(row["parent_email"]).strip()
    return f"{index + 1}. {student_name} ({student_id}) - {parent_email}"
