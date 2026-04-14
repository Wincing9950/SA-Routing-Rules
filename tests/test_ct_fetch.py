import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    'fetch_ct_domains',
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'fetch-ct-domains.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

parse_ct_response = _mod.parse_ct_response
extract_domains_from_cert = _mod.extract_domains_from_cert
normalize_domain = _mod.normalize_domain


def test_extract_domains_from_cert_name_value():
    cert = {
        'name_value': 'www.example.com.sa\nexample.com.sa\n*.example.com.sa',
        'common_name': 'example.com.sa'
    }
    domains = extract_domains_from_cert(cert)
    assert 'example.com.sa' in domains
    assert 'www.example.com.sa' in domains

def test_wildcard_stripped():
    cert = {'name_value': '*.stc.com.sa', 'common_name': 'stc.com.sa'}
    domains = extract_domains_from_cert(cert)
    assert 'stc.com.sa' in domains
    assert '*.stc.com.sa' not in domains

def test_normalize_domain_lowercase():
    assert normalize_domain('STc.Com.SA') == 'stc.com.sa'

def test_normalize_domain_strips_trailing_dot():
    assert normalize_domain('example.sa.') == 'example.sa'

def test_normalize_domain_strips_wildcard():
    assert normalize_domain('*.example.sa') == 'example.sa'

def test_parse_ct_response_returns_set():
    mock_json = [
        {'name_value': 'a.example.sa\nb.example.sa', 'common_name': 'example.sa'},
        {'name_value': 'a.example.sa', 'common_name': 'example.sa'},  # duplicate
    ]
    result = parse_ct_response(mock_json)
    assert isinstance(result, set)
    assert 'example.sa' in result
    assert len(result) == len(set(result))

def test_parse_ct_response_handles_empty():
    assert parse_ct_response([]) == set()
    assert parse_ct_response(None) == set()

def test_extract_domains_ignores_invalid():
    cert = {'name_value': '', 'common_name': ''}
    domains = extract_domains_from_cert(cert)
    assert isinstance(domains, set)
