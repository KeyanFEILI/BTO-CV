# Reuse evidence, deliver the ranking, then update Excel

Calculate all assessments privately. Send the chat ranking with only unrounded
scores >=60/100 before starting Excel inspection or planning. Keep descriptions
about fit and gaps only, with scores in separate fields. Then continue the Excel
update using its existing >=80/100 threshold (or explicit candidate selection),
and send a brief completion status after verification. No extra approval step is
needed for this already authorised sequence.

## Extraction and assessment reuse

Keep the cache under the private task's `work/` folder, outside the repository.
Never commit CVs, extracted text, profiles, employer registers or assessment data.

```sh
python scripts/evidence_cache.py TASK_CACHE SOURCE.pdf OTHER_SOURCE.docx
```

The standard-library helper calls the existing extractor on cache misses. Its
key covers file contents, file type and extractor version: renamed identical
files reuse text; changed contents invalidate it. Inspect extraction once, including
relevant images/tables, then use `EvidenceCache.save_profile(source_key, profile)`
to retain source-reconciled contacts, languages, dated roles and evidence references.
Do not conflate identical extraction with proof that two different people are one.
OCR/manual corrections belong in the reconciled profile with source references.

Reuse unchanged assessments from the private assessment JSON. Reassess affected
pairs only when their JD/rubric, source/profile, employer classification or relevant
date changes. Workbook-only edits need no reassessment. Keep all pairs in the
JSON passed to `rank.py`, which validates complete coverage. A separate
assessment-cache framework is not required.

## Context and recommendation consistency

Freeze the JD's purpose, expected outcomes, priorities and accepted equivalents
before rating candidates. `input-example.json` demonstrates the context schema.
Use `direct` evidence for delivered ownership, `equivalent` only with a named
frozen interpretation and reason, and `adjacent` for transferable but different
work. Keep required certifications/tenure/version gaps visible; never invent
equivalence to improve a score. Do not award Agile-metric points for unrelated
network SLAs or security incident counts.

The calculator returns one score/order, tied best-match IDs, missing-evidence
weight, confirmed shortfall points and validation items. Recommend from that
order. When all matches are poor, say so. Do not produce a second intuitive
ranking that contradicts the rubric; correct the interpretation for the whole JD
and rerun instead. Preserve ties and show prerequisite uncertainty separately.

## Connected Excel range workflow

1. Discover available document sessions once and verify the target workbook.
   Read the selected session's advertised tool schemas. If transport is
   unavailable, do not repeatedly rediscover it during the same unchanged run.
2. Through supported range reads, inspect sheet names, existing headers, Match
   number format and the full used role table. No new headers or metadata columns.
3. Save the observed table as a private snapshot:

```json
{
  "workbook_id": "verified-session-workbook-id",
  "sheet": "Example role",
  "jd_id": "jd-1",
  "complete": true,
  "score_format": "number",
  "headers": ["Candidate", "Match", "XP", "Phone Number", "Notes"],
  "rows": [
    {"row": 2, "values": {
      "Candidate": "Example Candidate", "Match": 81, "XP": "7-8 years",
      "Phone Number": "+352 000000", "Notes": "Preserve colleague note"
    }}
  ]
}
```

   Every existing header must be present in each row, including manual fields.
   Use `percentage` only after observing percentage formatting; numeric score
   columns use `number`. Represent formulas as `{"formula":"=...","value":123}`.
4. Prepare one plan:

```sh
python scripts/workbook_plan.py ranking.json snapshot.json plan.json
```

   Email is the primary identity key. Otherwise matching name plus phone is
   required. Same-name ambiguity stops planning rather than appending a duplicate.
   If a phone/email is absent, inspect career details and resolve the row manually
   before writing; do not bypass an ambiguity by inventing corroboration.
   The planner omits missing data, manual columns and batch ranks, preserves
   formulas, scales percentage scores, and groups adjacent changed cells without
   spanning manual/unchanged cells. Append rows retain blank unsupported fields.
5. Immediately before writing, re-read the target headers and all expected-before
   ranges in one batch. `workbook_plan.verify(plan, observed)` checks a structure
   with `workbook_id`, `sheet`, `headers`, and `ranges` mapping each planned address to its read
   matrix. Abort and replan on a conflict. No overwrite of newer colleague edits.
6. Apply the prepared ranges sequentially or with an advertised batch write.
   Respect `value_types`: phone, email and source text must be literal text,
   even if beginning with `+`, `-`, `=`, or `@`. Never treat them as formulas.
   Use the discovered session schema; do not invent tool names or use hidden
   browser APIs, tokens or direct network requests. Extend existing tables only
   over new rows, using supported controls, preserving formulas and styling.
7. Read back affected ranges and the save state once. Call `verify_applied` with
   the same target/header fields, actual range matrices and `saved: true` only
   after the service or visible UI confirms saving. A partial write or unverified
   save is not success. A second plan against the
   updated snapshot should emit no patches. A timeout requires reading back the
   affected ranges, then planning only unfinished changes; never replay appends.

The helper prepares and validates data; it does not establish Excel access or
execute cloud writes. A connected range-capable session is needed for the fast
path. When unavailable, retain the plan and use the existing normal browser
workflow if it is practical. Wait for actual cell selection and commit completion.
After one recovery for a repeated transport failure, report pending changes and
the concrete blocker rather than continuing unreliable cell edits.

## Explicit selections below 80

Only an explicit user selection authorizes an override. Pass each selected
candidate's validated ID with `--selected-id ID`, matching the named people to
the intended JD. Other candidates still require 80. Preserve actual scores and
record the selection/JD scope privately; do not add override notes or headers to
Excel. Do not export contextual recommendations automatically below the threshold.
