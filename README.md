# Automated Assessment Checker

Trial-ready local assessment review system for checking student submissions and returning the same document with assessor-style feedback embedded directly inside it.

## Project Goal

This project is designed to support assessors by reviewing student assessment files and inserting feedback into the submitted document itself.

The system is intended to identify:

- incorrect or off-task responses,
- insufficient or underdeveloped responses,
- areas that require improvement,
- unanswered questions,
- sections left blank by the student.

The reviewed output is not a separate report. The returned file is the original assessment document with feedback added at the relevant points, so it can be used immediately by an assessor.

## Current Trial Scope

This is a trial build for one unit only.

The active unit file is:

```text
knowledge/business_comm.json
```

The unit routing file is:

```text
knowledge/metadata.json
```

For the trial, the checker uses the questions, expected key points, and minimum word expectations defined in `knowledge/business_comm.json`.

## No External AI Dependency

This version does not use:

- OpenAI,
- GPT APIs,
- external AI services,
- external assessment platforms,
- third-party redirect workflows.

All assessment checks are performed locally using the configured unit criteria.

This makes the trial simple to run and test without API keys, external accounts, or usage costs.

## Supported File Types

The trial currently supports:

- `.docx`
- `.pdf`

### DOCX Output

For Word documents, feedback is inserted as inline assessor feedback paragraphs near the relevant question or answer section.

### PDF Output

For PDF files, feedback is inserted as embedded PDF note annotations near detected question markers.

PDF support is suitable for trial testing, but DOCX gives better control because Word documents preserve editable paragraph structure more reliably than PDFs.

## How Question Reading Works

The system can read question markers and question text from the uploaded document.

It currently detects common formats such as:

```text
Q1
Q1.
Q1:
Question 1
Question 1.
Question 1:
```

It then maps the text after each detected question as the student's answer until the next question is found.

Example supported structure:

```text
Q1. Explain the importance of effective communication in a business environment.

Student answer for Q1...

Q2. Identify common barriers to communication and explain how they can be reduced.

Student answer for Q2...
```

The checker can read the question in the uploaded file, but the marking criteria still come from the configured unit JSON file. For reliable trial results, the uploaded document should use question IDs or question wording that matches the configured unit.

## What The Checker Looks For

For each configured question, the system checks:

- whether an answer exists,
- whether the answer is blank or contains only placeholder characters,
- whether the answer is too short,
- whether the answer appears unrelated to the question,
- whether the answer covers the expected key points,
- whether the answer needs more explanation or examples.

The feedback is written in a professional assessor style using a consistent structure:

```text
Judgement: [assessment judgement]. [specific issue]. Action required: [clear improvement step].
```

Example:

```text
Assessor feedback: Judgement: Partially met. The answer includes clear message and audience, but it is not developed enough to demonstrate full understanding. Action required: Add specific detail on purpose and professional tone and make the link to the question explicit.
```

## Project Structure

```text
app/
  api/
    main.py
    routes/
      evaluation.py

core/
  analyzer/
    completeness.py
  annotator/
    pdf_comment_writer.py
    word_comment_writer.py
  evaluator/
    evaluator.py
  extractor/
    answer_mapper.py
  parser/
    docx_parser.py
    pdf_parser.py
    structure_detector.py
  router/
    unit_router.py

frontend/
  app.py

knowledge/
  business_comm.json
  metadata.json

services/
  pipeline.py

storage/
  uploads/
  outputs/
```

## Main Components

### API

`app/api/routes/evaluation.py`

Handles student-file upload, optional answer-sheet upload, runs the assessment pipeline, and returns the reviewed file directly.

### Pipeline

`services/pipeline.py`

Controls the full review process:

1. Detect file type.
2. Parse document text.
3. Detect the relevant unit.
4. Map questions to student answers.
5. If an answer sheet is uploaded, map the expected answers from that file.
6. Evaluate each student answer against the answer sheet and configured criteria.
7. Insert feedback into the original document.
8. Return the reviewed document.

### Parsers

`core/parser/docx_parser.py`

Reads paragraphs from Word documents.

`core/parser/pdf_parser.py`

Extracts text blocks from PDF files.

### Answer Mapper

`core/extractor/answer_mapper.py`

Finds question markers and maps the student's answer text to each configured question.

### Evaluator

`core/evaluator/evaluator.py`

Performs local assessment checks against the configured criteria. It produces professional feedback for blank, insufficient, incorrect, partially correct, and complete responses.

### Annotators

`core/annotator/word_comment_writer.py`

Adds feedback directly into DOCX files.

`core/annotator/pdf_comment_writer.py`

Adds feedback annotations into PDF files.

### Knowledge Base

`knowledge/business_comm.json`

Stores trial unit questions and assessment expectations.

`knowledge/metadata.json`

Stores unit routing information and keywords.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the full trial project with one command:

```powershell
python run_trial.py
```

This starts:

- the backend API on `http://127.0.0.1:8000`
- the Streamlit frontend on `http://127.0.0.1:8501`

If you prefer running each service separately:

```powershell
uvicorn app.api.main:app --reload
```

```powershell
streamlit run frontend/app.py
```

Open the Streamlit URL shown in the terminal, upload the student submission, optionally upload the assessor answer sheet, review the summary dashboard, and download the reviewed file.

## API Usage

Endpoint:

```text
POST /evaluate
```

Form field:

```text
file
```

Optional form field:

```text
answer_sheet
```

Accepted file types:

```text
.docx
.pdf
```

The API returns structured review data, including:

- unit identification,
- question-by-question review results,
- trial summary counts,
- a reviewed-file download URL.

## Editing The Trial Unit

To use your real trial unit, edit:

```text
knowledge/business_comm.json
```

Question marker detection is now configurable in the same JSON file.

Example:

```json
"question_markers": {
  "prefix_templates": ["{id}", "{id}:", "Task {number}", "Section {number}"],
  "pdf_search_templates": ["{id}", "Task {number}", "Section {number}"],
  "match_question_text": true
}
```

Per-question custom markers can also be added:

```json
{
  "id": "Q1",
  "question": "Explain the importance of effective communication in a business environment.",
  "markers": ["Task 1", "Task 1:", "Section 1"],
  "key_points": ["clear message", "audience", "purpose", "professional tone"],
  "minimum_words": 45
}
```

Supported template values:

- `{id}` for the configured question ID such as `Q1`
- `{number}` for the numeric part such as `1`
- `{question}` for the configured question text

Example question format:

```json
{
  "id": "Q1",
  "question": "Explain the importance of effective communication in a business environment.",
  "key_points": [
    "clear message",
    "audience",
    "purpose",
    "professional tone"
  ],
  "minimum_words": 45
}
```

### Field Meaning

`id`

The question ID expected in the uploaded document, such as `Q1`.

`question`

The question text used for matching and feedback context.

`key_points`

The expected concepts that the answer should cover.

`minimum_words`

The minimum expected response length for the trial checker.

## Adding More Units Later

For the final product, additional units can be added by creating more JSON files in `knowledge/`.

Example:

```text
knowledge/customer_service.json
knowledge/leadership.json
knowledge/marketing.json
```

Then add each unit to:

```text
knowledge/metadata.json
```

Example:

```json
{
  "file": "customer_service.json",
  "unit_id": "customer_service",
  "name": "Customer Service Unit",
  "keywords": ["customer service", "complaints", "client communication"]
}
```

The router will use keywords from the uploaded document to select the most relevant unit.

## Current Trial Limitations

- The system is criteria-based, not a full semantic AI marker.
- It works best when the uploaded document uses clear question labels such as `Q1`, `Q2`, and `Q3`.
- It does not currently grade with numeric marks.
- PDF annotation is less precise than DOCX insertion because PDFs are not structured like editable Word documents.
- The quality of feedback depends heavily on the quality of the configured `key_points`.
- For reliable production use, unit files should include detailed criteria, acceptable alternative terms, and stronger assessment rules.

## Recommended Trial Document Format

For best results, use this structure:

```text
Assessment Title

Q1. Question text here

Student answer here

Q2. Question text here

Student answer here

Q3. Question text here

Student answer here
```

Avoid putting multiple questions and answers in the same paragraph.

## Verification Performed

The current implementation has been smoke-tested for:

- Python compilation,
- DOCX upload and feedback insertion,
- PDF upload and annotation insertion,
- blank answer detection,
- insufficient answer detection,
- off-task answer detection,
- criteria-based improvement feedback.

## Production Considerations

Before moving from trial to final product, the following should be considered:

- stronger unit/course routing,
- richer marking rubrics,
- support for tables and complex Word layouts,
- true Word comment bubbles if required,
- assessor approval workflow,
- export audit logs,
- batch uploads,
- user authentication,
- secure file cleanup,
- configurable feedback tone,
- optional human review before final download.

## Summary

This trial build provides a local, document-based assessment checker. It reads uploaded student submissions, identifies answers against one configured unit, checks for blank, insufficient, incorrect, and incomplete responses, and returns the same file with professional assessor-style feedback embedded directly in the document.
