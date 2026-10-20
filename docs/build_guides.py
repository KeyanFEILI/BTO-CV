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
DATE = '20 October 2026'
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
    canvas.drawString(1.8*cm, 1.05*cm, f'BTO HR | Guide checked against v{VERSION} | {DATE}')
    canvas.drawRightString(19.2*cm, 1.05*cm, str(doc.page))


def build(name, story):
    target=ROOT/'docs'/name
    doc=SimpleDocTemplate(str(target), pagesize=(21*cm,29.7*cm), leftMargin=1.8*cm,
                          rightMargin=1.8*cm, topMargin=1.6*cm, bottomMargin=2*cm,
                          title=name.replace('_',' ').replace('.pdf',''), author='BTO HR')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(target)


team = [
    p('Set up BTO HR', 'title'),
    p('One plugin. Three skills: BTO CV, Score and Trello. One-time setup for colleagues.', 'sub'),
    p('1. Check access', 'h'),
    p('Confirm you can open <link href="https://github.com/KeyanFEILI/BTO-CV" color="#00665F">KeyanFEILI/BTO-CV</link> with your own GitHub account. If access is restricted, send your username to Keyan FEILI and accept the invitation.'),
    p('2. Open a local Codex chat', 'h'),
    p('Sign in to the Codex desktop app and start a local chat with command execution. For fewer installation prompts, select <b>Approve for me</b> below the message box. If unavailable, use <b>Ask for approval</b>.'),
    Image(str(ROOT/'docs/assets/approve-for-me.png'), width=13*cm, height=13*cm*237/858, hAlign='LEFT'),
    p('Complete sign-in and hook review when prompted.', 'small'),
    p('3. Drop this PDF into Codex', 'h'),
    p('Attach this PDF and send the following message. The agent-readable installation checklist is on page 2; workflow setup is on page 3.'),
    p('Set up BTO HR using all three pages of this guide. Reuse or migrate my installation, verify the three skills, guide sign-in and hook review, and configure the shared BTO candidates workbook. Connect Trello and verify board access. Report any setup steps that need my input.', 'box'),
    p('4. Finish sign-in, then start a new chat', 'h'),
    p('Complete GitHub, Microsoft or Trello sign-in yourself when needed. Review the BTO update hook when prompted. Start a new chat after installation; search for <b>bto-cv</b>, <b>score</b> or <b>trello</b> under BTO HR. Technical names use the prefix <b>bto-hr:</b>.'),
    p('Need help?', 'h'),
    p('Contact Keyan for GitHub access, the BTO candidates sharing link or Trello board access.'),
    PageBreak(),
    p('Agent installation checklist', 'title'),
    p('For the local Codex agent when the user requests setup. Complete page 3 as well.', 'sub'),
    p('1. Inspect the environment', 'h'),
    p('Reuse Python 3, Git and a plugin-capable Codex CLI. Guide supported installation for missing tools and user-controlled sign-in. Verify Git repository access non-interactively; browser sign-in alone is insufficient. Never request, print or store credentials. GitHub CLI is optional.'),
    p('2. Refresh and install', 'h'),
    p('Inspect current marketplaces and plugins first. Reuse the BTO Git source tracking main. Register only if absent:'),
    command('codex plugin marketplace add https://github.com/KeyanFEILI/BTO-CV.git --ref main'),
    command('codex plugin marketplace upgrade bto-cv-marketplace'),
    command('codex plugin add bto-hr@bto-cv-marketplace --json'),
    command('codex plugin list --marketplace bto-cv-marketplace --json'),
    p(f'The guide describes v{VERSION}. The current refreshed plugin.json is the version authority. Verify bto-hr is enabled and its installed version matches. Verify skills/bto-cv, skills/score and skills/trello each contain SKILL.md. Do not install three standalone copies.'),
    p('3. Migrate an older installation', 'h'),
    p('If bto-cv@bto-cv-marketplace or standalone Score/Talent Pool copies exist, preserve their private workbook configuration first. Install and verify BTO HR before removing the superseded plugin. Restore the private configuration in the new Score installation. Archive standalone duplicates outside skill discovery; preserve unrelated skills. Then remove the old plugin:'),
    command('codex plugin remove bto-cv@bto-cv-marketplace --json'),
    p('4. Verify the updater and hook trust', 'h'),
    command('python "<installed-plugin-root>/hooks/update.py" --force --check'),
    p('Use python3 where appropriate. Verify Python, Git and Codex resolve in the hook environment; BTO_CODEX_BIN can specify the CLI. current or updated confirms the direct script check. Guide the supported hook review without bypassing trust. In a fresh local session verify actual SessionStart execution separately; a direct script result or old state alone is not lifecycle proof. A throttled hook may be silent.'),
    p('Keep private setup outside Git', 'h'),
    p('Do not commit workbook links, candidate files, extracted text, rankings or credentials. Package upgrades may replace the installed cache: preserve the private workbook destination before updating and restore it afterward.'),
    PageBreak(),
    p('Configure and use the skills', 'title'),
    p('Complete the setup below, then use these skills in a new chat.', 'sub'),
    p('BTO HR : bto cv', 'h'),
    p('Attach an original CV and optionally a JD. Ask for an editable BTO Word CV. During setup, convert examples/sample-cv.txt with the installed template/generator and inspect every rendered page. Check Century Gothic and Wingdings; prefer Word rendering on Windows. For PDF input, use available pypdf or pdftotext; arrange a supported PDF reader if neither is available.'),
    p('BTO HR : score', 'h'),
    p('Attach one or more JDs and multiple CVs. Each JD receives its own ranking: 95 role-fit points plus up to 5 for relevant large-company/consulting experience. Language gaps are flagged without changing scores. Every entry includes full name, latest stated location, relevant years, description, phone, email and source language levels.'),
    p('The shared workbook is <b>BTO candidates</b>. Ask the user or Keyan for its sharing link once, sign in to Microsoft if needed and verify edit access. Save the link privately through SCORE_WORKBOOK_URL or references/workbook.local.json inside the installed Score skill: {&quot;url&quot;: &quot;the supplied sharing link&quot;}. Verify the workbook title and existing sheets before writing; never commit the link.'),
    p('Each ranking also updates <b>BTO candidates</b> for candidates scoring <b>at least 80/100</b>; all candidates remain in the chat ranking. Match the JD to an existing role sheet. Create a new sheet only for an unrelated role, using the JD title and existing headers. Reuse candidate rows, leave missing data blank and preserve colleague notes, rates and existing known values. Read back writes and confirm save; otherwise report the sync blocker.'),
    p('BTO HR : trello', 'h'),
    p('Enable the Trello connection in Codex and complete Trello sign-in. Verify read access to the BTO LUX Talent Pool board: <link href="https://trello.com/b/rHwW3Keo/talent-pool" color="#00665F">Open Talent Pool</link>. Confirm its lists and labels load. Then attach CVs and ask to add candidates; the skill checks duplicates, fills profiles, chooses role lists and applies seniority. Ask explicitly for client opportunity copies.'),
    p('Acceptance report', 'h'),
    p('Report installed version, the three visible skills, updater/hook status, sample CV result, BTO candidates edit access and Trello board access. List any remaining blockers. Verify actual Excel writes on the first requested candidate ranking; use read-only service checks during installation.'),
]

owner = [
    p('BTO HR owner checklist', 'title'),
    p('For Keyan FEILI. Use with BTO_HR_Team_Setup.pdf. Pilot on a colleague\'s own account.', 'sub'),
    p('1. Release and permissions', 'h'),
    p('Confirm main contains the tested release and plugin.json names bto-hr. Keep the existing repository URL and bto-cv-marketplace registration. Verify all three packaged skills: bto-cv, score and trello. Provide repository access if needed; provide the BTO candidates sharing link with edit access and Trello board access.'),
    p('2. Installation and migration', 'h'),
    p('Have a colleague drop the team PDF into a local Codex chat and send its setup message. Confirm enabled version matches the refreshed manifest. Migrate bto-cv only after BTO HR works; preserve private Excel configuration first. Archive standalone Score/Talent Pool duplicates outside discovery. In a fresh chat, confirm only the three repository HR skills appear, alongside any unrelated installed tools.'),
    p('3. Verify each capability separately', 'h'),
    p('<b>Updater:</b> installed hooks/update.py --force --check returns current or updated. Verify trusted SessionStart execution separately; direct execution does not prove hook lifecycle success.'),
    p('<b>CV:</b> convert the fictional sample; inspect all rendered pages, editable content, banner, native square bullets and 1.5-line spacing on Main responsibilities labels. Disclose missing fonts or rendering limits.'),
    p('<b>Score:</b> use fictional local assessment data to verify independent JD scores, language flags and the 0-5 employer bonus. Confirm BTO candidates edit access and private destination setup. Test real writes only with an authorised candidate batch; verify the >=80 boundary, correct existing sheet, duplicate handling, blanks and preservation of colleague columns. No qualifying candidate means no workbook change.'),
    p('<b>Trello:</b> verify authenticated board/list/label access without writing sample cards. For the first authorised batch, verify title, profile fields, list and seniority. Preserve existing content.'),
    p('Acceptance', 'h'),
    p('Record pass, pending or blocked for each item. Full setup is verified only when its required checks pass on the colleague\'s machine. '),
    PageBreak(),
    p('Updates and recovery', 'title'),
    p('Keep the shared package current without losing private configuration.', 'sub'),
    p('4. Maintain the release', 'h'),
    p('Edit the repository, not installed caches. Preserve CV layout and factual wording rules. Bump plugin.json for package changes and rebuild these guides. Run both suites and the CV input check:'),
    command('python -m unittest discover -s tests -v'),
    command('python -m unittest discover -s skills/score/tests -v'),
    command('python skills/bto-cv/scripts/build_docx.py skills/bto-cv/references/input-example.json --check'),
    command('python docs/build_guides.py'),
    p('Render and inspect every onboarding page before publishing. Never commit private workbook configuration, candidate CVs, rankings or reconciliation data. '),
    p('5. Refresh an installation', 'h'),
    p('Preserve references/workbook.local.json from the installed Score skill before an upgrade; alternatively use the privately configured SCORE_WORKBOOK_URL. Restore and verify the destination after the package changes.'),
    command('codex plugin marketplace upgrade bto-cv-marketplace'),
    command('codex plugin add bto-hr@bto-cv-marketplace --json'),
    command('codex plugin list --marketplace bto-cv-marketplace --json'),
    p('Compare the enabled installed version with the refreshed manifest. Start a new chat; changed hooks may need renewed review. SessionStart checks occur at most daily; failures retry at a later startup/resume after at least one hour. This is not a background timer.'),
    p('6. Handle failures without discarding working setup', 'h'),
    p('Check Git access, Python, Codex CLI and supported sign-in flows. Do not delete credentials or bypass hook trust. CV conversion can use the last verified template/generator pair offline. Report Excel/Trello access failures separately. Preserve completed local rankings when sync is blocked.'),
    p('References', 'h'),
    p('<link href="https://github.com/KeyanFEILI/BTO-CV" color="#00665F">BTO HR repository and current README</link><br/><link href="https://developers.openai.com/plugins/build/plugins" color="#00665F">Official OpenAI plugin documentation</link>', 'small'),
]

if __name__ == '__main__':
    build('BTO_HR_Team_Setup.pdf', team)
    build('BTO_HR_Owner_Checklist.pdf', owner)
