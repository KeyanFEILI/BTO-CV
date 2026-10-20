# Shared ranking workbook

## Destination and scope

Resolve the destination from `SCORE_WORKBOOK_URL`, or from a private
`references/workbook.local.json` beside this file containing
`{"url": "the user-provided Excel sharing link"}`. Never commit that file.
If neither is configured, ask once for the shared workbook link and retain it
in that private local configuration when authorised. Never guess the destination.
A colleague must configure their own authorised link; no workbook is bundled.

Update this workbook whenever `score` delivers a JD ranking, including revised
rankings. This is an in-task update, not a background watcher. Keep the link and
candidate data private; do not put them in a public repository. Never change
sharing permissions or send invitations. Other users need their own existing
workbook access; installing this skill does not grant it.

Use a connected cloud workbook tool when available; otherwise use the signed-in
browser and normal Excel web controls. Never overwrite the cloud file with a
locally edited copy, scrape authentication tokens or assume a sharing link proves
write access. If sign-in is required, hand sign-in to the user. If writing is
blocked, deliver the list, identify the blocker and retain the pending data locally.
Retry only after the blocker changes; do not claim automatic synchronisation.

## Match the posting and columns

Inspect all current sheet names and relevant headers before choosing a destination.
Reuse the sheet that best matches the JD's role, core duties and technologies;
exact title wording is not required. Existing role sheets include Network &
Security, IAM IGA and .NET. A new posting or different client does not by itself
require a new sheet. Prefer an explicit posting-specific match when present;
otherwise choose the most relevant existing role sheet. Ask only when materially
different destinations remain equally plausible after inspecting their context.
Create a new sheet only when the JD is unrelated to the existing sheets. Name it
after the JD's job title, replacing Excel-invalid characters, limiting it to 31
characters and resolving name collisions with a short suffix. Copy the complete
header row, in the same order and wording, from the most suitable populated role
sheet; preserve header styling and table conventions. Do not copy candidate rows.
Keep the JD title/reference in a ranking-run field or alongside the assessment
scope so different postings sharing a role sheet remain distinguishable.

Map by header text, not fixed letters; preserve the user's layout. The
following header mapping is a starting point; verify the actual sheet headers.

| Ranking data | Existing header or new header when absent |
| --- | --- |
| rank | Rank |
| candidate (full name) | Candidate |
| score /100 | Match |
| latest_location | Latest location |
| relevant_experience | XP |
| short_description | Short description |
| phone | Phone Number |
| email | Email address |
| source_languages | Languages |
| JD language checks | Language flags |

For Match, inspect the existing number format: a percentage cell receives
score/100; a numeric score column receives the /100 number. Never turn 78/100 into
7800%. Preserve core/bonus breakdown in the description if no dedicated columns
exist. Keep phone and email as literal text, including international prefixes;
never interpret source text as a formula. Reuse an equivalent existing header
rather than adding duplicates. Append only missing ranking columns, without
shifting existing formulas or other columns; extend native tables as needed.

## Update rows safely

Reuse the exact candidates, scores, JD-specific experience and descriptions from
the delivered list. No second extraction or scoring pass is needed. Only candidates
with a final score >=80/100 (including exactly 80) are eligible for Excel writes;
use the unrounded calculator score, including its employer bonus. Do not add or
update rows for candidates below 80, and do not delete their pre-existing rows.
The chat ranking still includes all candidates with their explanations. Write
every eligible listed candidate, not only the top five. If none qualifies, report
that no candidate met the Excel threshold and leave the workbook unchanged,
including not creating an empty sheet. Missing information means an empty cell,
not “Not provided”, “Unknown”, “Cannot determine”, a dash or a guessed value.
An explicit language gap or unspecified required level remains a meaningful flag.

Match an existing candidate by normalised email first, or by full name with a
corroborating detail such as phone or career history. Never merge namesakes or
use batch-local IDs as persistent identity. Inspect ambiguous matches before
writing. Update an existing row instead of appending a duplicate; the same person
may correctly have one row on each different posting's sheet.

For new rows, leave all unavailable fields blank. On existing rows, missing data
in the current list must not erase known values or colleague edits. Update only
ranking fields supported by the current list. Preserve all other columns,
including Availability, Last Salary (Brut), Points to Validate, Interview, Notes,
Prep Interview with Fra, Interview with Client, Grade and cost/rate columns.
Do not replace colleague notes with language flags. Preserve formulas, validation,
formatting and candidates not included in this run. Do not reorder whole rows
without preserving their associated manual fields.

Rank describes the current comparison set; do not imply that ranks from separate
batches form one global ranking. When updating only a subset, label that scope
and date beside the affected ranks or in a dedicated ranking-run column. Re-rank
the full posting pool only when its assessments are available under the same JD
rubric; never invent scores for existing unassessed candidates.

Batch writes where supported and write sequentially to the workbook. Re-read the
affected rows immediately before writing if colleagues are editing; refresh and
reconcile conflicts rather than overwriting newer changes. After writing, read
back affected rows to verify names, posting, scores, field placement and blanks.
Check that a repeated update would not append duplicates. Confirm the workbook
has saved before reporting success. Summarise sheets and rows added/updated and
provide the workbook link. Do not test writes with fabricated candidates.
