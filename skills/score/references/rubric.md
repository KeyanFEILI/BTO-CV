# Scoring contract

## Role fit: 95 points

Derive 4–10 distinct criteria from each JD. Weights are positive integers totalling
95. Combine overlapping wording so the same requirement is not scored twice.
Prefer explicit delivery and required capabilities to nice-to-haves. A typical
starting allocation is core skills 40, responsibility/delivery fit 30, relevant
experience/seniority 15 and sector/nice-to-haves 10; adapt to the actual JD, without
adding requirements it does not contain. Do not score CV design or keyword volume.
Exclude languages and employer prestige from these 95 points.

Each rating has a status, value, evidence references and a concise reason:

| Status | Rating | Meaning |
| --- | --- | --- |
| met | 1 | Evidence meets the criterion's required level/scope |
| partial | 0.75 | Strong relevant evidence with a specific remaining gap |
| partial | 0.5 | Some direct match, materially incomplete scope |
| partial | 0.25 | Limited or adjacent evidence, not an exact match |
| not_met | 0 | Explicit evidence confirms a shortfall |
| unknown | 0 | Insufficient CV evidence to assess |

Points = weight × rating. `met`, `partial` and `not_met` require a short CV quote
and filename/page reference. `unknown` requires an explanation, not fabricated
negative evidence. Zero for unknown means no demonstrated-match points; it does
not mean inability. Report weighted evidence coverage alongside major uncertainty.
Uncertainty should prompt verification, not an automatic hiring decision.

Use the same criterion interpretation for all candidates. A listed tool may
support basic familiarity but not years, production ownership or expert-level
delivery. A plan is not a delivered result. Count time without overlapping periods
twice; training/personal projects retain that context. Do not invent achievements,
degrees or experience duration. Keep confirmed must-have shortfalls visible even
if another criterion or the bonus raises the total. No automated exclusion.

## Relevant-employer bonus: up to 5 points

- 0: no evidenced relevant assignment at a qualifying employer, or unverified
  employer classification. State when classification remains uncertain.
- 2.5: at least one relevant assignment at a recognised large company or
  consulting firm, with both role relevance and company classification evidenced.
- 5: relevant assignments at two or more distinct qualifying employers/clients.

Use CV evidence for relevance and an employer-register entry for classification
(user-approved list, well-established company identity, or official company
reference). Apply the same register to everyone. A consulting employer and its
client on the same assignment count once. Repeat roles at the same employer count
once; parent company/subsidiary names do not multiply points. Bonus evidence must
identify the distinct assignments supporting the claimed tier. Do not give a
bonus merely for a company logo or unrelated role. Cap total score at 100.

## Language flags: zero scoring weight

Create one check per actual JD language condition, including an OR condition as
one combined check. Required and desirable conditions remain distinct. Allowed
statuses: `met`, `below_required`, `not_met`, `unknown`. Cite evidence for the first
three. If a language is listed without a level, report unknown when the required
level cannot be established; do not say it is not spoken. If the JD provides no
language conditions, use an empty list. Languages never affect score, rank,
bonus, evidence-coverage percentage or tie-breaks.

## Output and limits

Scores are demonstrated CV-to-JD fit under an explicit rubric, not objective
quality or hiring probabilities. Highlight top matches and explain low scores in
one short sentence using their most consequential weighted gaps. Avoid vague
judgments such as “weak candidate” when the actual issue is missing CV evidence.
Always assess every supplied CV for every supplied JD. Keep evidence and temporary
files local to the task; no external API, package installation or CV upload is
required for scoring arithmetic.
