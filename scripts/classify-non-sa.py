"""
classify-non-sa.py — Classify non-.sa domains for routing-utility inclusion.

Decision order:
  1. SKIP       — domain suffix in exclusion_set
  2. INCLUDE    (reason='sa-tld')          — domain ends with .sa or equals 'sa'
  3. INCLUDE    (reason='entity-registry') — domain in entity_set
  4a. INCLUDE   (reason='geo-block')       — probe_fn says geo_blocked=True
  4b. REVIEW    (reason=f"score={n}")      — probe_fn score >= REVIEW_THRESHOLD
  5. EXCLUDE    (reason='no-signals')
"""

import argparse
import sys
import os

REVIEW_THRESHOLD = 2


def _load_set(path: str) -> set[str]:
    """Read non-comment, non-blank lines from *path*, return lowercase set.

    Returns an empty set if the file does not exist.
    """
    result: set[str] = set()
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Strip inline comments
                line = line.split('#')[0].strip()
                if line:
                    result.add(line.lower())
    except FileNotFoundError:
        pass
    return result


def _is_excluded(domain: str, exclusion_set: set[str]) -> bool:
    """Return True if *domain* or any parent suffix is in *exclusion_set*."""
    domain = domain.lower().rstrip('.')
    parts = domain.split('.')
    for i in range(len(parts) - 1):
        candidate = '.'.join(parts[i:])
        if candidate in exclusion_set:
            return True
    return False


def classify_domain(
    domain: str,
    exclusion_set: set[str],
    entity_set: set[str],
    probe_fn,
) -> dict:
    """Classify *domain* according to the routing-utility decision tree.

    Returns a dict with keys: 'domain', 'verdict', 'reason'.
    verdict is one of: 'SKIP', 'INCLUDE', 'REVIEW', 'EXCLUDE'.
    """
    d = domain.lower().strip()

    # 1. SKIP — any suffix in exclusion_set
    if _is_excluded(d, exclusion_set):
        return {'domain': domain, 'verdict': 'SKIP', 'reason': 'excluded'}

    # 2. INCLUDE — .sa TLD
    if d == 'sa' or d.endswith('.sa'):
        return {'domain': domain, 'verdict': 'INCLUDE', 'reason': 'sa-tld'}

    # 3. INCLUDE — entity registry
    if d in entity_set:
        return {'domain': domain, 'verdict': 'INCLUDE', 'reason': 'entity-registry'}

    # 4. Probe-based decisions
    if probe_fn is not None:
        result = probe_fn(domain)

        # 4a. geo-block
        if result.get('geo_blocked') is True:
            return {'domain': domain, 'verdict': 'INCLUDE', 'reason': 'geo-block'}

        # 4b. score threshold
        score = result.get('score', 0)
        if score >= REVIEW_THRESHOLD:
            return {'domain': domain, 'verdict': 'REVIEW', 'reason': f'score={score}'}

    # 5. EXCLUDE — no signals
    return {'domain': domain, 'verdict': 'EXCLUDE', 'reason': 'no-signals'}


def main():
    parser = argparse.ArgumentParser(
        description='Classify non-.sa domains for geosite:sa routing.'
    )
    parser.add_argument('--input', required=True, help='Input domain list file')
    parser.add_argument('--output-include', required=True,
                        help='Output file for auto-included domains')
    parser.add_argument('--output-review', required=True,
                        help='Output file for domains queued for review')
    parser.add_argument('--entities', default='data/sa-entities.txt',
                        help='Entity registry file (default: data/sa-entities.txt)')
    parser.add_argument('--no-probe', action='store_true',
                        help='Skip HTTP probing (probe_fn=None)')
    args = parser.parse_args()

    entity_set = _load_set(args.entities)

    # Build exclusion set (use defaults — no network calls by default)
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            'exclusion',
            os.path.join(os.path.dirname(__file__), 'exclusion.py')
        )
        _exc_mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_exc_mod)
        exclusion_set = _exc_mod.TIER_B_DOMAINS
    except Exception:
        exclusion_set = set()

    probe_fn = None
    if not args.no_probe:
        try:
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location(
                'probe_sa_signals',
                os.path.join(os.path.dirname(__file__), 'probe-sa-signals.py')
            )
            _probe_mod = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_probe_mod)
            probe_fn = _probe_mod.probe_domain
        except Exception:
            pass

    domains = _load_set(args.input)

    includes = []
    reviews = []

    for domain in sorted(domains):
        result = classify_domain(domain, exclusion_set, entity_set, probe_fn)
        if result['verdict'] == 'INCLUDE':
            includes.append(domain)
        elif result['verdict'] == 'REVIEW':
            reviews.append(domain)

    with open(args.output_include, 'w', encoding='utf-8') as fh:
        fh.write('# Auto-included domains — generated by classify-non-sa.py\n')
        for d in includes:
            fh.write(d + '\n')

    with open(args.output_review, 'w', encoding='utf-8') as fh:
        fh.write('# Domains pending manual review — auto-generated\n')
        for d in reviews:
            fh.write(d + '\n')

    print(f'Included: {len(includes)}, Review: {len(reviews)}', file=sys.stderr)


if __name__ == '__main__':
    main()
