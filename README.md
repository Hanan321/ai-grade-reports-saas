# Student Grade Report Cleaner

A small Streamlit MVP that turns messy student grade sheets into cleaned data and downloadable summary reports.

The project now supports one shared codebase with two commercial modes:

- **Self-serve SaaS** for teachers, tutors, and school office staff.
- **School/private school** mode for branded school deployments and demos.

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
├── config/
│   ├── default_config.py
│   ├── saas_config.py
│   └── school_config.py
├── engine/
│   ├── processing.py
│   ├── summaries.py
│   ├── exports.py
│   ├── parent_contacts.py
│   ├── parent_matching.py
│   ├── email_settings.py
│   ├── storage.py
│   ├── report_files.py
│   ├── email_delivery.py
│   └── schemas.py
├── data/
│   ├── parent_contacts.csv
│   └── email_settings.json
├── ui/
│   ├── branding.py
│   ├── styles.py
│   ├── sections.py
│   ├── dashboard.py
│   ├── email_settings_section.py
│   ├── parent_contacts_section.py
│   └── email_section.py
├── utils/
│   ├── contact_validators.py
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

The default SaaS mode preserves the notebook's current scoring rules:

```text
final_score = homework * 0.30 + quizscore * 0.30 + exam_score * 0.40
```

Missing score values are treated as zero for the weighted score. `low_attendance` is true when attendance is below `80`. `at_risk` is true when `final_score` is below `70` or `low_attendance` is true.

School mode can override these values in `config/school_config.py` without changing the shared processing engine.

## Product Modes

Mode is selected by configuration, not by a second app or repository.

Default:

```bash
streamlit run app.py
```

Run SaaS mode explicitly:

```bash
APP_MODE=saas streamlit run app.py
```

Run school mode:

```bash
APP_MODE=school streamlit run app.py
```

On Streamlit Community Cloud, set `APP_MODE` in app secrets or environment settings if available. If `APP_MODE` is not set or is invalid, the app falls back to SaaS mode.

### SaaS Mode

Defined in:

```text
config/saas_config.py
```

SaaS mode uses:

- generic product title
- generic report title/footer
- standard scoring weights
- standard risk/high-performance thresholds
- no school logo/branding header

### School Mode

Defined in:

```text
config/school_config.py
```

School mode enables:

- school name in the app header
- school-specific colors
- sidebar navigation for the school dashboard
- persistent parent contact management before uploading a grade sheet
- persistent email settings management before uploading a grade sheet
- configurable report title/header/footer
- configurable grading weights
- configurable low-attendance, at-risk, and high-performance thresholds
- workbook metadata and student report text branding

To customize a private-school demo, edit `SCHOOL_CONFIG` in `config/school_config.py`.

Current school-mode demo values:

```text
school_name = Demo Private School
weights = homework 0.25, quizscore 0.25, exam_score 0.50
low_attendance_threshold = 85
at_risk_score_threshold = 72
high_performer_score_threshold = 90
```

Logo display is supported in the app header when `logo_path` points to a local image file. Full logo embedding inside every export is a next-step enhancement; the current MVP applies report title/header/footer text and workbook metadata.

## School Mode Dashboard

In school mode, the sidebar adds these pages:

- **Dashboard**: shows saved student count, saved parent email count, email settings status, and quick actions.
- **Upload & Reports**: keeps the normal upload, mapping, report generation, downloads, parent contacts, and parent email workflow.
- **Parent Contacts**: lets you add, edit, delete, and view saved parent contacts without uploading a grade sheet.
- **Email Settings**: lets you save SMTP settings without uploading a grade sheet.

The dashboard uses simple local files only:

```text
data/parent_contacts.csv
data/email_settings.json
```

The app creates the `data/` folder automatically. `parent_contacts.csv` is created with the expected columns when missing. `email_settings.json` is created when settings are saved from the **Email Settings** page.

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

After uploading a grade file and reviewing the column mapping, click **Generate Reports**. The app creates all student HTML reports at once. Open the **Parent Emails** tab to preview the ready-to-send parent email table before any email is sent.

The preview includes:

- student name
- student ID
- saved parent email
- parent name when available
- matched report filename
- match result
- send eligibility
- skip reason

Click **Send All Parent Reports** only after the preview looks correct. The main email table shows only rows marked as eligible with a valid matched parent email. Unmatched students and invalid parent emails are moved into **Skipped reports without sendable parent email** and are not sent.

## Maintaining Parent Contacts

The app-managed contact file lives here:

```text
data/parent_contacts.csv
```

Maintain this file manually with these columns:

```csv
student_name,student_id,parent1_name,parent1_email,parent2_name,parent2_email
Ali Ahmed,201,Ali Ahmed Parent,parent.ali@example.com,Second Parent,second.parent@example.com
```

Required columns:

- `student_name`
- `student_id`
- `parent1_email`

Optional columns:

- `parent1_name`
- `parent2_name`
- `parent2_email`

You can also upload a parent-contact CSV for the current Streamlit session from the **Parent Emails** tab. Uploaded CSV files may use either the newer `parent1_*` / `parent2_*` columns or the older `parent_email` / `parent_name` columns.

## Managing Parent Contacts In The App

After generating reports, open the **Parent Contacts** tab to add or update saved parent contacts without editing the CSV by hand.

The form saves:

- `student_id`
- `student_name`
- `parent1_name`
- `parent1_email`
- `parent2_name`
- `parent2_email`

`student_id`, `student_name`, and `parent1_email` are required for manual parent contact entry. Parent 2 is optional. If you save a contact with the same student ID or normalized student name, the app updates that one student row instead of creating duplicate student rows.

If the current generated reports contain the typed `student_id` for a different student name, the app blocks the save. This prevents a parent email from being attached to the wrong student's report.

The same tab also shows the saved contact table. Choose a saved contact to edit Parent 1, add or edit Parent 2, change the student details, or delete that saved contact.

The **Parent Emails** tab always includes saved contacts from `data/parent_contacts.csv`. You can also add an uploaded parent contacts CSV for the current session. The app expands `parent1_email` and `parent2_email` into separate recipients for sending. When the same student and same parent email appears in both places, the saved/manual contact from `data/parent_contacts.csv` takes priority over the uploaded CSV row.

The **Parent Emails** tab previews generated reports, not every saved contact. A manually saved contact appears in the email preview only when its `student_id` or normalized `student_name` matches one of the generated student reports. Contacts that do not match the current batch appear in **Saved/uploaded contacts not used in this batch**.

## Matching Rules

Parent contact matching is deterministic and uses your saved contact data as the source of truth.

- The app does not guess parent emails.
- The app does not use AI to infer parent emails.
- If a generated report has `student_id` and the parent contact file has the same `student_id`, the app matches by `student_id`.
- If no ID match is available, the app falls back to normalized `student_name`.
- Name normalization trims extra spacing and ignores case differences.
- If no match is found, the row is marked `unmatched` and is not sent.
- If multiple saved contacts with different parent emails match the same report, each parent email gets its own sendable row.
- If the same parent email is duplicated for one student, the app dedupes it so only one email is sent.
- If the matched parent email is invalid, the row is skipped.

## Email Configuration

Configure SMTP with environment variables or Streamlit secrets. Do not hardcode passwords in the repo.

You can also enter SMTP settings manually in the **Parent Emails** tab by choosing **Enter manually for this session** under **Email Sending Settings**. Manual values are session-only and are useful for quick testing on Streamlit Cloud.

In school mode, you can save SMTP settings from **Email Settings** before uploading a grade file. Those settings are stored in:

```text
data/email_settings.json
```

The **Parent Emails** tab can then use **Use saved school email settings** so you do not need to re-enter SMTP details after refreshing the app.

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

## Testing Persistence In School Mode

Use this flow to confirm local file persistence:

1. Start school mode:

```bash
APP_MODE=school streamlit run app.py
```

2. Open **Parent Contacts** and save a test student/parent row.
3. Refresh the browser. The row should still appear because it was saved to `data/parent_contacts.csv`.
4. Open **Email Settings** and save test SMTP settings.
5. Refresh the browser. The settings should reload from `data/email_settings.json`; the password field is visually masked by Streamlit.
6. Stop and restart Streamlit. The saved files should still be present locally.

## Run Tests

```bash
pytest
```

Smoke-test both product modes locally:

```bash
APP_MODE=saas streamlit run app.py
APP_MODE=school streamlit run app.py
```

Use `Ctrl+C` to stop the first server before starting the second, or run the second on another port:

```bash
APP_MODE=school streamlit run app.py --server.port 8502
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
- School dashboard persistence uses local files, not a database.
- Local files work well for a single local/admin deployment, but they are not a multi-user storage system.
- On some hosted platforms, including Streamlit Community Cloud, local file changes can be reset when the app redeploys or the runtime restarts.
- `data/email_settings.json` may contain an SMTP password or app password in plain local JSON. Treat that file carefully and do not commit real credentials.
- Date parsing uses pandas with `dayfirst=False`, matching the notebook's assumption.
- Missing score values count as zero in the final score, matching the notebook.
- Missing attendance does not automatically trigger `low_attendance`.
- Batch parent email sending requires SMTP configuration from environment variables, Streamlit secrets, manual session entry, or saved school email settings.
