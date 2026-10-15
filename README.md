# BTO CV

Convert an original PDF or Word CV into an editable BTO Word document in English, using the bundled R.R./A.F.R. master, Century Gothic typography and native square bullet lists.

Version **3.4.1** requires every source or user-approved skill to remain in IT SKILLS even when repeated under experience, with an inventory check before delivery. It retains the streamlined build-and-verify command and unchanged Word layout, including 1.5-line spacing on each “Main responsibilities:” label. Wording stays unchanged unless translation or necessary cleanup is required. Candidate facts and documents are never repository fixtures.

## Install and update

Use a local Codex environment with plugin support, Python 3 and Git. The repository's current access settings determine whether a GitHub invitation is necessary; an install link does not grant repository access.

Copy this message into a local Codex chat:

> Install BTO CV from https://github.com/KeyanFEILI/BTO-CV.git. Check whether bto-cv@bto-cv-marketplace is already installed. If not, register the marketplace with `codex plugin marketplace add https://github.com/KeyanFEILI/BTO-CV.git --ref main`, then run `codex plugin add bto-cv@bto-cv-marketplace`. Verify that it is installed and enabled, preserve any standalone skill until the plugin is verified, and tell me when to start a new chat. Do not ask for passwords or tokens.

After installation, start a new chat and select **BTO CV**, attach the original CV and ask for a BTO Word conversion. [Install BTO CV](codex://plugins/install/bto-cv?marketplace=bto-cv-marketplace) opens the install screen after marketplace registration where supported.

To update:

> Update bto-cv@bto-cv-marketplace from its registered source. Run `codex plugin marketplace upgrade bto-cv-marketplace`, inspect the installed version, and use the supported plugin update or reinstall flow if needed. Verify the result without creating a second copy and tell me when to start a new chat.

Conversion uses the template and generator from the **same installed release**. It does not fetch a template from GitHub or need network access. A failed update check does not prevent conversion with the verified installed pair. Start a new chat after an update; an existing chat does not hot-reload instructions.

## Conversion contract

- English unless another language is requested. Faithful translation; no stylistic rewrite of clear source text, stronger verbs or invented technical scope.
- Experience dates use `MM/YYYY` when months exist; year-only dates stay years. No invented days or months.
- Education and certifications put dates last: `Qualification or school, supplied location | dates`. Missing degree titles remain missing; user-approved education wording is preserved.
- IT skills have at most four coherent groups without losing tools or methods.
- Languages use Native, Fluent or Professional according to the BTO display convention. All languages remain, and exam names, scores, status and dates move to certifications.
- Responsibilities retain distinct projects, combine only related fragments, and avoid redundant "Objective" labels and duplicate bullets.

The complete content contract is in [content.md](skills/bto-cv/references/content.md); the measured layout is in [format.md](skills/bto-cv/references/format.md). The agent extracts and reconciles source content once, prepares private UTF-8 JSON, validates it, builds the document, verifies it and inspects its rendered pages. JSON is an internal step, not a user requirement.

## Verification and maintenance

Run these from the repository with Python 3:

```sh
python -m unittest discover -s tests -v
python skills/bto-cv/scripts/build_docx.py skills/bto-cv/references/input-example.json --check
```

For a finished, source-reconciled candidate JSON, build and verify in one process:

```sh
python skills/bto-cv/scripts/convert.py candidate.json BTO_CV_A.E.docx
```

The command reports build/verification times without candidate content. It does not render the document or replace source reconciliation and visual review. Reuse extracted text and JSON on revisions. Skip a separate pre-build `--check`: build already validates.

Standalone commands remain available for draft validation and diagnostics:

```sh
python skills/bto-cv/scripts/build_docx.py candidate.json --check
python skills/bto-cv/scripts/build_docx.py candidate.json BTO_CV_A.E.docx
python skills/bto-cv/scripts/verify_docx.py candidate.json BTO_CV_A.E.docx
```

Tests run in GitHub Actions on Windows and Linux. Checks cover date normalization, source precision, qualification date placement, language/exam retention, category limits, duplicate labels, editable content, native numbering, unchanged design parts and overwrite protection. They cannot prove that a translation faithfully represents an unseen CV. Source reconciliation and inspection of every rendered page are separate required checks. Prefer Word PDF export on Windows when available; use a supported renderer elsewhere. If rendering is unavailable, disclose that limitation.

The Word master is `skills/bto-cv/assets/BTO_CV_Template.docx`, paired with `skills/bto-cv/scripts/build_docx.py`. Only `word/document.xml` changes in generated documents. The anonymized master banner, styles, numbering and page settings remain intact. Do not force page counts or shrink fonts. Rendered pagination depends on content, fonts and software.

For releases, bump `plugin.json`, keep instructions, examples and tests consistent, and run the full suite. Never commit candidate originals, approved candidate CVs, extracted text or reconciliation data. Use fictional examples such as [sample-cv.txt](examples/sample-cv.txt). Setup PDFs in `docs/` predate the current content contract; use this README and the installed skill for current conversion rules.

## Automatic updater

The BTO-only SessionStart hook checks the registered marketplace at startup/resume at most once per day, retries failures after an hour, respects disabled installations and prevents overlapping checks. Review and trust it through the supported hook-review interface. Installation alone does not trust it. The hook never reads candidate documents.

Python 3, Git and a plugin-capable Codex CLI must be available. `BTO_CODEX_BIN` supports an explicit CLI path. Git access must work non-interactively; credentials are never requested or printed by the hook. To diagnose, run the installed `hooks/update.py --force --check`. `current` or `updated` confirms success; `failed` needs attention. A changed hook definition may require renewed review. New chats are required after package updates.

Maintainer: Keyan FEILI. Colleagues may generate and edit their own CVs; shared package changes are coordinated with Keyan. This convention is not an access-control mechanism.
