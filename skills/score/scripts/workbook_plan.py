#!/usr/bin/env python3
"""Prepare changed ranges from a complete observed sheet snapshot, without Excel I/O.

Usage: workbook_plan.py ranking.json snapshot.json plan.json [--selected-id ID]
Snapshot: {workbook_id, sheet, jd_id, headers: [...], complete: true,
           score_format: "number"|"percentage",
           rows: [{row: 2, values: {"Candidate": "...", ...}}]}
Read the entire used table (including manual columns); values are scalars.
Formula cells must be represented as {"formula": "=...", "value": ...}.
Apply patches as literal values, using the discovered connector schema. Re-read
every expected_before value before writing and abort/replan on any conflict.
This helper never opens, uploads, replaces or writes a cloud workbook.
"""
import argparse
import json
import re
from pathlib import Path

from rank import require
from workbook_rows import columns, project


def norm(value):
    return ' '.join(str(value or '').strip().casefold().split())


def phone(value):
    return re.sub(r'\D', '', str(value or ''))


def value(cell):
    return cell.get('value', '') if isinstance(cell, dict) else cell


def letter(index):
    result = ''
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def plan(jobs, snapshot, selected_ids=()):
    require(snapshot.get('complete') is True, 'Read a complete used-table snapshot first')
    require(isinstance(snapshot.get('workbook_id'), str) and snapshot['workbook_id'].strip(),
            'Bind the snapshot to the verified workbook ID or canonical link')
    require(snapshot.get('score_format') in ('number', 'percentage'),
            'Inspect the Match number format before planning')
    headers = snapshot['headers']
    mapping = columns(headers)
    require('candidate' in mapping and 'score' in mapping, 'Candidate and Match columns are required')
    require(len(set(headers)) == len(headers), 'Duplicate headers are ambiguous')
    column_numbers = {header: index for index, header in enumerate(headers, 1)}
    source = snapshot['rows']
    row_numbers = [r['row'] for r in source]
    require(all(type(r) is int and r >= 2 for r in row_numbers)
            and len(set(row_numbers)) == len(row_numbers), 'Invalid/duplicate worksheet row numbers')
    require(all(set(r['values']) == set(headers) for r in source),
            'Snapshot rows must include every existing header, including manual fields')
    job = [j for j in jobs if j['jd_id'] == snapshot['jd_id']]
    require(len(job) == 1, 'Select exactly one JD matching this sheet snapshot')
    projected = project(job, headers, selected_ids=selected_ids)[0]['rows']
    occupied = [r['row'] for r in source if any(value(v) not in ('', None)
                                               or isinstance(v, dict) and v.get('formula')
                                               for v in r['values'].values())]
    next_row = max(occupied, default=1) + 1
    patches, identities, claimed_rows = [], [], set()
    # Virtual rows make repeats inside this batch idempotent too.
    working = [dict(row=r['row'], values=dict(r['values'])) for r in source]
    for candidate in projected:
        identity = candidate['identity']
        matches = []
        if identity['email'] and 'email' in mapping:
            matches = [r for r in working if norm(value(r['values'].get(mapping['email'])))
                       == norm(identity['email'])]
        if not matches:
            names = [r for r in working if norm(value(r['values'].get(mapping['candidate'])))
                     == norm(identity['name'])]
            if names:
                matches = [r for r in names if 'phone' in mapping and phone(identity['phone'])
                           and phone(value(r['values'].get(mapping['phone']))) == phone(identity['phone'])]
                require(bool(matches), 'Same-name candidate needs phone/email corroboration; do not append')
        require(len(matches) <= 1, 'Ambiguous candidate identity; inspect before writing')
        if matches:
            target = matches[0]
            require(norm(value(target['values'].get(mapping['candidate']))) == norm(identity['name']),
                    'Matched email has a conflicting name; inspect identity')
        else:
            target = dict(row=next_row, values={h: '' for h in headers})
            working.append(target)
            next_row += 1
        require(target['row'] not in claimed_rows,
                'Two selected profiles match the same person; reconcile duplicate versions first')
        claimed_rows.add(target['row'])
        changes = []
        for header, desired in candidate['values'].items():
            if header == mapping['score'] and snapshot['score_format'] == 'percentage':
                desired = desired / 100
            old = target['values'].get(header, '')
            if isinstance(old, dict) and old.get('formula'):
                raise ValueError(f'Preserve formula in {header}; resolve before writing')
            if value(old) == desired:
                continue
            col = column_numbers[header]
            changes.append((col, value(old), desired))
            target['values'][header] = desired
        changes.sort()
        # Coalesce adjacent changed columns; never span manual/unchanged cells.
        groups = []
        for change in changes:
            if not groups or change[0] != groups[-1][-1][0] + 1:
                groups.append([])
            groups[-1].append(change)
        for group in groups:
            start, end = group[0][0], group[-1][0]
            address = f'{letter(start)}{target["row"]}:{letter(end)}{target["row"]}'
            patches.append(dict(range=address,
                                expected_before=[[x[1] for x in group]],
                                values=[[x[2] for x in group]],
                                value_types=[['text' if isinstance(x[2], str) else 'number'
                                              for x in group]]))
        identities.append(dict(candidate_id=candidate['candidate_id'], row=target['row'],
                               action='update' if matches else 'append'))
    return dict(workbook_id=snapshot['workbook_id'], sheet=snapshot['sheet'],
                jd_id=snapshot['jd_id'], headers=headers,
                identities=identities, patches=patches,
                transport='Use discovered range-write tools; literal values only, no formula interpretation',
                precondition='Re-read headers and expected_before ranges; abort/replan on any difference')


def verify(plan_data, observed):
    """Fail closed on colleague edits or schema changes before applying a plan."""
    require(observed['workbook_id'] == plan_data['workbook_id']
            and observed['sheet'] == plan_data['sheet'] and observed['headers'] == plan_data['headers'],
            'Workbook target/headers changed; replan')
    for patch in plan_data['patches']:
        require(observed['ranges'].get(patch['range']) == patch['expected_before'],
                f'Workbook changed at {patch["range"]}; replan')


def verify_applied(plan_data, observed):
    require(observed['workbook_id'] == plan_data['workbook_id']
            and observed['sheet'] == plan_data['sheet'] and observed['headers'] == plan_data['headers'],
            'Workbook target/headers changed during write')
    for patch in plan_data['patches']:
        require(observed['ranges'].get(patch['range']) == patch['values'],
                f'Write not verified at {patch["range"]}; reconcile partial results')
    require(observed.get('saved') is True, 'Workbook save state is not verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ranking', type=Path)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--selected-id', action='append', default=[])
    args = parser.parse_args()
    try:
        result = plan(json.loads(args.ranking.read_text(encoding='utf-8-sig')),
                      json.loads(args.snapshot.read_text(encoding='utf-8-sig')), args.selected_id)
        with args.output.open('x', encoding='utf-8') as target:
            json.dump(result, target, ensure_ascii=False, indent=2, allow_nan=False)
    except (ValueError, TypeError, KeyError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    print(f'Prepared {len(result["patches"])} changed ranges; no cloud writes performed')


if __name__ == '__main__':
    main()
