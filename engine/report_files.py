"""Structured per-student report file generation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from engine.student_reports import (
    _first_present,
    _student_groups,
    _student_report_filename,
    build_student_report_html,
)


@dataclass(frozen=True)
class StudentReportFile:
    """One generated parent-facing student report."""

    student_name: str
    student_id: str
    filename: str
    content: bytes


def build_student_report_files(cleaned: pd.DataFrame) -> list[StudentReportFile]:
    """Build one report file object per student."""

    reports: list[StudentReportFile] = []
    for index, (student_key, student_df) in enumerate(_student_groups(cleaned), start=1):
        report_html = build_student_report_html(student_df)
        filename = _student_report_filename(student_df, student_key, index)
        student_name = _first_present(student_df, "student_name", "Unknown Student")
        student_id = _first_present(student_df, "student_id", "")
        reports.append(
            StudentReportFile(
                student_name=str(student_name),
                student_id="" if pd.isna(student_id) else str(student_id),
                filename=filename,
                content=report_html.encode("utf-8"),
            )
        )
    return reports
