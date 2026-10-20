#!/usr/bin/env python3
"""Project final rankings onto observed headers; never create workbook columns.

Usage: workbook_rows.py ranking.json headers.json rows.json
headers.json is the exact existing header row, as a JSON list of strings.
Output rows contain only supported non-empty fields, keyed by existing headers.
Resolve candidate identities/row destinations and inspect number formats before
applying this projection with a connected workbook tool or normal Excel UI.
"""
import argparse
import json
from pathlib import Path

from rank import experience_label, require


FIELDS = {
    'rank': ('rank',),
    'candidate': ('candidate', 'full name', 'candidate name', 'name'),
    'score': ('match', 'score', 'score /100'),
    'latest_location': ('latest location', 'location'),
    'relevant_experience': ('xp', 'relevant experience'),
    'short_description': ('short description', 'description'),
    'phone': ('phone number', 'phone'),
    'email': ('email address', 'email'),
    'source_languages': ('languages',),
}
MISSING = {'', 'not provided', 'unknown', 'cannot determine'}


def columns(headers):
    require(isinstance(headers, list) and all(isinstance(h, str) for h in headers),
            'headers must be the observed list of strings')
    mapping = {}
    for field, aliases in FIELDS.items():
        matches = [h for h in headers if h.strip().casefold() in aliases]
        require(len(matches) <= 1, f'Ambiguous existing headers for {field}')
        if matches:
            mapping[field] = matches[0]
    return mapping


def project(jobs, headers, *, selected_ids=(), write_batch_ranks=False):
    require(isinstance(jobs, list), 'ranking must be a list of job results')
    mapping = columns(headers)
    selected_ids = set(selected_ids)
    known = {r['candidate_id'] for j in jobs for r in j['ranking'] if 'candidate_id' in r}
    require(selected_ids <= known, 'Explicit selection contains unknown candidate IDs')
    output = []
    for job in jobs:
        rows = []
        for row in job['ranking']:
            # Use the final, unrounded score including bonus, without reassessment.
            if row['score'] < 80 and row.get('candidate_id') not in selected_ids:
                continue
            experience_label(row.get('relevant_experience', ''))
            values = {}
            for field, header in mapping.items():
                if field == 'rank' and not write_batch_ranks:
                    continue  # Do not replace whole-pool ranks with a batch rank.
                value = row.get(field, '')
                if value is None or (isinstance(value, str)
                                     and value.strip().casefold() in MISSING):
                    continue  # Never erase an existing value with missing data.
                values[header] = value
            rows.append({'candidate_id': row.get('candidate_id', ''),
                         'identity': {'name': row['candidate'],
                                     'email': row.get('email', ''),
                                     'phone': row.get('phone', '')},
                         'values': values})
        output.append({'jd_id': job['jd_id'], 'title': job['title'], 'rows': rows,
                       'omitted_fields': [f for f in FIELDS if f not in mapping]})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ranking', type=Path)
    parser.add_argument('headers', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--selected-id', action='append', default=[],
                        help='Only use for candidates explicitly selected by the user; overrides 80 threshold')
    args = parser.parse_args()
    try:
        jobs = json.loads(args.ranking.read_text(encoding='utf-8-sig'))
        headers = json.loads(args.headers.read_text(encoding='utf-8-sig'))
        result = project(jobs, headers, selected_ids=args.selected_id)
        with args.output.open('x', encoding='utf-8') as target:
            json.dump(result, target, ensure_ascii=False, indent=2, allow_nan=False)
    except (ValueError, OSError, TypeError, KeyError) as error:
        parser.exit(1, str(error) + '\n')
    print(f'Prepared {sum(len(j["rows"]) for j in result)} rows; headers unchanged')


if __name__ == '__main__':
    main()
