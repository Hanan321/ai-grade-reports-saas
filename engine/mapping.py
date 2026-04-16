"""Column mapping helpers for uploaded grade sheets."""

from __future__ import annotations

from typing import Mapping

import pandas as pd

from engine.schemas import CANONICAL_FIELDS, canonicalize_column_name


ColumnMapping = dict[str, str | None]


def infer_column_mapping(df: pd.DataFrame) -> ColumnMapping:
    """Infer uploaded source columns for the app's canonical fields."""

    mapping: ColumnMapping = {field: None for field in CANONICAL_FIELDS}
    for source_column in df.columns:
        canonical = canonicalize_column_name(source_column)
        if canonical in mapping and mapping[canonical] is None:
            mapping[canonical] = str(source_column)

    return mapping


def apply_column_mapping(df: pd.DataFrame, mapping: Mapping[str, str | None]) -> pd.DataFrame:
    """Return a DataFrame with selected source columns renamed to canonical fields."""

    source_lookup = {str(source_column): source_column for source_column in df.columns}
    selected_mapping = {
        source_lookup[source_column]: canonical_field
        for canonical_field, source_column in mapping.items()
        if source_column
    }

    mapped = df.loc[:, list(selected_mapping)].copy()
    mapped = mapped.rename(columns=selected_mapping)
    return mapped
