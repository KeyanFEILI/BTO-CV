import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('score_rank', ROOT/'scripts/rank.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/'references/input-example.json').read_text())

    def assignment(self, company='example-consultancy', assignment='project-1'):
        return dict(company_id=company, assignment_id=assignment, type='consulting',
                    company_basis='User-approved employer register',
                    relevance='Python delivery on the relevant project',
                    evidence=['example-cv.pdf p.1: Python developer at Example Consultancy.'])

    def test_weights_evidence_and_totals(self):
        row = engine.rank(self.data)[0]['ranking'][0]
        self.assertEqual(row['core'], 70)
        self.assertEqual(row['score'], 70)
        self.assertEqual(row['employer_bonus'], 0)
        self.assertEqual(row['biggest_gaps'][0]['criterion_id'], 'delivery')
        self.assertEqual(row['evidence_coverage_pct'], 89.5)

    def test_candidate_fields_repeat_with_jd_specific_experience(self):
        candidate = self.data['candidates'][0]
        candidate.update(latest_location='Luxembourg', phone='+352 000000',
                         email='example@example.com', source_languages='English: level unspecified')
        second_job = copy.deepcopy(self.data['jobs'][0])
        second_job['id'] = 'jd-2'
        self.data['jobs'].append(second_job)
        first = self.data['assessments'][0]
        first.update(relevant_experience='3 years', short_description='Python delivery; testing partially evidenced.')
        second = copy.deepcopy(first)
        second.update(jd_id='jd-2', relevant_experience='2 years', short_description='Different relevant scope.')
        self.data['assessments'].append(second)
        rows = [job['ranking'][0] for job in engine.rank(self.data)]
        for row in rows:
            for key in ('latest_location', 'phone', 'email', 'source_languages'):
                self.assertEqual(row[key], candidate[key])
            self.assertEqual(row['score'], 70)
        self.assertEqual([r['relevant_experience'] for r in rows], ['3 years', '2 years'])
        self.assertEqual(rows[1]['short_description'], second['short_description'])
        candidate.pop('phone')
        self.assertEqual(engine.rank(self.data)[0]['ranking'][0]['phone'], '')

    def test_languages_never_change_score_or_rank(self):
        expected = engine.rank(self.data)[0]['ranking'][0]
        check = self.data['assessments'][0]['languages']['english']
        for status in ('met', 'below_required', 'not_met', 'unknown'):
            check.update(status=status, evidence=['example-cv.pdf p.1: English B1.'])
            row = engine.rank(self.data)[0]['ranking'][0]
            for key in ('score', 'core', 'rank', 'employer_bonus', 'evidence_coverage_pct'):
                self.assertEqual(row[key], expected[key])

    def test_bonus_cap_and_no_double_counting(self):
        self.assertEqual(engine.bonus([]), 0)
        self.assertEqual(engine.bonus([self.assignment()]), 2.5)
        self.assertEqual(engine.bonus([self.assignment(), self.assignment()]), 2.5)
        self.assertEqual(engine.bonus([self.assignment(), self.assignment('client')]), 2.5)
        self.assertEqual(engine.bonus([self.assignment(), self.assignment(assignment='project-2')]), 2.5)
        many = [self.assignment('company-'+str(i), 'project-'+str(i)) for i in range(8)]
        self.assertEqual(engine.bonus(many), 5)
        # Counting must be order-independent even for overlapping employer/client entries.
        overlapping = [self.assignment('b','1'), self.assignment('a','1'), self.assignment('b','2')]
        self.assertEqual(engine.bonus(overlapping), 5)

    def test_every_jd_has_an_independent_complete_ranking_and_ties(self):
        second_job = copy.deepcopy(self.data['jobs'][0]); second_job['id'] = 'jd-2'
        self.data['jobs'].append(second_job)
        self.data['candidates'].append(dict(id='candidate-2', name='Second Candidate'))
        first = self.data['assessments'][0]
        for jid, cid in [('jd-1','candidate-2'), ('jd-2','candidate-1'), ('jd-2','candidate-2')]:
            item = copy.deepcopy(first); item.update(jd_id=jid, candidate_id=cid)
            if jid == 'jd-2' and cid == 'candidate-2':
                item['ratings']['delivery'].update(status='met', rating=1)
            self.data['assessments'].append(item)
        result = engine.rank(self.data)
        self.assertEqual([r['candidate_id'] for r in result[0]['ranking']], ['candidate-1','candidate-2'])
        self.assertEqual([r['rank'] for r in result[0]['ranking']], [1,1])
        self.assertEqual(result[1]['ranking'][0]['candidate_id'], 'candidate-2')
        self.data['assessments'].pop()
        with self.assertRaisesRegex(ValueError, 'every candidate'):
            engine.rank(self.data)

    def test_reject_missing_evidence_bad_weights_and_invalid_ratings(self):
        for mutation in ('evidence', 'weight', 'rating', 'language', 'company', 'duplicate', 'criterion'):
            data = copy.deepcopy(self.data)
            item = data['assessments'][0]
            if mutation == 'evidence': item['ratings']['core']['evidence'] = []
            if mutation == 'weight': data['jobs'][0]['criteria'][0]['weight'] = 45
            if mutation == 'rating': item['ratings']['core']['rating'] = True
            if mutation == 'language': item['languages'] = {}
            if mutation == 'company': item['employers'] = [dict(company_id='brand')]
            if mutation == 'duplicate': data['assessments'].append(copy.deepcopy(item))
            if mutation == 'criterion': data['jobs'][0]['criteria'][0]['kind'] = 'language'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                engine.rank(data)

    def test_cli_preserves_existing_output_and_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'input.json'; output = Path(folder)/'output.json'
            source.write_text(json.dumps(self.data), encoding='utf-8')
            command = [sys.executable, str(ROOT/'scripts/rank.py'), str(source), str(output)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = output.read_bytes()
            self.assertEqual(json.loads(original)[0]['ranking'][0]['score'], 70)
            retry = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(output.read_bytes(), original)
            self.assertEqual(json.loads(source.read_text()), self.data)

    def test_perfect_fit_caps_at_100_and_needs_no_language_requirement(self):
        job = self.data['jobs'][0]
        job['languages'] = []
        item = self.data['assessments'][0]
        item['languages'] = {}
        for rating in item['ratings'].values():
            rating.update(status='met', rating=1, evidence=['example-cv.pdf p.1: Direct evidence.'])
        item['employers'] = [self.assignment('a','1'), self.assignment('b','2')]
        row = engine.rank(self.data)[0]['ranking'][0]
        self.assertEqual(row['score'], 100)
        self.assertEqual(row['evidence_coverage_pct'], 100)
        self.assertEqual(row['languages'], [])

    def test_unknown_and_confirmed_shortfall_are_kept_distinct(self):
        criterion = self.data['assessments'][0]['ratings']['sector']
        unknown = engine.rank(self.data)[0]['ranking'][0]
        criterion.update(status='not_met', evidence=['example-cv.pdf p.1: No banking experience.'])
        confirmed = engine.rank(self.data)[0]['ranking'][0]
        self.assertEqual(unknown['score'], confirmed['score'])
        self.assertNotEqual(unknown['evidence_coverage_pct'], confirmed['evidence_coverage_pct'])
        self.assertEqual(unknown['criteria'][-1]['status'], 'unknown')
        self.assertEqual(confirmed['criteria'][-1]['status'], 'not_met')


if __name__ == '__main__':
    unittest.main()
