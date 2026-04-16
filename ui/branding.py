"""Mode-specific Streamlit branding helpers."""

from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from config.default_config import AppConfig


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


def render_config_sidebar(app_config: AppConfig) -> None:
    """Show the active product mode and key configurable values."""

    with st.sidebar:
        st.subheader("Product Mode")
        st.write(app_config.mode.upper())
        if app_config.branding.show_branding:
            st.write(f"School: {app_config.branding.school_name}")
        st.caption("Switch modes with the APP_MODE environment variable.")

        st.subheader("Scoring Config")
        for field, weight in app_config.grade_report.weights.items():
            st.write(f"{field}: {weight:.2f}")
        st.write(f"At-risk threshold: {app_config.grade_report.at_risk_score_threshold:g}")
        st.write(f"Low attendance: {app_config.grade_report.low_attendance_threshold:g}")
        st.write(f"High performer: {app_config.grade_report.high_performer_score_threshold:g}")
