# BTO CV

Give the plugin an original PDF or Word CV and receive an editable **BTO .docx**, with the original banner, Century Gothic typography, measured spacing and real square bullet lists.

Version 3 uses one native Word template derived exclusively from D.P. The original D.P. banner, square list markers, first-job indentation, later-job alignment and paragraph spacing are retained. There is no layout switch. The original candidate files are not distributed.

## Start here

Accept the owner's GitHub invitation to this private repository first. You need a local Codex environment that supports plugins and authenticated Git access; installing the ordinary ChatGPT desktop app alone is not enough.

Copy this message into a local Codex chat:

> Install BTO CV from https://github.com/KeyanFEILI/BTO-CV.git. First check whether bto-cv@bto-cv-marketplace is already installed. If not, register the marketplace using `codex plugin marketplace add https://github.com/KeyanFEILI/BTO-CV.git --ref main`, then run `codex plugin add bto-cv@bto-cv-marketplace`. Stop and explain if repository access or the required commands are unavailable. Verify that the plugin is installed and enabled. If a standalone bto-cv skill exists, preserve it until the plugin is verified, then help me retire that duplicate. Do not ask me to paste passwords or tokens. Tell me when to start a new chat.

Once installed, start a new chat, select **BTO CV** from the plugin menu, attach your CV, and ask:

> Convert this original CV into an editable BTO Word document using the latest template.

**Only need the install screen?** After marketplace registration, use [Install BTO CV](codex://plugins/install/bto-cv?marketplace=bto-cv-marketplace), or open Plugins Ã¢â€ â€™ BTO CV Marketplace Ã¢â€ â€™ BTO CV. Some browsers do not open app links; use the plugin menu instead.

## Test it without personal data

Use [the fictional sample CV](examples/sample-cv.txt). Check that all supplied facts are preserved, no qualifications are invented, and the response identifies the template revision. Open the DOCX in Word, edit the initials, and press Enter at the end of a bullet: Word should create another list item. Check the banner and page breaks in Print Layout.

The owner can then push a small template change. Generate a new CV and check that it uses the new revision. A colleague's separate account still needs this pilot test.

## Updates

| Change | What happens |
| --- | --- |
| Owner edits and pushes the Word master | The next generation retrieves it from GitHub, subject to working access. |
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
| Output looks different on another computer | Check Century Gothic and Tw Cen MT font availability and use Microsoft Word Print Layout. |

## For the maintainer

- Master template: `skills/bto-cv/assets/BTO_CV_Template.docx`.
- Workflow instructions: `skills/bto-cv/SKILL.md`.
- Plugin version and presentation: `plugin.json`.
- Marketplace catalog: `.agents/plugins/marketplace.json`.

Edit the master in this repository, review it, commit, and push. Increment the plugin version for package releases. Keep candidate files and generated CVs outside this repository. The installed template is a fallback snapshot, not a second master.

This private marketplace requires initial GitHub access and marketplace registration. A repository or install link cannot grant either automatically.

## Exact formatting and conversion

The generator clones native Word paragraph prototypes and preserves the embedded banner, numbering, styles and page settings. It does not convert HTML to Word. IT skills, education, certificates and languages use native bullets as well as job responsibilities. Body content remains editable. Different candidate lengths naturally change pagination; fonts and rendering software can also affect page breaks. D.P. is the only formatting authority, documented in `skills/bto-cv/references/format.md`.

The agent extracts candidate information into temporary JSON and runs the bundled Python 3 generator. Users only provide their original CV; they do not need to prepare JSON. Optional HTML is a secondary preview and cannot override the Word master.

Developer check: `python -m unittest discover -s tests` verifies package preservation, native numbering, text escaping, optional sections and overwrite protection. The corrected fictional result and the D.P. reference-content replay are validated with Microsoft Word. Keep these candidate-content QA files local.

For layout updates, retain the placeholder tokens in the DOCX master. For code or rule changes, bump the plugin version and update the installed plugin.
