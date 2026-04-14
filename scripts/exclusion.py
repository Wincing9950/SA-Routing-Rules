"""
Two-tier exclusion engine for the geosite:sa classification pipeline.

Tier A: Fetched apex domains from v2fly geosite categories at runtime.
Tier B: Hardcoded set of domains that must always be excluded.
"""

import re
import requests

TIER_A_CATEGORIES = [
    'google',
    'amazon',
    'apple',
    'microsoft',
    'netflix',
    'facebook',
    'instagram',
    'category-ads-all',
]

TIER_B_DOMAINS = {
    # TikTok / ByteDance
    'tiktok.com', 'bytedance.com', 'tiktokv.com', 'musically.com',
    # Twitter / X
    'twitter.com', 'x.com', 't.co', 'twimg.com',
    # Snapchat
    'snapchat.com', 'snap.com',
    # Telegram
    'telegram.org', 't.me', 'telegram.me', 'telegra.ph',
    # WhatsApp
    'whatsapp.com', 'whatsapp.net',
    # YouTube (belt-and-suspenders)
    'youtube.com',
}

_V2FLY_BASE_URL = (
    'https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/{category}'
)

# Directives to strip from line prefixes
_DIRECTIVE_RE = re.compile(
    r'^(?:include:|domain:|full:|regexp:)',
    re.IGNORECASE,
)

# Attribute annotations to strip (e.g. @cn, @ads)
_ATTR_RE = re.compile(r'\s*@\S+')


def _parse_category_text(text: str) -> set[str]:
    """Parse a v2fly category file text and return apex domain strings."""
    domains: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        # Skip blank lines and comments
        if not line or line.startswith('#'):
            continue
        # Strip directive prefixes
        line = _DIRECTIVE_RE.sub('', line)
        # Strip attribute annotations
        line = _ATTR_RE.sub('', line).strip()
        if line:
            domains.add(line.lower())
    return domains


def _fetch_category(category: str) -> set[str]:
    """Fetch a single v2fly category and return parsed apex domains.

    Returns an empty set on any network or HTTP error.
    """
    url = _V2FLY_BASE_URL.format(category=category)
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return _parse_category_text(response.text)
    except Exception:
        return set()


def build_exclusion_set(tier_a_categories: list[str] | None = None) -> set[str]:
    """Build and return the combined exclusion apex set.

    Parameters
    ----------
    tier_a_categories:
        List of v2fly category names to fetch. If ``None``, defaults to
        ``TIER_A_CATEGORIES``.

    Returns
    -------
    set[str]
        Combined set of apex domain strings from Tier A (fetched) and Tier B
        (hardcoded).
    """
    if tier_a_categories is None:
        tier_a_categories = TIER_A_CATEGORIES

    apex_set: set[str] = set()
    for category in tier_a_categories:
        apex_set |= _fetch_category(category)

    # Always include Tier B
    apex_set |= TIER_B_DOMAINS
    return apex_set


def is_excluded(domain: str, apex_set: set[str]) -> bool:
    """Return True if *domain* or any parent apex suffix is in *apex_set*.

    Examples
    --------
    >>> is_excluded('maps.google.com', {'google.com'})
    True
    >>> is_excluded('noon.com', {'google.com'})
    False
    """
    domain = domain.lower().rstrip('.')
    parts = domain.split('.')
    # Check the full domain and every parent suffix
    for i in range(len(parts) - 1):
        candidate = '.'.join(parts[i:])
        if candidate in apex_set:
            return True
    return False
