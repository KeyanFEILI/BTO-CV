# BTO CV

Convert supplied PDF or Word CVs and career details into BTO-branded HTML. PDF export is optional when a renderer is available.

## Install and use

This is a local Codex skill, not a published ChatGPT plugin. Use a desktop environment with local skill installation. Ordinary ChatGPT desktop access alone is not sufficient proof of compatibility.

1. Give the colleague read access to this private GitHub repository and complete their normal GitHub authentication.
2. In their supported desktop environment, ask: `Install the bto-cv skill from https://github.com/KeyanFEILI/BTO-CV at path skills/bto-cv.`
3. On the next turn, attach a candidate CV and ask: `Use $bto-cv to convert this CV into BTO HTML format.`

If the skill is not listed, start a new chat. If the environment has no skill installer or authenticated repository retrieval, resolve those prerequisites before using this workflow. Never paste passwords or tokens into a chat.

## Maintain the template

The single editable master is `skills/bto-cv/assets/BTO_CV_Template.html` in this repository. Edit it here, review the result, commit, and push to the default branch using GitHub Desktop.

For each new CV, the skill attempts to retrieve that master from GitHub. Changes apply after a successful retrieval. If retrieval fails, it reports the problem and asks before using the bundled snapshot. This is not background auto-sync. Previously generated CVs do not change.

The installed asset is an intentional fallback snapshot, not another master. Update installed skill instructions separately after changing `skills/bto-cv/SKILL.md`; request an update to the existing skill rather than creating a second copy. The installer may reject an already-existing destination.

## Edit a generated CV

Open the HTML in a browser, choose Edit CV, and change the text. Save HTML copy downloads the current edits. Print / Save PDF opens the browser print dialog; use Letter paper with browser headers and footers disabled. Closing without saving loses edits.

## Verification and sharing

Authenticated installation and retrieval have been tested on the maintainer's computer, along with HTML editing, saving, responsive layout, and print rendering. A colleague's separate account still needs a pilot test: install, retrieve the current template, generate a fictional CV, and confirm that a later pushed template change appears on the next generation. Failed retrieval must be reported explicitly.

Keep candidate CVs, generated candidate output, and credentials outside this repository. Only the reusable skill, template, and maintenance documentation belong here.
