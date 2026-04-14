# tests/test_probe.py
import sys, os, importlib.util

_spec = importlib.util.spec_from_file_location(
    "probe_sa_signals",
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'probe-sa-signals.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
probe_sa_signals = _mod

from unittest.mock import patch, MagicMock


def _mock_resp(status=200, text='', url='https://example.com/', headers=None):
    r = MagicMock()
    r.status_code = status
    r.text = text
    r.url = url
    r.headers = headers or {'Content-Type': 'text/html'}
    return r


def test_detects_geo_block_403():
    with patch('requests.get') as mock_get:
        mock_get.return_value = _mock_resp(status=403)
        result = probe_sa_signals.probe_domain('example.com')
    assert result['geo_blocked'] is True


def test_detects_geo_block_sa_redirect():
    with patch('requests.get') as mock_get:
        mock_get.return_value = _mock_resp(status=200, url='https://example.com/sa/home')
        result = probe_sa_signals.probe_domain('example.com')
    assert result['geo_blocked'] is True


def test_detects_arabic_content():
    arabic_body = '<html><body>مرحباً بكم في موقعنا السعودي</body></html>'
    with patch('requests.get') as mock_get:
        mock_get.return_value = _mock_resp(text=arabic_body)
        result = probe_sa_signals.probe_domain('example.com')
    assert result['signals']['arabic_content'] is True


def test_detects_sar_currency():
    sar_body = '<html><body>Price: 299 SAR</body></html>'
    with patch('requests.get') as mock_get:
        mock_get.return_value = _mock_resp(text=sar_body)
        result = probe_sa_signals.probe_domain('example.com')
    assert result['signals']['sar_currency'] is True


def test_score_calculation():
    body = 'SAR price ريال +966501234567'
    with patch('requests.get') as mock_get:
        mock_get.return_value = _mock_resp(text=body)
        result = probe_sa_signals.probe_domain('example.com')
    assert result['score'] == sum(1 for v in result['signals'].values() if v)


def test_timeout_returns_empty_result():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection timed out")
        result = probe_sa_signals.probe_domain('example.com')
    assert result['score'] == 0
    assert result['geo_blocked'] is False
    assert result['error'] is not None
