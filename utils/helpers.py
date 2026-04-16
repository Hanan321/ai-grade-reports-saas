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


def style_grade_dataframe(df: pd.DataFrame, max_rows: int = 100):
    """Return a styled preview with risk and performance cues."""

    preview = display_dataframe(df, max_rows=max_rows)
    styled = _base_light_table_style(preview.style)

    score_columns = [column for column in ("final_score", "avg_final_score") if column in preview.columns]
    if score_columns:
        styled = _map_cell_styles(styled, _score_style, subset=score_columns)

    attendance_columns = [
        column for column in ("attendance_percent", "avg_attendance") if column in preview.columns
    ]
    if attendance_columns:
        styled = _map_cell_styles(styled, _attendance_style, subset=attendance_columns)

    if "at_risk" in preview.columns or "any_risk" in preview.columns:
        styled = styled.apply(_risk_row_style, axis=1)

    return styled


def style_high_performer_dataframe(df: pd.DataFrame, max_rows: int = 100):
    """Return a styled high performer preview."""

    preview = display_dataframe(df, max_rows=max_rows)
    return _base_light_table_style(preview.style).apply(_high_performer_row_style, axis=1)


def _base_light_table_style(styler):
    return styler.set_table_styles(
        [
            {
                "selector": "thead th",
                "props": [
                    ("background-color", "#f8fafc"),
                    ("color", "#111827"),
                    ("font-weight", "700"),
                    ("border-bottom", "1px solid #d9e2ef"),
                ],
            },
            {
                "selector": "tbody td",
                "props": [
                    ("color", "#111827"),
                    ("border-color", "#edf2f7"),
                ],
            },
        ]
    )


def _map_cell_styles(styler, style_func, subset: list[str]):
    """Apply cell-level styles across pandas Styler versions."""

    if hasattr(styler, "map"):
        return styler.map(style_func, subset=subset)
    return styler.applymap(style_func, subset=subset)


def _score_style(value: object) -> str:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return ""
    if score < 70:
        return "background-color: #fff1f2; color: #b42318; font-weight: 650;"
    if score >= 85:
        return "background-color: #ecfdf3; color: #166534; font-weight: 650;"
    return "background-color: #f8fafc; color: #111827;"


def _attendance_style(value: object) -> str:
    try:
        attendance = float(value)
    except (TypeError, ValueError):
        return ""
    if attendance < 80:
        return "background-color: #fff8e6; color: #9a6700; font-weight: 650;"
    return ""


def _risk_row_style(row: pd.Series) -> list[str]:
    if bool(row.get("at_risk", False)) or bool(row.get("any_risk", False)):
        return ["background-color: #fff1f2; color: #7f1d1d;" for _ in row]
    return ["" for _ in row]


def _high_performer_row_style(row: pd.Series) -> list[str]:
    return ["background-color: #ecfdf3; color: #14532d;" for _ in row]


def bytes_to_buffer(data: bytes) -> BytesIO:
    """Wrap bytes in a buffer for tools that expect a file-like object."""

    return BytesIO(data)
