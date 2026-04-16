"""Streamlit UI for matching and sending parent report emails."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from engine.email_delivery import (
    DEFAULT_BODY_TEMPLATE,
    DEFAULT_SUBJECT_TEMPLATE,
    SmtpConfig,
    send_parent_report_batch,
)
from engine.parent_contacts import load_saved_parent_contacts, merge_parent_contacts
from engine.parent_matching import (
    load_parent_contacts,
    match_reports_to_parent_contacts,
    matches_to_dataframe,
    normalize_student_id,
    normalize_student_name,
)
from engine.report_files import StudentReportFile
from utils.email_validators import is_valid_email


TEST_BATCH_LIMIT = 3


def render_email_section(reports: list[StudentReportFile]) -> None:
    """Render the parent email matching, preview, and send workflow."""

    st.subheader("Parent Report Emails")
    st.caption(
        "Match generated reports to your maintained parent-contact file, preview every row, "
        "then send the batch when it looks right."
    )

    contacts_df = _load_contacts_ui()
    if contacts_df is None:
        return

    try:
        matches = match_reports_to_parent_contacts(reports, contacts_df)
    except ValueError as exc:
        st.error(str(exc))
        return

    preview_df = matches_to_dataframe(matches)
    matched_count = int(preview_df["send_eligible"].sum()) if not preview_df.empty else 0
    unmatched_count = int((preview_df["match_result"] == "unmatched").sum()) if not preview_df.empty else 0
    skipped_count = len(preview_df) - matched_count

    metric_cols = st.columns(4)
    metric_cols[0].metric("Reports Generated", len(reports))
    metric_cols[1].metric("Matched Parents", matched_count)
    metric_cols[2].metric("Unmatched Students", unmatched_count)
    metric_cols[3].metric("Skipped Rows", skipped_count)

    st.dataframe(preview_df, use_container_width=True)
    _render_contacts_not_used_in_batch(contacts_df, reports)

    subject_template = st.text_input("Email subject", value=DEFAULT_SUBJECT_TEMPLATE)
    body_template = st.text_area("Email body", value=DEFAULT_BODY_TEMPLATE, height=180)

    smtp_config, test_email, config_errors = _render_email_config_ui()
    if config_errors:
        st.warning("Email sending is disabled until this configuration is complete:")
        for error in config_errors:
            st.write(f"- {error}")

    action_cols = st.columns(2)
    test_disabled = bool(config_errors) or matched_count == 0 or not test_email
    live_disabled = bool(config_errors) or matched_count == 0

    with action_cols[0]:
        if st.button(
            "Send Test Batch to Me",
            disabled=test_disabled,
            use_container_width=True,
        ):
            assert smtp_config is not None
            _send_batch(
                matches,
                smtp_config,
                subject_template,
                body_template,
                override_recipient=test_email,
                max_messages=TEST_BATCH_LIMIT,
                result_key="test_batch_results",
            )

    with action_cols[1]:
        if st.button(
            "Send All Parent Reports",
            type="primary",
            disabled=live_disabled,
            use_container_width=True,
        ):
            assert smtp_config is not None
            _send_batch(
                matches,
                smtp_config,
                subject_template,
                body_template,
                override_recipient=None,
                max_messages=None,
                result_key="live_batch_results",
            )

    if test_disabled and not test_email:
        st.info("Set TEST_PARENT_REPORT_EMAIL to enable safe test batches.")

    _render_send_results("Test Batch Results", st.session_state.get("test_batch_results"))
    _render_send_results("Parent Batch Results", st.session_state.get("live_batch_results"))


def _load_contacts_ui() -> pd.DataFrame | None:
    st.markdown("**Parent Contact Source**")
    st.caption(
        "Saved manual contacts are always included. You can optionally upload a CSV for "
        "this session; saved manual contacts take priority when the same student appears in both."
    )

    saved_contacts = load_saved_parent_contacts()
    uploaded_contacts = None
    include_upload = st.checkbox("Add an uploaded parent contacts CSV for this session")
    if include_upload:
        uploaded_contacts = st.file_uploader(
            "Upload parent contacts CSV",
            type=["csv"],
            key="parent_contacts_upload",
        )
        if uploaded_contacts is None:
            st.info("Upload a CSV with student_name, optional student_id, parent_email, and optional parent_name.")
        else:
            try:
                uploaded_contacts = load_parent_contacts(uploaded_contacts)
            except ValueError as exc:
                st.error(str(exc))
                return None

    combined_contacts = merge_parent_contacts(uploaded_contacts, saved_contacts)
    if combined_contacts.empty:
        st.warning("No parent contacts are available. Add saved contacts or upload a parent contacts CSV.")
        return None

    metric_cols = st.columns(3)
    metric_cols[0].metric("Saved Contacts", len(saved_contacts))
    metric_cols[1].metric("Uploaded Contacts", 0 if uploaded_contacts is None else len(uploaded_contacts))
    metric_cols[2].metric("Combined Contacts", len(combined_contacts))
    return combined_contacts


def _render_contacts_not_used_in_batch(
    contacts_df: pd.DataFrame,
    reports: list[StudentReportFile],
) -> None:
    unused_contacts = _contacts_not_matching_reports(contacts_df, reports)
    if unused_contacts.empty:
        return

    with st.expander("Saved/uploaded contacts not used in this batch"):
        st.caption(
            "These contacts are saved or uploaded, but they do not match any generated "
            "student report by student ID or normalized student name."
        )
        st.dataframe(unused_contacts, use_container_width=True)


def _contacts_not_matching_reports(
    contacts_df: pd.DataFrame,
    reports: list[StudentReportFile],
) -> pd.DataFrame:
    report_ids = {
        normalize_student_id(report.student_id)
        for report in reports
        if normalize_student_id(report.student_id)
    }
    report_names = {
        normalize_student_name(report.student_name)
        for report in reports
        if normalize_student_name(report.student_name)
    }
    unused_rows = []

    for _, row in contacts_df.iterrows():
        contact_id = normalize_student_id(row["student_id"])
        contact_name = normalize_student_name(row["student_name"])
        if (contact_id and contact_id in report_ids) or (contact_name and contact_name in report_names):
            continue
        unused_rows.append(row)

    if not unused_rows:
        return pd.DataFrame(columns=contacts_df.columns)
    return pd.DataFrame(unused_rows, columns=contacts_df.columns)


def _render_email_config_ui() -> tuple[SmtpConfig | None, str, list[str]]:
    st.markdown("**Email Sending Settings**")
    config_mode = st.radio(
        "Email configuration source",
        options=["Use saved secrets/environment", "Enter manually for this session"],
        horizontal=True,
    )

    saved_values = _saved_email_config_values()
    if config_mode == "Enter manually for this session":
        values = _manual_email_config_values(saved_values)
    else:
        values = saved_values
        st.caption("Using SMTP values from Streamlit secrets or environment variables.")

    return _build_smtp_config(values)


def _saved_email_config_values() -> dict[str, str]:
    return {
        "host": _config_value("SMTP_HOST"),
        "port": _config_value("SMTP_PORT", "587"),
        "sender": _config_value("SMTP_SENDER_EMAIL") or _config_value("SMTP_USERNAME"),
        "username": _config_value("SMTP_USERNAME"),
        "password": _config_value("SMTP_PASSWORD"),
        "use_tls": _config_value("SMTP_USE_TLS", "true"),
        "use_ssl": _config_value("SMTP_USE_SSL", "false"),
        "test_email": _config_value("TEST_PARENT_REPORT_EMAIL"),
    }


def _manual_email_config_values(saved_values: dict[str, str]) -> dict[str, str]:
    st.caption("Manual values are used for this Streamlit session only and are not saved to the repo.")
    col1, col2 = st.columns([2, 1])
    host = col1.text_input("SMTP host", value=saved_values["host"], placeholder="smtp.gmail.com")
    port = col2.text_input("SMTP port", value=saved_values["port"] or "587")

    sender = st.text_input(
        "Sender email",
        value=saved_values["sender"],
        placeholder="teacher@example.com",
    )
    username = st.text_input(
        "SMTP username",
        value=saved_values["username"],
        placeholder="teacher@example.com",
    )
    password = st.text_input(
        "SMTP password or app password",
        value=saved_values["password"],
        type="password",
    )
    test_email = st.text_input(
        "Test/admin email",
        value=saved_values["test_email"],
        placeholder="you@example.com",
    )

    security = st.selectbox(
        "SMTP security",
        options=["STARTTLS", "SSL", "None"],
        index=_security_index(saved_values),
    )

    return {
        "host": host,
        "port": port,
        "sender": sender,
        "username": username,
        "password": password,
        "use_tls": "true" if security == "STARTTLS" else "false",
        "use_ssl": "true" if security == "SSL" else "false",
        "test_email": test_email,
    }


def _build_smtp_config(values: dict[str, str]) -> tuple[SmtpConfig | None, str, list[str]]:
    host = values["host"].strip()
    port = values["port"].strip() or "587"
    sender = values["sender"].strip()
    username = values["username"].strip()
    password = values["password"].strip()
    use_tls = values["use_tls"].strip().lower() in {"1", "true", "yes", "on"}
    use_ssl = values["use_ssl"].strip().lower() in {"1", "true", "yes", "on"}
    test_email = values["test_email"].strip()

    errors: list[str] = []
    if not host:
        errors.append("SMTP_HOST is required.")
    if not sender or not is_valid_email(sender):
        errors.append("SMTP_SENDER_EMAIL must be a valid sender email.")
    if password and not username:
        errors.append("SMTP_USERNAME is required when SMTP_PASSWORD is set.")
    if test_email and not is_valid_email(test_email):
        errors.append("TEST_PARENT_REPORT_EMAIL must be a valid email when set.")

    try:
        parsed_port = int(port)
    except ValueError:
        parsed_port = 587
        errors.append("SMTP_PORT must be a number.")

    if errors:
        return None, test_email, errors

    return (
        SmtpConfig(
            host=host,
            port=parsed_port,
            sender_email=sender,
            username=username,
            password=password,
            use_tls=use_tls,
            use_ssl=use_ssl,
        ),
        test_email,
        [],
    )


def _security_index(values: dict[str, str]) -> int:
    use_ssl = values["use_ssl"].strip().lower() in {"1", "true", "yes", "on"}
    use_tls = values["use_tls"].strip().lower() in {"1", "true", "yes", "on"}
    if use_ssl:
        return 1
    if use_tls:
        return 0
    return 2


def _config_value(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is not None:
        return value.strip()

    try:
        secret_value = st.secrets.get(name, default)
    except Exception:
        secret_value = default
    return str(secret_value).strip()


def _send_batch(
    matches,
    smtp_config: SmtpConfig,
    subject_template: str,
    body_template: str,
    override_recipient: str | None,
    max_messages: int | None,
    result_key: str,
) -> None:
    try:
        results = send_parent_report_batch(
            matches,
            smtp_config,
            subject_template=subject_template,
            body_template=body_template,
            override_recipient=override_recipient,
            max_messages=max_messages,
        )
    except Exception as exc:
        st.error(f"Batch send could not start: {exc}")
        return

    st.session_state[result_key] = results
    sent_count = sum(1 for result in results if result.status == "sent")
    failed_count = sum(1 for result in results if result.status == "failed")
    st.success(f"Batch finished: {sent_count} sent, {failed_count} failed.")


def _render_send_results(title: str, results) -> None:
    if not results:
        return

    st.markdown(f"**{title}**")
    result_df = pd.DataFrame(
        [
            {
                "student_name": result.student_name,
                "recipient": result.parent_email,
                "report_filename": result.report_filename,
                "status": result.status,
                "message": result.message,
            }
            for result in results
        ]
    )
    sent_count = int((result_df["status"] == "sent").sum())
    failed_count = int((result_df["status"] == "failed").sum())
    cols = st.columns(2)
    cols[0].metric("Emails Sent Successfully", sent_count)
    cols[1].metric("Failed Sends", failed_count)
    st.dataframe(result_df, use_container_width=True)
