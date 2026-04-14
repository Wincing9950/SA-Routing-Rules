import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    'fetch_majestic_sa',
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'fetch-majestic-sa.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

classify_majestic_row = _mod.classify_majestic_row

HEADER = ['GlobalRank', 'TldRank', 'Domain', 'TLD', 'RefSubNets',
          'RefIPs', 'IDN_Domain', 'IDN_TLD', 'PrevGlobalRank',
          'PrevTldRank', 'PrevRefSubNets', 'PrevRefIPs']


def _row(rank, domain, tld):
    return dict(zip(HEADER, [str(rank), '1', domain, tld, '10', '8', '', '', '', '', '', '']))


def test_sa_tld_always_included():
    assert classify_majestic_row(_row(500000, 'alrajhi', 'sa')) == 'tld'

def test_com_sa_included():
    assert classify_majestic_row(_row(1, 'stc', 'com.sa')) is not None

def test_keyword_match():
    assert classify_majestic_row(_row(10000, 'saudia-airlines', 'com')) == 'keyword'

def test_unknown_not_included():
    assert classify_majestic_row(_row(100000, 'randomdomain', 'com')) is None

def test_known_sa_domain():
    assert classify_majestic_row(_row(5000, 'noon', 'com')) == 'known'

def test_global_service_excluded():
    assert classify_majestic_row(_row(1, 'google', 'com')) is None

def test_top_50k_unknown_dns_check():
    assert classify_majestic_row(_row(25000, 'unknowndomain123', 'com')) == 'dns_check'

def test_low_rank_unknown_excluded():
    assert classify_majestic_row(_row(500000, 'unknowndomain123', 'com')) is None
