# R.R. / A.F.R. formatting contract

The R.R./A.F.R. design is retained with user-approved corrected margins and gaps. Written requirements override the corrected example where they differ (its bottom margin is 1.5 cm; the required bottom margin is 1.25 cm). The anonymized packaged master uses R.R. paragraph prototypes, shared by A.F.R., with keepLines added to lists and keepNext to skill categories to prevent split bullets and orphan labels. Reference candidate content must never be copied into generated CVs.

- A4 portrait: 11906 x 16838 twips; left/right 1134, top 850, bottom 709 (2 cm, 1.5 cm, 1.25 cm respectively, rounded to Word twips); header/footer 708. One section, no page numbers or repeating banner.
- Preserve the shared inline banner image (SHA-256 aaa03ec16e78150da31f576946e12651c07167defe1b03fc382d9d9146b12cfc), centered drawing at 6172200 x 789232 EMU, no paragraph indentation and zero space after as in the corrected reference.
- Initials: centered, bold Century Gothic 16 pt; 120 twips after, single line spacing. Follow with the corrected reference's blank 11 pt title gap (single line, 120 twips after, keepNext).
- Body: Century Gothic 11 pt. Dates and roles bold, employer regular. Main responsibilities: underlined, regular weight as in both references. Job labels have zero after and single line spacing. All jobs are unindented.
- Headings: Century Gothic 13 pt bold, #00665F, uppercase, unindented; before 0, after 80 twips, single line spacing, keepNext. Order: WORK EXPERIENCE, EDUCATION, IT SKILLS, CERTIFICATIONS AND TRAINING, LANGUAGES. Empty sections are omitted.
- Native square Word lists: numId 9, level 0, abstractNum 10; U+F0A7 in Wingdings. Numbering indentation left 360, hanging 360 twips. ListParagraph inherits Normal/Century Gothic. Preserve its contextualSpacing and reference paragraph spacing: after 10 twips, line 228, auto. All applicable sections use genuine Word lists, never typed markers.
- Insert one empty 11 pt Century Gothic body paragraph between experience entries, even if dates or bullets are missing. Insert two such paragraphs between populated major sections; omit gaps for absent sections. Gap paragraphs have single line spacing, zero before/after, keepNext and no numbering. Skill categories receive 60 before, zero after, single line spacing and keepNext.
- Use the explicit body-line gaps above without extra job/heading spacing or trailing first-job line breaks. Candidate-specific empty paragraphs and manual pagination are not reusable layout rules. Do not force a page count, shrink fonts or add unconditional page breaks. Word paginates according to content, keepNext and keepLines.
- Equivalent rendering requires Century Gothic and Wingdings. Report font substitution. Longer content naturally changes wrapping and pagination.

## Master and compatibility

The only master is assets/BTO_CV_Template.docx. Version 3.2.2 requires the layout_rr_afr_v2 marker and slots gap, initial_gap, initials, dates, role, employer, responsibilities, experience_bullet, education_bullet, skill_category, skill_bullet, certification_bullet and language_bullet. The marker is never emitted. Fixed headings identify section prototypes. D.P. masters fail validation rather than silently mixing layouts.

The generator changes only word/document.xml. Styles, numbering, theme, relationships, metadata and image bytes remain unchanged from the selected master. Banner and section properties are cloned unchanged. The master retains the previous anonymized package metadata; only layout paragraphs, styles, numbering and theme were taken from the reference. Never commit candidate originals, normalized candidate data or generated candidate CVs.

HTML is a secondary browser approximation and never the DOCX source.

## Paired release selection

Use the master bundled beside the installed generator. Do not download the latest main-branch template into an older release. Updates replace the whole installed package through the existing SessionStart updater. Offline generation uses the installed pair without Git authentication or a fallback approval. Record the installed plugin version; a remote release's version does not prove that its instructions were loaded in the current chat. An explicitly supplied incompatible master must fail before output is written; normal conversion can then retry using the bundled pair.

## Verification

Run automated tests. Reconcile all normalized content against the original CV, preserving date precision, client names, language levels and quantified claims. Then render with Word or a supported renderer and inspect every page for banner, square glyphs, spacing, wrapping, section order, orphan headings, split bullets and blank pages. Compare against references using the same renderer, fonts and resolution. XML checks prove structure and unchanged package parts, not visual equivalence or factual truth of source claims. Disclose incomplete rendering rather than claim an exact visual match.

## Language display rules

Use English language names and only Native, Fluent, Professional. Professional represents Professional working proficiency. Native / mother tongue maps to Native; C1 / C2 / fluent to Fluent; B2 / professional working proficiency / full professional proficiency to Professional. Include only explicit, source-supported levels meeting this threshold. Omit B1, A1, A2, intermediate, basic, beginner, elementary and limited proficiency without upgrading them. Omit missing, ambiguous or conflicting levels and flag them separately for review, including conflicts across entries. Do not infer levels from nationality, residence, work location, the CV language, exam scores or a short video spoken sample. Native requires an explicit native or mother-tongue statement.

Use Language (Level), for example French (Native), English (Fluent), German (Professional). No CEFR codes, scores, progress bars or other labels in LANGUAGES. Keep the existing native square bullet formatting and source order. Omit the section if no language qualifies. Every output entry must pass source-evidence, approved-label and threshold checks. Keep supplied language exam/certification facts in certifications, including scores, source exam levels, dates and status, even when the corresponding language is omitted; never invent an earned qualification. Generator language_review notes and CLI stderr warnings remain outside the CV.
