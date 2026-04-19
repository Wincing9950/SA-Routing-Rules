"""probe-sa-signals.py

HTTP probe classifier for geo-block detection and Saudi Arabia content signals.
"""

import re
import sys
import requests

_SA_PATH_RE = re.compile(r'/(sa|ar-sa|en-sa)(/|$)', re.IGNORECASE)
_ARABIC_RE = re.compile(r'[\u0600-\u06ff]')
_SAR_RE = re.compile(r'SAR|ريال|SR ', re.IGNORECASE)
_SA_PHONE_RE = re.compile(r'\+966|0966')
_SA_VAT_RE = re.compile(r'\b3\d{14}\b')
_SA_LINK_RE = re.compile(r'href=["\'][^"\']*\.sa[/"\']', re.IGNORECASE)

_BODY_CAP = 50_000


def probe_domain(domain: str, timeout: int = 10) -> dict:
    result = {
        'domain': domain,
        'geo_blocked': False,
        'signals': {
            'arabic_content': False,
            'sar_currency': False,
            'sa_phone': False,
            'sa_vat': False,
            'sa_links': False,
        },
        'score': 0,
        'error': None,
    }

    try:
        resp = requests.get(f'https://{domain}', timeout=timeout, allow_redirects=True)
    except Exception as e:
        result['error'] = str(e)
        return result

    # Geo-block: 403 or SA path in final URL
    if resp.status_code == 403 or _SA_PATH_RE.search(resp.url):
        result['geo_blocked'] = True

    # Content signals: only when status == 200
    if resp.status_code == 200:
        body = resp.text[:_BODY_CAP]
        result['signals']['arabic_content'] = bool(_ARABIC_RE.search(body))
        result['signals']['sar_currency'] = bool(_SAR_RE.search(body))
        result['signals']['sa_phone'] = bool(_SA_PHONE_RE.search(body))
        result['signals']['sa_vat'] = bool(_SA_VAT_RE.search(body))
        result['signals']['sa_links'] = bool(_SA_LINK_RE.search(body))

    result['score'] = sum(1 for v in result['signals'].values() if v)
    return result


def main():
    domains = sys.argv[1:]
    if not domains:
        print("Usage: probe-sa-signals.py <domain> [domain ...]")
        sys.exit(1)

    for domain in domains:
        r = probe_domain(domain)
        geo = 'GEO-BLOCKED' if r['geo_blocked'] else 'not-geo-blocked'
        err = f" [error: {r['error']}]" if r['error'] else ''
        active = [k for k, v in r['signals'].items() if v]
        signals_str = ', '.join(active) if active else 'none'
        print(f"{domain}: {geo}, score={r['score']}, signals=[{signals_str}]{err}")


if __name__ == '__main__':
    main()
