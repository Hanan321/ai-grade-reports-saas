"""Export helpers for downloadable report outputs."""

from __future__ import annotations

from io import BytesIO

import pandas as pd

from engine.filters import (
    get_at_risk_students,
    get_high_performing_students,
    get_low_attendance_students,
)
from engine.schemas import DEFAULT_CONFIG, GradeReportConfig
from utils.excel_formatting import format_report_workbook


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return a DataFrame as UTF-8 CSV bytes for downloads."""

    return df.to_csv(index=False).encode("utf-8")


def export_outputs(
    cleaned: pd.DataFrame,
    student_summary: pd.DataFrame,
    subject_summary: pd.DataFrame,
) -> dict[str, bytes]:
    """Build all standard CSV output files in memory."""

    return {
        "cleaned_grade_report.csv": dataframe_to_csv_bytes(cleaned),
        "summary_by_student.csv": dataframe_to_csv_bytes(student_summary),
        "summary_by_subject.csv": dataframe_to_csv_bytes(subject_summary),
    }


def export_excel_workbook(
    cleaned: pd.DataFrame,
    student_summary: pd.DataFrame,
    subject_summary: pd.DataFrame,
    warnings: list[str] | None = None,
    config: GradeReportConfig = DEFAULT_CONFIG,
) -> bytes:
    """Create a polished multi-sheet Excel workbook in memory."""

    at_risk = get_at_risk_students(cleaned)
    high_performers = get_high_performing_students(cleaned, config=config)
    low_attendance = get_low_attendance_students(cleaned)
    validation_summary = build_validation_summary_frame(warnings or [])

    sheets = {
        "Cleaned Data": cleaned,
        "Summary By Student": student_summary,
        "Summary By Subject": subject_summary,
        "At-Risk Students": at_risk,
        "High-Performing Students": high_performers,
        "Low Attendance Students": low_attendance,
        "Validation Summary": validation_summary,
    }

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, dataframe in sheets.items():
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
        format_report_workbook(
            writer.book,
            high_performer_threshold=config.high_performer_score_threshold,
        )
    return output.getvalue()


def build_validation_summary_frame(warnings: list[str]) -> pd.DataFrame:
    """Return workbook-friendly validation notes."""

    if not warnings:
        return pd.DataFrame(
            [{"severity": "info", "message": "No non-blocking data quality warnings were found."}]
        )
    return pd.DataFrame({"severity": ["warning"] * len(warnings), "message": warnings})
