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


# --- normalize_domain geosite-validity tests ---

def test_normalize_rejects_underscore_label():
    """SRV-type names like _collab-edge._tls.mof.gov.sa must be dropped."""
    assert normalize_domain('_collab-edge._tls.mof.gov.sa') == ''
    assert normalize_domain('_dmarc.gov.sa') == ''

def test_normalize_rejects_leading_hyphen():
    assert normalize_domain('-invalid.gov.sa') == ''

def test_normalize_rejects_trailing_hyphen():
    assert normalize_domain('trailing-.gov.sa') == ''

def test_normalize_rejects_single_label():
    assert normalize_domain('justalabel') == ''

def test_normalize_rejects_empty_label():
    assert normalize_domain('..gov.sa') == ''
    assert normalize_domain('test..sa') == ''

def test_normalize_accepts_valid_domains():
    assert normalize_domain('absher.gov.sa') == 'absher.gov.sa'
    assert normalize_domain('xn--mgbaam7a8h.sa') == 'xn--mgbaam7a8h.sa'
    assert normalize_domain('valid-domain.com.sa') == 'valid-domain.com.sa'
    assert normalize_domain('123.gov.sa') == '123.gov.sa'
    assert normalize_domain('my--domain.sa') == 'my--domain.sa'

def test_extract_domains_drops_underscore_srv_names():
    """CT certs with SRV names should not produce any domains."""
    cert = {
        'name_value': '_collab-edge._tls.mof.gov.sa\n_dmarc.gov.sa',
        'common_name': '_collab-edge._tls.mof.gov.sa'
    }
    domains = extract_domains_from_cert(cert)
    assert domains == set()

def test_extract_domains_mixed_valid_and_invalid():
    """Valid domains pass through; SRV names are silently dropped."""
    cert = {
        'name_value': '_collab-edge._tls.mof.gov.sa\nabsher.gov.sa',
        'common_name': 'mof.gov.sa'
    }
    domains = extract_domains_from_cert(cert)
    assert '_collab-edge._tls.mof.gov.sa' not in domains
    assert 'absher.gov.sa' in domains
    assert 'mof.gov.sa' in domains
