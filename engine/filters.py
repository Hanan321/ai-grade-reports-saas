"""Filtered report views for product tabs."""

from __future__ import annotations

import pandas as pd

from engine.schemas import DEFAULT_CONFIG, GradeReportConfig


def get_at_risk_students(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows flagged as at risk."""

    if "at_risk" not in df.columns:
        return df.iloc[0:0].copy()
    return df[df["at_risk"]].copy()


def get_high_performing_students(
    df: pd.DataFrame,
    config: GradeReportConfig = DEFAULT_CONFIG,
) -> pd.DataFrame:
    """Return rows meeting the high performer score threshold."""

    if "final_score" not in df.columns:
        return df.iloc[0:0].copy()
    return df[df["final_score"] >= config.high_performer_score_threshold].copy()


def get_low_attendance_students(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows flagged for low attendance."""

    if "low_attendance" not in df.columns:
        return df.iloc[0:0].copy()
    return df[df["low_attendance"]].copy()
