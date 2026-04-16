# tests/test_classify.py
import sys, os, importlib.util

_spec = importlib.util.spec_from_file_location(
    "classify_non_sa",
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'classify-non-sa.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
clf = _mod

MOCK_EXCLUSION = {'google.com', 'youtube.com', 'tiktok.com', 'twitter.com',
                  'x.com', 't.co', 'twimg.com', 'snapchat.com',
                  'telegram.org', 't.me', 'whatsapp.com', 'facebook.com',
                  'amazon.com', 'apple.com', 'microsoft.com'}

MOCK_ENTITIES = {'aramco.com', 'sabic.com', 'stc.com', 'noon.com'}


def test_excluded_domain_is_skipped():
    result = clf.classify_domain('google.com', MOCK_EXCLUSION, MOCK_ENTITIES, probe_fn=None)
    assert result['verdict'] == 'SKIP'


def test_entity_registry_is_auto_included():
    result = clf.classify_domain('aramco.com', MOCK_EXCLUSION, MOCK_ENTITIES, probe_fn=None)
    assert result['verdict'] == 'INCLUDE'
    assert result['reason'] == 'entity-registry'


def test_geo_blocked_domain_is_included():
    def fake_probe(domain):
        return {'geo_blocked': True, 'score': 0, 'signals': {}, 'error': None}
    result = clf.classify_domain('somelocal.com', MOCK_EXCLUSION, MOCK_ENTITIES, probe_fn=fake_probe)
    assert result['verdict'] == 'INCLUDE'
    assert result['reason'] == 'geo-block'


def test_strong_sa_signals_queued_for_review():
    def fake_probe(domain):
        return {'geo_blocked': False, 'score': 3,
                'signals': {'arabic_content': True, 'sar_currency': True, 'sa_phone': True},
                'error': None}
    result = clf.classify_domain('somesite.com', MOCK_EXCLUSION, MOCK_ENTITIES, probe_fn=fake_probe)
    assert result['verdict'] == 'REVIEW'


def test_weak_signals_excluded():
    def fake_probe(domain):
        return {'geo_blocked': False, 'score': 1, 'signals': {}, 'error': None}
    result = clf.classify_domain('somesite.com', MOCK_EXCLUSION, MOCK_ENTITIES, probe_fn=fake_probe)
    assert result['verdict'] == 'EXCLUDE'


def test_score_of_two_is_now_excluded():
    """Score of 2 was REVIEW at threshold=2; must be EXCLUDE at threshold=3."""
    def fake_probe(domain):
        return {'geo_blocked': False, 'score': 2,
                'signals': {'arabic_content': True, 'sar_currency': True},
                'error': None}
    result = clf.classify_domain('arabnews.com', MOCK_EXCLUSION, MOCK_ENTITIES, probe_fn=fake_probe)
    assert result['verdict'] == 'EXCLUDE'


def test_sa_tld_domain_is_always_included():
    result = clf.classify_domain('example.sa', MOCK_EXCLUSION, MOCK_ENTITIES, probe_fn=None)
    assert result['verdict'] == 'INCLUDE'
    assert result['reason'] == 'sa-tld'
