"""Small app helpers."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def display_dataframe(df: pd.DataFrame, max_rows: int = 100) -> pd.DataFrame:
    """Return a display-friendly copy with datetimes formatted as dates."""

    preview = df.head(max_rows).copy()
    for column in preview.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        preview[column] = preview[column].dt.strftime("%Y-%m-%d")
    return preview


def bytes_to_buffer(data: bytes) -> BytesIO:
    """Wrap bytes in a buffer for tools that expect a file-like object."""

    return BytesIO(data)

