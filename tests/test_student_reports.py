from io import BytesIO
from zipfile import ZipFile

import pandas as pd

from config.default_config import ReportBrandingConfig
from engine.student_reports import build_student_report_html, export_student_reports_zip


def test_build_student_report_html_contains_parent_facing_fields():
    df = pd.DataFrame(
        {
            "student_id": [201],
            "student_name": ["Ali Ahmed"],
            "grade": [7],
            "subject": ["Math"],
            "homework": [85],
            "quizscore": [78],
            "exam_score": [92],
            "attendance_percent": [88],
            "final_score": [85.7],
            "at_risk": [False],
            "low_attendance": [False],
            "notes": ["good progress"],
        }
    )

    html = build_student_report_html(df)

    assert "Ali Ahmed" in html
    assert "Assessment Details" in html
    assert "good progress" in html


def test_build_student_report_html_applies_report_branding():
    df = pd.DataFrame(
        {
            "student_id": [201],
            "student_name": ["Ali Ahmed"],
            "final_score": [85.7],
            "attendance_percent": [88],
            "at_risk": [False],
            "low_attendance": [False],
        }
    )
    branding = ReportBrandingConfig(
        report_title="Demo School Report",
        header_text="Official progress update",
        footer_text="Demo School footer",
    )

    html = build_student_report_html(df, report_branding=branding)

    assert "Demo School Report" in html
    assert "Official progress update" in html
    assert "Demo School footer" in html


def test_export_student_reports_zip_creates_one_html_file_per_student():
    df = pd.DataFrame(
        {
            "student_id": [201, 202],
            "student_name": ["Ali Ahmed", "Aisha Ali"],
            "final_score": [85.7, 90.0],
            "attendance_percent": [88, 95],
            "at_risk": [False, False],
            "low_attendance": [False, False],
        }
    )

    zip_bytes = export_student_reports_zip(df)

    with ZipFile(BytesIO(zip_bytes)) as archive:
        names = archive.namelist()
        assert len(names) == 2
        assert all(name.endswith(".html") for name in names)
        assert "Ali Ahmed" in archive.read(names[0]).decode("utf-8")
