# Bulk UPSC Question Import — CSV Specification & Contract (Phase 3F)

## 1. Overview
The Bulk UPSC Question Import subsystem allows authorized Superadministrators to ingest batches of UPSC previous-year questions and original editorial questions into the Nexora Question Bank.

All imported questions enter the Question Bank as:
`DRAFT` (Version 1).

No questions are automatically published, approved, or made live to students.

---

## 2. Limits & Safety Safeguards
- **Format**: Comma-Separated Values (CSV).
- **Encoding**: Strict UTF-8 or UTF-8 with BOM (`utf-8-sig`). Files with null bytes (`\x00`), binary payloads, or invalid encodings are rejected safely.
- **File Validation**: Strict multi-stage inspection: size check → null byte check → strict UTF-8 decode → CSV structure validation → row validation. Uploaded content is never executed.
- **V1 Synchronous-Import Safety Limits**: Maximum 500 question data rows and 5 MB per CSV. These limits are operational safeguards to preserve server responsiveness without background queues, not a guaranteed latency SLA.
- **Duplicate Semantics**:
  - **Strong Duplicate**: Scoped to `(source_type, external_question_id)` or intra-batch collisions. Authoritative idempotency signal. Safely skipped when `skip_duplicates=true`.
  - **Potential Textual Match**: Conservative normalization preserving math symbols, operators (`==`, `!=`), code tokens, and punctuation. Advisory only (`duplicate_type="POTENTIAL"`), never automatically suppressed.
- **Transaction Model**: Option A (All-or-Nothing atomic transaction).
- **Authorization**: Superadmin only (`IsSuperadminOnly`). Students receive `403 Forbidden`.

---

## 3. CSV Column Definitions

| Column Name | Required | Description | Example / Allowed Values |
|---|---|---|---|
| `question_type` | Yes | Type of question | `MCQ`, `MULTIPLE_SELECT`, `TRUE_FALSE`, `ASSERTION_REASON`, `MATCH_FOLLOWING`, `DESCRIPTIVE` |
| `text` | Yes | Question stem / prompt | `"With reference to the Constitution of India..."` |
| `difficulty` | Yes | Question difficulty | `EASY`, `MEDIUM`, `HARD` |
| `topic_name` | Conditional | Human-readable topic name | `"Fundamental Rights"` |
| `chapter_name` | Optional | Chapter name for disambiguation | `"Constitution & Fundamental Rights"` |
| `subject_name` | Optional | Subject name for disambiguation | `"Polity"` |
| `domain_name` | Optional | Domain name for context | `"General Studies"` |
| `topic_id` | Optional | UUID of topic in Learning taxonomy | `"c56a4180-65aa-42ec-a945-5fd21dec0538"` |
| `choice_a` | MCQ / MS | Option A text | `"Right to Freedom of Religion"` |
| `choice_b` | MCQ / MS | Option B text | `"Right to Property"` |
| `choice_c` | Optional | Option C text | `"Right to Equality"` |
| `choice_d` | Optional | Option D text | `"Right to Constitutional Remedies"` |
| `choice_e` | Optional | Option E text | `""` |
| `correct_answer` | MCQ / MS / TF | Correct choice letter or boolean | `D` (MCQ), `A, C` (MS), `TRUE` or `FALSE` (TF) |
| `assertion` | Assertion-Reason | Assertion statement text | `"The Attorney General has the right to speak..."` |
| `reason` | Assertion-Reason | Reason statement text | `"The Attorney General has the right to vote..."` |
| `correct_relationship` | Assertion-Reason | Correct relationship code or text | `A` (Both true, R explains A), `B` (Both true, R not explanation), `C` (A true, R false), `D` (A false, R false) |
| `match_left_items` | Match-Following | Pipe-separated list of left items | `"1. Dehong-Debang \| 2. Nokrek \| 3. Simlipal"` |
| `match_right_items` | Match-Following | Pipe-separated list of right items | `"A. Arunachal Pradesh \| B. Meghalaya \| C. Odisha"` |
| `match_pairs` | Match-Following | Comma-separated pairs | `"1:A, 2:B, 3:C"` |
| `marks` | Descriptive | Maximum marks for answer | `"15.00"` |
| `expected_answer` | Descriptive | Scoring rubric / model answer | `"Key aspects: 73rd Amendment, 3-tier structure..."` |
| `explanation` | Optional | Pedagogical explanation | `"Article 32 provides remedies..."` |
| `source_type` | Optional | Source provenance type | `UPSC_PREVIOUS_YEAR`, `ORIGINAL`, `LICENSED`, `CONTRIBUTOR` |
| `source_name` | Optional | Name of examining/origin body | `"UPSC"`, `"Nexora Editorial"` |
| `source_year` | Optional | Examination year (4 digits) | `2022` |
| `source_reference` | Optional | Paper or publication reference | `"Civil Services Preliminary Exam 2022 Paper I"` |
| `external_question_id` | Optional | Stable source identifier | `"UPSC-CSE-2022-GS1-Q15"` |

---

## 4. Question-Type Specific Examples

### 4.1 MCQ (Multiple Choice Question)
```csv
question_type,text,difficulty,topic_name,choice_a,choice_b,choice_c,choice_d,correct_answer,explanation,source_type,source_year,external_question_id
MCQ,"Which Article of the Constitution guarantees the Right to Equality?","EASY","Fundamental Rights","Article 14","Article 19","Article 21","Article 32","A","Article 14 guarantees equality before law.","UPSC_PREVIOUS_YEAR","2022","UPSC-2022-Q01"
```

### 4.2 MULTIPLE_SELECT
```csv
question_type,text,difficulty,topic_name,choice_a,choice_b,choice_c,choice_d,correct_answer,explanation,source_type,source_year,external_question_id
MULTIPLE_SELECT,"Which of the following are tributaries of the Indus River?","HARD","Drainage System","Shyok River","Zanskar River","Gilgit River","Gomati River","A, B, C","Shyok, Zanskar, and Gilgit are tributaries of Indus. Gomati is tributary of Ganges.","UPSC_PREVIOUS_YEAR","2021","UPSC-2021-Q28"
```

### 4.3 TRUE_FALSE
```csv
question_type,text,difficulty,topic_name,correct_answer,explanation,source_type,external_question_id
TRUE_FALSE,"The Governor of a State has the power to pardon a death sentence under Article 161.","EASY","State Executive","FALSE","The President alone has the power to pardon death sentences under Article 72.","ORIGINAL","NEX-POL-TF-001"
```

### 4.4 ASSERTION_REASON
```csv
question_type,text,difficulty,topic_name,assertion,reason,correct_relationship,explanation,source_type,source_year,external_question_id
ASSERTION_REASON,"Consider the following statements regarding the Attorney General:","MEDIUM","Constitutional Bodies","The Attorney General has the right to speak in Parliament.","The Attorney General has the right to vote in parliamentary joint sittings.","C","Under Article 88, the Attorney General can speak but cannot vote.","UPSC_PREVIOUS_YEAR","2019","UPSC-2019-Q54"
```

### 4.5 MATCH_FOLLOWING
```csv
question_type,text,difficulty,topic_name,match_left_items,match_right_items,match_pairs,explanation,source_type,source_year,external_question_id
MATCH_FOLLOWING,"Match the Biosphere Reserves with their States:","HARD","Biodiversity","1. Dehong-Debang | 2. Nokrek | 3. Simlipal","A. Arunachal Pradesh | B. Meghalaya | C. Odisha","1:A, 2:B, 3:C","Dehong-Debang is in AP, Nokrek in Meghalaya, Simlipal in Odisha.","UPSC_PREVIOUS_YEAR","2020","UPSC-2020-Q72"
```

### 4.6 DESCRIPTIVE
```csv
question_type,text,difficulty,topic_name,marks,expected_answer,explanation,source_type,source_year,external_question_id
DESCRIPTIVE,"Critically evaluate the significance of the 73rd Constitutional Amendment Act. (Answer in 250 words)","HARD","Local Governance","15","Constitutional status, 3-tier structure, reservation for women, financial challenges.","UPSC Mains GS Paper 2 analytical question.","UPSC_PREVIOUS_YEAR","2023","UPSC-2023-GS2-Q04"
```

---

## 5. API Endpoints

All endpoints are registered under `/api/v1/question-bank/imports/` and require Superadmin authentication:

1. **`GET /api/v1/question-bank/imports/template/`**
   - Returns downloadable `nexora_upsc_question_import_template.csv` with headers and full sample rows for all 6 question types.

2. **`POST /api/v1/question-bank/imports/preview/`**
   - Accepts `multipart/form-data` with `file`.
   - Validates file without database modifications.
   - Returns preview breakdown, type summary, and row-level validation errors.

3. **`POST /api/v1/question-bank/imports/execute/`**
   - Accepts `multipart/form-data` with `file` and optional boolean `skip_duplicates` (default: `true`).
   - Executes atomic transaction creating questions as `DRAFT`.
   - Returns total, imported, and skipped counts, plus created question UUIDs.
