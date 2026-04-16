"""Mode-specific Streamlit branding helpers."""

from __future__ import annotations

from dataclasses import replace
from html import escape
from pathlib import Path

import streamlit as st

from config.default_config import AppConfig
from engine.schemas import GradeReportConfig


def render_app_header(app_config: AppConfig) -> None:
    """Render the top app title with optional school branding."""

    branding = app_config.branding
    if branding.show_branding and branding.logo_path and Path(branding.logo_path).exists():
        st.image(branding.logo_path, width=88)

    kicker = branding.school_name if branding.show_branding else "Self-Serve SaaS"
    title = branding.school_name or branding.app_name
    subtitle = (
        f"{branding.app_name} - {app_config.report_branding.header_text}"
        if branding.show_branding
        else "Upload a CSV or Excel grade sheet, review mapping, and generate reports."
    )
    st.markdown(
        f"""
        <div class="brand-header">
            <div class="brand-kicker">{escape(kicker)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_config_sidebar(app_config: AppConfig) -> AppConfig:
    """Show school-mode sidebar controls and return the active config."""

    with st.sidebar:
        st.subheader("Product Mode")
        st.write(app_config.mode.upper())
        st.write(f"School: {app_config.branding.school_name}")
        st.caption("Switch modes with the APP_MODE environment variable.")

        st.subheader("Scoring Config")
        st.caption("These values apply to this Streamlit session before report generation.")
        edited_grade_report = render_scoring_controls(app_config.grade_report, mode=app_config.mode)
        return replace(app_config, grade_report=edited_grade_report)


def render_scoring_panel(app_config: AppConfig) -> AppConfig:
    """Render click-to-open scoring controls in the main SaaS workflow."""

    with st.expander("Scoring Config", expanded=False):
        st.caption("Optional: adjust scoring before uploading or generating reports.")
        edited_grade_report = render_scoring_controls(app_config.grade_report, mode=app_config.mode)
    return replace(app_config, grade_report=edited_grade_report)


def render_scoring_controls(config: GradeReportConfig, mode: str) -> GradeReportConfig:
    """Render controls for score weights and thresholds."""

    weights = config.weights
    homework_weight = st.number_input(
        "Homework weight",
        min_value=0.0,
        max_value=1.0,
        value=float(weights.get("homework", 0.0)),
        step=0.05,
        format="%.2f",
        key=f"{mode}_homework_weight",
    )
    quiz_weight = st.number_input(
        "Quiz score weight",
        min_value=0.0,
        max_value=1.0,
        value=float(weights.get("quizscore", 0.0)),
        step=0.05,
        format="%.2f",
        key=f"{mode}_quizscore_weight",
    )
    exam_weight = st.number_input(
        "Exam score weight",
        min_value=0.0,
        max_value=1.0,
        value=float(weights.get("exam_score", 0.0)),
        step=0.05,
        format="%.2f",
        key=f"{mode}_exam_score_weight",
    )

    weight_total = homework_weight + quiz_weight + exam_weight
    st.caption(f"Weight total: {weight_total:.2f}")
    if abs(weight_total - 1.0) > 0.001:
        st.warning("Weights usually should total 1.00.")

    at_risk_threshold = st.number_input(
        "At-risk threshold",
        min_value=0.0,
        max_value=100.0,
        value=float(config.at_risk_score_threshold),
        step=1.0,
        format="%.1f",
        key=f"{mode}_at_risk_threshold",
    )
    low_attendance_threshold = st.number_input(
        "Low attendance",
        min_value=0.0,
        max_value=100.0,
        value=float(config.low_attendance_threshold),
        step=1.0,
        format="%.1f",
        key=f"{mode}_low_attendance_threshold",
    )
    high_performer_threshold = st.number_input(
        "High performer",
        min_value=0.0,
        max_value=100.0,
        value=float(config.high_performer_score_threshold),
        step=1.0,
        format="%.1f",
        key=f"{mode}_high_performer_threshold",
    )

    return replace(
        config,
        score_weights={
            "homework": homework_weight,
            "quizscore": quiz_weight,
            "exam_score": exam_weight,
        },
        at_risk_score_threshold=at_risk_threshold,
        low_attendance_threshold=low_attendance_threshold,
        high_performer_score_threshold=high_performer_threshold,
    )
