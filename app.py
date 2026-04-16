"""Streamlit app for reviewing, cleaning, and exporting grade reports."""

from __future__ import annotations

from html import escape

import streamlit as st

from engine.exports import export_excel_workbook, export_outputs
from engine.filters import get_at_risk_students, get_high_performing_students, get_low_attendance_students
from engine.mapping import apply_column_mapping, infer_column_mapping
from engine.processing import load_data, process_mapped_grade_report
from engine.report_files import build_student_report_files
from engine.schemas import CANONICAL_FIELDS, DEFAULT_CONFIG
from engine.student_reports import export_student_reports_zip
from engine.summaries import build_student_summary, build_subject_summary
from ui.email_section import render_email_section
from ui.parent_contacts_section import render_parent_contacts_section
from utils.helpers import display_dataframe, style_grade_dataframe, style_high_performer_dataframe
from utils.validators import build_quality_warnings, validate_column_mapping


UNMAPPED_LABEL = "Not mapped"


st.set_page_config(page_title="Student Grade Report Cleaner", layout="wide")


def render_page_styles() -> None:
    """Add light product styling without overwhelming Streamlit defaults."""

    st.markdown(
        """
        <style>
        :root {
            --app-bg: #f6f8fb;
            --surface: #ffffff;
            --surface-soft: #f9fbff;
            --border: #d9e2ef;
            --border-strong: #c7d3e3;
            --text: #111827;
            --muted: #5b677a;
            --accent: #2563eb;
            --accent-soft: #eaf2ff;
            --danger-soft: #fff1f2;
            --danger: #b42318;
            --warning-soft: #fff8e6;
            --warning: #9a6700;
        }
        .stApp,
        [data-testid="stAppViewContainer"] {
            background:
                linear-gradient(
                    rgba(246, 248, 251, 0.48),
                    rgba(246, 248, 251, 0.48)
                ),
                url("https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=1800&q=80");
            background-attachment: fixed;
            background-color: var(--app-bg);
            background-position: center;
            background-size: cover;
            color: var(--text);
        }
        section[data-testid="stMain"],
        div[data-testid="stMainBlockContainer"] {
            background: transparent;
        }
        [data-testid="stHeader"] {
            background: rgba(246, 248, 251, 0.68);
            backdrop-filter: blur(4px);
        }
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.86);
        }
        .block-container {
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 14px 40px rgba(17, 24, 39, 0.06);
            backdrop-filter: blur(2px);
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
            padding-top: 2rem;
        }
        h1, h2, h3, h4, h5, h6, p, label, span {
            color: var(--text);
        }
        div[data-testid="stFileUploader"] section {
            background: var(--surface-soft);
            border-color: var(--border-strong);
            border-radius: 8px;
        }
        div[data-testid="stDataFrame"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 6px 18px rgba(17, 24, 39, 0.04);
            overflow: hidden;
        }
        div[data-testid="stMetric"] {
            background: var(--surface-soft);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem 1rem;
        }
        div[data-testid="stMetricLabel"] {
            color: var(--muted);
        }
        div[data-baseweb="select"] > div {
            background: var(--surface);
            border-color: var(--border-strong);
            color: var(--text);
            border-radius: 8px;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input {
            color: var(--text);
        }
        div[data-baseweb="popover"],
        ul[data-testid="stVirtualDropdown"] {
            background: var(--surface);
            color: var(--text);
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            background: var(--surface);
            border: 1px solid #bdd4f8;
            border-radius: 8px;
            color: var(--accent);
            font-weight: 650;
            box-shadow: 0 3px 10px rgba(37, 99, 235, 0.08);
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            background: var(--accent-soft);
            border-color: #8db7f4;
            color: #1d4ed8;
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            background: var(--accent-soft);
            border-color: #8db7f4;
            color: #1d4ed8;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.12);
        }
        div[data-baseweb="tab-list"] {
            background: var(--surface-soft);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.25rem;
        }
        button[data-baseweb="tab"] {
            border-radius: 8px;
            color: var(--muted);
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: var(--accent-soft);
            color: var(--accent);
        }
        div[data-testid="stAlert"] {
            background: var(--surface-soft);
            color: var(--text);
            border-radius: 8px;
        }
        .validation-box {
            border: 1px solid var(--border);
            border-left-width: 5px;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin: 0.75rem 0;
            background: var(--surface-soft);
            color: var(--text);
        }
        .validation-box strong {
            display: block;
            margin-bottom: 0.35rem;
        }
        .validation-error {
            border-left-color: var(--danger);
            background: var(--danger-soft);
        }
        .validation-warning {
            border-left-color: var(--warning);
            background: var(--warning-soft);
        }
        .muted-note {
            color: var(--muted);
            font-size: 0.95rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_validation_summary(title: str, messages: list[str], level: str) -> None:
    """Render compact validation feedback grouped by severity."""

    if not messages:
        return

    class_name = "validation-error" if level == "error" else "validation-warning"
    message_items = "".join(f"<li>{escape(message)}</li>" for message in messages)
    st.markdown(
        f"""
        <div class="validation-box {class_name}">
            <strong>{escape(title)}</strong>
            <ul>{message_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def upload_signature(uploaded_file) -> tuple[str, int]:
    """Return a stable key for the current uploaded file."""

    size = getattr(uploaded_file, "size", 0)
    return uploaded_file.name, size


def reset_mapping_state(raw_df) -> None:
    """Initialize session state for a newly uploaded file."""

    inferred_mapping = infer_column_mapping(raw_df)
    st.session_state.detected_column_mapping = inferred_mapping.copy()
    st.session_state.column_mapping = inferred_mapping
    st.session_state.generated_outputs = None
    st.session_state.generated_mapping = None

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


def build_outputs(raw_df, mapping: dict[str, str | None]) -> dict[str, object]:
    """Apply mapping, process the data, and build all report outputs."""

    mapped_df = apply_column_mapping(raw_df, mapping)
    cleaned_df = process_mapped_grade_report(mapped_df)
    student_summary = build_student_summary(cleaned_df)
    subject_summary = build_subject_summary(cleaned_df)
    at_risk = get_at_risk_students(cleaned_df)
    high_performers = get_high_performing_students(cleaned_df)
    low_attendance = get_low_attendance_students(cleaned_df)
    student_report_files = build_student_report_files(cleaned_df)

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


render_page_styles()

st.title("Student Grade Report Cleaner")
st.write(
    "Upload a CSV or Excel grade sheet, review the detected column mapping, "
    "then generate cleaned data, risk views, summaries, and downloads."
)

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
        outputs = build_outputs(raw_df, selected_mapping)
    except Exception as exc:
        render_validation_summary("The report could not be generated", [str(exc)], "error")
        st.stop()

    st.session_state.generated_outputs = outputs
    st.session_state.generated_mapping = selected_mapping.copy()

outputs = st.session_state.get("generated_outputs")
generated_mapping = st.session_state.get("generated_mapping")

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

tabs = st.tabs(
    [
        "Cleaned Data",
        "At-Risk Students",
        "High-Performing Students",
        "Summary by Student",
        "Summary by Subject",
        "Downloads",
        "Parent Contacts",
        "Parent Emails",
    ]
)

with tabs[0]:
    st.dataframe(style_grade_dataframe(cleaned_df), use_container_width=True)

with tabs[1]:
    if at_risk.empty:
        st.success("No at-risk students were found with the current thresholds.")
    else:
        st.dataframe(style_grade_dataframe(at_risk), use_container_width=True)

with tabs[2]:
    threshold = DEFAULT_CONFIG.high_performer_score_threshold
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
    st.caption("Primary exports include the formatted workbook and parent-ready student report package.")
    primary_downloads = st.columns(2)
    with primary_downloads[0]:
        st.download_button(
            label="Excel Workbook",
            data=export_excel_workbook(
                cleaned_df,
                student_summary,
                subject_summary,
                warnings=warnings,
            ),
            file_name="grade_report_workbook.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with primary_downloads[1]:
        st.download_button(
            label="Student Reports ZIP",
            data=export_student_reports_zip(cleaned_df),
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

with tabs[6]:
    render_parent_contacts_section(student_report_files)

with tabs[7]:
    render_email_section(student_report_files)
