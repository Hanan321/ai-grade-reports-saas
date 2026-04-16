import pandas as pd

from engine.email_delivery import build_parent_report_message
from engine.parent_matching import match_reports_to_parent_contacts
from engine.report_files import StudentReportFile


def test_build_parent_report_message_attaches_report_and_marks_test_mode():
    report = StudentReportFile(
        student_name="Ali Ahmed",
        student_id="201",
        filename="ali.html",
        content=b"<html>report</html>",
    )
    contacts = pd.DataFrame(
        [{"student_name": "Ali Ahmed", "student_id": "201", "parent_email": "parent@example.com"}]
    )
    match = match_reports_to_parent_contacts([report], contacts)[0]

    message = build_parent_report_message(
        match,
        sender="teacher@example.com",
        recipient="admin@example.com",
        test_mode=True,
    )

    assert message["To"] == "admin@example.com"
    assert message["Subject"] == "[TEST] Student Progress Report - Ali Ahmed"
    assert "Original parent recipient: parent@example.com" in message.get_body().get_content()
    assert len(list(message.iter_attachments())) == 1
