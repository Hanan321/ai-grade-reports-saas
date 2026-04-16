import pandas as pd

from engine.mapping import apply_column_mapping, infer_column_mapping
from utils.validators import validate_column_mapping


def test_infer_column_mapping_detects_known_source_columns():
    df = pd.DataFrame(columns=["Student  Name", "homework score", "QuizScore", "attendance %"])

    mapping = infer_column_mapping(df)

    assert mapping["student_name"] == "Student  Name"
    assert mapping["homework"] == "homework score"
    assert mapping["quizscore"] == "QuizScore"
    assert mapping["attendance_percent"] == "attendance %"


def test_apply_column_mapping_renames_selected_columns_only():
    df = pd.DataFrame(
        {
            "Student  Name": ["Ali"],
            "Math Homework": [95],
            "Ignored Column": ["extra"],
        }
    )
    mapping = {
        "student_name": "Student  Name",
        "homework": "Math Homework",
        "subject": None,
    }

    mapped = apply_column_mapping(df, mapping)

    assert mapped.columns.tolist() == ["student_name", "homework"]
    assert mapped.loc[0, "student_name"] == "Ali"


def test_validate_column_mapping_blocks_missing_required_fields_and_duplicates():
    mapping = {
        "student_name": "Name",
        "subject": "Name",
        "test_date": None,
        "homework": "Homework",
        "quizscore": "Quiz",
        "exam_score": "Exam",
        "attendance_percent": "Attendance",
    }

    errors = validate_column_mapping(mapping, ["Name", "Homework", "Quiz", "Exam", "Attendance"])

    assert any("test_date" in error for error in errors)
    assert any("Name" in error for error in errors)
