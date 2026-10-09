# BTO CV

Give the plugin an original PDF or Word CV and receive an editable **BTO .docx**, with the original banner, Century Gothic typography, measured spacing and real square bullet lists.

## Talent Pool workflow (3.3.0)

The same plugin now includes `skills/bto-talent-pool`, which calls the existing `skills/bto-cv` converter and reuses its verified DOCX. There is one Word template and one generator. Both skills ship and update together through `bto-cv@bto-cv-marketplace`; no standalone Talent Pool skill is needed.

With Trello connected and access to the BTO LUX Talent Pool board, attach an original CV and ask:

> Add this CV to the Talent Pool, create its BTO Word CV, and attach both the original and BTO CVs.

The workflow checks for an existing candidate, prepares a concise profile and structured fields, selects the appropriate New list, and applies seniority based on total experience. Hybrid roles use `/`, unknown field values stay empty, exactly 5 years is Mid, and exactly 10 years is Senior. Reviewed means screened/interviewed; processing a CV alone does not change that status. When a client submission is requested, copy the pool card into the relevant opportunity group and retain its pool original.

CV-only conversion still produces a DOCX without creating Trello cards. An already verified DOCX from the same original in the current task is reused. Candidate CVs and working data stay outside this repository.

The current Trello connector supports card creation and labels but does not expose file uploads or native copying. Completing both attachments or a client copy therefore requires an authenticated browser session with those capabilities. The workflow verifies both attachments and reports incomplete steps if unavailable; it does not claim that card creation alone completes the task.

After this release is merged, update the existing plugin and start a new chat. Verify that both plugin skills are available before retiring any personal standalone `bto-talent-pool` skill created during setup. The updater already refreshes the entire plugin; no additional hook or second installation is needed.

Version 3.1 uses one native Word template derived exclusively from D.P. The original D.P. banner, square list markers, first-job indentation, later-job alignment and paragraph spacing are retained. There is no layout switch. The original candidate files are not distributed.

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
| Owner updates plugin or skill instructions | The trusted session hook checks daily at startup/resume and installs a changed version; start a new chat after an update. |
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

## Automatic updater setup (3.1.0)

Use local Codex desktop sessions. Python 3 must be available as `python` on Windows (`python3` on macOS/Linux); Git and a plugin-capable Codex CLI must be accessible to the hook. An explicit `BTO_CODEX_BIN` path is supported when Codex is not on PATH. Configure GitHub credentials for non-interactive Git access. GitHub CLI is optional if another credential helper already works.

Review and trust the BTO hook using `/hooks` in Codex CLI (or the desktop hook-review control if available). Installation alone does not trust it. No trust bypass is required. The hook checks at startup/resume, not simply when an app window opens. It is silent when current, checks at most once per 24 hours, and retries a failed check at a later session start after one hour. It updates only this marketplace/plugin, respects disabled installations, uses a lock against overlapping checks, and stores only check time/version/status in PLUGIN_DATA.

For an immediate diagnostic, run the installed `hooks/update.py --force --check` with Python. A result of `current` or `updated` confirms success; `failed` needs attention. Reopen a local session to verify the trusted hook actually fires. A changed hook definition can require renewed trust. New chats are required after package updates; old chats do not hot-reload instructions.

Maintainer: Keyan FEILI. Ask Keyan for changes to the shared plugin. You may edit your generated CVs. Private personal-repository collaborators have write access; this convention is not an access-control mechanism.

See `docs/BTO_CV_Team_Setup.pdf` and `docs/BTO_CV_Owner_Checklist.pdf`. Owner verification includes unit tests and a live GitHub update check; a separate-account pilot and each colleague's hook-trust step remain required.
