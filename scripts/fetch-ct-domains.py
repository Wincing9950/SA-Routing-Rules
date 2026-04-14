#!/usr/bin/env python3
"""
Certificate Transparency Domain Fetcher
========================================
Queries crt.sh to find all domains from Saudi Arabia Certificate
Transparency logs. Targets:
  1. All .sa TLD variants (direct cert query)
  2. Certificates issued to Saudi organizations (org name pivoting)

Rate-limited to ~3 req/s. Run weekly.
Output: domains/sa-ct.txt
"""

import sys
import time
import argparse
import requests

SA_TLD_PATTERNS = [
    '%.sa',
    '%.com.sa',
    '%.gov.sa',
    '%.edu.sa',
    '%.org.sa',
    '%.net.sa',
    '%.med.sa',
    '%.sch.sa',
]

SA_ORG_PIVOTS = [
    'Aramco', 'STC', 'Mobily', 'NEOM', 'Alrajhi', 'Alinma', 'SABIC',
    'Samba', 'Misk', 'AlBilad', 'Zain Saudi', 'CITC', 'KAUST',
]

CRT_SH_URL = "https://crt.sh/"
REQUEST_DELAY = 0.4


def normalize_domain(domain):
    """Lowercase, strip trailing dot and wildcard prefix."""
    if not domain:
        return ''
    d = domain.strip().lower().rstrip('.')
    if d.startswith('*.'):
        d = d[2:]
    return d


def extract_domains_from_cert(cert):
    """Extract all domain names from a crt.sh certificate entry."""
    domains = set()
    for field in ('name_value', 'common_name'):
        raw = cert.get(field, '') or ''
        for part in raw.replace(',', '\n').split('\n'):
            d = normalize_domain(part.strip())
            if d and '.' in d:
                domains.add(d)
    return domains


def parse_ct_response(data):
    """Parse a crt.sh JSON response list into a set of domain strings."""
    if not data:
        return set()
    domains = set()
    for cert in data:
        domains.update(extract_domains_from_cert(cert))
    return domains


def query_crtsh(q, retries=3):
    """Query crt.sh and return parsed JSON or empty list on failure."""
    params = {'q': q, 'output': 'json'}
    for attempt in range(retries):
        try:
            r = requests.get(CRT_SH_URL, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
        except Exception as e:
            print(f"  Warning: crt.sh query failed for {q!r}: {e}", file=sys.stderr)
            time.sleep(5)
    return []


def fetch_all_sa_ct_domains(output_file=None):
    """Fetch all SA-related domains from CT logs via crt.sh."""
    all_domains = set()

    print("==> Phase 1: Querying .sa TLD patterns...", file=sys.stderr)
    for pattern in SA_TLD_PATTERNS:
        print(f"  -> {pattern}", file=sys.stderr)
        certs = query_crtsh(pattern)
        domains = parse_ct_response(certs)
        all_domains.update(domains)
        print(f"     +{len(domains)} domains (total: {len(all_domains)})", file=sys.stderr)
        time.sleep(REQUEST_DELAY)

    print("==> Phase 2: Querying Saudi organization names...", file=sys.stderr)
    for org in SA_ORG_PIVOTS:
        print(f"  -> {org}", file=sys.stderr)
        certs = query_crtsh(org)
        domains = {d for d in parse_ct_response(certs) if d.endswith('.sa')}
        all_domains.update(domains)
        print(f"     +{len(domains)} .sa domains", file=sys.stderr)
        time.sleep(REQUEST_DELAY)

    sa_domains = {d for d in all_domains if d.endswith('.sa') or '.sa.' in d}
    print(f"\n==> Total unique SA CT domains: {len(sa_domains)}", file=sys.stderr)

    if output_file:
        with open(output_file, 'w') as f:
            f.write("# Saudi Arabia domains from Certificate Transparency logs\n")
            f.write("# Source: crt.sh — fetched by scripts/fetch-ct-domains.py\n\n")
            for d in sorted(sa_domains):
                f.write(d + '\n')
        print(f"Written to {output_file}", file=sys.stderr)
    else:
        for d in sorted(sa_domains):
            print(d)

    return sa_domains


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch SA domains from CT logs via crt.sh')
    parser.add_argument('-o', '--output', help='Output file path')
    args = parser.parse_args()
    fetch_all_sa_ct_domains(output_file=args.output)
