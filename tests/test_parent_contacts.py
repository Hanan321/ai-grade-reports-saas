import pandas as pd

from engine.parent_contacts import (
    delete_parent_contact,
    merge_parent_contacts,
    upsert_parent_contact,
)


def test_upsert_creates_contact_with_valid_email():
    contacts, action, messages = upsert_parent_contact(
        pd.DataFrame(),
        student_id="201",
        student_name="Ali Ahmed",
        parent_email="parent@example.com",
        parent_name="Parent",
    )

    assert action == "created"
    assert messages == []
    assert contacts.loc[0, "student_id"] == "201"
    assert contacts.loc[0, "parent_email"] == "parent@example.com"


def test_upsert_updates_existing_contact_by_student_id():
    initial = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent_email": "old@example.com",
                "parent_name": "Old",
            }
        ]
    )

    contacts, action, messages = upsert_parent_contact(
        initial,
        student_id="201",
        student_name="Ali Ahmed",
        parent_email="new@example.com",
        parent_name="New",
    )

    assert action == "updated"
    assert messages == []
    assert len(contacts) == 1
    assert contacts.loc[0, "parent_email"] == "new@example.com"


def test_upsert_rejects_student_id_used_by_different_student_name():
    initial = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent_email": "ali@example.com",
                "parent_name": "Ali Parent",
            }
        ]
    )

    contacts, action, messages = upsert_parent_contact(
        initial,
        student_id="201",
        student_name="Different Student",
        parent_email="different@example.com",
        parent_name="Different Parent",
    )

    assert action == "error"
    assert len(contacts) == 1
    assert contacts.loc[0, "student_name"] == "Ali Ahmed"
    assert any("Student ID 201 is already saved for Ali Ahmed" in message for message in messages)


def test_upsert_rejects_invalid_email():
    contacts, action, messages = upsert_parent_contact(
        pd.DataFrame(),
        student_id="201",
        student_name="Ali Ahmed",
        parent_email="bad-email",
        parent_name="Parent",
    )

    assert action == "error"
    assert contacts.empty
    assert "Parent email must be a valid email address." in messages


def test_upsert_rejects_missing_student_id():
    contacts, action, messages = upsert_parent_contact(
        pd.DataFrame(),
        student_id="",
        student_name="Ali Ahmed",
        parent_email="parent@example.com",
        parent_name="Parent",
    )

    assert action == "error"
    assert contacts.empty
    assert "Student ID is required for manual parent contacts." in messages


def test_delete_parent_contact_by_normalized_name():
    initial = pd.DataFrame(
        [{"student_name": "Ali Ahmed", "student_id": "", "parent_email": "parent@example.com"}]
    )

    contacts, deleted = delete_parent_contact(initial, student_id="", student_name=" ali  ahmed ")

    assert deleted is True
    assert contacts.empty


def test_merge_parent_contacts_prefers_saved_contact_over_uploaded_contact():
    uploaded = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent_email": "uploaded@example.com",
                "parent_name": "Uploaded",
            }
        ]
    )
    saved = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent_email": "saved@example.com",
                "parent_name": "Saved",
            }
        ]
    )

    merged = merge_parent_contacts(uploaded, saved)

    assert len(merged) == 1
    assert merged.loc[0, "parent_email"] == "saved@example.com"


def test_merge_parent_contacts_prefers_saved_contact_by_name_when_uploaded_has_no_id():
    uploaded = pd.DataFrame(
        [
            {
                "student_name": "ali  ahmed",
                "student_id": "",
                "parent_email": "uploaded@example.com",
                "parent_name": "Uploaded",
            }
        ]
    )
    saved = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent_email": "saved@example.com",
                "parent_name": "Saved",
            }
        ]
    )

    merged = merge_parent_contacts(uploaded, saved)

    assert len(merged) == 1
    assert merged.loc[0, "student_id"] == "201"
    assert merged.loc[0, "parent_email"] == "saved@example.com"
