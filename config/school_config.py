"""Private school product configuration."""

from __future__ import annotations

from config.default_config import AppConfig, BrandingConfig, ReportBrandingConfig
from engine.schemas import GradeReportConfig


SCHOOL_CONFIG = AppConfig(
    mode="school",
    branding=BrandingConfig(
        app_name="School Progress Reports",
        page_title="School Progress Reports",
        school_name="Demo Private School",
        logo_path="",
        show_branding=True,
        primary_color="#0f766e",
        accent_color="#0d9488",
    ),
    report_branding=ReportBrandingConfig(
        report_title="Demo Private School Progress Report",
        header_text="Official student progress report",
        footer_text="Prepared for Demo Private School families.",
    ),
    grade_report=GradeReportConfig(
        score_weights={
            "homework": 0.25,
            "quizscore": 0.25,
            "exam_score": 0.50,
        },
        low_attendance_threshold=85.0,
        at_risk_score_threshold=72.0,
        high_performer_score_threshold=90.0,
    ),
)
