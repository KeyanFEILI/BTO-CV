"""BTO-only session updater. Python 3 standard library; never prompts for login."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

MARKET = 'bto-cv-marketplace'
PLUGIN = 'bto-cv@' + MARKET
SOURCE = 'https://github.com/KeyanFEILI/BTO-CV.git'

def run(cli, args):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never', GH_PROMPT_DISABLED='1')
    # No shell, no transcript/candidate content, and no credential output.
    p = subprocess.run([cli] + args, env=env, stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=12)
    if p.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(args[:3]))
    return json.loads(p.stdout) if '--json' in args else None

def notify(message):
    print(json.dumps({'systemMessage': message, 'hookSpecificOutput': {
        'hookEventName': 'SessionStart', 'additionalContext': message}}))

def update(data_dir, cli=None, force=False, runner=run, now=None):
    now = time.time() if now is None else now
    data_dir = Path(data_dir); data_dir.mkdir(parents=True, exist_ok=True)
    state_path = data_dir / 'update-state.json'
    lock = data_dir / 'update.lock'
    try:
        state = json.loads(state_path.read_text())
    except (OSError, ValueError):
        state = {}
    if not isinstance(state, dict) or not isinstance(state.get('checked_at', 0), (int, float)):
        state = {}
    interval = 86400 if state.get('ok') else 3600
    if not force and 0 <= now - state.get('checked_at', 0) < interval:
        return 'throttled'
    # Short-lived exclusive file lock; recover an abandoned hook after five minutes.
    try:
        if lock.exists() and now - lock.stat().st_mtime > 300:
            lock.unlink()
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return 'busy'
    os.close(fd)
    ok = False
    version = None
    try:
        cli = cli or os.environ.get('BTO_CODEX_BIN') or shutil.which('codex')
        if not cli:
            raise RuntimeError('Codex CLI not found')
        sources = runner(cli, ['plugin', 'marketplace', 'list', '--json'])['marketplaces']
        source = next((m for m in sources if m['name'] == MARKET), {})
        origin = source.get('marketplaceSource', {})
        if origin.get('sourceType') != 'git' or origin.get('source', '').rstrip('/') not in (SOURCE, SOURCE[:-4]):
            raise RuntimeError('Expected GitHub marketplace is not registered')
        def installed():
            result = runner(cli, ['plugin', 'list', '--marketplace', MARKET, '--json'])
            return next((p for p in result['installed'] if p['pluginId'] == PLUGIN), None)
        before = installed()
        if not before or not before.get('enabled'):
            return 'disabled'
        runner(cli, ['plugin', 'marketplace', 'upgrade', MARKET])
        # A refresh can update the plugin itself. Inspect before reinstalling.
        refreshed = installed()
        root = Path(source['root'])
        manifest = json.loads((root / 'plugin.json').read_text(encoding='utf-8'))
        if manifest.get('name') != 'bto-cv' or not manifest.get('version'):
            raise RuntimeError('Invalid BTO manifest')
        version = manifest['version']
        if not refreshed or refreshed.get('version') != version:
            runner(cli, ['plugin', 'add', PLUGIN, '--json'])
        after = installed()
        if not after or after.get('version') != version or not after.get('enabled'):
            raise RuntimeError('Updated version could not be verified')
        ok = True
        if version != before.get('version'):
            notify('BTO CV updated to ' + version + '. Start a new chat before generating a CV. Review the hook again if Codex requests it.')
            return 'updated'
        return 'current'
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired):
        notify('BTO CV automatic update could not be verified. No uninstall was attempted. Ask Keyan to check GitHub sign-in, Git and Codex CLI access. Retrying at a later session start after one hour.')
        return 'failed'
    finally:
        payload = {'checked_at': now, 'ok': ok, 'version': version}
        temp = state_path.with_suffix('.tmp')
        temp.write_text(json.dumps(payload), encoding='utf-8'); temp.replace(state_path)
        lock.unlink(missing_ok=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Ignore the daily check interval')
    parser.add_argument('--check', action='store_true', help='Print the result for assisted setup')
    args = parser.parse_args()
    folder = os.environ.get('PLUGIN_DATA')
    if not folder:
        home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
        folder = home / 'plugin-data' / MARKET / 'bto-cv'
    try:
        result = update(folder, force=args.force)
        if args.check:
            print('BTO updater: ' + result)
            if result == 'failed': raise SystemExit(1)
    except OSError:
        notify('BTO CV updater cannot write its state. Ask Keyan to check plugin data-directory permissions.')
        if args.check: raise SystemExit(1)

if __name__ == '__main__':
    main()
