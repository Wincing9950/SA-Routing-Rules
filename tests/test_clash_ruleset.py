# tests/test_clash_ruleset.py
import sys, os

# Handle hyphenated module name
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "generate_clash_ruleset",
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'generate-clash-ruleset.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
gen = _mod


def _write_domains(path, lines):
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def test_sa_tld_becomes_domain_suffix():
    """.sa-only entry must use DOMAIN-SUFFIX in YAML output."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, 'sa.txt')
        out = os.path.join(d, 'sa.yaml')
        _write_domains(inp, ['sa', 'gov.sa', 'alrajhibank.com.sa'])
        gen.generate_yaml(inp, out)
        content = open(out).read()
    assert 'DOMAIN-SUFFIX,.sa' in content or 'DOMAIN-SUFFIX,sa' in content
    assert 'DOMAIN-SUFFIX,.gov.sa' in content or 'DOMAIN-SUFFIX,gov.sa' in content
    assert 'DOMAIN-SUFFIX,.alrajhibank.com.sa' in content or 'DOMAIN-SUFFIX,alrajhibank.com.sa' in content


def test_non_sa_apex_becomes_domain():
    """Non-.sa apex domains must use DOMAIN-SUFFIX in YAML output."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, 'sa.txt')
        out = os.path.join(d, 'sa.yaml')
        _write_domains(inp, ['noon.com', 'aramco.com'])
        gen.generate_yaml(inp, out)
        content = open(out).read()
    assert 'DOMAIN,noon.com' in content or 'DOMAIN-SUFFIX,noon.com' in content
    assert 'DOMAIN,aramco.com' in content or 'DOMAIN-SUFFIX,aramco.com' in content


def test_comments_and_blanks_skipped():
    """Comment lines and blank lines must not appear in YAML output."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, 'sa.txt')
        out = os.path.join(d, 'sa.yaml')
        _write_domains(inp, ['# comment', '', 'noon.com', '# another'])
        gen.generate_yaml(inp, out)
        content = open(out).read()
    assert '# comment' not in content
    assert content.count('noon.com') == 1


def test_yaml_has_payload_key():
    """Output must have 'payload:' as root key (Clash rule-provider format)."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, 'sa.txt')
        out = os.path.join(d, 'sa.yaml')
        _write_domains(inp, ['noon.com'])
        gen.generate_yaml(inp, out)
        content = open(out).read()
    assert content.startswith('payload:') or 'payload:\n' in content
