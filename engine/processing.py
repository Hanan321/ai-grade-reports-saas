"""Deterministic data cleaning and scoring pipeline."""

from __future__ import annotations

from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from engine.schemas import DEFAULT_CONFIG, GradeReportConfig, canonicalize_column_name


TEXT_COLUMNS = ("student_name", "subject", "notes")
NUMERIC_COLUMNS = ("homework", "quizscore", "exam_score", "attendance_percent")


def load_data(file: str | Path | BinaryIO | BytesIO, filename: str | None = None) -> pd.DataFrame:
    """Load a CSV or Excel file into a DataFrame."""

    source_name = filename or str(file)
    suffix = Path(source_name).suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(file)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(file)

    raise ValueError("Please upload a CSV or Excel file with a .csv, .xlsx, or .xls extension.")


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize uploaded columns and apply known aliases."""

    cleaned = df.copy()
    mapped_columns = [canonicalize_column_name(column) for column in cleaned.columns]
    duplicate_names = {name for name, count in Counter(mapped_columns).items() if count > 1}
    if duplicate_names:
        names = ", ".join(sorted(duplicate_names))
        raise ValueError(f"Multiple uploaded columns map to the same field: {names}.")

    cleaned.columns = mapped_columns
    return cleaned


def normalize_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Trim string columns and normalize key display fields."""

    normalized = df.copy()

    for column in normalized.select_dtypes(include=["object", "string"]).columns:
        normalized[column] = normalized[column].astype("string").str.strip()
        normalized[column] = normalized[column].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    if "student_name" in normalized.columns:
        normalized["student_name"] = (
            normalized["student_name"]
            .str.replace(r"\s+", " ", regex=True)
            .str.title()
        )

    if "subject" in normalized.columns:
        normalized["subject"] = (
            normalized["subject"]
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .str.title()
        )

    return normalized


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse test dates without failing the whole upload on invalid values."""

    parsed = df.copy()
    if "test_date" in parsed.columns:
        try:
            parsed["test_date"] = pd.to_datetime(
                parsed["test_date"],
                errors="coerce",
                dayfirst=False,
                format="mixed",
            )
        except TypeError:
            parsed["test_date"] = pd.to_datetime(parsed["test_date"], errors="coerce", dayfirst=False)
    return parsed


def convert_numeric_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Convert score and attendance fields to numbers safely."""

    converted = df.copy()
    missing_markers = {"absent": pd.NA, "missing": pd.NA, "na": pd.NA, "n/a": pd.NA, "": pd.NA}

    for column in NUMERIC_COLUMNS:
        if column in converted.columns:
            converted[column] = converted[column].replace(missing_markers)
            converted[column] = pd.to_numeric(converted[column], errors="coerce")

    return converted


def remove_duplicates(df: pd.DataFrame, config: GradeReportConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """Remove duplicate test rows using stable identifying fields."""

    deduped = df.copy()
    subset = [column for column in config.duplicate_subset if column in deduped.columns]

    if not subset:
        return deduped.drop_duplicates().reset_index(drop=True)

    return deduped.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)


def compute_scores(df: pd.DataFrame, config: GradeReportConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """Compute weighted final scores and risk flags."""

    scored = df.copy()

    for column in config.weights:
        if column not in scored.columns:
            scored[column] = pd.NA

    final_score = sum(scored[column].fillna(0) * weight for column, weight in config.weights.items())
    scored["final_score"] = final_score.round(1)

    attendance = scored.get("attendance_percent", pd.Series(pd.NA, index=scored.index))
    scored["low_attendance"] = attendance < config.low_attendance_threshold
    scored["low_attendance"] = scored["low_attendance"].fillna(False)
    scored["at_risk"] = (scored["final_score"] < config.at_risk_score_threshold) | scored["low_attendance"]

    if "attendance_percent" in scored.columns:
        scored["attendance_percent"] = scored["attendance_percent"].round(0)

    return scored


def process_grade_report(df: pd.DataFrame, config: GradeReportConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    """Run the full cleaning, parsing, deduping, and scoring pipeline."""

    processed = clean_columns(df)
    processed = normalize_text_fields(processed)
    processed = convert_numeric_fields(processed)
    processed = parse_dates(processed)
    processed = remove_duplicates(processed, config=config)
    processed = compute_scores(processed, config=config)
    return processed
