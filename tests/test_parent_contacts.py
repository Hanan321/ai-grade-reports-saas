import pandas as pd

from engine.parent_contacts import (
    delete_parent_contact,
    merge_parent_contacts,
    saved_contacts_to_recipient_contacts,
    upsert_parent_contact,
)


def test_upsert_creates_contact_with_valid_email():
    contacts, action, messages = upsert_parent_contact(
        pd.DataFrame(),
        student_id="201",
        student_name="Ali Ahmed",
        parent1_email="parent@example.com",
        parent1_name="Parent",
    )

    assert action == "created"
    assert messages == []
    assert contacts.loc[0, "student_id"] == "201"
    assert contacts.loc[0, "parent1_email"] == "parent@example.com"


def test_upsert_updates_existing_contact_by_student_and_parent_email():
    initial = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent1_email": "parent@example.com",
                "parent1_name": "Old",
            }
        ]
    )

    contacts, action, messages = upsert_parent_contact(
        initial,
        student_id="201",
        student_name="Ali Ahmed",
        parent1_email="parent@example.com",
        parent1_name="New",
    )

    assert action == "updated"
    assert messages == []
    assert len(contacts) == 1
    assert contacts.loc[0, "parent1_email"] == "parent@example.com"
    assert contacts.loc[0, "parent1_name"] == "New"


def test_upsert_rejects_student_id_used_by_different_student_name():
    initial = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent1_email": "ali@example.com",
                "parent1_name": "Ali Parent",
            }
        ]
    )

    contacts, action, messages = upsert_parent_contact(
        initial,
        student_id="201",
        student_name="Different Student",
        parent1_email="different@example.com",
        parent1_name="Different Parent",
    )

    assert action == "error"
    assert len(contacts) == 1
    assert contacts.loc[0, "student_name"] == "Ali Ahmed"
    assert any("Student ID 201 is already saved for Ali Ahmed" in message for message in messages)


def test_upsert_saves_two_parent_emails_on_one_student_row():
    contacts, action, messages = upsert_parent_contact(
        pd.DataFrame(),
        student_id="201",
        student_name="Ali Ahmed",
        parent1_email="mother@example.com",
        parent1_name="Mother",
        parent2_email="father@example.com",
        parent2_name="Father",
    )

    assert action == "created"
    assert messages == []
    assert len(contacts) == 1
    assert contacts.loc[0, "parent1_email"] == "mother@example.com"
    assert contacts.loc[0, "parent2_email"] == "father@example.com"


def test_upsert_rejects_invalid_email():
    contacts, action, messages = upsert_parent_contact(
        pd.DataFrame(),
        student_id="201",
        student_name="Ali Ahmed",
        parent1_email="bad-email",
        parent1_name="Parent",
    )

    assert action == "error"
    assert contacts.empty
    assert "Parent 1 email must be a valid email address." in messages


def test_upsert_rejects_missing_student_id():
    contacts, action, messages = upsert_parent_contact(
        pd.DataFrame(),
        student_id="",
        student_name="Ali Ahmed",
        parent1_email="parent@example.com",
        parent1_name="Parent",
    )

    assert action == "error"
    assert contacts.empty
    assert "Student ID is required for manual parent contacts." in messages


def test_upsert_rejects_invalid_parent2_email():
    contacts, action, messages = upsert_parent_contact(
        pd.DataFrame(),
        student_id="201",
        student_name="Ali Ahmed",
        parent1_email="mother@example.com",
        parent1_name="Mother",
        parent2_email="bad-email",
        parent2_name="Father",
    )

    assert action == "error"
    assert contacts.empty
    assert "Parent 2 email must be a valid email address when provided." in messages


def test_delete_parent_contact_deletes_student_contact_row():
    initial = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent1_email": "mother@example.com",
                "parent1_name": "Mother",
                "parent2_email": "father@example.com",
                "parent2_name": "Father",
            },
            {
                "student_name": "Aisha Ali",
                "student_id": "202",
                "parent1_email": "aisha@example.com",
                "parent1_name": "Aisha Parent",
            },
        ]
    )

    contacts, deleted = delete_parent_contact(
        initial,
        student_id="201",
        student_name=" ali  ahmed ",
    )

    assert deleted is True
    assert len(contacts) == 1
    assert contacts.loc[0, "student_id"] == "202"


def test_merge_parent_contacts_prefers_saved_contact_for_same_student_and_parent_email():
    uploaded = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent_email": "parent@example.com",
                "parent_name": "Uploaded",
            }
        ]
    )
    saved = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent1_email": "parent@example.com",
                "parent1_name": "Saved",
            }
        ]
    )

    merged = merge_parent_contacts(uploaded, saved)

    assert len(merged) == 1
    assert merged.loc[0, "parent_name"] == "Saved"


def test_merge_parent_contacts_keeps_different_parent_emails_for_same_student():
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
                "parent1_email": "saved@example.com",
                "parent1_name": "Saved",
            }
        ]
    )

    merged = merge_parent_contacts(uploaded, saved)

    assert len(merged) == 2
    assert set(merged["parent_email"]) == {"uploaded@example.com", "saved@example.com"}


def test_merge_parent_contacts_keeps_different_parent_email_by_name_when_uploaded_has_no_id():
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
                "parent1_email": "saved@example.com",
                "parent1_name": "Saved",
            }
        ]
    )

    merged = merge_parent_contacts(uploaded, saved)

    assert len(merged) == 2
    assert set(merged["parent_email"]) == {"uploaded@example.com", "saved@example.com"}


def test_saved_contacts_to_recipient_contacts_expands_parent1_and_parent2():
    saved = pd.DataFrame(
        [
            {
                "student_name": "Ali Ahmed",
                "student_id": "201",
                "parent1_name": "Mother",
                "parent1_email": "mother@example.com",
                "parent2_name": "Father",
                "parent2_email": "father@example.com",
            }
        ]
    )

    recipients = saved_contacts_to_recipient_contacts(saved)

    assert len(recipients) == 2
    assert set(recipients["parent_email"]) == {"mother@example.com", "father@example.com"}
