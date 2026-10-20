#!/usr/bin/env python3
"""Validate evidence assessments and rank every CV separately for each JD."""
import argparse
import json
from itertools import combinations
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def evidence(value):
    return isinstance(value, list) and bool(value) and all(text(v) for v in value)


def indexed(items, label):
    require(isinstance(items, list) and items, f'{label} must be a non-empty list')
    require(all(isinstance(x, dict) and text(x.get('id')) for x in items),
            f'{label} entries need unique non-empty IDs')
    result = {x['id']: x for x in items}
    require(len(result) == len(items), f'Duplicate {label} ID')
    return result


def bonus(assignments):
    require(isinstance(assignments, list), 'employers must be a list')
    for item in assignments:
        require(isinstance(item, dict), 'Invalid employer assignment')
        require(all(text(item.get(k)) for k in
                    ('company_id', 'assignment_id', 'company_basis', 'relevance')),
                'Bonus needs employer classification, assignment and relevance')
        require(item.get('type') in ('large_company', 'consulting'),
                'Bonus employer type must be large_company or consulting')
        require(evidence(item.get('evidence')), 'Bonus needs CV evidence')
    keys = [(a['company_id'].strip().casefold(), a['assignment_id'].strip().casefold())
            for a in assignments]
    distinct = any(a[0] != b[0] and a[1] != b[1] for a, b in combinations(keys, 2))
    return 5 if distinct else 2.5 if keys else 0


def rank(data):
    require(isinstance(data, dict), 'Input must be an object')
    jobs = indexed(data.get('jobs'), 'jobs')
    candidates = indexed(data.get('candidates'), 'candidates')
    for candidate in candidates.values():
        require(text(candidate.get('name')), 'Candidate name missing')
        for field in ('latest_location', 'phone', 'email', 'source_languages'):
            require(isinstance(candidate.get(field, ''), str), f'{field} must be text')
    for job in jobs.values():
        require(text(job.get('title')), 'JD title missing')
        criteria = indexed(job.get('criteria'), 'criteria')
        for criterion in criteria.values():
            require(text(criterion.get('text')), 'Criterion text missing')
            weight = criterion.get('weight')
            require(type(weight) is int and weight > 0, 'Weights must be positive integers')
            require(type(criterion.get('required', False)) is bool, 'required must be boolean')
            require(criterion.get('kind') in ('skills', 'delivery', 'experience', 'sector'),
                    'Criterion kind must be skills, delivery, experience or sector; no language/employer criteria')
        require(sum(c['weight'] for c in criteria.values()) == 95, 'JD weights must total 95')
        languages = job.get('languages', [])
        require(isinstance(languages, list), 'JD languages must be a list')
        if languages:
            indexed(languages, 'languages')
        for language in languages:
            require(text(language.get('condition')), 'Language condition missing')
            require(type(language.get('required')) is bool, 'Language required must be boolean')
    assessments = data.get('assessments')
    require(isinstance(assessments, list), 'assessments must be a list')
    seen, results = set(), {key: [] for key in jobs}
    statuses = {'met': (1,), 'partial': (.25, .5, .75), 'not_met': (0,), 'unknown': (0,)}
    for assessment in assessments:
        require(isinstance(assessment, dict), 'Invalid assessment')
        jid, cid = assessment.get('jd_id'), assessment.get('candidate_id')
        require(jid in jobs and cid in candidates, 'Unknown JD or candidate ID')
        require((jid, cid) not in seen, 'Duplicate JD/candidate assessment')
        seen.add((jid, cid))
        job = jobs[jid]
        for field in ('relevant_experience', 'short_description'):
            require(isinstance(assessment.get(field, ''), str), f'{field} must be text')
        ratings = assessment.get('ratings')
        require(isinstance(ratings, dict), 'ratings must be an object')
        require(set(ratings) == {c['id'] for c in job['criteria']}, 'Incomplete criterion ratings')
        core, coverage, details = 0, 0, []
        for criterion in job['criteria']:
            item = ratings[criterion['id']]
            require(isinstance(item, dict), 'Invalid rating')
            status, value = item.get('status'), item.get('rating')
            require(status in statuses and type(value) in (int, float)
                    and value in statuses[status], 'Invalid status/rating combination')
            require(text(item.get('reason')), 'Every rating needs a reason')
            require(status == 'unknown' or evidence(item.get('evidence')),
                    'Supported ratings need CV evidence; otherwise use unknown')
            points = criterion['weight'] * value
            core += points
            coverage += criterion['weight'] if status != 'unknown' else 0
            details.append(dict(criterion_id=criterion['id'], criterion=criterion['text'],
                                required=criterion.get('required', False), status=status,
                                points=points, lost_points=criterion['weight'] - points,
                                reason=item['reason'], evidence=item.get('evidence', [])))
        checks = assessment.get('languages', {})
        require(isinstance(checks, dict), 'Language checks must be an object')
        require(set(checks) == {x['id'] for x in job.get('languages', [])},
                'Incomplete language conditions')
        flags = []
        for language in job.get('languages', []):
            check = checks[language['id']]
            require(isinstance(check, dict), 'Invalid language check')
            require(check.get('status') in ('met', 'below_required', 'not_met', 'unknown'),
                    'Invalid language status')
            require(text(check.get('note')), 'Language check needs a note')
            require(check['status'] == 'unknown' or evidence(check.get('evidence')),
                    'Confirmed language findings need CV evidence')
            flags.append(dict(condition=language['condition'], required=language['required'], **check))
        extra = bonus(assessment.get('employers', []))
        results[jid].append(dict(candidate_id=cid, candidate=candidates[cid]['name'],
                                 **{k: candidates[cid].get(k, '') for k in
                                    ('latest_location', 'phone', 'email', 'source_languages')},
                                 **{k: assessment.get(k, '') for k in
                                    ('relevant_experience', 'short_description')},
                                 score=core + extra, core=core, employer_bonus=extra,
                                 evidence_coverage_pct=round(100 * coverage / 95, 1),
                                 languages=flags, criteria=details,
                                 biggest_gaps=sorted((x for x in details if x['lost_points']),
                                                     key=lambda x: -x['lost_points'])[:3]))
    require(len(seen) == len(jobs) * len(candidates), 'Assess every candidate against every JD')
    output = []
    order = {cid: i for i, cid in enumerate(candidates)}
    for jid, rows in results.items():
        rows.sort(key=lambda x: (-x['score'], order[x['candidate_id']]))
        previous, position = None, 0
        for i, row in enumerate(rows, 1):
            if row['score'] != previous:
                position, previous = i, row['score']
            row['rank'] = position
        output.append(dict(jd_id=jid, title=jobs[jid]['title'], ranking=rows))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        result = rank(json.loads(args.input.read_text(encoding='utf-8-sig')))
        require(args.output.resolve() != args.input.resolve(), 'Never overwrite input')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=2, allow_nan=False)
    except (ValueError, OSError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
    print(f'Ranked {sum(len(j["ranking"]) for j in result)} assessments across {len(result)} JDs')


if __name__ == '__main__':
    main()
