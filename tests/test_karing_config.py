import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))
from conftest import generate_karing_config_mod as mod

extract_keywords = mod.extract_keywords


def test_sld_from_com_sa_domain():
    """For 'shop.example.com.sa' the keyword should be 'example', not 'shop'."""
    kws = extract_keywords(['shop.example.com.sa'])
    assert 'example' in kws, f"Expected 'example', got: {kws}"
    assert 'shop' not in kws, "'shop' is a subdomain, not the SLD"

def test_sld_from_plain_sa_domain():
    """For 'example.sa' the keyword should be 'example'."""
    kws = extract_keywords(['example.sa'])
    assert 'example' in kws

def test_sld_from_gov_sa_domain():
    """For 'portal.ministry.gov.sa' the keyword should be 'ministry'."""
    kws = extract_keywords(['portal.ministry.gov.sa'])
    assert 'ministry' in kws, f"Expected 'ministry', got: {kws}"
    assert 'portal' not in kws

def test_sld_from_plain_com_domain():
    """For 'noon.com' the keyword should be 'noon'."""
    kws = extract_keywords(['noon.com'])
    assert 'noon' in kws

def test_keyword_cap_raised():
    """With 2100 unique domains, at least 2000 keywords should be returned."""
    domains = [f'd{i:04d}.com.sa' for i in range(2100)]
    kws = extract_keywords(domains)
    assert len(kws) >= 2000, f"Expected >= 2000, got {len(kws)}"

def test_generic_words_excluded():
    for word in ['mail', 'admin', 'shop', 'store', 'blog', 'api', 'app']:
        result = extract_keywords([f'{word}.example.com.sa'])
        assert word not in result, f"Generic word '{word}' should be excluded"
