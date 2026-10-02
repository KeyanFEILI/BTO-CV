# BTO CV Marketplace

An installable BTO CV plugin for supported local Codex desktop environments. It converts supplied CVs into self-contained BTO-branded HTML. This private repository marketplace is separate from the public ChatGPT plugin directory; ordinary ChatGPT desktop access alone does not guarantee support.

## Install on a colleague's account

1. The repository owner invites the colleague's GitHub account to this private repository. The colleague accepts and signs into GitHub using their normal local Git authentication.
2. In a terminal with Codex CLI available, register this marketplace:

   ```sh
   codex plugin marketplace add https://github.com/KeyanFEILI/BTO-CV.git --ref main
   ```

   Alternatively, ask a local Codex chat to run that command. No passwords or tokens should be pasted into a chat.
3. Restart the desktop app. In Plugins, choose **BTO CV Marketplace**, then install **BTO CV**. This link can open installation after registration:

   [Install BTO CV](codex://plugins/install/bto-cv?marketplace=bto-cv-marketplace)

4. Start a new chat, select the BTO CV plugin, attach a fictional test CV, and ask: **Convert this CV into BTO HTML format.**

The install link cannot register an unknown marketplace or grant access to this private repository. If the marketplace command or local plugin browser is unavailable, that client cannot use these steps. This repository is not a public-directory listing or a verified cross-account ChatGPT share link.

## Send this to a colleague

Send the repository link: https://github.com/KeyanFEILI/BTO-CV

Ask them to follow the installation steps above after accepting your GitHub invitation. They need to complete registration and installation once. A link alone cannot replace the private-repository access and marketplace registration steps.

## Avoid duplicate installations

Use either the plugin or the standalone bto-cv skill. Existing standalone users should confirm that the plugin works, then remove their old personal bto-cv skill using their supported skill-management workflow. Do not install a second renamed copy. The maintainer's existing standalone install has not been removed by publishing this marketplace.

## Updates

The single editable template remains `skills/bto-cv/assets/BTO_CV_Template.html`. Edit, review, commit, and push it to main. The skill attempts to retrieve that file for every new CV; successful retrieval picks up the current template. If retrieval fails it asks before using the bundled snapshot. Existing CVs are unchanged.

Changes to plugin metadata or skill instructions require a plugin update. Increment `version` in `plugin.json` when releasing package changes, then refresh the marketplace:

```sh
codex plugin marketplace upgrade bto-cv-marketplace
```

Restart the desktop app and use its plugin update/reinstall flow as needed. Marketplace refresh is not a guarantee that an active chat has reloaded skill instructions. Test updates in a new chat.

## Pilot test

- Confirm installation under a colleague's separate account.
- Generate a fictional CV and check that the current GitHub template was retrieved.
- Push a small template change and generate another CV; check that it appears.
- Check that unavailable repository access produces an explicit retrieval failure.

Template retrieval, editing, saving, responsive layout, and print rendering have been tested on the maintainer's computer. A colleague-account installation still requires testing.

## Browser editing

Choose Edit CV, replace the text, and use Save HTML copy before closing. For PDF, use Print / Save PDF with Letter paper and browser headers and footers disabled.

Store only reusable plugin files here. Keep candidate CVs, generated candidate output, and credentials outside the repository.
