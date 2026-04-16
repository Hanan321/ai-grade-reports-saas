import pandas as pd

from engine.processing import clean_columns, compute_scores, parse_dates, process_grade_report, remove_duplicates


def test_clean_columns_maps_known_aliases():
    df = pd.DataFrame(columns=["Student  Name", "homework score", "QuizScore", "attendance %"])

    cleaned = clean_columns(df)

    assert cleaned.columns.tolist() == ["student_name", "homework", "quizscore", "attendance_percent"]


def test_remove_duplicates_uses_student_date_subject_identity():
    df = pd.DataFrame(
        {
            "student_id": [1, 1, 2],
            "student_name": ["Ali Ahmed", "Ali Ahmed", "Aisha Ali"],
            "test_date": pd.to_datetime(["2025-01-03", "2025-01-03", "2025-01-05"]),
            "subject": ["Math", "Math", "Math"],
        }
    )

    deduped = remove_duplicates(df)

    assert len(deduped) == 2


def test_compute_scores_preserves_weighted_logic_and_missing_scores_count_as_zero():
    df = pd.DataFrame(
        {
            "homework": [85, None],
            "quizscore": [78, 81],
            "exam_score": [92, 89],
            "attendance_percent": [88, 95],
        }
    )

    scored = compute_scores(df)

    assert scored["final_score"].tolist() == [85.7, 59.9]


def test_parse_dates_handles_mixed_notebook_formats():
    df = pd.DataFrame({"test_date": ["2025-1-03", "01/05/25", "2025/01/07", "09-01-2025"]})

    parsed = parse_dates(df)

    assert parsed["test_date"].notna().all()


def test_compute_scores_builds_risk_flags():
    df = pd.DataFrame(
        {
            "homework": [95, 80, 40],
            "quizscore": [94, 80, 40],
            "exam_score": [99, 80, 40],
            "attendance_percent": [100, 75, 95],
        }
    )

    scored = compute_scores(df)

    assert scored["low_attendance"].tolist() == [False, True, False]
    assert scored["at_risk"].tolist() == [False, True, True]


def test_full_pipeline_normalizes_text_and_scores():
    raw = pd.DataFrame(
        {
            "Student  Name": [" ali  ahmed "],
            "subject": [" math "],
            "Test Date": ["2025-01-03"],
            "homework score": ["85"],
            "QuizScore": ["78"],
            "Exam score": ["92"],
            "attendance %": ["88"],
        }
    )

    processed = process_grade_report(raw)

    assert processed.loc[0, "student_name"] == "Ali Ahmed"
    assert processed.loc[0, "subject"] == "Math"
    assert processed.loc[0, "final_score"] == 85.7
