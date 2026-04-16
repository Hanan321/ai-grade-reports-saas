import pandas as pd

from engine.filters import get_at_risk_students, get_high_performing_students, get_low_attendance_students


def test_get_at_risk_students_returns_only_flagged_rows():
    df = pd.DataFrame(
        {
            "student_name": ["Ali", "Aisha"],
            "at_risk": [True, False],
            "final_score": [65, 92],
        }
    )

    at_risk = get_at_risk_students(df)

    assert at_risk["student_name"].tolist() == ["Ali"]


def test_get_high_performing_students_uses_config_threshold():
    df = pd.DataFrame(
        {
            "student_name": ["Ali", "Aisha"],
            "final_score": [84.9, 85.0],
        }
    )

    high_performers = get_high_performing_students(df)

    assert high_performers["student_name"].tolist() == ["Aisha"]


def test_get_low_attendance_students_returns_only_flagged_rows():
    df = pd.DataFrame(
        {
            "student_name": ["Ali", "Aisha"],
            "low_attendance": [True, False],
        }
    )

    low_attendance = get_low_attendance_students(df)

    assert low_attendance["student_name"].tolist() == ["Ali"]
