"""Rebuild the two public onboarding PDFs. Maintenance only; requires reportlab."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Image

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / 'plugin.json').read_text())['version']
DATE = '16 October 2026'
TEAL = colors.HexColor('#00665F')
INK = colors.HexColor('#203239')
STYLES = {
    'title': ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=25, leading=29, textColor=TEAL, spaceAfter=13),
    'sub': ParagraphStyle('Subtitle', fontName='Helvetica', fontSize=11, leading=15, textColor=INK, spaceAfter=15),
    'h': ParagraphStyle('Heading', fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=TEAL, spaceBefore=12, spaceAfter=6, keepWithNext=True),
    'body': ParagraphStyle('Body', fontName='Helvetica', fontSize=10.5, leading=14, textColor=INK, spaceAfter=8),
    'box': ParagraphStyle('Prompt', fontName='Helvetica', fontSize=10.2, leading=14, textColor=INK, backColor=colors.HexColor('#EDF6F4'), borderPadding=10, spaceBefore=7, spaceAfter=15),
    'code': ParagraphStyle('Code', fontName='Courier', fontSize=8, leading=11, textColor=INK, spaceAfter=7),
    'small': ParagraphStyle('Small', fontName='Helvetica', fontSize=8.5, leading=11, textColor=INK, spaceAfter=6),
}


def p(text, style='body'):
    return Paragraph(text, STYLES[style])


def command(text):
    return p(escape(text), 'code')


def footer(canvas, doc):
    canvas.setStrokeColor(TEAL)
    canvas.line(1.8*cm, 1.5*cm, 19.2*cm, 1.5*cm)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(INK)
    canvas.drawString(1.8*cm, 1.05*cm, f'BTO CV | Guide checked against v{VERSION} | {DATE}')
    canvas.drawRightString(19.2*cm, 1.05*cm, str(doc.page))


def build(name, story):
    target=ROOT/'docs'/name
    doc=SimpleDocTemplate(str(target), pagesize=(21*cm,29.7*cm), leftMargin=1.8*cm,
                          rightMargin=1.8*cm, topMargin=1.6*cm, bottomMargin=2*cm,
                          title=name.replace('_',' ').replace('.pdf',''), author='BTO CV')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(target)


team = [
    p('Set up BTO CV', 'title'),
    p('One-time setup for colleagues. Your local Codex agent handles the technical steps.', 'sub'),
    p('1. Get repository access', 'h'),
    p('Send your GitHub username to Keyan FEILI. Accept any invitation and confirm you can open <link href="https://github.com/KeyanFEILI/BTO-CV" color="#00665F">KeyanFEILI/BTO-CV</link>. Need an account? Use <link href="https://github.com/signup" color="#00665F">github.com/signup</link>.'),
    p('2. Open a local Codex chat', 'h'),
    p('Open the Codex desktop app, sign in and start a local chat that can run commands on your computer. Ask Keyan or IT if this option is unavailable.'),
    p('For fewer setup prompts, click the permissions control below the message box and select <b>Approve for me</b>. If unavailable or restricted, use <b>Ask for approval</b>.'),
    Image(str(ROOT/'docs/assets/approve-for-me.png'), width=13*cm, height=13*cm*237/858, hAlign='LEFT'),
    p('Eligible actions get automatic review, not guaranteed approval. Sign-in and hook trust still need your input. Menu appearance and model choice may differ.', 'small'),
    p('3. Attach this PDF and send this message', 'h'),
    p('Set up BTO CV using the agent checklist on page 2. Reuse or update my installation, verify the current version, guide sign-in and hook review, and test a fictional CV. Never ask for passwords or tokens.', 'box'),
    p('4. Complete the setup prompts', 'h'),
    p('Complete GitHub sign-in in the browser and approve any required missing tools. Review and trust the BTO update hook when prompted; installation alone does not trust it.'),
    p('5. Start a new chat and use BTO CV', 'h'),
    p('After verified setup, start a new local chat, select BTO CV or ask to use its installed skill. Attach your original CV and send:'),
    p('Convert this into an editable BTO Word CV. Preserve the facts and wording, except for necessary translation and corrections.', 'box'),
    p('You can also attach a job description for light tailoring. Use only candidate documents permitted by your company. Check the finished CV before sharing it.'),
    p('Updates and help', 'h'),
    p('Updates are checked at session startup/resume, at most daily. Start a new chat after an update and review the hook again if prompted. Contact Keyan for setup or shared-format changes.'),
    PageBreak(),
    p('Agent setup checklist', 'title'),
    p('For the local Codex agent. The user explicitly requests these steps by sending the setup message on page 1.', 'sub'),
    p('1. Check access and tools', 'h'),
    p('Reuse Python 3, Git and a plugin-capable Codex CLI. Install missing tools only with the user\'s approval. Verify non-interactive Git access to the repository; browser sign-in alone is not proof. If authentication is needed, guide the user through the supported browser flow. GitHub CLI is optional. Never request or print credentials.'),
    p('2. Register, refresh and verify', 'h'),
    p('Inspect existing marketplaces and installations first. Reuse the BTO Git source tracking main. If absent, register it:'),
    command('codex plugin marketplace add https://github.com/KeyanFEILI/BTO-CV.git --ref main'),
    command('codex plugin marketplace upgrade bto-cv-marketplace'),
    command('codex plugin list --marketplace bto-cv-marketplace --json'),
    p('Read plugin.json at the refreshed marketplace root. The installed BTO version must match that manifest and be enabled. If missing or still behind, install/refresh and verify again:'),
    command('codex plugin add bto-cv@bto-cv-marketplace --json'),
    p(f'This guide was checked against v{VERSION}; use the current refreshed manifest, not a fixed minimum version. Preserve any old standalone skill until the plugin works, then resolve duplicates with the user.'),
    p('3. Verify the updater and hook trust', 'h'),
    p('Locate the verified installed plugin root. Ensure its hook environment resolves python on Windows (python3 elsewhere), Git and Codex; BTO_CODEX_BIN can specify the CLI path. Run the updater using that installed root:'),
    command('python "<installed-plugin-root>/hooks/update.py" --force --check'),
    p('Use python3 where appropriate. The command performs an update check; current or updated means success. A failure is not a verified setup. Guide the user through the supported hook review; never bypass trust. In a new local session, verify actual SessionStart execution. A direct script run alone does not prove that the trusted hook fired; a daily-throttled hook may be silent.'),
    p('4. Test in a fresh chat', 'h'),
    p('Generate an editable Word CV from the installed examples/sample-cv.txt. Verify source facts, native square bullets and every rendered page. Prefer Microsoft Word on Windows; the CV requires Century Gothic and Wingdings. Report missing fonts or incomplete visual review. Use the template and generator from the same installed release; no template download is needed during conversion.'),
    p('Report installed version, enabled status, updater result, hook verification and sample-CV result separately. If hook execution or a required check cannot be verified, explain the remaining step and contact Keyan; do not claim full setup success.'),
    p('Official references: <link href="https://developers.openai.com/plugins/build/plugins" color="#00665F">OpenAI plugin packaging and hook trust</link>; <link href="https://learn.chatgpt.com/docs/permission-modes" color="#00665F">permission modes</link>. BTO-specific behavior: repository README and installed hook.', 'small'),
]

owner = [
    p('Owner onboarding checklist', 'title'),
    p('For Keyan FEILI. Use with BTO_CV_Team_Setup.pdf. Verify on one colleague\'s account before wider rollout.', 'sub'),
    p('1. Confirm the release and access', 'h'),
    p('Confirm main contains the intended tested release. The refreshed marketplace manifest is the version authority; compare the installed version with it. Confirm the repository access settings and invite colleagues if needed. Ask them to verify access using their own accounts.'),
    p('For a personal private repository, collaborators can have write access. The instruction to contact Keyan for shared changes is workflow guidance, not access enforcement. Manage invitations and remove access when no longer needed.'),
    p('2. Confirm the supported local environment', 'h'),
    p('Use a local Codex environment with command execution and plugin support. Python 3, Git and a plugin-capable Codex CLI must resolve in the hook environment. Verify Git credentials non-interactively. Prefer Microsoft Word for CV rendering on Windows. Required CV fonts are Century Gothic and Wingdings.'),
    p('The team guide shows the optional Approve for me permission mode. It routes eligible requests to automatic review; it does not guarantee approval or replace sign-in and hook trust. If unavailable or restricted, use Ask for approval.'),
    p('3. Run the separate-account pilot', 'h'),
    p('Have one colleague follow both pages of the team guide. Confirm all of the following:'),
    p('<b>Installation:</b> one active BTO plugin is enabled, with version matching the refreshed marketplace plugin.json. Resolve any old standalone copy only after verification.'),
    p('<b>Updater:</b> the installed hooks/update.py --force --check returns current or updated. Its state in PLUGIN_DATA records ok: true. This proves script success, not lifecycle execution.'),
    p('<b>Trust and lifecycle:</b> the colleague reviews the current hook definition in a supported review control. Start/resume a new local session and verify the hook ran from the host\'s hook execution evidence. Recent state may cause a silent throttled run; state alone does not prove a new invocation. If the host provides no evidence, mark lifecycle verification pending.'),
    p('<b>Document:</b> create the fictional sample in a fresh chat. Inspect editable text, the R.R./A.F.R. banner/layout, native square lists and every rendered page. Each Main responsibilities: label uses 1.5-line spacing; bullets keep their existing spacing.'),
    p('The team guide can be shared for the pilot. Treat wider rollout as ready only after installation, updater, trusted lifecycle execution and document checks pass on that colleague\'s machine.'),
    PageBreak(),
    p('Updates and recovery', 'title'),
    p('Keep the release central and make failures diagnosable without disrupting CV work.', 'sub'),
    p('4. Confirm a real version upgrade', 'h'),
    p('At the next tested release, confirm the colleague\'s trusted hook updates BTO after the daily interval, or test the updater directly with --force --check. Verify the installed version equals the refreshed manifest, then open a new chat. Record lifecycle evidence separately from a forced script check.'),
    p('5. Handle update failures', 'h'),
    p('A failed check must leave the installed package available. Conversion uses its paired local master and generator; it does not fetch a newer template or require fallback approval. After restoring connectivity/access, refresh and inspect:'),
    command('codex plugin marketplace upgrade bto-cv-marketplace'),
    command('codex plugin list --marketplace bto-cv-marketplace --json'),
    p('Compare with the refreshed plugin.json. Only if installation is missing or still behind:'),
    command('codex plugin add bto-cv@bto-cv-marketplace --json'),
    p('Verify enabled status and version again, and start a new chat. If the updater fails, inspect the failing stage, CLI access, Git credentials and interpreter paths. Do not delete credentials, uninstall a working package, bypass hook trust or create another BTO copy.'),
    p('6. Maintain future releases', 'h'),
    p('Edit the repository, not the installed cache. Preserve the R.R./A.F.R. master and content rules. Run the relevant tests; render and inspect fictional output for formatting changes. Bump plugin.json for package changes, publish the tested release, and keep these guides consistent.'),
    command('python -m unittest discover -s tests -v'),
    p('Current conversion: extract once, reconcile source facts and the complete IT-skills inventory, then use scripts/convert.py to build and structurally verify. Visual review remains separate. Skills intentionally appear under both experience and IT SKILLS; at most four skill groups. Never commit candidate files or private reconciliation data.'),
    p('Update behavior', 'h'),
    p('SessionStart checks occur at startup/resume, at most once per 24 hours. Failed checks retry no sooner than one hour. This is not a background timer. Package updates need a fresh chat; changed hooks may require renewed trust. Existing CV files are unchanged.'),
    p('References', 'h'),
    p('<link href="https://github.com/KeyanFEILI/BTO-CV" color="#00665F">BTO repository and current README</link><br/><link href="https://developers.openai.com/plugins/build/plugins" color="#00665F">Official OpenAI marketplace and hook-trust documentation</link>', 'small'),
]

if __name__ == '__main__':
    build('BTO_CV_Team_Setup.pdf', team)
    build('BTO_CV_Owner_Checklist.pdf', owner)
