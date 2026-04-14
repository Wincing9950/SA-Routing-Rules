#!/usr/bin/env python3
"""
Deduplicate entries across curated data/*.txt files.
Files are processed in order; a domain that appears in file N is removed
from all subsequent files (N+1, N+2, ...) and within each file itself.
Comments and blank lines are preserved.
"""
import sys


def dedup_curated(filepaths):
    """
    Deduplicate domains across and within the given files.
    Modifies files in-place.
    """
    global_seen = set()

    for filepath in filepaths:
        with open(filepath, encoding='utf-8') as f:
            raw_lines = f.readlines()

        out_lines = []
        file_seen = set()

        for line in raw_lines:
            stripped = line.rstrip('\n')
            domain = stripped.strip().lower()

            # Preserve comments and blank lines
            if not domain or domain.startswith('#'):
                out_lines.append(line)
                continue

            if domain in global_seen or domain in file_seen:
                continue  # skip duplicate

            file_seen.add(domain)
            global_seen.add(domain)
            out_lines.append(line)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(out_lines)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} file1.txt [file2.txt ...]")
        sys.exit(1)
    dedup_curated(sys.argv[1:])
    print(f"Deduplicated {len(sys.argv) - 1} file(s)")
