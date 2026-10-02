# BTO CV skill

A portable desktop skill for producing BTO-branded HTML CVs from supplied candidate information.

## Publish these files

Copy the contents of this folder into the existing local BTO-CV repository shown by GitHub Desktop (Repository > Show in Explorer). Preserve any existing repository files; merge this README if one already exists. Commit the new files and select Push origin.

The expected repository path is:

skills/bto-cv/SKILL.md
skills/bto-cv/assets/BTO_CV_Template.html

No candidate CVs or credentials belong in this repository.

## Install on a colleague's desktop

This package is a standalone skill, not a published ChatGPT plugin. Desktop application availability alone does not guarantee that its current mode supports filesystem skills. First test with one colleague whose desktop provides local skill installation (for example, a supported Codex environment).

In that environment, ask its skill installer:

Install the bto-cv skill from https://github.com/KeyanFEILI/BTO-CV at path skills/bto-cv.

The colleague needs authorized access to the private repository and an available authenticated retrieval tool. Use the application's normal GitHub connection or local Git authentication; do not paste access tokens into chats. Start a new chat after installation and check that bto-cv is available. If the application offers no local skill installation, this package needs a supported plugin distribution route before it can be used there.

Example request after installation:

Use the bto-cv skill to convert the attached CV into BTO HTML format.

## How updates work

Edit skills/bto-cv/assets/BTO_CV_Template.html, commit, and push to the default branch. On the next CV generation the installed skill attempts to retrieve that exact file from the default branch. A successful fetch uses the updated template. An unsuccessful fetch is reported and requires a user decision before using the bundled snapshot.

This is retrieval at use time, not automatic installation or guaranteed background synchronization. Existing generated CVs are unchanged. Changes to SKILL.md itself require updating or reinstalling the installed skill using the client's supported workflow.

## First-colleague check

1. Grant the colleague repository access and install the skill.
2. Generate a CV from fictional sample information. Check that the current template was retrieved.
3. Make a small template change, commit and push it, and generate another CV. Confirm that the new output uses that change.
4. Confirm that loss of repository access produces an explicit retrieval failure rather than silently using an old template.

The package has been checked structurally. Authenticated GitHub retrieval and cross-account installation have not yet been tested.
