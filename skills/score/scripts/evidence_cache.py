#!/usr/bin/env python3
"""Private content-addressed extraction/profile cache. No network access.

Usage: evidence_cache.py TASK_CACHE SOURCE [SOURCE ...]
Prints only cache keys and reuse status, never CV text or contact details.
"""
import argparse
import hashlib
import json
from pathlib import Path

from extract_text import extract


def digest(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             allow_nan=False).encode('utf-8'))


class EvidenceCache:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.extractor = digest(Path(__file__).with_name('extract_text.py').read_bytes())

    def path(self, key):
        if len(key) != 64 or any(c not in '0123456789abcdef' for c in key):
            raise ValueError('Invalid cache key')
        return self.folder / (key + '.json')

    def read(self, key):
        path = self.path(key)
        if not path.exists():
            return None
        record = json.loads(path.read_text(encoding='utf-8'))
        if record.get('key') != key:
            raise ValueError('Cache key mismatch; reconcile the private cache')
        return record

    def write(self, key, record):
        temporary = self.path(key).with_suffix('.tmp')
        temporary.write_text(json.dumps(dict(record, key=key), ensure_ascii=False,
                                        indent=2, allow_nan=False), encoding='utf-8')
        temporary.replace(self.path(key))

    def source(self, source):
        source = Path(source)
        source_hash = digest(source.read_bytes())
        key = fingerprint(dict(source_hash=source_hash, suffix=source.suffix.lower(),
                               extractor=self.extractor))
        record = self.read(key)
        if record is not None:
            return key, record, True
        content = extract(source)
        if not content.strip():
            raise ValueError('No extractable text; inspect/OCR the source')
        record = dict(source_hash=source_hash, extractor=self.extractor,
                      text=content, profile=None)
        self.write(key, record)
        return key, record, False

    def save_profile(self, source_key, profile):
        record = self.read(source_key)
        if record is None or 'text' not in record:
            raise ValueError('Extract the source before reconciling its profile')
        record['profile'] = profile
        self.write(source_key, record)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('sources', nargs='+', type=Path)
    args = parser.parse_args()
    cache = EvidenceCache(args.folder)
    for source in args.sources:
        key, _, reused = cache.source(source)
        print(json.dumps(dict(key=key, reused=reused)))


if __name__ == '__main__':
    main()
