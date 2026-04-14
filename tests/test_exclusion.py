# tests/test_exclusion.py
from unittest.mock import patch, MagicMock
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import exclusion


FAKE_GOOGLE_DATA = """\
google.com
youtube.com
googleapis.com
# a comment line
"""

FAKE_FACEBOOK_DATA = """\
facebook.com
instagram.com
whatsapp.com
"""


def _make_response(text, status=200):
    r = MagicMock()
    r.status_code = status
    r.text = text
    r.raise_for_status = MagicMock()
    return r


def test_tier_a_parses_domains(monkeypatch):
    """Tier A must parse apex domains from v2fly category files."""
    responses = {
        'google': _make_response(FAKE_GOOGLE_DATA),
        'facebook': _make_response(FAKE_FACEBOOK_DATA),
    }
    def fake_get(url, **kwargs):
        for cat, resp in responses.items():
            if cat in url:
                return resp
        r = MagicMock()
        r.status_code = 404
        r.raise_for_status.side_effect = Exception("404")
        return r

    monkeypatch.setattr('exclusion.requests.get', fake_get)
    apex_set = exclusion.build_exclusion_set(tier_a_categories=['google', 'facebook'])
    assert 'google.com' in apex_set
    assert 'youtube.com' in apex_set
    assert 'facebook.com' in apex_set
    assert 'instagram.com' in apex_set


def test_tier_b_always_present():
    """Tier B hardcoded list must always be in the exclusion set."""
    with patch('exclusion.requests.get') as mock_get:
        mock_get.return_value = _make_response('')
        apex_set = exclusion.build_exclusion_set(tier_a_categories=[])
    for domain in ['tiktok.com', 'twitter.com', 'x.com', 'snapchat.com',
                   'telegram.org', 't.me', 'whatsapp.com']:
        assert domain in apex_set, f"{domain} missing from Tier B"


def test_is_excluded_apex():
    """is_excluded must match both exact apex and subdomains."""
    with patch('exclusion.requests.get') as mock_get:
        mock_get.return_value = _make_response('google.com\n')
        apex_set = exclusion.build_exclusion_set(tier_a_categories=['google'])
    assert exclusion.is_excluded('google.com', apex_set) is True
    assert exclusion.is_excluded('maps.google.com', apex_set) is True
    assert exclusion.is_excluded('noon.com', apex_set) is False


def test_fetch_failure_skips_category(monkeypatch):
    """A 404 on a category file must not crash the engine."""
    def fake_get(url, **kwargs):
        r = MagicMock()
        r.raise_for_status.side_effect = Exception("404")
        return r
    monkeypatch.setattr('exclusion.requests.get', fake_get)
    apex_set = exclusion.build_exclusion_set(tier_a_categories=['nonexistent'])
    # Should still have Tier B
    assert 'tiktok.com' in apex_set
