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
- generates one HTML report per student
- matches generated reports to saved parent contacts
- sends matched parent report emails in one batch

## Project Structure

```text
.
├── app.py
├── engine/
│   ├── processing.py
│   ├── summaries.py
│   ├── exports.py
│   ├── parent_matching.py
│   ├── email_delivery.py
│   └── schemas.py
├── data/
│   └── parent_contacts.csv
├── ui/
│   └── email_section.py
├── utils/
│   ├── email_validators.py
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

## Parent Report Email Workflow

After uploading a grade file and reviewing the column mapping, click **Generate Reports**. The app creates all student HTML reports at once. Open the **Parent Emails** tab to preview the parent-contact match table before any email is sent.

The preview includes:

- student name
- student ID when available
- saved parent email
- parent name when available
- matched report filename
- match result
- send eligibility
- skip reason

Click **Send All Parent Reports** only after the preview looks correct. The app sends only rows marked as eligible. Unmatched students, duplicate matches, and invalid parent emails are skipped.

## Maintaining Parent Contacts

The app-managed contact file lives here:

```text
data/parent_contacts.csv
```

Maintain this file manually with these columns:

```csv
student_name,student_id,parent_email,parent_name
Ali Ahmed,201,parent.ali@example.com,Ali Ahmed Parent
```

Required columns:

- `student_name`
- `parent_email`

Optional columns:

- `student_id` is preferred when available because it is the safest match key.
- `parent_name` is included for clarity in the preview.

You can also upload a parent-contact CSV for the current Streamlit session from the **Parent Emails** tab. That is useful for testing a revised contact list before replacing `data/parent_contacts.csv`.

## Matching Rules

Parent contact matching is deterministic and uses your saved contact data as the source of truth.

- The app does not guess parent emails.
- The app does not use AI to infer parent emails.
- If a generated report has `student_id` and the parent contact file has the same `student_id`, the app matches by `student_id`.
- If no ID match is available, the app falls back to normalized `student_name`.
- Name normalization trims extra spacing and ignores case differences.
- If no match is found, the row is marked `unmatched` and is not sent.
- If multiple saved contacts match the same report, the row is marked as a duplicate and is not sent until the contact data is fixed.
- If the matched parent email is invalid, the row is skipped.

## Email Configuration

Configure SMTP with environment variables or Streamlit secrets. Do not hardcode passwords in the repo.

Required:

```text
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SENDER_EMAIL=teacher@example.com
```

Usually required by your email provider:

```text
SMTP_USERNAME=teacher@example.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

For safe testing:

```text
TEST_PARENT_REPORT_EMAIL=you@example.com
```

On Streamlit Community Cloud, add the same keys in app secrets. Locally, you can export environment variables before starting Streamlit:

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_SENDER_EMAIL=teacher@example.com
export SMTP_USERNAME=teacher@example.com
export SMTP_PASSWORD=your-app-password
export SMTP_USE_TLS=true
export SMTP_USE_SSL=false
export TEST_PARENT_REPORT_EMAIL=you@example.com
streamlit run app.py
```

## Testing Batch Sending Safely

Use **Send Test Batch to Me** before sending real parent emails. Test mode sends up to three matched reports to `TEST_PARENT_REPORT_EMAIL` instead of the saved parent addresses. Test messages include `[TEST]` in the subject and show the original parent recipient in the body.

Recommended safe flow:

1. Upload the grade file.
2. Review and fix column mapping.
3. Click **Generate Reports**.
4. Open **Parent Emails**.
5. Confirm the preview table.
6. Click **Send Test Batch to Me**.
7. Check the email body and HTML attachments.
8. Click **Send All Parent Reports** when ready.

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
- Batch parent email sending requires SMTP configuration from environment variables or Streamlit secrets.
