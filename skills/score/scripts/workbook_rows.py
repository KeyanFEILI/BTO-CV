#!/usr/bin/env python3
"""Existing-header projection shared by workbook_plan.py and its tests.

Only non-empty supported fields are projected. Manual columns and posting-pool
ranks are preserved. Use workbook_plan.py as the single export command.
"""
from rank import experience_label, require


FIELDS = {
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


def project(jobs, headers, *, selected_ids=()):
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
