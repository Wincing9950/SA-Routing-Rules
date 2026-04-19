#!/usr/bin/env python3
"""
sanitize-domains.py
Filters stdin/file domain list to only output geosite-valid domains.

A domain is valid for v2fly geosite if every dot-separated label:
  - Is non-empty
  - Starts with [a-z0-9]
  - Contains only [a-z0-9-]
  - Ends with [a-z0-9]
  - Is 1–63 characters long
And the full domain has at least 2 labels and is ≤253 characters.

Usage:
  python3 scripts/sanitize-domains.py < input.txt > output.txt
  python3 scripts/sanitize-domains.py input.txt > output.txt
"""

import re
import sys

_label_re = re.compile(r'^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$')


def is_valid_geosite_domain(domain):
    if not domain or len(domain) > 253:
        return False
    labels = domain.split('.')
    if len(labels) < 2:
        return False
    for label in labels:
        if not label or len(label) > 63:
            return False
        if not _label_re.match(label):
            return False
    return True


def main():
    src = open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin
    kept = dropped = 0
    for line in src:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if is_valid_geosite_domain(line):
            print(line)
            kept += 1
        else:
            dropped += 1
    print(f"sanitize-domains: kept {kept}, dropped {dropped} invalid", file=sys.stderr)


if __name__ == '__main__':
    main()
