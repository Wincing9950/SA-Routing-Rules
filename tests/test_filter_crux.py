import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from filter_crux_sa_domains import (
    is_known_saudi, has_sa_keyword, is_sa_tld, is_global_exclude,
    get_registrable_domain, KNOWN_SAUDI_DOMAINS, SA_KEYWORDS
)

# ── KNOWN_SAUDI_DOMAINS coverage ──────────────────────────────────────────────

def test_known_saudi_fintech_coverage():
    for domain in ['stcpay.com.sa', 'foodics.com', 'tamara.co', 'tabby.ai',
                   'geidea.net', 'urpay.com', 'paytabs.com']:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_delivery_coverage():
    for domain in ['mrsool.co', 'jeeny.com', 'jahez.net', 'naqel.com.sa']:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_media_coverage():
    for domain in ['okaz.com.sa', 'jawwy.tv', 'sauress.com']:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_real_estate():
    for domain in ['aqar.fm', 'wasalt.com']:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_telecom():
    for domain in ['stc.com.sa', 'mobily.com.sa', 'zain.com.sa', 'salam.sa']:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_travel():
    for domain in ['flynas.com', 'flyadeal.com', 'saudia.com', 'almosafer.com']:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_not_false_positive_global():
    for domain in ['google.com', 'shopify.com', 'netflix.com', 'stripe.com']:
        assert not is_known_saudi(domain), f"{domain} should NOT be known Saudi"

# ── SA_KEYWORDS coverage ──────────────────────────────────────────────────────

def test_keyword_new_cities():
    assert has_sa_keyword('qatif-services.com')
    assert has_sa_keyword('alkharj-delivery.net')

def test_keyword_sa_services():
    assert has_sa_keyword('tasheel-platform.com')
    assert has_sa_keyword('madrasati-portal.edu.sa')

def test_keyword_sa_brands():
    assert has_sa_keyword('bindawood-online.com')
    assert has_sa_keyword('aldawaa-pharmacy.com')
    assert has_sa_keyword('alnahdi-health.sa')

def test_keyword_no_false_positive():
    assert not has_sa_keyword('nebraska.gov')

# ── Minimum count thresholds ──────────────────────────────────────────────────

def test_known_saudi_minimum_count():
    assert len(KNOWN_SAUDI_DOMAINS) >= 200, f"Only {len(KNOWN_SAUDI_DOMAINS)} — need 200+"

def test_sa_keywords_minimum_count():
    assert len(SA_KEYWORDS) >= 70, f"Only {len(SA_KEYWORDS)} — need 70+"
