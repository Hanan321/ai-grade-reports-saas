import pandas as pd

from engine.summaries import build_student_summary, build_subject_summary


def test_build_student_summary_outputs_expected_rollups():
    df = pd.DataFrame(
        {
            "student_name": ["Ali Ahmed", "Ali Ahmed", "Aisha Ali"],
            "subject": ["Math", "Science", "Math"],
            "test_date": pd.to_datetime(["2025-01-03", "2025-01-04", "2025-01-05"]),
            "final_score": [80.0, 90.0, 70.0],
            "attendance_percent": [90.0, 80.0, 75.0],
            "at_risk": [False, False, True],
        }
    )

    summary = build_student_summary(df)
    ali = summary[summary["student_name"] == "Ali Ahmed"].iloc[0]

    assert ali["tests_taken"] == 2
    assert ali["avg_final_score"] == 85.0
    assert ali["avg_attendance"] == 85.0
    assert bool(ali["any_risk"]) is False


def test_build_subject_summary_outputs_expected_rollups():
    df = pd.DataFrame(
        {
            "student_name": ["Ali Ahmed", "Aisha Ali"],
            "subject": ["Math", "Math"],
            "test_date": pd.to_datetime(["2025-01-03", "2025-01-05"]),
            "final_score": [80.0, 70.0],
            "attendance_percent": [90.0, 70.0],
            "at_risk": [False, True],
        }
    )

    summary = build_subject_summary(df)

    assert summary.loc[0, "subject"] == "Math"
    assert summary.loc[0, "tests_taken"] == 2
    assert summary.loc[0, "avg_final_score"] == 75.0
    assert summary.loc[0, "avg_attendance"] == 80.0

