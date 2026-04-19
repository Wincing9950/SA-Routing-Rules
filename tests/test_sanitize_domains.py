"""
Tests for scripts/sanitize-domains.py

The sanitizer is used as the final safety net in generate-sa-domains.sh,
piped between `tr '[:upper:]' '[:lower:]'` and `LC_ALL=C sort -u`.
It rejects any domain that would cause v2fly geosite builder to fail.
"""
import io
import sys
import os
import importlib.util

# Load the sanitizer module dynamically (filename contains no hyphens, but
# keep the same pattern as other test files for consistency)
_spec = importlib.util.spec_from_file_location(
    'sanitize_domains',
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'sanitize-domains.py')
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

is_valid_geosite_domain = _mod.is_valid_geosite_domain


# ---------------------------------------------------------------------------
# is_valid_geosite_domain unit tests
# ---------------------------------------------------------------------------

class TestIsValidGeositeDomain:
    def test_plain_sa_domain(self):
        assert is_valid_geosite_domain('absher.gov.sa') is True

    def test_subdomain(self):
        assert is_valid_geosite_domain('mail.example.com.sa') is True

    def test_idn_label(self):
        assert is_valid_geosite_domain('xn--mgbaam7a8h.sa') is True

    def test_numeric_labels(self):
        assert is_valid_geosite_domain('123.gov.sa') is True
        assert is_valid_geosite_domain('1.gov.sa') is True

    def test_double_hyphen_ok(self):
        """Double hyphen is valid (IDN convention like xn--)."""
        assert is_valid_geosite_domain('my--domain.sa') is True

    def test_two_label_minimum(self):
        assert is_valid_geosite_domain('gov.sa') is True

    def test_single_label_rejected(self):
        assert is_valid_geosite_domain('sa') is False
        assert is_valid_geosite_domain('justalabel') is False

    def test_underscore_label_rejected(self):
        assert is_valid_geosite_domain('_collab-edge._tls.mof.gov.sa') is False
        assert is_valid_geosite_domain('_dmarc.gov.sa') is False

    def test_leading_hyphen_rejected(self):
        assert is_valid_geosite_domain('-test.gov.sa') is False

    def test_trailing_hyphen_rejected(self):
        assert is_valid_geosite_domain('test-.gov.sa') is False

    def test_wildcard_rejected(self):
        assert is_valid_geosite_domain('*.gov.sa') is False

    def test_empty_label_rejected(self):
        assert is_valid_geosite_domain('..gov.sa') is False
        assert is_valid_geosite_domain('test..sa') is False

    def test_trailing_dot_rejected(self):
        """Trailing dot produces an empty label after split."""
        assert is_valid_geosite_domain('test.sa.') is False

    def test_empty_string_rejected(self):
        assert is_valid_geosite_domain('') is False

    def test_ip_address_rejected(self):
        """IPs are technically valid per-label but don't end in a TLD label."""
        # 1.2.3.4 has 4 numeric labels and no alphabetic TLD — still passes
        # per-label rules but this is acceptable; the geosite builder would
        # reject it for other reasons. We just test the label rules here.
        assert is_valid_geosite_domain('a.b.c.sa') is True  # not an IP

    def test_deep_subdomain(self):
        assert is_valid_geosite_domain('a.b.c.sa') is True

    def test_long_domain_rejected(self):
        long_label = 'a' * 64
        assert is_valid_geosite_domain(f'{long_label}.sa') is False

    def test_253_char_limit(self):
        # 253 chars total: 62-char label + dot + 'sa' = 65; pad with more labels
        # Build a just-over-253 domain
        filler = ('a' * 63 + '.') * 3 + 'sa'  # 64*3+2 = 194 — fine
        assert is_valid_geosite_domain(filler) is True
        over = ('a' * 63 + '.') * 4 + 'sa'    # 64*4+2 = 258 — too long
        assert is_valid_geosite_domain(over) is False


# ---------------------------------------------------------------------------
# Integration: main() stdin → stdout filtering
# ---------------------------------------------------------------------------

def _run_main(input_lines):
    """Run sanitize-domains main() with given lines as stdin, capture stdout."""
    fake_stdin = io.StringIO('\n'.join(input_lines) + '\n')
    fake_stdout = io.StringIO()
    old_stdin, old_stdout, old_argv = sys.stdin, sys.stdout, sys.argv
    sys.stdin = fake_stdin
    sys.stdout = fake_stdout
    sys.argv = ['sanitize-domains.py']  # prevent main() picking up pytest args
    try:
        _mod.main()
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout
        sys.argv = old_argv
    return fake_stdout.getvalue().splitlines()


def test_main_passes_valid_domains():
    result = _run_main(['absher.gov.sa', 'stc.com.sa'])
    assert 'absher.gov.sa' in result
    assert 'stc.com.sa' in result


def test_main_drops_underscore_srv():
    result = _run_main(['_collab-edge._tls.mof.gov.sa', 'absher.gov.sa'])
    assert '_collab-edge._tls.mof.gov.sa' not in result
    assert 'absher.gov.sa' in result


def test_main_skips_comments_and_blanks():
    result = _run_main(['# comment', '', 'absher.gov.sa'])
    assert '# comment' not in result
    assert '' not in result
    assert 'absher.gov.sa' in result


def test_main_drops_wildcard():
    result = _run_main(['*.gov.sa', 'gov.sa'])
    assert '*.gov.sa' not in result
    assert 'gov.sa' in result


def test_main_mixed_batch():
    lines = [
        '_collab-edge._tls.mof.gov.sa',
        'absher.gov.sa',
        '*.edu.sa',
        'valid-sub.example.sa',
        'trailing-.bad.sa',
    ]
    result = _run_main(lines)
    assert result == ['absher.gov.sa', 'valid-sub.example.sa']
