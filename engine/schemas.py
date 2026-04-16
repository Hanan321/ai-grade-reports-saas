"""Column schema and mapping helpers for grade report uploads."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class GradeReportConfig:
    """Configuration for deterministic report processing.

    The alias mapping is intentionally simple. A future AI mapping layer can
    propose or update these aliases before the deterministic pipeline runs.
    """

    required_columns: tuple[str, ...] = (
        "student_name",
        "subject",
        "test_date",
        "homework",
        "quizscore",
        "exam_score",
        "attendance_percent",
    )
    duplicate_subset: tuple[str, ...] = ("student_id", "student_name", "test_date", "subject")
    score_weights: Mapping[str, float] | None = None
    low_attendance_threshold: float = 80.0
    at_risk_score_threshold: float = 70.0

    @property
    def weights(self) -> Mapping[str, float]:
        return self.score_weights or {
            "homework": 0.30,
            "quizscore": 0.30,
            "exam_score": 0.40,
        }


CANONICAL_COLUMN_ALIASES: dict[str, str] = {
    "student_name": "student_name",
    "student__name": "student_name",
    "student": "student_name",
    "name": "student_name",
    "student_id": "student_id",
    "studentid": "student_id",
    "id": "student_id",
    "grade": "grade",
    "subject": "subject",
    "test_date": "test_date",
    "date": "test_date",
    "assessment_date": "test_date",
    "homework": "homework",
    "homework_score": "homework",
    "quiz": "quizscore",
    "quiz_score": "quizscore",
    "quizscore": "quizscore",
    "exam": "exam_score",
    "exam_score": "exam_score",
    "test_score": "exam_score",
    "attendance": "attendance_percent",
    "attendance_percent": "attendance_percent",
    "attendance_percentage": "attendance_percent",
    "notes": "notes",
}


DEFAULT_CONFIG = GradeReportConfig()


def clean_column_name(column: object) -> str:
    """Convert one uploaded column label into a predictable snake_case name."""

    cleaned = str(column).strip().lower()
    cleaned = cleaned.replace("%", " percent ")
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def canonicalize_column_name(column: object) -> str:
    """Map a cleaned uploaded column name to the app's canonical schema."""

    cleaned = clean_column_name(column)
    return CANONICAL_COLUMN_ALIASES.get(cleaned, cleaned)

