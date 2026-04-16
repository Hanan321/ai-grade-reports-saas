"""Validation helpers with user-facing error messages."""

from __future__ import annotations

import pandas as pd

from engine.schemas import DEFAULT_CONFIG, GradeReportConfig


class ValidationError(ValueError):
    """Raised when uploaded data cannot be processed safely."""


def validate_required_columns(df: pd.DataFrame, config: GradeReportConfig = DEFAULT_CONFIG) -> None:
    """Raise a clear error if required canonical columns are missing."""

    missing = [column for column in config.required_columns if column not in df.columns]
    if missing:
        missing_text = ", ".join(missing)
        available_text = ", ".join(df.columns.astype(str))
        raise ValidationError(
            f"Missing required columns: {missing_text}. Available columns after mapping: {available_text}."
        )


def validate_column_mapping(
    mapping: dict[str, str | None],
    available_columns: list[str],
    config: GradeReportConfig = DEFAULT_CONFIG,
) -> list[str]:
    """Return blocking, user-facing mapping errors."""

    errors: list[str] = []
    missing_required = [field for field in config.required_columns if not mapping.get(field)]
    if missing_required:
        errors.append(
            "Choose source columns for these required fields before generating: "
            + ", ".join(missing_required)
            + "."
        )

    selected_sources = [source for source in mapping.values() if source]
    duplicate_sources = sorted(
        source for source in set(selected_sources) if selected_sources.count(source) > 1
    )
    if duplicate_sources:
        errors.append(
            "Each uploaded column can only be used once. Check these repeated selections: "
            + ", ".join(duplicate_sources)
            + "."
        )

    unknown_sources = sorted(source for source in selected_sources if source not in available_columns)
    if unknown_sources:
        errors.append(
            "These selected columns are no longer in the uploaded file: "
            + ", ".join(unknown_sources)
            + "."
        )

    return errors


def build_quality_warnings(df: pd.DataFrame) -> list[str]:
    """Return non-blocking warnings about values that could not be parsed."""

    warnings: list[str] = []

    if "test_date" in df.columns:
        invalid_dates = int(df["test_date"].isna().sum())
        if invalid_dates:
            warnings.append(f"{invalid_dates} row(s) have an invalid or missing test date.")

    for column in ("homework", "quizscore", "exam_score", "attendance_percent"):
        if column in df.columns:
            missing_values = int(df[column].isna().sum())
            if missing_values:
                warnings.append(f"{missing_values} row(s) have a missing or non-numeric value in {column}.")

    return warnings
