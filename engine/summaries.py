"""Summary builders for processed grade reports."""

from __future__ import annotations

import pandas as pd


def build_student_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build one row per student with score, attendance, and risk rollups."""

    summary = (
        df.groupby("student_name", dropna=False)
        .agg(
            tests_taken=("test_date", "count"),
            avg_final_score=("final_score", "mean"),
            avg_attendance=("attendance_percent", "mean"),
            any_risk=("at_risk", "max"),
        )
        .reset_index()
        .sort_values("avg_final_score", ascending=False)
    )
    summary["avg_final_score"] = summary["avg_final_score"].round(1)
    summary["avg_attendance"] = summary["avg_attendance"].round(0)
    return summary


def build_subject_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build one row per subject with score and attendance rollups."""

    summary = (
        df.groupby("subject", dropna=False)
        .agg(
            tests_taken=("test_date", "count"),
            avg_final_score=("final_score", "mean"),
            avg_attendance=("attendance_percent", "mean"),
        )
        .reset_index()
        .sort_values("subject")
    )
    summary["avg_final_score"] = summary["avg_final_score"].round(1)
    summary["avg_attendance"] = summary["avg_attendance"].round(0)
    return summary

