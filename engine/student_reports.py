"""Individual student report exports."""

from __future__ import annotations

from html import escape
from io import BytesIO
import re
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd


REPORT_COLUMNS: tuple[str, ...] = (
    "student_id",
    "student_name",
    "grade",
    "subject",
    "test_date",
    "homework",
    "quizscore",
    "exam_score",
    "attendance_percent",
    "final_score",
    "at_risk",
    "low_attendance",
    "notes",
)


def export_student_reports_zip(cleaned: pd.DataFrame) -> bytes:
    """Create a ZIP file containing one HTML report per student."""

    output = BytesIO()
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED) as archive:
        for index, (student_key, student_df) in enumerate(_student_groups(cleaned), start=1):
            report_html = build_student_report_html(student_df)
            filename = _student_report_filename(student_df, student_key, index)
            archive.writestr(filename, report_html)

    return output.getvalue()


def build_student_report_html(student_df: pd.DataFrame) -> str:
    """Build one readable parent-facing HTML report."""

    student_name = _first_present(student_df, "student_name", "Unknown Student")
    student_id = _first_present(student_df, "student_id", "")
    grade = _first_present(student_df, "grade", "")
    avg_score = _mean_or_blank(student_df, "final_score")
    avg_attendance = _mean_or_blank(student_df, "attendance_percent")
    any_risk = bool(student_df.get("at_risk", pd.Series(dtype=bool)).fillna(False).any())
    any_low_attendance = bool(
        student_df.get("low_attendance", pd.Series(dtype=bool)).fillna(False).any()
    )

    detail_columns = [column for column in REPORT_COLUMNS if column in student_df.columns]
    detail_table = _html_table(student_df[detail_columns])
    status_text = "At Risk" if any_risk else "On Track"
    attendance_text = "Low Attendance" if any_low_attendance else "Attendance OK"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(str(student_name))} - Student Report</title>
  <style>
    body {{
      background: #f6f8fb;
      color: #111827;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.45;
      margin: 32px;
    }}
    header {{
      border-bottom: 2px solid #d9e2ef;
      margin-bottom: 20px;
      padding-bottom: 14px;
    }}
    h1 {{
      font-size: 28px;
      margin: 0 0 4px;
    }}
    .subtitle {{
      color: #526070;
      font-size: 14px;
    }}
    .summary {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      margin: 18px 0 24px;
    }}
    .metric {{
      background: #f8fafc;
      border: 1px solid #d7dee8;
      border-radius: 8px;
      padding: 12px;
    }}
    .label {{
      color: #526070;
      font-size: 12px;
      text-transform: uppercase;
    }}
    .value {{
      font-size: 20px;
      font-weight: 700;
      margin-top: 4px;
    }}
    .status-risk {{
      color: #991b1b;
    }}
    .status-ok {{
      color: #166534;
    }}
    table {{
      border-collapse: collapse;
      font-size: 13px;
      width: 100%;
    }}
    th {{
      background: #f8fafc;
      color: #111827;
      font-weight: 700;
      text-align: left;
    }}
    th, td {{
      border: 1px solid #d7dee8;
      padding: 8px;
      vertical-align: top;
    }}
    tr:nth-child(even) {{
      background: #f8fafc;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(str(student_name))}</h1>
    <div class="subtitle">Student progress report for parent or teacher review</div>
  </header>
  <section class="summary">
    <div class="metric"><div class="label">Student ID</div><div class="value">{escape(str(student_id or "N/A"))}</div></div>
    <div class="metric"><div class="label">Grade</div><div class="value">{escape(str(grade or "N/A"))}</div></div>
    <div class="metric"><div class="label">Average Score</div><div class="value">{escape(str(avg_score))}</div></div>
    <div class="metric"><div class="label">Average Attendance</div><div class="value">{escape(str(avg_attendance))}</div></div>
    <div class="metric"><div class="label">Academic Status</div><div class="value {'status-risk' if any_risk else 'status-ok'}">{status_text}</div></div>
    <div class="metric"><div class="label">Attendance Status</div><div class="value {'status-risk' if any_low_attendance else 'status-ok'}">{attendance_text}</div></div>
  </section>
  <h2>Assessment Details</h2>
  {detail_table}
</body>
</html>
"""


def _student_groups(df: pd.DataFrame):
    if "student_id" in df.columns:
        group_columns = ["student_id", "student_name"]
    else:
        group_columns = ["student_name"]
    return df.groupby(group_columns, dropna=False, sort=True)


def _html_table(df: pd.DataFrame) -> str:
    display_df = df.copy()
    for column in display_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        display_df[column] = display_df[column].dt.strftime("%Y-%m-%d")
    display_df = display_df.where(pd.notna(display_df), "")
    return display_df.to_html(index=False, escape=True, border=0)


def _first_present(df: pd.DataFrame, column: str, default: object) -> object:
    if column not in df.columns:
        return default
    values = df[column].dropna()
    if values.empty:
        return default
    return values.iloc[0]


def _mean_or_blank(df: pd.DataFrame, column: str) -> str:
    if column not in df.columns:
        return "N/A"
    value = pd.to_numeric(df[column], errors="coerce").mean()
    if pd.isna(value):
        return "N/A"
    return f"{value:.1f}"


def _student_report_filename(student_df: pd.DataFrame, student_key: object, index: int) -> str:
    student_name = _first_present(student_df, "student_name", f"student_{index}")
    student_id = _first_present(student_df, "student_id", "")
    base = f"{student_id}_{student_name}" if student_id != "" else str(student_name)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(base)).strip("_").lower()
    return f"{index:03d}_{slug or 'student_report'}.html"
