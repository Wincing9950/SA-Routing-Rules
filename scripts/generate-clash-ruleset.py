#!/usr/bin/env python3
"""
generate-clash-ruleset.py
Converts domains/sa.txt to Clash/Mihomo rule-provider YAML (sa.yaml).
The sa.mrs binary is then compiled via: mihomo convert-ruleset domain yaml sa.yaml sa.mrs

Clash rule-provider format:
  payload:
    - DOMAIN-SUFFIX,sa
    - DOMAIN-SUFFIX,gov.sa
    - DOMAIN-SUFFIX,noon.com

Usage:
  python3 scripts/generate-clash-ruleset.py --input domains/sa.txt --output release/sa.yaml
"""

import argparse
import sys
import os


def generate_yaml(input_path: str, output_path: str) -> int:
    """
    Read domain list and write Clash rule-provider YAML.
    Returns the number of rules written.
    """
    rules = []
    with open(input_path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            # All entries are DOMAIN-SUFFIX to catch all subdomains.
            rules.append(f"DOMAIN-SUFFIX,{line}")

    with open(output_path, 'w') as f:
        f.write('payload:\n')
        for rule in rules:
            f.write(f'  - {rule}\n')

    return len(rules)


def main():
    parser = argparse.ArgumentParser(description="Generate Clash/Mihomo rule-provider YAML")
    parser.add_argument('--input', default='domains/sa.txt')
    parser.add_argument('--output', default='release/sa.yaml')
    args = parser.parse_args()

    count = generate_yaml(args.input, args.output)
    print(f"  [clash-ruleset] Wrote {count} rules to {args.output}", flush=True)


if __name__ == '__main__':
    main()
