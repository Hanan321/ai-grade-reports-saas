"""SMTP email delivery for parent report batches."""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import smtplib
import ssl

from engine.parent_matching import ReportParentMatch


DEFAULT_SUBJECT_TEMPLATE = "Student Progress Report - {student_name}"
DEFAULT_BODY_TEMPLATE = """Dear Parent/Guardian,

Please find attached the latest progress report for {student_name}.

Thank you,
School Team
"""


@dataclass(frozen=True)
class SmtpConfig:
    """SMTP configuration loaded from environment variables or Streamlit secrets."""

    host: str
    port: int
    sender_email: str
    username: str = ""
    password: str = ""
    use_tls: bool = True
    use_ssl: bool = False


@dataclass(frozen=True)
class EmailSendResult:
    """Delivery result for one report email."""

    student_name: str
    parent_email: str
    report_filename: str
    status: str
    message: str


def send_parent_report_batch(
    matches: list[ReportParentMatch],
    smtp_config: SmtpConfig,
    subject_template: str = DEFAULT_SUBJECT_TEMPLATE,
    body_template: str = DEFAULT_BODY_TEMPLATE,
    override_recipient: str | None = None,
    max_messages: int | None = None,
) -> list[EmailSendResult]:
    """Send all eligible matched reports in one SMTP batch."""

    eligible_matches = [match for match in matches if match.send_eligible]
    if max_messages is not None:
        eligible_matches = eligible_matches[:max_messages]

    results: list[EmailSendResult] = []
    if not eligible_matches:
        return results

    with _smtp_client(smtp_config) as server:
        if smtp_config.username and smtp_config.password:
            server.login(smtp_config.username, smtp_config.password)

        for match in eligible_matches:
            recipient = override_recipient or match.parent_email
            try:
                message = build_parent_report_message(
                    match,
                    sender=smtp_config.sender_email,
                    recipient=recipient,
                    subject_template=subject_template,
                    body_template=body_template,
                    test_mode=override_recipient is not None,
                )
                server.send_message(message)
                results.append(
                    EmailSendResult(
                        student_name=match.student_name,
                        parent_email=recipient,
                        report_filename=match.report_filename,
                        status="sent",
                        message="Email sent.",
                    )
                )
            except Exception as exc:
                results.append(
                    EmailSendResult(
                        student_name=match.student_name,
                        parent_email=recipient,
                        report_filename=match.report_filename,
                        status="failed",
                        message=str(exc),
                    )
                )

    return results


def build_parent_report_message(
    match: ReportParentMatch,
    sender: str,
    recipient: str,
    subject_template: str = DEFAULT_SUBJECT_TEMPLATE,
    body_template: str = DEFAULT_BODY_TEMPLATE,
    test_mode: bool = False,
) -> EmailMessage:
    """Build one parent report email with the HTML report attached."""

    subject = subject_template.format(student_name=match.student_name, student_id=match.student_id)
    body = body_template.format(student_name=match.student_name, student_id=match.student_id)
    if test_mode:
        subject = f"[TEST] {subject}"
        body = (
            "Test batch delivery. This message was sent to the configured test/admin email "
            "instead of the saved parent address.\n\n"
            f"Original parent recipient: {match.parent_email}\n\n"
            f"{body}"
        )

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    message.add_attachment(
        match.report.content,
        maintype="text",
        subtype="html",
        filename=match.report_filename,
    )
    return message


def _smtp_client(smtp_config: SmtpConfig):
    if smtp_config.use_ssl:
        return smtplib.SMTP_SSL(smtp_config.host, smtp_config.port, timeout=30)

    client = smtplib.SMTP(smtp_config.host, smtp_config.port, timeout=30)
    if smtp_config.use_tls:
        client.starttls(context=ssl.create_default_context())
    return client
