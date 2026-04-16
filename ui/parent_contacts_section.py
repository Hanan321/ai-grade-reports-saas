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
from engine.parent_matching import normalize_student_id, normalize_student_name
from engine.report_files import StudentReportFile


def render_parent_contacts_section(reports: list[StudentReportFile]) -> None:
    """Render manual parent contact entry and management controls."""

    st.subheader("Manage Parent Contacts")
    st.caption(
        "Add or update saved parent contacts here. These saved contacts are reused for "
        "report matching and take priority over uploaded CSV contacts."
    )
    st.caption(f"Saved contacts file: `{SAVED_PARENT_CONTACTS_PATH}`")

    contacts = load_saved_parent_contacts()
    _render_contact_form(contacts, reports)
    contacts = load_saved_parent_contacts()

    st.markdown("**Saved Parent Contacts**")
    if contacts.empty:
        st.info("No saved parent contacts yet. Add one with the form above.")
    else:
        st.dataframe(contacts, use_container_width=True)
        _render_delete_contact(contacts)


def _render_contact_form(contacts: pd.DataFrame, reports: list[StudentReportFile]) -> None:
    st.markdown("**Add Or Update Contact**")
    st.caption(
        "The student ID and name should match a generated report. If the ID belongs to "
        "another generated student, the app will block the save."
    )
    with st.form("parent_contact_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        student_id = col1.text_input("Student ID", placeholder="Required")
        student_name = col2.text_input("Student name")
        parent_email = col1.text_input("Parent email")
        parent_name = col2.text_input("Parent name", placeholder="Optional")

        submitted = st.form_submit_button("Save Parent Contact")

    if not submitted:
        return

    report_conflict = _generated_report_id_conflict(reports, student_id, student_name)
    if report_conflict:
        st.error(
            f"Student ID {normalize_student_id(student_id)} belongs to {report_conflict} "
            "in the generated reports. Use the correct student ID for this student."
        )
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


def _generated_report_id_conflict(
    reports: list[StudentReportFile],
    student_id: object,
    student_name: object,
) -> str:
    typed_id = normalize_student_id(student_id)
    typed_name = normalize_student_name(student_name)
    if not typed_id:
        return ""

    for report in reports:
        report_id = normalize_student_id(report.student_id)
        report_name = normalize_student_name(report.student_name)
        if report_id == typed_id and report_name != typed_name:
            return report.student_name
    return ""
