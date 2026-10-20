"""Fictional behavior tests for caching, contextual scoring and range plans."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import evidence_cache
import rank
import workbook_plan


class CacheTests(unittest.TestCase):
    def test_content_reuse_and_targeted_invalidation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'fictional.txt'
            source.write_text('Fictional CV', encoding='utf-8')
            cache = evidence_cache.EvidenceCache(Path(tmp)/'private-cache')
            with patch.object(evidence_cache, 'extract', wraps=evidence_cache.extract) as extractor:
                key, record, reused = cache.source(source)
                self.assertFalse(reused)
                renamed = Path(tmp)/'renamed.txt'
                renamed.write_bytes(source.read_bytes())
                self.assertEqual(cache.source(renamed)[0], key)
                self.assertTrue(cache.source(source)[2])
                self.assertEqual(extractor.call_count, 1)
                cache.save_profile(key, {'name': 'Example', 'roles': []})
                self.assertEqual(cache.source(source)[1]['profile']['name'], 'Example')
                cache.save_profile(key, {'name': 'Corrected Example', 'roles': []})
                self.assertEqual(cache.source(source)[1]['profile']['name'], 'Corrected Example')
                source.write_text('Revised fictional CV', encoding='utf-8')
                revised_key, revised, reused = cache.source(source)
                self.assertNotEqual(revised_key, key)
                self.assertIsNone(revised['profile'])
                self.assertFalse(reused)
                self.assertEqual(extractor.call_count, 2)

    def test_cache_key_cannot_escape_private_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                evidence_cache.EvidenceCache(tmp).read('../outside')


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/'references/input-example.json').read_text(encoding='utf-8'))

    def test_recommendations_follow_calculated_order_and_uncertainty_is_separate(self):
        result = rank.rank(self.data)[0]
        row = result['ranking'][0]
        self.assertEqual(result['recommended_candidate_ids'], [row['candidate_id']])
        self.assertEqual(row['score'], 70)
        self.assertEqual(row['uncertainty'], {'unknown_weight': 10, 'confirmed_gap_points': 0})
        self.assertEqual([v['criterion'] for v in row['points_to_validate']],
                         ['Automated testing and reliable delivery'])

    def test_unfrozen_equivalence_and_overcredited_adjacent_work_fail(self):
        rating = self.data['assessments'][0]['ratings']['core']
        rating.update(match_basis='equivalent', equivalence_reason='Related tools')
        with self.assertRaisesRegex(ValueError, 'frozen'):
            rank.rank(self.data)
        rating.update(match_basis='adjacent')
        with self.assertRaisesRegex(ValueError, 'Adjacent'):
            rank.rank(self.data)

    def test_accepted_equivalence_and_confirmed_prerequisite_gap(self):
        criterion = self.data['jobs'][0]['criteria'][0]
        criterion['accepted_equivalents'] = ['Equivalent production runtime delivery']
        self.data['assessments'][0]['ratings']['core'].update(
            match_basis='equivalent', equivalent='Equivalent production runtime delivery',
            equivalence_reason='Same delivered runtime scope under the frozen interpretation')
        criterion = self.data['jobs'][0]['criteria'][-1]
        criterion.update(priority='prerequisite', required=True)
        self.data['assessments'][0]['ratings']['sector'].update(
            status='not_met', evidence=['example-cv.pdf p.1: No banking experience.'])
        row = rank.rank(self.data)[0]['ranking'][0]
        self.assertEqual(row['score'], 70)
        self.assertEqual(row['uncertainty']['confirmed_gap_points'], 10)
        self.assertTrue(any(x['priority'] == 'prerequisite' for x in row['points_to_validate']))


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.headers = ['Rank', 'name', 'Match', 'Xp', 'Description', 'Availability',
                        'Phone Number', 'Email address', 'Notes', 'Cost']
        values = {h: '' for h in self.headers}
        values.update({'Rank': 4, 'name': 'Example Candidate', 'Match': .8, 'Xp': '6 years',
                       'Availability': 'Next month', 'Phone Number': '+352 000000',
                       'Email address': 'EXAMPLE@example.com', 'Notes': 'Colleague note',
                       'Cost': {'formula': '=1+2', 'value': 3}})
        self.snapshot = dict(workbook_id='fictional-workbook', sheet='Example', jd_id='one', complete=True,
                             headers=self.headers, score_format='percentage',
                             rows=[dict(row=2, values=values)])
        self.row = dict(candidate_id='c1', candidate='Example Candidate', score=85,
                        rank=1, relevant_experience='7-8 years',
                        short_description='Delivered programme outcomes.', phone='+352 000000',
                        email='example@example.com')
        self.jobs = [dict(jd_id='one', title='Example role', ranking=[self.row])]

    def apply_fictional(self, planned):
        # Model literal writes to verify re-planning, not a real workbook adapter.
        rows = {r['row']: r for r in self.snapshot['rows']}
        for identity in planned['identities']:
            rows.setdefault(identity['row'], dict(row=identity['row'],
                                                 values={h: '' for h in self.headers}))
        for p in planned['patches']:
            import re
            m = re.fullmatch(r'([A-Z]+)(\d+):([A-Z]+)\d+', p['range'])
            first = 0
            for c in m[1]:
                first = first*26 + ord(c)-64
            for offset, v in enumerate(p['values'][0]):
                rows[int(m[2])]['values'][self.headers[first-1+offset]] = v
        self.snapshot['rows'] = list(rows.values())

    def test_batch_plan_is_idempotent_preserves_manual_fields_and_scales_scores(self):
        before = copy.deepcopy(self.snapshot)
        planned = workbook_plan.plan(self.jobs, self.snapshot)
        self.assertEqual(planned['identities'][0]['action'], 'update')
        patch = next(p for p in planned['patches'] if p['range'] == 'C2:E2')
        self.assertEqual(patch['values'][0][0], .85)
        self.assertFalse(any(p['range'].startswith(('A', 'F', 'I', 'J')) for p in planned['patches']))
        self.assertEqual(self.snapshot, before)
        self.apply_fictional(planned)
        self.assertEqual(workbook_plan.plan(self.jobs, self.snapshot)['patches'], [])
        for field in ['Rank', 'Availability', 'Notes', 'Cost']:
            self.assertEqual(self.snapshot['rows'][0]['values'][field], before['rows'][0]['values'][field])

    def test_name_and_phone_match_without_email_column(self):
        self.snapshot['headers'].remove('Email address')
        self.snapshot['rows'][0]['values'].pop('Email address')
        planned = workbook_plan.plan(self.jobs, self.snapshot)
        self.assertEqual(planned['identities'][0]['row'], 2)

    def test_namesake_and_duplicate_email_stop_before_writing(self):
        self.snapshot['rows'][0]['values']['Email address'] = 'other@example.com'
        self.snapshot['rows'][0]['values']['Phone Number'] = 'different'
        with self.assertRaisesRegex(ValueError, 'corroboration'):
            workbook_plan.plan(self.jobs, self.snapshot)
        self.snapshot['rows'][0]['values']['Email address'] = self.row['email']
        other = copy.deepcopy(self.snapshot['rows'][0]); other['row'] = 3
        self.snapshot['rows'].append(other)
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            workbook_plan.plan(self.jobs, self.snapshot)

    def test_conflicts_and_formula_targets_fail_closed(self):
        planned = workbook_plan.plan(self.jobs, self.snapshot)
        observed = dict(workbook_id='fictional-workbook', sheet='Example', headers=self.headers,
                        ranges={p['range']: p['expected_before'] for p in planned['patches']})
        workbook_plan.verify(planned, observed)
        observed['ranges'][planned['patches'][0]['range']] = [['New colleague edit']]
        with self.assertRaisesRegex(ValueError, 'changed'):
            workbook_plan.verify(planned, observed)
        self.snapshot['rows'][0]['values']['Match'] = {'formula': '=1', 'value': 1}
        with self.assertRaisesRegex(ValueError, 'Preserve formula'):
            workbook_plan.plan(self.jobs, self.snapshot)

    def test_wrong_workbook_partial_writes_and_unsaved_results_fail_verification(self):
        planned = workbook_plan.plan(self.jobs, self.snapshot)
        observed = dict(workbook_id='different-workbook', sheet='Example', headers=self.headers,
                        ranges={p['range']: p['values'] for p in planned['patches']}, saved=True)
        with self.assertRaisesRegex(ValueError, 'target'):
            workbook_plan.verify_applied(planned, observed)
        observed['workbook_id'] = 'fictional-workbook'
        workbook_plan.verify_applied(planned, observed)
        observed['saved'] = False
        with self.assertRaisesRegex(ValueError, 'save state'):
            workbook_plan.verify_applied(planned, observed)
        observed['saved'] = True
        observed['ranges'][planned['patches'][0]['range']] = [['Incomplete write']]
        with self.assertRaisesRegex(ValueError, 'not verified'):
            workbook_plan.verify_applied(planned, observed)

    def test_explicit_selection_overrides_threshold_only_for_named_candidate(self):
        self.row['score'] = 59
        self.assertEqual(workbook_plan.plan(self.jobs, self.snapshot)['patches'], [])
        planned = workbook_plan.plan(self.jobs, self.snapshot, ['c1'])
        self.assertTrue(planned['patches'])
        self.assertEqual(next(p for p in planned['patches'] if p['range'] == 'C2:E2')['values'][0][0], .59)
        with self.assertRaisesRegex(ValueError, 'unknown'):
            workbook_plan.plan(self.jobs, self.snapshot, ['wrong'])

    def test_append_preserves_literal_text_and_no_headers_are_added(self):
        self.row.update(candidate_id='c2', candidate='New Example', email='new@example.com',
                        phone='+352 111111', short_description='=source text, not a formula')
        planned = workbook_plan.plan(self.jobs, self.snapshot)
        self.assertEqual(planned['headers'], self.headers)
        self.assertEqual(planned['identities'][0]['row'], 3)
        p = next(p for p in planned['patches'] if p['range'] == 'B3:E3')
        self.assertEqual(p['value_types'][0], ['text', 'number', 'text', 'text'])
        self.apply_fictional(planned)
        self.assertEqual(workbook_plan.plan(self.jobs, self.snapshot)['patches'], [])


if __name__ == '__main__':
    unittest.main()
