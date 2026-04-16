"""Match generated student reports to maintained parent contact records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import BinaryIO

import pandas as pd

from engine.student_reports import StudentReportFile
from utils.email_validators import is_valid_email


REQUIRED_CONTACT_COLUMNS = ("student_name", "parent_email")
CONTACT_COLUMNS = ("student_name", "student_id", "parent_email", "parent_name")


@dataclass(frozen=True)
class ReportParentMatch:
    """One generated report and its parent-contact matching outcome."""

    student_name: str
    student_id: str
    parent_email: str
    parent_name: str
    report_filename: str
    match_result: str
    send_eligible: bool
    skip_reason: str
    report: StudentReportFile


def normalize_student_name(value: object) -> str:
    """Normalize a student name for deterministic matching."""

    if value is None or pd.isna(value):
        return ""
    normalized = re.sub(r"\s+", " ", str(value).strip().lower())
    return normalized


def normalize_student_id(value: object) -> str:
    """Normalize a student ID for deterministic matching."""

    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def load_parent_contacts(source: str | Path | BinaryIO) -> pd.DataFrame:
    """Load maintained parent contacts from a CSV file."""

    contacts = pd.read_csv(source, dtype=str).fillna("")
    return prepare_parent_contacts(contacts)


def prepare_parent_contacts(contacts: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize parent contact data."""

    prepared = contacts.copy()
    prepared.columns = [str(column).strip().lower() for column in prepared.columns]

    missing = [column for column in REQUIRED_CONTACT_COLUMNS if column not in prepared.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Parent contacts file is missing required columns: {missing_text}.")

    if "student_id" not in prepared.columns:
        prepared["student_id"] = ""
    if "parent_name" not in prepared.columns:
        prepared["parent_name"] = ""

    prepared = prepared[list(CONTACT_COLUMNS)].fillna("")
    for column in CONTACT_COLUMNS:
        prepared[column] = prepared[column].astype(str).str.strip()

    prepared["_normalized_student_name"] = prepared["student_name"].map(normalize_student_name)
    prepared["_normalized_student_id"] = prepared["student_id"].map(normalize_student_id)
    prepared["_valid_parent_email"] = prepared["parent_email"].map(is_valid_email)
    return prepared


def match_reports_to_parent_contacts(
    reports: list[StudentReportFile],
    parent_contacts: pd.DataFrame,
) -> list[ReportParentMatch]:
    """Match each report to one saved parent contact record."""

    contacts = prepare_parent_contacts(parent_contacts)
    id_groups = _build_group_lookup(contacts, "_normalized_student_id", ignore_blank=True)
    name_groups = _build_group_lookup(contacts, "_normalized_student_name", ignore_blank=True)

    matches: list[ReportParentMatch] = []
    for report in reports:
        student_id = normalize_student_id(report.student_id)
        student_name = str(report.student_name).strip()
        name_key = normalize_student_name(student_name)

        match_rows = []
        match_basis = ""
        if student_id and student_id in id_groups:
            match_rows = id_groups[student_id]
            match_basis = "student_id"
        elif name_key and name_key in name_groups:
            match_rows = name_groups[name_key]
            match_basis = "student_name"

        matches.append(_build_match(report, student_name, student_id, match_rows, match_basis))

    return matches


def matches_to_dataframe(matches: list[ReportParentMatch]) -> pd.DataFrame:
    """Return a display-friendly table for preview and send results."""

    return pd.DataFrame(
        [
            {
                "student_name": match.student_name,
                "student_id": match.student_id,
                "parent_email": match.parent_email,
                "parent_name": match.parent_name,
                "report_filename": match.report_filename,
                "match_result": match.match_result,
                "send_eligible": match.send_eligible,
                "skip_reason": match.skip_reason,
            }
            for match in matches
        ]
    )


def _build_group_lookup(
    contacts: pd.DataFrame,
    column: str,
    ignore_blank: bool,
) -> dict[str, list[pd.Series]]:
    groups: dict[str, list[pd.Series]] = {}
    for _, row in contacts.iterrows():
        key = row[column]
        if ignore_blank and not key:
            continue
        groups.setdefault(key, []).append(row)
    return groups


def _build_match(
    report: StudentReportFile,
    student_name: str,
    student_id: str,
    match_rows: list[pd.Series],
    match_basis: str,
) -> ReportParentMatch:
    if not match_rows:
        return ReportParentMatch(
            student_name=student_name,
            student_id=student_id,
            parent_email="",
            parent_name="",
            report_filename=report.filename,
            match_result="unmatched",
            send_eligible=False,
            skip_reason="No saved parent contact matched this report.",
            report=report,
        )

    if len(match_rows) > 1:
        emails = ", ".join(sorted({str(row["parent_email"]).strip() for row in match_rows}))
        return ReportParentMatch(
            student_name=student_name,
            student_id=student_id,
            parent_email=emails,
            parent_name="",
            report_filename=report.filename,
            match_result=f"duplicate_{match_basis}",
            send_eligible=False,
            skip_reason="Multiple saved parent contacts matched this report.",
            report=report,
        )

    row = match_rows[0]
    parent_email = str(row["parent_email"]).strip()
    if not is_valid_email(parent_email):
        return ReportParentMatch(
            student_name=student_name,
            student_id=student_id,
            parent_email=parent_email,
            parent_name=str(row["parent_name"]).strip(),
            report_filename=report.filename,
            match_result="invalid_email",
            send_eligible=False,
            skip_reason="Matched contact has an invalid parent email.",
            report=report,
        )

    return ReportParentMatch(
        student_name=student_name,
        student_id=student_id,
        parent_email=parent_email,
        parent_name=str(row["parent_name"]).strip(),
        report_filename=report.filename,
        match_result=f"matched_by_{match_basis}",
        send_eligible=True,
        skip_reason="",
        report=report,
    )
