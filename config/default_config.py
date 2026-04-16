"""Shared product configuration for the grade report app."""

from __future__ import annotations

from dataclasses import dataclass
import os

from engine.schemas import GradeReportConfig


VALID_MODES = ("saas", "school")


@dataclass(frozen=True)
class BrandingConfig:
    """UI branding values controlled by product mode."""

    app_name: str
    page_title: str
    school_name: str = ""
    logo_path: str = ""
    primary_color: str = "#2563eb"
    accent_color: str = "#1d4ed8"
    show_branding: bool = False


@dataclass(frozen=True)
class ReportBrandingConfig:
    """Report/export branding values controlled by product mode."""

    report_title: str = "Student Progress Report"
    header_text: str = "Student progress report for parent or teacher review"
    footer_text: str = ""


@dataclass(frozen=True)
class AppConfig:
    """Top-level app configuration for one deployable codebase."""

    mode: str
    branding: BrandingConfig
    report_branding: ReportBrandingConfig
    grade_report: GradeReportConfig


def load_app_config(mode: str | None = None) -> AppConfig:
    """Load the app configuration for the requested product mode."""

    selected_mode = (mode or os.getenv("APP_MODE") or "saas").strip().lower()
    if selected_mode not in VALID_MODES:
        selected_mode = "saas"

    if selected_mode == "school":
        from config.school_config import SCHOOL_CONFIG

        return SCHOOL_CONFIG

    from config.saas_config import SAAS_CONFIG

    return SAAS_CONFIG
