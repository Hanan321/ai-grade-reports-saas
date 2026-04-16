"""Validation helpers for parent contact records."""

from __future__ import annotations

from engine.parent_matching import normalize_student_id, normalize_student_name
from utils.email_validators import is_valid_email


def validate_parent_contact(
    student_name: object,
    parent_email: object,
    student_id: object = "",
) -> list[str]:
    """Return validation errors for one parent contact."""

    errors: list[str] = []
    if not normalize_student_name(student_name):
        errors.append("Student name cannot be blank.")
    if not is_valid_email(parent_email):
        errors.append("Parent email must be a valid email address.")
    if not normalize_student_id(student_id):
        errors.append("Student ID is optional, but adding it is recommended for safer matching.")
    return errors


def has_blocking_contact_errors(errors: list[str]) -> bool:
    """Return True when errors should prevent saving."""

    blocking_messages = (
        "Student name cannot be blank.",
        "Parent email must be a valid email address.",
    )
    return any(error in blocking_messages for error in errors)
