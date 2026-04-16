"""Persistent parent contact storage and merge helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from engine.parent_matching import CONTACT_COLUMNS, normalize_student_id, normalize_student_name
from utils.contact_validators import has_blocking_contact_errors, validate_parent_contact


SAVED_PARENT_CONTACTS_PATH = Path("data/parent_contacts.csv")


def empty_parent_contacts() -> pd.DataFrame:
    """Return an empty parent contacts table with the expected columns."""

    return pd.DataFrame(columns=list(CONTACT_COLUMNS))


def load_saved_parent_contacts(path: Path = SAVED_PARENT_CONTACTS_PATH) -> pd.DataFrame:
    """Load manually saved parent contacts, creating an empty table when missing."""

    if not path.exists():
        return empty_parent_contacts()
    return normalize_contact_columns(pd.read_csv(path, dtype=str).fillna(""))


def save_parent_contacts(contacts: pd.DataFrame, path: Path = SAVED_PARENT_CONTACTS_PATH) -> None:
    """Persist parent contacts to CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    normalize_contact_columns(contacts).to_csv(path, index=False)


def normalize_contact_columns(contacts: pd.DataFrame) -> pd.DataFrame:
    """Return contacts with consistent columns and trimmed text values."""

    normalized = contacts.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]
    for column in CONTACT_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""
    normalized = normalized[list(CONTACT_COLUMNS)].fillna("")
    for column in CONTACT_COLUMNS:
        normalized[column] = normalized[column].astype(str).str.strip()
    return normalized


def upsert_parent_contact(
    contacts: pd.DataFrame,
    student_id: object,
    student_name: object,
    parent_email: object,
    parent_name: object = "",
) -> tuple[pd.DataFrame, str, list[str]]:
    """Insert or update one contact by matching student ID or normalized student name."""

    errors = validate_parent_contact(student_name, parent_email, student_id)
    if has_blocking_contact_errors(errors):
        return normalize_contact_columns(contacts), "error", errors

    normalized = normalize_contact_columns(contacts)
    row = {
        "student_name": str(student_name).strip(),
        "student_id": normalize_student_id(student_id),
        "parent_email": str(parent_email).strip(),
        "parent_name": str(parent_name).strip(),
    }
    id_conflict = _student_id_conflict(normalized, row["student_id"], row["student_name"])
    if id_conflict is not None:
        conflict_name = id_conflict["student_name"]
        errors.append(
            f"Student ID {row['student_id']} is already saved for {conflict_name}. "
            "Use the correct student ID or update that existing contact."
        )
        return normalized, "error", errors

    matching_index = _matching_parent_contact_index(
        normalized,
        row["student_id"],
        row["student_name"],
        row["parent_email"],
    )

    if matching_index is not None:
        updated = normalized.copy()
        updated.loc[matching_index, list(CONTACT_COLUMNS)] = [row[column] for column in CONTACT_COLUMNS]
        return updated.reset_index(drop=True), "updated", errors

    updated = pd.concat([normalized, pd.DataFrame([row])], ignore_index=True)
    return updated, "created", errors


def delete_parent_contact(
    contacts: pd.DataFrame,
    student_id: object,
    student_name: object,
    parent_email: object = "",
) -> tuple[pd.DataFrame, bool]:
    """Delete one contact matching the student and parent email."""

    normalized = normalize_contact_columns(contacts)
    matching_index = _matching_parent_contact_index(
        normalized,
        normalize_student_id(student_id),
        str(student_name).strip(),
        str(parent_email).strip(),
    )
    if matching_index is None:
        return normalized, False
    updated = normalized.drop(index=matching_index).reset_index(drop=True)
    return updated, True


def merge_parent_contacts(
    uploaded_contacts: pd.DataFrame | None,
    saved_contacts: pd.DataFrame,
) -> pd.DataFrame:
    """Combine uploaded and saved contacts, with saved contacts taking priority."""

    uploaded = (
        normalize_contact_columns(uploaded_contacts)
        if uploaded_contacts is not None
        else empty_parent_contacts()
    )
    saved = normalize_contact_columns(saved_contacts)
    merged = uploaded.copy()

    for _, row in saved.iterrows():
        matching_index = _matching_parent_contact_index(
            merged,
            normalize_student_id(row["student_id"]),
            str(row["student_name"]).strip(),
            str(row["parent_email"]).strip(),
        )
        if matching_index is not None:
            merged = merged.drop(index=matching_index).reset_index(drop=True)
        merged = pd.concat(
            [merged, pd.DataFrame([{column: row[column] for column in CONTACT_COLUMNS}])],
            ignore_index=True,
        )

    if merged.empty:
        return empty_parent_contacts()
    return normalize_contact_columns(merged).reset_index(drop=True)


def _matching_contact_indexes(
    contacts: pd.DataFrame,
    student_id: str,
    student_name: str,
) -> list[int]:
    normalized_name = normalize_student_name(student_name)
    matching_indexes: list[int] = []
    for index, row in contacts.iterrows():
        row_id = normalize_student_id(row["student_id"])
        row_name = normalize_student_name(row["student_name"])
        if student_id and row_id == student_id:
            matching_indexes.append(index)
        elif normalized_name and row_name == normalized_name:
            matching_indexes.append(index)
    return matching_indexes


def _matching_parent_contact_index(
    contacts: pd.DataFrame,
    student_id: str,
    student_name: str,
    parent_email: str,
) -> int | None:
    normalized_name = normalize_student_name(student_name)
    normalized_email = str(parent_email).strip().lower()
    for index, row in contacts.iterrows():
        row_email = str(row["parent_email"]).strip().lower()
        if row_email != normalized_email:
            continue

        row_id = normalize_student_id(row["student_id"])
        row_name = normalize_student_name(row["student_name"])
        if student_id and row_id == student_id:
            return index
        if normalized_name and row_name == normalized_name:
            return index
    return None


def _student_id_conflict(
    contacts: pd.DataFrame,
    student_id: str,
    student_name: str,
) -> pd.Series | None:
    if not student_id:
        return None

    normalized_name = normalize_student_name(student_name)
    for _, row in contacts.iterrows():
        row_id = normalize_student_id(row["student_id"])
        row_name = normalize_student_name(row["student_name"])
        if row_id == student_id and row_name != normalized_name:
            return row
    return None
