# tests/test_cloudflare_radar.py
import sys, os

# Handle hyphenated module name
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "fetch_cloudflare_radar",
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'fetch-cloudflare-radar.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
fetch_cloudflare_radar = _mod

from unittest.mock import patch, MagicMock

FAKE_RADAR_RESPONSE = {
    "result": {
        "top": [
            {"domain": "google.com", "rank": 1},
            {"domain": "stc.com", "rank": 2},
            {"domain": "youtube.com", "rank": 3},
            {"domain": "sabq.org", "rank": 4},
            {"domain": "noon.com", "rank": 5},
            {"domain": "twitter.com", "rank": 6},
            {"domain": "tiktok.com", "rank": 7},
        ]
    },
    "success": True
}


def _mock_response(data):
    r = MagicMock()
    r.json.return_value = data
    r.raise_for_status = MagicMock()
    return r


def test_fetch_filters_exclusions():
    excluded = {'google.com', 'youtube.com', 'twitter.com', 'x.com', 't.co', 'twimg.com',
                'tiktok.com', 'bytedance.com'}
    with patch('requests.get') as mock_get:
        mock_get.return_value = _mock_response(FAKE_RADAR_RESPONSE)
        result = fetch_cloudflare_radar.fetch_top_sa_domains(api_token='fake', exclusion_set=excluded)
    assert 'google.com' not in result
    assert 'youtube.com' not in result
    assert 'tiktok.com' not in result
    assert 'twitter.com' not in result


def test_fetch_keeps_sa_relevant_domains():
    excluded = {'google.com', 'youtube.com', 'twitter.com', 'tiktok.com'}
    with patch('requests.get') as mock_get:
        mock_get.return_value = _mock_response(FAKE_RADAR_RESPONSE)
        result = fetch_cloudflare_radar.fetch_top_sa_domains(api_token='fake', exclusion_set=excluded)
    assert 'stc.com' in result
    assert 'sabq.org' in result
    assert 'noon.com' in result


def test_missing_api_token_returns_empty():
    with patch('requests.get') as mock_get:
        result = fetch_cloudflare_radar.fetch_top_sa_domains(api_token='', exclusion_set=set())
    mock_get.assert_not_called()
    assert result == []


def test_api_error_returns_empty():
    with patch('requests.get') as mock_get:
        mock_get.return_value = _mock_response({})
        mock_get.return_value.raise_for_status.side_effect = Exception("403")
        result = fetch_cloudflare_radar.fetch_top_sa_domains(api_token='bad', exclusion_set=set())
    assert result == []
