# R.R. / A.F.R. formatting contract

The user-supplied BTO_CV_RR.docx and BTO_CV_AFR.docx share the authoritative layout. The anonymized packaged master uses R.R. paragraph prototypes, shared by A.F.R., with keepLines added to lists and keepNext to skill categories to prevent split bullets and orphan labels. Reference candidate content must never be copied into generated CVs.

- A4 portrait: 11906 x 16838 twips; top/left 1440, right 1274, bottom 1276; header/footer 708. One section, no page numbers or repeating banner.
- Preserve the shared inline banner image (SHA-256 aaa03ec16e78150da31f576946e12651c07167defe1b03fc382d9d9146b12cfc), centered drawing at 6172200 x 789232 EMU, hanging indent 284 and 180 twips after.
- Initials: centered, bold Century Gothic 16 pt; 120 twips after, single line spacing.
- Body: Century Gothic 11 pt. Dates and roles bold, employer regular. Main responsibilities: underlined, regular weight as in both references. Job labels have zero after and single line spacing. All jobs are unindented.
- Headings: Century Gothic 13 pt bold, #00665F, uppercase, unindented; before 110, after 80 twips, single line spacing, keepNext. Order: WORK EXPERIENCE, EDUCATION, IT SKILLS, CERTIFICATIONS AND TRAINING, LANGUAGES. Empty sections are omitted.
- Native square Word lists: numId 9, level 0, abstractNum 10; U+F0A7 in Wingdings. Numbering indentation left 360, hanging 360 twips. ListParagraph inherits Normal/Century Gothic. Preserve its contextualSpacing and reference paragraph spacing: after 10 twips, line 228, auto. All applicable sections use genuine Word lists, never typed markers.
- Later jobs receive 100 twips before their first emitted label, even if dates are missing. Skill categories receive 60 before, zero after, single line spacing and keepNext.
- Use paragraph spacing rather than D.P.'s blank paragraphs or trailing first-job line break. Candidate-specific empty paragraphs and manual pagination are not reusable layout rules. Do not force a page count, shrink fonts or add unconditional page breaks. Word paginates according to content, keepNext and keepLines.
- Equivalent rendering requires Century Gothic and Wingdings. Report font substitution. Longer content naturally changes wrapping and pagination.

## Master and compatibility

The only master is assets/BTO_CV_Template.docx. Version 3.2 requires the layout_rr_afr_v1 marker and slots initials, dates, role, employer, responsibilities, experience_bullet, education_bullet, skill_category, skill_bullet, certification_bullet and language_bullet. The marker is never emitted. Fixed headings identify section prototypes. D.P. masters fail validation rather than silently mixing layouts.

The generator changes only word/document.xml. Styles, numbering, theme, relationships, metadata and image bytes remain unchanged from the selected master. Banner and section properties are cloned unchanged. The master retains the previous anonymized package metadata; only layout paragraphs, styles, numbering and theme were taken from the reference. Never commit candidate originals, normalized candidate data or generated candidate CVs.

HTML is a secondary browser approximation and never the DOCX source.

## Paired release selection

Use the master bundled beside the installed generator. Do not download the latest main-branch template into an older release. Updates replace the whole installed package through the existing SessionStart updater. Offline generation uses the installed pair without Git authentication or a fallback approval. Record the installed plugin version; a remote release's version does not prove that its instructions were loaded in the current chat. An explicitly supplied incompatible master must fail before output is written; normal conversion can then retry using the bundled pair.

## Verification

Run automated tests. Reconcile all normalized content against the original CV, preserving date precision, client names, language levels and quantified claims. Then render with Word or a supported renderer and inspect every page for banner, square glyphs, spacing, wrapping, section order, orphan headings, split bullets and blank pages. Compare against references using the same renderer, fonts and resolution. XML checks prove structure and unchanged package parts, not visual equivalence or factual truth of source claims. Disclose incomplete rendering rather than claim an exact visual match.
