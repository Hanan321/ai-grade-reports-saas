"""Streamlit app for reviewing, cleaning, and exporting grade reports."""

from __future__ import annotations

import streamlit as st

from config.default_config import AppConfig, load_app_config
from engine.exports import export_excel_workbook, export_outputs
from engine.filters import get_at_risk_students, get_high_performing_students, get_low_attendance_students
from engine.mapping import apply_column_mapping, infer_column_mapping
from engine.processing import load_data, process_mapped_grade_report
from engine.report_files import build_student_report_files
from engine.schemas import CANONICAL_FIELDS
from engine.student_reports import export_student_reports_zip
from engine.storage import ensure_data_dir
from engine.summaries import build_student_summary, build_subject_summary
from ui.branding import render_app_header, render_config_sidebar
from ui.dashboard import render_school_dashboard
from ui.email_section import render_email_section
from ui.email_settings_section import render_email_settings_section
from ui.parent_contacts_section import render_parent_contacts_section
from ui.sections import render_validation_summary
from ui.styles import render_page_styles
from utils.helpers import display_dataframe, style_grade_dataframe, style_high_performer_dataframe
from utils.validators import build_quality_warnings, validate_column_mapping


UNMAPPED_LABEL = "Not mapped"


APP_CONFIG = load_app_config()

st.set_page_config(page_title=APP_CONFIG.branding.page_title, layout="wide")


def upload_signature(uploaded_file) -> tuple[str, int]:
    """Return a stable key for the current uploaded file."""

    size = getattr(uploaded_file, "size", 0)
    return uploaded_file.name, size


def scoring_config_signature(app_config: AppConfig) -> tuple[object, ...]:
    """Return the values that affect generated report calculations."""

    weights = app_config.grade_report.weights
    return (
        round(float(weights.get("homework", 0.0)), 6),
        round(float(weights.get("quizscore", 0.0)), 6),
        round(float(weights.get("exam_score", 0.0)), 6),
        round(float(app_config.grade_report.at_risk_score_threshold), 6),
        round(float(app_config.grade_report.low_attendance_threshold), 6),
        round(float(app_config.grade_report.high_performer_score_threshold), 6),
    )


def reset_mapping_state(raw_df) -> None:
    """Initialize session state for a newly uploaded file."""

    inferred_mapping = infer_column_mapping(raw_df)
    st.session_state.detected_column_mapping = inferred_mapping.copy()
    st.session_state.column_mapping = inferred_mapping
    st.session_state.generated_outputs = None
    st.session_state.generated_mapping = None
    st.session_state.generated_scoring_config = None

    for field in CANONICAL_FIELDS:
        st.session_state[f"mapping_{field}"] = inferred_mapping.get(field) or UNMAPPED_LABEL


def collect_mapping_from_widgets() -> dict[str, str | None]:
    """Collect the currently selected column mapping from Streamlit widgets."""

    mapping: dict[str, str | None] = {}
    for field in CANONICAL_FIELDS:
        selected = st.session_state.get(f"mapping_{field}", UNMAPPED_LABEL)
        mapping[field] = None if selected == UNMAPPED_LABEL else selected
    st.session_state.column_mapping = mapping
    return mapping


def render_mapping_review(raw_df) -> dict[str, str | None]:
    """Show detected columns and editable mapping controls."""

    st.subheader("Review Column Mapping")
    st.markdown(
        '<p class="muted-note">Confirm the detected source columns before generating the report. '
        "Required fields must be mapped; optional fields can stay unmapped.</p>",
        unsafe_allow_html=True,
    )

    source_columns = [str(column) for column in raw_df.columns]
    options = [UNMAPPED_LABEL, *source_columns]
    detected_mapping = st.session_state.detected_column_mapping

    header = st.columns([1.4, 1.6, 2.4])
    header[0].caption("Canonical field")
    header[1].caption("Detected source")
    header[2].caption("Editable selection")

    for field in CANONICAL_FIELDS:
        detected_source = detected_mapping.get(field) or UNMAPPED_LABEL
        current_value = st.session_state.get(f"mapping_{field}", detected_source)
        if current_value not in options:
            current_value = UNMAPPED_LABEL
        index = options.index(current_value)

        row = st.columns([1.4, 1.6, 2.4])
        row[0].markdown(f"`{field}`")
        row[1].write(detected_source)
        row[2].selectbox(
            f"Select source column for {field}",
            options=options,
            index=index,
            key=f"mapping_{field}",
            label_visibility="collapsed",
        )

    return collect_mapping_from_widgets()


def build_outputs(
    raw_df,
    mapping: dict[str, str | None],
    app_config: AppConfig,
) -> dict[str, object]:
    """Apply mapping, process the data, and build all report outputs."""

    mapped_df = apply_column_mapping(raw_df, mapping)
    cleaned_df = process_mapped_grade_report(mapped_df, config=app_config.grade_report)
    student_summary = build_student_summary(cleaned_df)
    subject_summary = build_subject_summary(cleaned_df)
    at_risk = get_at_risk_students(cleaned_df)
    high_performers = get_high_performing_students(cleaned_df, config=app_config.grade_report)
    low_attendance = get_low_attendance_students(cleaned_df)
    student_report_files = build_student_report_files(
        cleaned_df,
        report_branding=app_config.report_branding,
    )

    return {
        "cleaned_df": cleaned_df,
        "student_summary": student_summary,
        "subject_summary": subject_summary,
        "at_risk": at_risk,
        "high_performers": high_performers,
        "low_attendance": low_attendance,
        "student_report_files": student_report_files,
        "warnings": build_quality_warnings(cleaned_df),
    }


render_page_styles(APP_CONFIG)
APP_CONFIG = render_config_sidebar(APP_CONFIG)
render_app_header(APP_CONFIG)

if APP_CONFIG.mode == "school":
    ensure_data_dir()
    school_pages = ["Dashboard", "Upload & Reports", "Parent Contacts", "Email Settings"]
    current_page = st.session_state.get("school_nav", "Dashboard")
    if current_page not in school_pages:
        st.session_state.school_nav = "Dashboard"
    selected_page = st.sidebar.radio(
        "School Navigation",
        options=school_pages,
        key="school_nav",
    )

    if selected_page == "Dashboard":
        render_school_dashboard(APP_CONFIG)
        st.stop()
    if selected_page == "Parent Contacts":
        render_parent_contacts_section([])
        st.stop()
    if selected_page == "Email Settings":
        render_email_settings_section()
        st.stop()

uploaded_file = st.file_uploader("Upload a grade sheet", type=["csv", "xlsx", "xls"])

if uploaded_file is None:
    st.info("Upload a CSV or Excel file to begin. A sample file is included in `sample_data/`.")
    st.stop()

try:
    uploaded_file.seek(0)
    raw_df = load_data(uploaded_file, filename=uploaded_file.name)
except Exception as exc:
    render_validation_summary("This file could not be opened", [str(exc)], "error")
    st.stop()

current_signature = upload_signature(uploaded_file)
if st.session_state.get("upload_signature") != current_signature:
    st.session_state.upload_signature = current_signature
    reset_mapping_state(raw_df)

st.subheader("Raw Data Preview")
st.dataframe(display_dataframe(raw_df), use_container_width=True)

selected_mapping = render_mapping_review(raw_df)
available_columns = [str(column) for column in raw_df.columns]
mapping_errors = validate_column_mapping(selected_mapping, available_columns)

if mapping_errors:
    render_validation_summary("Before generating, fix these required mapping items", mapping_errors, "error")

generate_clicked = st.button(
    "Generate Reports",
    type="primary",
    disabled=bool(mapping_errors),
    use_container_width=False,
)

if generate_clicked:
    try:
        outputs = build_outputs(raw_df, selected_mapping, APP_CONFIG)
    except Exception as exc:
        render_validation_summary("The report could not be generated", [str(exc)], "error")
        st.stop()

    st.session_state.generated_outputs = outputs
    st.session_state.generated_mapping = selected_mapping.copy()
    st.session_state.generated_scoring_config = scoring_config_signature(APP_CONFIG)

outputs = st.session_state.get("generated_outputs")
generated_mapping = st.session_state.get("generated_mapping")
generated_scoring_config = st.session_state.get("generated_scoring_config")

if outputs is None:
    st.markdown(
        '<p class="muted-note">No report has been generated yet. Review the mapping, then click '
        "<strong>Generate Reports</strong>.</p>",
        unsafe_allow_html=True,
    )
    st.stop()

if selected_mapping != generated_mapping:
    render_validation_summary(
        "Mapping changed after generation",
        ["Click Generate Reports again so the final outputs match the current mapping."],
        "warning",
    )
    st.stop()

if generated_scoring_config != scoring_config_signature(APP_CONFIG):
    render_validation_summary(
        "Scoring settings changed after generation",
        ["Click Generate Reports again so the final outputs match the current sidebar scoring settings."],
        "warning",
    )
    st.stop()

warnings = outputs["warnings"]
render_validation_summary("Non-blocking data quality notes", warnings, "warning")

cleaned_df = outputs["cleaned_df"]
student_summary = outputs["student_summary"]
subject_summary = outputs["subject_summary"]
at_risk = outputs["at_risk"]
high_performers = outputs["high_performers"]
low_attendance = outputs["low_attendance"]
student_report_files = outputs["student_report_files"]

metric_cols = st.columns(5)
metric_cols[0].metric("Rows Processed", len(cleaned_df))
metric_cols[1].metric("At-Risk Rows", len(at_risk))
metric_cols[2].metric("High Performers", len(high_performers))
metric_cols[3].metric("Low Attendance", len(low_attendance))
metric_cols[4].metric("Subjects", subject_summary["subject"].nunique() if "subject" in subject_summary else 0)

tab_names = [
    "Cleaned Data",
    "At-Risk Students",
    "High-Performing Students",
    "Summary by Student",
    "Summary by Subject",
    "Downloads",
]
if APP_CONFIG.mode == "school":
    tab_names.extend(["Parent Contacts", "Parent Emails"])

tabs = st.tabs(tab_names)

with tabs[0]:
    st.dataframe(style_grade_dataframe(cleaned_df), use_container_width=True)

with tabs[1]:
    if at_risk.empty:
        st.success("No at-risk students were found with the current thresholds.")
    else:
        st.dataframe(style_grade_dataframe(at_risk), use_container_width=True)

with tabs[2]:
    threshold = APP_CONFIG.grade_report.high_performer_score_threshold
    if high_performers.empty:
        st.info(f"No students met the high performer threshold of {threshold:g}.")
    else:
        st.caption(f"High performers are rows with final_score >= {threshold:g}.")
        st.dataframe(style_high_performer_dataframe(high_performers), use_container_width=True)

with tabs[3]:
    st.dataframe(style_grade_dataframe(student_summary), use_container_width=True)

with tabs[4]:
    st.dataframe(style_grade_dataframe(subject_summary), use_container_width=True)

with tabs[5]:
    if APP_CONFIG.mode == "school":
        st.caption("Primary exports include the formatted workbook and parent-ready student report package.")
    else:
        st.caption("Primary exports include the formatted workbook and student report package.")
    primary_downloads = st.columns(2)
    with primary_downloads[0]:
        st.download_button(
            label="Excel Workbook",
            data=export_excel_workbook(
                cleaned_df,
                student_summary,
                subject_summary,
                warnings=warnings,
                config=APP_CONFIG.grade_report,
                report_branding=APP_CONFIG.report_branding,
            ),
            file_name="grade_report_workbook.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with primary_downloads[1]:
        st.download_button(
            label="Student Reports ZIP",
            data=export_student_reports_zip(
                cleaned_df,
                report_branding=APP_CONFIG.report_branding,
            ),
            file_name="student_reports_html.zip",
            mime="application/zip",
            use_container_width=True,
        )

    st.divider()
    st.caption("Single-table CSV downloads are still available for quick spreadsheet workflows.")
    downloads = export_outputs(cleaned_df, student_summary, subject_summary)
    download_cols = st.columns(3)
    for index, (filename, data) in enumerate(downloads.items()):
        with download_cols[index]:
            st.download_button(
                label=filename.replace("_", " ").replace(".csv", "").title(),
                data=data,
                file_name=filename,
                mime="text/csv",
                use_container_width=True,
            )

if APP_CONFIG.mode == "school":
    with tabs[6]:
        render_parent_contacts_section(student_report_files)

    with tabs[7]:
        render_email_section(student_report_files, app_config=APP_CONFIG)
