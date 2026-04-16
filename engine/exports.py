"""Export helpers for downloadable report outputs."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


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
) -> bytes:
    """Create a simple multi-sheet Excel workbook in memory."""

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        cleaned.to_excel(writer, sheet_name="Cleaned Data", index=False)
        student_summary.to_excel(writer, sheet_name="By Student", index=False)
        subject_summary.to_excel(writer, sheet_name="By Subject", index=False)
    return output.getvalue()

