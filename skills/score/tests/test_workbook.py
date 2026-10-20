"""Fictional regressions: fixed headers, plain XP, no cloud side effects."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('workbook_rows', SCRIPTS/'workbook_rows.py')
workbook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workbook)


class WorkbookTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(candidate='Example Candidate', score=80, rank=1,
                        relevant_experience='7-8 years', phone='+352 000000',
                        email='example@example.com', source_languages='French: fluent',
                        short_description='Digital delivery; mobile scope unspecified.',
                        latest_location='Example City', languages=[{'status': 'met'}])
        self.headers = ['Rank', 'Candidate', 'Match', 'XP', 'Short description',
                        'Phone Number', 'Notes', 'Availability']

    def project(self, rows=None, headers=None):
        return workbook.project([dict(jd_id='example', title='Example role',
                                      ranking=rows or [self.row])],
                                self.headers if headers is None else headers)[0]

    def test_only_existing_headers_are_written_and_manual_fields_are_untouched(self):
        before = copy.deepcopy((self.row, self.headers))
        result = self.project()
        values = result['rows'][0]['values']
        self.assertLessEqual(set(values), set(self.headers))
        self.assertNotIn('Notes', values)
        self.assertNotIn('Availability', values)
        self.assertIn('email', result['omitted_fields'])
        self.assertEqual(values['Short description'], self.row['short_description'])
        self.assertEqual(values['Match'], 80)
        self.assertEqual(values['Phone Number'], '+352 000000')
        self.assertEqual((self.row, self.headers), before)

    def test_flags_and_run_metadata_are_never_projected_even_with_headers(self):
        result = self.project(headers=self.headers + ['Language flags', 'Ranking run'])
        self.assertNotIn('Language flags', result['rows'][0]['values'])
        self.assertNotIn('Ranking run', result['rows'][0]['values'])

    def test_threshold_uses_unrounded_final_score(self):
        below = dict(self.row, score=79.999, candidate='Below threshold')
        above = dict(self.row, score=80.001, candidate='Above threshold')
        rows = self.project([below, self.row, above])['rows']
        self.assertEqual([r['values']['Match'] for r in rows], [80, 80.001])

    def test_missing_values_are_omitted_not_used_to_erase_existing_data(self):
        self.row.update(phone='', email='Not provided', relevant_experience='Cannot determine')
        values = self.project(headers=self.headers+['Email address'])['rows'][0]['values']
        for header in ['Phone Number', 'Email address', 'XP']:
            self.assertNotIn(header, values)

    def test_ambiguous_equivalent_headers_fail_before_writes(self):
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            self.project(headers=self.headers+['Score'])

    def test_display_experience_accepts_ranges_without_inventing_precision(self):
        for value in ['7-8 years', '12–13 years', '1 year', '0.5 years', '10+ years',
                      'Cannot determine', '']:
            with self.subTest(value=value):
                self.assertEqual(workbook.experience_label(value), value)

    def test_verbose_or_invalid_experience_fails_before_projection(self):
        for value in ['Approximately 7-8 years', '12 years, evidenced through May 2024',
                      '7 years (10 including leadership)', '8-7 years', '7-8+ years',
                      'Digital PM since 2022']:
            self.row['relevant_experience'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.project()


if __name__ == '__main__':
    unittest.main()
