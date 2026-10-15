#!/usr/bin/env python3
"""Build and structurally verify a CV in one process; source and visual review remain required."""
import argparse
import json
from pathlib import Path
from time import perf_counter
import zipfile

import verify_docx


def convert(source, output, template=None):
    started = perf_counter()
    data = json.loads(Path(source).read_text(encoding='utf-8-sig'))
    # Build already validates the input. Do not run a separate --check first.
    verify_docx.builder.build(data, output, template)
    built = perf_counter()
    result = verify_docx.verify(data, output, template)
    checked = perf_counter()
    return dict(result, build_seconds=round(built - started, 4),
                verify_seconds=round(checked - built, 4))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='Reconciled UTF-8 candidate JSON')
    parser.add_argument('output', type=Path, help='New editable .docx file')
    parser.add_argument('--template', type=Path, help='Explicit approved paired Word master')
    args = parser.parse_args()
    try:
        result = convert(args.input, args.output, args.template)
    except (ValueError, KeyError, IndexError, OSError, zipfile.BadZipFile) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(dict(result, source_review='required', visual_review='required')))


if __name__ == '__main__':
    main()
