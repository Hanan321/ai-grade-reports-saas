# Student Grade Report Cleaner

A small Streamlit MVP that turns messy student grade sheets into cleaned data and downloadable summary reports.

The app currently:

- uploads CSV or Excel files
- standardizes messy column names
- normalizes student names and subjects
- parses test dates
- removes duplicate student/date/subject rows
- computes weighted final scores
- flags low attendance and at-risk students
- builds student and subject summaries
- exports cleaned CSV files and an Excel workbook

## Project Structure

```text
.
├── app.py
├── engine/
│   ├── processing.py
│   ├── summaries.py
│   ├── exports.py
│   └── schemas.py
├── utils/
│   ├── validators.py
│   └── helpers.py
├── sample_data/
│   └── students_sample_raw.csv
├── tests/
│   ├── test_processing.py
│   └── test_summaries.py
├── requirements.txt
└── README.md
```

## Grading Logic

The MVP preserves the notebook's current scoring rules:

```text
final_score = homework * 0.30 + quizscore * 0.30 + exam_score * 0.40
```

Missing score values are treated as zero for the weighted score. `low_attendance` is true when attendance is below `80`. `at_risk` is true when `final_score` is below `70` or `low_attendance` is true.

## Supported Columns

The app maps common teacher-uploaded column names into a canonical schema.

Required canonical columns:

- `student_name`
- `subject`
- `test_date`
- `homework`
- `quizscore`
- `exam_score`
- `attendance_percent`

Supported aliases include names like `Student Name`, `student__name`, `homework score`, `QuizScore`, `Exam score`, and `attendance %`.

The mapping lives in `engine/schemas.py` so a future AI column-mapping layer can suggest mappings before the deterministic Python pipeline runs.

## Local Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

Try the included sample file:

```text
sample_data/students_sample_raw.csv
```

## Run Tests

```bash
pytest
```

## Deployment

### Streamlit Community Cloud

1. Push this project to GitHub.
2. In Streamlit Community Cloud, create a new app from the repository.
3. Set the main file path to `app.py`.
4. Deploy. Streamlit will install dependencies from `requirements.txt`.

### Render

1. Push this project to GitHub.
2. Create a new Web Service from the repository.
3. Use a Python environment.
4. Set the build command:

```bash
pip install -r requirements.txt
```

5. Set the start command:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## Future Roadmap

- AI-assisted column mapping for messy teacher spreadsheets
- PDF report generation
- formatted Excel exports
- multi-class and multi-file uploads
- richer validation reports before processing
- class-level dashboards

## Notes And Limitations

- This MVP does not include authentication, billing, databases, Stripe, or Supabase.
- Date parsing uses pandas with `dayfirst=False`, matching the notebook's assumption.
- Missing score values count as zero in the final score, matching the notebook.
- Missing attendance does not automatically trigger `low_attendance`.
