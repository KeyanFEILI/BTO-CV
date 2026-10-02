# BTO formatting contract

Design authority: BTO_CV_M.M.docx and BTO_CV_D.P.docx supplied 2 October 2026. Both were rendered with Microsoft Word and all three pages of each inspected. Originals stay local; packaged masters are anonymized derivatives.

Default layout is M.M: consistent title/body indentation. DP preserves its unindented headings and category labels and its extra gap after WORK EXPERIENCE. The references differ, so they cannot both define one pixel-identical layout. Never promise identical pagination for different candidate text or a different font/rendering environment.

- Letter portrait: 12240 x 15840 twips; top/bottom 648 (.45 in), left/right 792 (.55 in); one column. Header/footer distances 720; no repeated banner, page numbers, tables, or added header/footer.
- Banner: original embedded image retained byte-for-byte; inline drawing 6126480 x 783386 EMU (6.7 x .85672 in), centered in first body paragraph. Never redraw, crop, stretch, or repeat it on later pages.
- Candidate title: initials such as A.E., centered, bold 16 pt Century Gothic. No photo/contact block unless explicitly requested.
- Body: Century Gothic 11 pt, black. Single line spacing (240 auto), zero space after. Dates and role bold; employer regular; Main responsibilities: bold and underlined.
- Section headings: 13 pt bold Century Gothic, #00665E, uppercase, source order WORK EXPERIENCE; EDUCATION; IT SKILLS; CERTIFICATIONS AND TRAINING; LANGUAGES.
- M.M regular paragraph indentation: left 426 twips, hanging 284 (first line starts 142 twips from margin). DP headings/categories have no indent. Cloned role prototypes retain their exact properties.
- Lists: native w:numPr level 0 numId 1, resolved to square-bullet definition. Marker is U+25AA in numbering, not typed text. Paragraph left 567 twips, hanging 387; marker starts 180 twips from margin, text 567. KeepLines true. No extra spacing between bullets. Education, skill content, certificates and languages are all real bullets too.
- KeepNext on headings, date, role, employer, responsibility label and skill category. Do not keep entire jobs together; long jobs can span pages, with each bullet kept intact when possible.
- One empty body line after initials and between jobs; two between major sections. DP adds a line after first section heading. These normalize inconsistent incidental blank lines in the references without shrinking or imposing a page limit.
- IT SKILLS uses bold category labels followed by one or more square bullet paragraphs. Preserve project evidence under a relevant category when supplied.

## Slots and package preservation

assets/BTO_CV_Template.docx is the default; BTO_CV_Template_DP.docx is optional. Exact paragraph tokens in word/document.xml locate initials, gap, dates, role, employer, responsibilities, experience_bullet, education_bullet, skill_category, skill_bullet, certification_bullet, language_bullet. Fixed heading text locates heading prototypes. First paragraph contains the banner; final sectPr controls page geometry.

The generator clones these source paragraphs and replaces their runs' text. It changes only word/document.xml in the selected anonymized master; styles, numbering, theme, drawing relationships, image bytes and section properties are preserved. Template preparation removed personal text, bibliography storage and identifying document properties. No source candidate records may be committed.

## Verification

Validate native lists, section geometry, all remaining package parts, literal text preservation and absence of placeholders. Render with installed Microsoft Word when available, or a supported document renderer; inspect every page. The bundled renderer was unavailable on the maintainer machine, so Microsoft Word was used. Do not claim a render passed from XML checks alone. Century Gothic and the list-marker font Tw Cen MT must resolve for equivalent appearance; report substitutions rather than silently accepting them.
