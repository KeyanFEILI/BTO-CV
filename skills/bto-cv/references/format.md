# D.P. formatting contract

The sole design authority is BTO_CV_D.P.docx supplied by the user. The packaged master is an anonymized derivative. Never blend another CV's layout, recreate bullets, apply generic Word styles or use HTML-to-DOCX conversion.

- Letter portrait: 12240 x 15840 twips; top/bottom 648, left/right 792; header/footer distances 720. One section, no page numbers, tables or repeating banner.
- Preserve the original inline banner image and drawing: 6126480 x 783386 EMU. The source banner paragraph's centered alignment and indentation are retained.
- Initials: centered, bold Century Gothic 16 pt, no paragraph indentation.
- Body: Century Gothic 11 pt; source single line spacing, zero space after. Dates and roles bold, employer regular; Main responsibilities: bold and underlined.
- Headings: Century Gothic 13 pt bold, #00665E, uppercase, unindented. Order: WORK EXPERIENCE, EDUCATION, IT SKILLS, CERTIFICATIONS AND TRAINING, LANGUAGES. Empty optional sections are omitted.
- First job's date, role, employer and responsibility label: left 426 twips, hanging 284. Subsequent jobs have no indentation. Skills category labels have no indentation.
- Native Word square lists: numId 1, level 0, abstractNum 9; U+25AA in Tw Cen MT. Bullet paragraphs have left 567 twips, hanging 387 (marker at 180, text at 567), keepLines and source line spacing. Responsibilities, education, skills, certifications and languages all use these native lists. No literal bullet prefixes in candidate text.
- Retain source keepNext settings for headings and job/category labels. Do not force a page count or shrink fonts to fit.
- Preserve distinct blank paragraph prototypes: regular body gap, 13 pt bold heading gap after WORK EXPERIENCE, and the list gap after experience/certifications and at the document end. D.P.'s first job ends in a trailing line break before the second job; subsequent jobs use one empty body paragraph. Between sections use the two source blank paragraphs, including the list-gap variant where applicable.
- Preserve supplied content; different text lengths naturally change wrapping and pagination. Equivalent rendering requires Century Gothic and Tw Cen MT. Report font substitution.

## Master and compatibility

The only master is assets/BTO_CV_Template.docx. There is no layout selector. Version 3 adds distinct first-job, later-job and blank-paragraph slots; older masters must fail validation instead of falling back to another layout.

The slots are initials, gap, heading_gap, list_gap, first_dates, first_role, first_employer, first_responsibilities, first_last_bullet, dates, role, employer, responsibilities, experience_bullet, education_bullet, skill_category, skill_bullet, certification_bullet and language_bullet. Fixed heading text identifies section prototypes. Preserve all tokens when editing the master.

The generator changes only word/document.xml. Styles, numbering, theme, relationships and image bytes remain unchanged. The banner and section properties are cloned unchanged. Template preparation removed personal content, bibliography storage and identifying metadata. Never commit source candidate CVs or generated candidate output.

HTML is only a browser approximation. It cannot replace the native Word master or determine the DOCX's formatting.

## Verification

Run the automated tests, then render with Microsoft Word or a supported document renderer and inspect every page. For design changes, replay D.P.'s content locally and compare against the original's rendered pages. Verify bullet glyph, font, indentation, first/subsequent-job distinction, blank-line variants and unchanged package parts. Pixel comparisons must use the same renderer, fonts and resolution. Keep candidate-content QA files local. XML checks alone do not prove visual equivalence.
