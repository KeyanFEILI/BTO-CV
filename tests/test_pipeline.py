"""The combined command must preserve package bytes and existing failure behavior."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/bto-cv'
SCRIPT = SKILL / 'scripts/convert.py'


class PipelineTests(unittest.TestCase):
    def run_command(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True)

    def test_pipeline_preserves_every_package_member(self):
        source = SKILL / 'references/input-example.json'
        with tempfile.TemporaryDirectory() as folder:
            combined = Path(folder) / 'combined.docx'
            standalone = Path(folder) / 'standalone.docx'
            result = self.run_command(source, combined)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['roles'], 2)
            self.assertEqual(report['visual_review'], 'required')
            self.assertEqual(report['source_review'], 'required')
            self.assertGreaterEqual(report['build_seconds'], 0)
            self.assertGreaterEqual(report['verify_seconds'], 0)
            subprocess.run([sys.executable, str(SKILL/'scripts/build_docx.py'),
                            str(source), str(standalone)], check=True, capture_output=True)
            with zipfile.ZipFile(combined) as a, zipfile.ZipFile(standalone) as b:
                self.assertEqual(a.namelist(), b.namelist())
                for name in a.namelist():
                    self.assertEqual(a.read(name), b.read(name), name)
            original = combined.read_bytes()
            retry = self.run_command(source, combined)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(combined.read_bytes(), original)

    def test_invalid_input_fails_without_output_or_success_report(self):
        cases = ['{', json.dumps({'initials':'T.E.','experience':[{'dates':'13/2025'}]})]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'input.json'
            output = Path(folder) / 'cv.docx'
            for text in cases:
                source.write_text(text, encoding='utf-8')
                result = self.run_command(source, output)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())
                self.assertEqual(result.stdout, '')
                self.assertNotIn('Traceback', result.stderr)

    def test_verification_failure_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as folder:
            broken = Path(folder) / 'broken.docx'
            with zipfile.ZipFile(SKILL/'assets/BTO_CV_Template.docx') as a:
                with zipfile.ZipFile(broken, 'w') as b:
                    for name in a.namelist():
                        content = a.read(name)
                        if name == 'word/document.xml':
                            content = content.replace(b'w:line="360"', b'w:line="240"')
                        b.writestr(name, content)
            result = self.run_command(SKILL/'references/input-example.json',
                                      Path(folder)/'cv.docx', '--template', broken)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('1.5-line spacing', result.stderr)
            self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
