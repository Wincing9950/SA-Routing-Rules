"""
fetch-cloudflare-radar.py

Fetches the Cloudflare Radar top-100 domains for Saudi Arabia and filters
them through the exclusion engine before writing to an output file.
"""

import os
import sys
import importlib.util

import requests

# ---------------------------------------------------------------------------
# Import exclusion helpers from the sibling exclusion.py
# ---------------------------------------------------------------------------
_excl_spec = importlib.util.spec_from_file_location(
    'exclusion',
    os.path.join(os.path.dirname(__file__), 'exclusion.py')
)
_excl_mod = importlib.util.module_from_spec(_excl_spec)
_excl_spec.loader.exec_module(_excl_mod)
build_exclusion_set = _excl_mod.build_exclusion_set
is_excluded = _excl_mod.is_excluded

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_RADAR_URL = (
    'https://api.cloudflare.com/client/v4/radar/ranking/top'
    '?country_code=SA&limit=100&rankingType=POPULAR'
)
_DEFAULT_OUTPUT = 'sa-radar.txt'


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_top_sa_domains(api_token: str, exclusion_set: set) -> list:
    """Fetch Cloudflare Radar top SA domains and return filtered list.

    Parameters
    ----------
    api_token:
        Cloudflare API bearer token. If empty/None, prints a warning and
        returns an empty list without making any network calls.
    exclusion_set:
        Set of apex domains (and suffixes) to exclude.

    Returns
    -------
    list[str]
        Domains that passed the exclusion filter, in ranking order.
    """
    if not api_token:
        print('WARNING: CF_API_KEY is not set; skipping Cloudflare Radar fetch.')
        return []

    try:
        response = requests.get(
            _RADAR_URL,
            headers={'Authorization': f'Bearer {api_token}'},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        top_entries = data['result']['top']
    except Exception as exc:
        print(f'WARNING: Cloudflare Radar request failed: {exc}')
        return []

    kept = []
    for entry in top_entries:
        domain = entry.get('domain', '').lower().strip()
        if not domain:
            continue
        if is_excluded(domain, exclusion_set):
            continue
        kept.append(domain)

    return kept


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main():
    api_token = os.environ.get('CF_API_KEY', '')
    output_path = os.environ.get('RADAR_OUTPUT', _DEFAULT_OUTPUT)

    exclusion_set = build_exclusion_set()
    domains = fetch_top_sa_domains(api_token=api_token, exclusion_set=exclusion_set)

    with open(output_path, 'w') as fh:
        for domain in domains:
            fh.write(domain + '\n')

    print(f'Wrote {len(domains)} domains to {output_path}')


if __name__ == '__main__':
    main()
