#!/usr/bin/env python3
"""
Majestic Million Saudi Arabia Domain Filter
============================================
Downloads the Majestic Million top-1M CSV (updated weekly) and filters
for Saudi Arabia domains using:
  1. .sa / .com.sa TLD column match (immediate include)
  2. Known Saudi company domains (immediate include)
  3. Saudi keyword match in domain name (immediate include)
  4. DNS resolution to Saudi IP ranges for top-50K unknown domains

Output: domains/sa-majestic.txt
"""

import sys
import csv
import io
import time
import ipaddress
import concurrent.futures
import argparse
import os
import importlib.util

import requests

# Re-use filter constants from filter_crux_sa_domains.py
_scripts_dir = os.path.dirname(__file__)
_spec = importlib.util.spec_from_file_location(
    '_crux_filter',
    os.path.join(_scripts_dir, 'filter_crux_sa_domains.py')
)
_crux = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_crux)

is_global_exclude = _crux.is_global_exclude
is_known_saudi = _crux.is_known_saudi
has_sa_keyword = _crux.has_sa_keyword
load_sa_ip_ranges = _crux.load_sa_ip_ranges
is_saudi_ip = _crux.is_saudi_ip
resolve_domain = _crux.resolve_domain

MAJESTIC_CSV_URL = "https://downloads.majestic.com/majestic_million.csv"
SA_TLDS = {'sa', 'com.sa', 'gov.sa', 'edu.sa', 'org.sa', 'net.sa', 'med.sa', 'sch.sa'}
DNS_CHECK_TOP_N = 50_000


def classify_majestic_row(row):
    """
    Return classification string or None to skip.
    Returns: 'tld' | 'known' | 'keyword' | 'dns_check' | None
    """
    domain = row.get('Domain', '').lower().strip()
    tld = row.get('TLD', '').lower().strip()
    try:
        rank = int(row.get('GlobalRank', 9_999_999))
    except (ValueError, TypeError):
        rank = 9_999_999

    if not domain:
        return None

    full = f"{domain}.{tld}" if tld else domain

    if is_global_exclude(full):
        return None

    if tld in SA_TLDS:
        return 'tld'

    if is_known_saudi(full):
        return 'known'

    if has_sa_keyword(domain):
        return 'keyword'

    if rank <= DNS_CHECK_TOP_N:
        return 'dns_check'

    return None


def download_majestic_csv():
    """Download and return Majestic Million CSV rows as list of dicts."""
    print("==> Downloading Majestic Million CSV...", file=sys.stderr)
    r = requests.get(MAJESTIC_CSV_URL, timeout=120, stream=True)
    r.raise_for_status()
    content = r.content.decode('utf-8', errors='replace')
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    print(f"  -> Downloaded {len(rows):,} rows", file=sys.stderr)
    return rows


def filter_majestic(rows, sa_ip_file=None, resolve_dns=False, max_workers=100):
    """Filter Majestic rows for Saudi domains."""
    sa_networks = load_sa_ip_ranges(sa_ip_file) if sa_ip_file else []

    immediate = set()
    dns_candidates = []

    for row in rows:
        cls = classify_majestic_row(row)
        if cls is None:
            continue
        domain = row.get('Domain', '').lower()
        tld = row.get('TLD', '').lower()
        full = f"{domain}.{tld}" if tld else domain

        if cls == 'dns_check':
            dns_candidates.append(full)
        else:
            immediate.add(full)

    print(f"  -> Immediate SA: {len(immediate)}", file=sys.stderr)
    print(f"  -> DNS candidates: {len(dns_candidates)}", file=sys.stderr)

    dns_saudi = set()
    if resolve_dns and sa_networks and dns_candidates:
        print(f"  -> Resolving {len(dns_candidates)} DNS candidates...", file=sys.stderr)

        def check(domain):
            ips = resolve_domain(domain)
            for ip in ips:
                if is_saudi_ip(ip, sa_networks):
                    return domain, True
            return domain, False

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            for domain, is_sa in ex.map(check, dns_candidates):
                if is_sa:
                    dns_saudi.add(domain)

        print(f"  -> DNS-verified SA: {len(dns_saudi)}", file=sys.stderr)

    return immediate | dns_saudi


def main():
    parser = argparse.ArgumentParser(description='Filter Majestic Million for SA domains')
    parser.add_argument('-i', '--ip-file', help='Saudi IP ranges CIDR file')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--resolve-dns', action='store_true')
    parser.add_argument('--max-workers', type=int, default=100)
    args = parser.parse_args()

    rows = download_majestic_csv()
    domains = filter_majestic(rows, sa_ip_file=args.ip_file,
                              resolve_dns=args.resolve_dns,
                              max_workers=args.max_workers)

    print(f"\n==> Total SA Majestic domains: {len(domains)}", file=sys.stderr)

    out = sorted(domains)
    if args.output:
        with open(args.output, 'w') as f:
            f.write("# Saudi Arabia domains from Majestic Million\n")
            f.write("# Source: majestic.com/reports/majestic-million\n\n")
            for d in out:
                f.write(d + '\n')
    else:
        for d in out:
            print(d)


if __name__ == '__main__':
    main()
