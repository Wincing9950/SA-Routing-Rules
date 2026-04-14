import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    'dedup_curated',
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'dedup-curated.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
dedup_curated = _mod.dedup_curated


def _write(path, lines):
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')

def _read_domains(path):
    with open(path) as f:
        return [l.rstrip('\n') for l in f
                if l.strip() and not l.strip().startswith('#')]


def test_removes_cross_file_duplicates(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    _write(a, ['# comment', 'noon.com', 'stc.com.sa'])
    _write(b, ['# comment', 'noon.com', 'salla.com'])  # noon.com is duplicate
    dedup_curated([str(a), str(b)])
    domains_b = _read_domains(str(b))
    assert 'noon.com' not in domains_b
    assert 'salla.com' in domains_b

def test_preserves_comments(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    _write(a, ['# file a', 'noon.com'])
    _write(b, ['# file b', '', 'salla.com'])
    dedup_curated([str(a), str(b)])
    with open(b) as f:
        content = f.read()
    assert '# file b' in content

def test_within_file_dedup(tmp_path):
    a = tmp_path / "a.txt"
    _write(a, ['noon.com', 'salla.com', 'noon.com'])
    dedup_curated([str(a)])
    domains = _read_domains(str(a))
    assert domains.count('noon.com') == 1

def test_case_insensitive(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    _write(a, ['Noon.com'])
    _write(b, ['noon.com'])
    dedup_curated([str(a), str(b)])
    domains_b = _read_domains(str(b))
    assert 'noon.com' not in domains_b
