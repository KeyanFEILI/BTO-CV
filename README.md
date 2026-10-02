# BTO CV

Turn a supplied CV into BTO-branded HTML, with browser editing and print-to-PDF support.

## Start here

Accept the owner's GitHub invitation to this private repository first. You need a local Codex environment that supports plugins and authenticated Git access; installing the ordinary ChatGPT desktop app alone is not enough.

Copy this message into a local Codex chat:

> Install BTO CV from https://github.com/KeyanFEILI/BTO-CV.git. First check whether bto-cv@bto-cv-marketplace is already installed. If not, register the marketplace using `codex plugin marketplace add https://github.com/KeyanFEILI/BTO-CV.git --ref main`, then run `codex plugin add bto-cv@bto-cv-marketplace`. Stop and explain if repository access or the required commands are unavailable. Verify that the plugin is installed and enabled. If a standalone bto-cv skill exists, preserve it until the plugin is verified, then help me retire that duplicate. Do not ask me to paste passwords or tokens. Tell me when to start a new chat.

Once installed, start a new chat, select **BTO CV** from the plugin menu, attach your CV, and ask:

> Convert this CV into BTO HTML format using the latest template.

**Only need the install screen?** After marketplace registration, use [Install BTO CV](codex://plugins/install/bto-cv?marketplace=bto-cv-marketplace), or open Plugins → BTO CV Marketplace → BTO CV. Some browsers do not open app links; use the plugin menu instead.

## Test it without personal data

Use [the fictional sample CV](examples/sample-cv.txt). Check that all supplied facts are preserved, no qualifications are invented, and the response identifies the template revision. Open the HTML, edit the name, save a copy, reopen it, and check Print / Save PDF.

The owner can then push a small template change. Generate a new CV and check that it uses the new revision. A colleague's separate account still needs this pilot test.

## Updates

| Change | What happens |
| --- | --- |
| Owner edits and pushes the HTML template | The next generation retrieves it from GitHub, subject to working access. |
| Owner updates plugin or skill instructions | Refresh the marketplace and update the installed plugin; use a new chat. |
| A CV was already generated | That file remains unchanged. |

To request a package update, paste this into local Codex:

> Update bto-cv@bto-cv-marketplace from its registered GitHub source. Run `codex plugin marketplace upgrade bto-cv-marketplace`, inspect the installed version, and use the supported plugin update or reinstall flow if needed. Verify the resulting version without creating a second copy. Tell me when to start a new chat.

If template retrieval fails, the skill asks before using its bundled fallback. Refreshing a marketplace alone does not guarantee that an installed plugin or an active chat has reloaded its instructions.

## Troubleshooting

| Problem | Next step |
| --- | --- |
| Repository unavailable or 404 | Accept the GitHub invitation and check the signed-in GitHub account. |
| Codex/plugin commands unavailable | Use a supported local Codex environment; this is not a public ChatGPT directory listing. |
| Plugin not visible after installation | Start a new chat; restart the desktop app if necessary. |
| Two BTO CV skills appear | Keep the verified plugin and retire the old standalone installation. |
| Changes disappear after closing HTML | Use Save HTML copy before closing; edits are not automatically stored. |

## For the maintainer

- Master template: `skills/bto-cv/assets/BTO_CV_Template.html`.
- Workflow instructions: `skills/bto-cv/SKILL.md`.
- Plugin version and presentation: `plugin.json`.
- Marketplace catalog: `.agents/plugins/marketplace.json`.

Edit the master in this repository, review it, commit, and push. Increment the plugin version for package releases. Keep candidate files and generated CVs outside this repository. The installed template is a fallback snapshot, not a second master.

This private marketplace requires initial GitHub access and marketplace registration. A repository or install link cannot grant either automatically.
