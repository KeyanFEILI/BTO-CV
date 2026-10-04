import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('updater', ROOT/'hooks/update.py')
updater = importlib.util.module_from_spec(spec); spec.loader.exec_module(updater)

class UpdateTests(unittest.TestCase):
    def simulate(self, current='3.0.0', target='3.1.0', fail=False, origin=None, enabled=True, refresh_updates=False):
        self.calls=[];self.version=current
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root=Path(tmp.name);(root/'plugin.json').write_text(json.dumps({'name':'bto-cv','version':target}))
        def runner(cli,args):
            self.calls.append(args)
            if args[:3]==['plugin','marketplace','list']:
                return {'marketplaces':[{'name':updater.MARKET,'root':str(root),'marketplaceSource':{'sourceType':'git','source':origin or updater.SOURCE}}]}
            if args[:2]==['plugin','list']:
                return {'installed':[{'pluginId':updater.PLUGIN,'enabled':enabled,'version':self.version}]}
            if args[:3]==['plugin','marketplace','upgrade']:
                if fail:raise RuntimeError('offline')
                if refresh_updates:self.version=target
            if args[:2]==['plugin','add']:self.version=target
        self.state=root/'state'
        self.runner=runner
        return self.invoke()
    def invoke(self,force=False,now=100000):
        with contextlib.redirect_stdout(io.StringIO()) as capture:
            result=updater.update(self.state,cli='codex',runner=self.runner,now=now,force=force)
        self.output=capture.getvalue();return result
    def test_update_and_daily_throttle(self):
        self.assertEqual(self.simulate(),'updated');self.assertIn('Start a new chat',self.output)
        self.assertIn(['plugin','add',updater.PLUGIN,'--json'],self.calls)
        self.calls.clear();self.assertEqual(self.invoke(now=100010),'throttled');self.assertEqual(self.calls,[])
    def test_current_does_not_reinstall(self):
        self.assertEqual(self.simulate(current='3.1.0'),'current');self.assertEqual(self.output,'')
        self.assertFalse(any(x[:2]==['plugin','add'] for x in self.calls))
    def test_refresh_can_update_without_add(self):
        self.assertEqual(self.simulate(refresh_updates=True),'updated')
        self.assertFalse(any(x[:2]==['plugin','add'] for x in self.calls))
    def test_failure_retries_after_hour(self):
        self.assertEqual(self.simulate(fail=True),'failed');self.assertEqual(self.version,'3.0.0')
        self.assertEqual(self.invoke(now=100010),'throttled')
        self.assertEqual(self.invoke(now=103601),'failed')
    def test_different_source_not_modified(self):
        self.assertEqual(self.simulate(origin='https://github.com/other/repo.git'),'failed')
        self.assertEqual(len(self.calls),1)
    def test_disabled_not_reenabled(self):
        self.assertEqual(self.simulate(enabled=False),'disabled')
        self.assertFalse(any(x[:2]==['plugin','add'] for x in self.calls))
    def test_lock_and_forced_check(self):
        self.simulate(current='3.1.0')
        self.assertEqual(self.invoke(force=True),'current')
        (self.state/'update.lock').touch()
        self.assertEqual(self.invoke(force=True),'busy')
    def test_manifest_has_safe_event_filter(self):
        hooks=json.loads((ROOT/'hooks/hooks.json').read_text())['hooks']
        self.assertEqual(list(hooks),['SessionStart'])
        self.assertEqual(hooks['SessionStart'][0]['matcher'],'^(startup|resume)$')
    def test_corrupt_state_is_recovered(self):
        self.simulate(current='3.1.0')
        (self.state/'update-state.json').write_text('[]')
        self.assertEqual(self.invoke(),'current')
    def test_timeout_is_nonblocking(self):
        self.simulate(current='3.1.0')
        def timeout(cli,args):raise updater.subprocess.TimeoutExpired('codex',12)
        self.runner=timeout
        self.assertEqual(self.invoke(force=True),'failed')
        self.assertFalse((self.state/'update.lock').exists())

if __name__=='__main__':unittest.main()
