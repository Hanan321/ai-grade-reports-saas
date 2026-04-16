"""Streamlit MVP for turning uploaded grade sheets into clean reports."""

from __future__ import annotations

import streamlit as st

from engine.exports import export_excel_workbook, export_outputs
from engine.processing import clean_columns, load_data, process_grade_report
from engine.summaries import build_student_summary, build_subject_summary
from utils.helpers import display_dataframe
from utils.validators import ValidationError, build_quality_warnings, validate_required_columns


st.set_page_config(page_title="Student Grade Report Cleaner", layout="wide")

st.title("Student Grade Report Cleaner")
st.write(
    "Upload a CSV or Excel grade sheet, clean messy fields, calculate weighted final scores, "
    "and download student and subject summaries."
)

uploaded_file = st.file_uploader("Upload a grade sheet", type=["csv", "xlsx", "xls"])

if uploaded_file is None:
    st.info("Upload a CSV or Excel file to begin. A sample file is included in `sample_data/`.")
    st.stop()

try:
    raw_df = load_data(uploaded_file, filename=uploaded_file.name)
except Exception as exc:
    st.error(str(exc))
    st.stop()

st.subheader("Raw Preview")
st.dataframe(display_dataframe(raw_df), use_container_width=True)

try:
    mapped_df = clean_columns(raw_df)
    validate_required_columns(mapped_df)
    cleaned_df = process_grade_report(raw_df)
    student_summary = build_student_summary(cleaned_df)
    subject_summary = build_subject_summary(cleaned_df)
except ValidationError as exc:
    st.error(str(exc))
    st.caption(
        "Tip: supported aliases include Student Name, student__name, homework score, QuizScore, "
        "Exam score, attendance %, subject, test date, and student id."
    )
    st.stop()
except Exception as exc:
    st.error(f"Could not process this file: {exc}")
    st.stop()

warnings = build_quality_warnings(cleaned_df)
for warning in warnings:
    st.warning(warning)

st.subheader("Cleaned Data")
st.dataframe(display_dataframe(cleaned_df), use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Summary By Student")
    st.dataframe(display_dataframe(student_summary), use_container_width=True)

with right:
    st.subheader("Summary By Subject")
    st.dataframe(display_dataframe(subject_summary), use_container_width=True)

st.subheader("Downloads")
downloads = export_outputs(cleaned_df, student_summary, subject_summary)

download_cols = st.columns(4)
for index, (filename, data) in enumerate(downloads.items()):
    with download_cols[index]:
        st.download_button(
            label=filename.replace("_", " ").replace(".csv", "").title(),
            data=data,
            file_name=filename,
            mime="text/csv",
        )

with download_cols[3]:
    st.download_button(
        label="Excel Workbook",
        data=export_excel_workbook(cleaned_df, student_summary, subject_summary),
        file_name="grade_report_outputs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

