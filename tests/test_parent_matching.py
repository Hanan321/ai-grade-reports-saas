import pandas as pd

from engine.parent_matching import match_reports_to_parent_contacts, matches_to_dataframe
from engine.report_files import StudentReportFile


def _report(student_name, student_id="", filename="report.html"):
    return StudentReportFile(
        student_name=student_name,
        student_id=student_id,
        filename=filename,
        content=b"<html>report</html>",
    )


def test_matches_by_student_id_before_name():
    reports = [_report("Ali Ahmed", "201", "ali.html")]
    contacts = pd.DataFrame(
        [
            {
                "student_name": "Different Name",
                "student_id": "201",
                "parent_email": "parent@example.com",
                "parent_name": "Parent",
            }
        ]
    )

    matches = match_reports_to_parent_contacts(reports, contacts)

    assert matches[0].send_eligible is True
    assert matches[0].parent_email == "parent@example.com"
    assert matches[0].match_result == "matched_by_student_id"


def test_falls_back_to_normalized_student_name():
    reports = [_report("  Aisha   Ali  ", "", "aisha.html")]
    contacts = pd.DataFrame(
        [
            {
                "student_name": "aisha ali",
                "parent_email": "parent@example.com",
            }
        ]
    )

    matches = match_reports_to_parent_contacts(reports, contacts)

    assert matches[0].send_eligible is True
    assert matches[0].match_result == "matched_by_student_name"


def test_multiple_parent_contacts_for_same_student_are_sendable():
    reports = [_report("Ali Ahmed", "", "ali.html")]
    contacts = pd.DataFrame(
        [
            {"student_name": "Ali Ahmed", "parent_email": "mother@example.com", "parent_name": "Mother"},
            {"student_name": " ali  ahmed ", "parent_email": "father@example.com", "parent_name": "Father"},
        ]
    )

    matches = match_reports_to_parent_contacts(reports, contacts)

    assert len(matches) == 2
    assert all(match.send_eligible for match in matches)
    assert {match.parent_email for match in matches} == {"mother@example.com", "father@example.com"}


def test_duplicate_same_parent_email_is_deduped_for_one_student():
    reports = [_report("Ali Ahmed", "", "ali.html")]
    contacts = pd.DataFrame(
        [
            {"student_name": "Ali Ahmed", "parent_email": "parent@example.com", "parent_name": "One"},
            {"student_name": " ali  ahmed ", "parent_email": "parent@example.com", "parent_name": "Two"},
        ]
    )

    matches = match_reports_to_parent_contacts(reports, contacts)

    assert len(matches) == 1
    assert matches[0].send_eligible is True
    assert matches[0].parent_email == "parent@example.com"


def test_unmatched_report_is_marked_and_displayed():
    reports = [_report("No Match", "999", "none.html")]
    contacts = pd.DataFrame([{"student_name": "Ali Ahmed", "parent_email": "parent@example.com"}])

    preview = matches_to_dataframe(match_reports_to_parent_contacts(reports, contacts))

    assert preview.loc[0, "match_result"] == "unmatched"
    assert not bool(preview.loc[0, "send_eligible"])
