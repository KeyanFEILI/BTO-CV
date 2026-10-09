# Local CV uploader setup

This Windows-only helper uses Python's standard library and Windows Credential Manager. No extra paid automation service or file host is needed. The script sends files straight to api.trello.com over verified HTTPS. The existing Trello connector is still used to create cards and labels.

## One-time setup performed by the user

1. In Trello's [Power-Up administration](https://trello.com/apps/admin), create/access a Power-Up and generate its API key in the Trello Auth tab. This is an API credential setup, not a requirement to publish a Power-Up or add a paid integration.
2. Follow [Trello's authorization documentation](https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/) to authorize that key with `read,write` scope, no `account` scope. Prefer an expiring token (for example 30 days); renew when needed. The token is account-wide for its scopes: the uploader's board restriction is an application guard, not a Trello token scope. A dedicated Trello account with access only to the required board reduces credential exposure.
3. Run `python skills/trello/scripts/upload_cvs.py --configure` locally. Enter the key/token into the masked setup window. Never paste them into chat, CLI arguments, source files, GitHub secrets, or transcripts. The window stores them under `BTO-CV/TrelloUploader` in Windows Credential Manager; it performs no upload.
4. Keep the Talent Pool board private. The helper rejects public/workspace-visible boards. Authorized board members can access both CVs; private does not mean only the uploader can see them.

Do not run --configure inside a captured computer-use session while entering secrets. Let the user complete the setup window themselves. Each colleague configures their own credentials on their own machine. Windows Credential Manager is scoped to the Windows user; same-user processes can access those credentials. Use a trusted managed computer.

## Skill execution

Resolve the script from the installed Trello skill directory, not an arbitrary downloaded copy. Pass the created card's 24-character object ID or BTO LUX card ARI and absolute paths to the original and verified DOCX:

```text
python <installed-skill>/scripts/upload_cvs.py --card <card-id> --original <original-file> --bto <verified-bto.docx> --check
python <installed-skill>/scripts/upload_cvs.py --card <card-id> --original <original-file> --bto <verified-bto.docx>
```

`--check` verifies credentials, file readability/type/size, the card's board and the board's private visibility without uploading. It does not verify recruiting-team membership or promise later upload success. Ordinary execution uploads only missing matching files and verifies their returned attachment IDs, uploaded-file flags and sizes. This is metadata verification, not a byte-for-byte download comparison. SHA-256-based attachment names distinguish versions and omit the candidate name.

Files must be nonempty, at most 10 MiB each, original PDF/DOC/DOCX and BTO DOCX. This conservative cap supports small CV files; a plan/API limit can still reject them. The helper does not transform the originals, create another disk copy, log contents, delete files, or transmit to GitHub. It buffers each file in process memory and uses only direct requests to api.trello.com; redirects and environment proxies are disabled. Managed networks requiring a proxy need a reviewed adaptation rather than bypassing corporate controls.

Do not run two uploader instances for the same card concurrently. On any failure, stop, read the existing card attachments, and resume only after resolving the error. There are no blind POST retries or silent deletion of originals/older CV versions. Preserve user files; remove only task-owned temporary extraction/rendering files according to the user's retention rules. Never commit real CVs, extracted candidate data or tokens into this repository.

## Verification status

Offline tests exercise destination restrictions, multipart payloads, duplicate avoidance, partial-failure resumption, file constraints and error redaction. Windows credential storage and real Trello uploads require a local setup and a live fictional-CV test before claiming the whole workflow is verified.
