"""Persistent parent contact storage and merge helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from engine.parent_matching import (
    CONTACT_COLUMNS,
    WIDE_CONTACT_COLUMNS,
    normalize_student_id,
    normalize_student_name,
    prepare_parent_contacts,
)
from utils.contact_validators import (
    has_blocking_contact_errors,
    validate_saved_parent_contact,
)


SAVED_PARENT_CONTACTS_PATH = Path("data/parent_contacts.csv")


def empty_parent_contacts() -> pd.DataFrame:
    """Return an empty parent contacts table with the expected columns."""

    return pd.DataFrame(columns=list(WIDE_CONTACT_COLUMNS))


def load_saved_parent_contacts(path: Path = SAVED_PARENT_CONTACTS_PATH) -> pd.DataFrame:
    """Load manually saved parent contacts, creating an empty table when missing."""

    if not path.exists():
        return empty_parent_contacts()
    return normalize_saved_contact_columns(pd.read_csv(path, dtype=str).fillna(""))


def save_parent_contacts(contacts: pd.DataFrame, path: Path = SAVED_PARENT_CONTACTS_PATH) -> None:
    """Persist parent contacts to CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    normalize_saved_contact_columns(contacts).to_csv(path, index=False)


def normalize_saved_contact_columns(contacts: pd.DataFrame) -> pd.DataFrame:
    """Return saved contacts with one row per student and parent1/parent2 columns."""

    normalized = contacts.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]

    if "parent_email" in normalized.columns and "parent1_email" not in normalized.columns:
        normalized = _long_contacts_to_wide(normalized)

    for column in WIDE_CONTACT_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""
    normalized = normalized[list(WIDE_CONTACT_COLUMNS)].fillna("")
    for column in WIDE_CONTACT_COLUMNS:
        normalized[column] = normalized[column].astype(str).str.strip()
    normalized["student_id"] = normalized["student_id"].map(normalize_student_id)
    return normalized


def upsert_parent_contact(
    contacts: pd.DataFrame,
    student_id: object,
    student_name: object,
    parent1_email: object,
    parent1_name: object = "",
    parent2_email: object = "",
    parent2_name: object = "",
) -> tuple[pd.DataFrame, str, list[str]]:
    """Insert or update one student contact row with up to two parent emails."""

    errors = validate_saved_parent_contact(
        student_id=student_id,
        student_name=student_name,
        parent1_email=parent1_email,
        parent2_email=parent2_email,
    )
    if has_blocking_contact_errors(errors):
        return normalize_saved_contact_columns(contacts), "error", errors

    normalized = normalize_saved_contact_columns(contacts)
    row = {
        "student_name": str(student_name).strip(),
        "student_id": normalize_student_id(student_id),
        "parent1_name": str(parent1_name).strip(),
        "parent1_email": str(parent1_email).strip(),
        "parent2_name": str(parent2_name).strip(),
        "parent2_email": str(parent2_email).strip(),
    }
    id_conflict = _student_id_conflict(normalized, row["student_id"], row["student_name"])
    if id_conflict is not None:
        conflict_name = id_conflict["student_name"]
        errors.append(
            f"Student ID {row['student_id']} is already saved for {conflict_name}. "
            "Use the correct student ID or update that existing contact."
        )
        return normalized, "error", errors

    matching_index = _matching_student_contact_index(normalized, row["student_id"], row["student_name"])

    if matching_index is not None:
        updated = normalized.copy()
        updated.loc[matching_index, list(WIDE_CONTACT_COLUMNS)] = [
            row[column] for column in WIDE_CONTACT_COLUMNS
        ]
        return updated.reset_index(drop=True), "updated", errors

    updated = pd.concat([normalized, pd.DataFrame([row])], ignore_index=True)
    return updated, "created", errors


def delete_parent_contact(
    contacts: pd.DataFrame,
    student_id: object,
    student_name: object,
) -> tuple[pd.DataFrame, bool]:
    """Delete one saved student contact row."""

    normalized = normalize_saved_contact_columns(contacts)
    matching_index = _matching_student_contact_index(
        normalized,
        normalize_student_id(student_id),
        str(student_name).strip(),
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
        prepare_parent_contacts(uploaded_contacts)[list(CONTACT_COLUMNS)]
        if uploaded_contacts is not None
        else pd.DataFrame(columns=list(CONTACT_COLUMNS))
    )
    saved = saved_contacts_to_recipient_contacts(saved_contacts)
    merged = uploaded.copy()

    for _, row in saved.iterrows():
        matching_index = _matching_recipient_contact_index(
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
        return pd.DataFrame(columns=list(CONTACT_COLUMNS))
    return prepare_parent_contacts(merged)[list(CONTACT_COLUMNS)].reset_index(drop=True)


def saved_contacts_to_recipient_contacts(saved_contacts: pd.DataFrame) -> pd.DataFrame:
    """Expand saved parent1/parent2 rows into one row per parent email."""

    saved = normalize_saved_contact_columns(saved_contacts)
    rows: list[dict[str, str]] = []
    for _, row in saved.iterrows():
        base = {
            "student_name": row["student_name"],
            "student_id": row["student_id"],
        }
        for parent_number in (1, 2):
            email = str(row[f"parent{parent_number}_email"]).strip()
            name = str(row[f"parent{parent_number}_name"]).strip()
            if not email:
                continue
            rows.append(
                {
                    **base,
                    "parent_email": email,
                    "parent_name": name,
                }
            )
    return pd.DataFrame(rows, columns=list(CONTACT_COLUMNS))


def _matching_student_contact_index(
    contacts: pd.DataFrame,
    student_id: str,
    student_name: str,
) -> int | None:
    normalized_name = normalize_student_name(student_name)
    for index, row in contacts.iterrows():
        row_id = normalize_student_id(row["student_id"])
        row_name = normalize_student_name(row["student_name"])
        if student_id and row_id == student_id:
            return index
        elif normalized_name and row_name == normalized_name:
            return index
    return None


def _matching_recipient_contact_index(
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


def _long_contacts_to_wide(contacts: pd.DataFrame) -> pd.DataFrame:
    for column in CONTACT_COLUMNS:
        if column not in contacts.columns:
            contacts[column] = ""

    wide_rows: dict[str, dict[str, str]] = {}
    for _, row in contacts.iterrows():
        student_id = normalize_student_id(row["student_id"])
        student_name = str(row["student_name"]).strip()
        key = student_id or normalize_student_name(student_name)
        if not key:
            continue

        wide_row = wide_rows.setdefault(
            key,
            {
                "student_name": student_name,
                "student_id": student_id,
                "parent1_name": "",
                "parent1_email": "",
                "parent2_name": "",
                "parent2_email": "",
            },
        )
        parent_email = str(row["parent_email"]).strip()
        parent_name = str(row["parent_name"]).strip()
        if not parent_email:
            continue
        if not wide_row["parent1_email"]:
            wide_row["parent1_name"] = parent_name
            wide_row["parent1_email"] = parent_email
        elif not wide_row["parent2_email"] and wide_row["parent1_email"].lower() != parent_email.lower():
            wide_row["parent2_name"] = parent_name
            wide_row["parent2_email"] = parent_email

    return pd.DataFrame(list(wide_rows.values()), columns=list(WIDE_CONTACT_COLUMNS))
