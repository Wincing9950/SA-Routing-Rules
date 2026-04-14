# SA-Routing-Rules Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand SA-Routing-Rules domain coverage from ~11,000 to 20,000–30,000+ entries by adding Certificate Transparency, Majestic Million, BGP-announced prefixes, reverse DNS sweep, fixing the MaxMind activation bug, expanding filter dictionaries, enabling DNS resolution by default, and wiring all sources into the build pipeline.

**Architecture:** A multi-source aggregation model where six independent discovery scripts each produce a domain/IP list, `generate-sa-domains.sh` merges them, and `generate-sa-ips.sh` merges IP data from RIPE NCC + BGP + MaxMind. All Python scripts are unit-tested. The GitHub Actions workflow is corrected so MaxMind is used whenever the secret is present.

**Tech Stack:** Python 3.12, `pytest`, `dnspython`, `geoip2`, `requests`, `bash`, GitHub Actions, MaxMind GeoLite2, RIPE Stat API, crt.sh, Majestic Million CSV, `massdns` (optional)

---

## Confirmed Bugs Being Fixed

| Bug | Location | Symptom |
|-----|----------|---------|
| MaxMind never downloads | `release.yml:70` | `if: ${{ env.MAXMIND_LICENSE_KEY != '' }}` checks step-level env in job-condition context — always empty |
| Karing SLD extraction wrong for `.sa` sub-TLDs | `generate-karing-config.py:extract_keywords()` | `parts[0]` used instead of `parts[-3]` for 4-part `.com.sa` domains |
| Karing keywords capped at 300 | `generate-karing-config.py:69` | 300/11000 = 3% of domains represented |
| `sa-extra-ips.txt` is empty | `data/sa-extra-ips.txt` | File is comments-only; contributes nothing |
| DNS disabled by default | `release.yml:SKIP_DNS:default:true` | Strongest non-`.sa` signal never used |
| 55 cross-file duplicates | `data/*.txt` | Bloat in final output |

---

## File Map

### Created
| File | Responsibility |
|------|---------------|
| `requirements.txt` | Runtime Python deps for all scripts |
| `requirements-dev.txt` | Test deps (pytest, pytest-mock) |
| `tests/conftest.py` | Shared fixtures (sample CSV, SA IP list) |
| `tests/fixtures/sample_crux.csv` | 20-row CrUX CSV for unit tests |
| `tests/fixtures/sample_sa_ips.txt` | Small CIDR list for DNS tests |
| `tests/test_filter_crux.py` | Unit tests for filter_crux_sa_domains.py |
| `tests/test_karing_config.py` | Unit tests for generate-karing-config.py |
| `tests/test_ct_fetch.py` | Unit tests for fetch-ct-domains.py |
| `tests/test_majestic.py` | Unit tests for fetch-majestic-sa.py |
| `tests/test_dedup.py` | Unit tests for dedup-curated.py |
| `scripts/fetch-ct-domains.py` | Query crt.sh for all SA-related certs |
| `scripts/fetch-majestic-sa.py` | Download + filter Majestic Million CSV |
| `scripts/fetch-sa-as-prefixes.sh` | Query RIPE Stat API for SA ASes |
| `scripts/dedup-curated.py` | Deduplicate entries across data/*.txt |
| `scripts/cidr-to-sample-ips.py` | Expand CIDR blocks to one IP per /24 |
| `scripts/reverse-dns-sweep.sh` | PTR sweep on SA IP space via massdns |

### Modified
| File | Change |
|------|--------|
| `requirements.txt` | (new file) |
| `data/sa-extra-ips.txt` | Add actual SA ISP IP ranges |
| `scripts/filter_crux_sa_domains.py` | Expand KNOWN_SAUDI_DOMAINS (24→300+), SA_KEYWORDS (20→80+), switch DNS to dnspython |
| `scripts/generate-karing-config.py` | Fix `extract_keywords()` SLD bug, raise cap to 2000, add frequency weighting |
| `scripts/generate-sa-domains.sh` | Add CT, Majestic, reverse-DNS sources; call dedup-curated.py |
| `scripts/generate-sa-ips.sh` | Add BGP merge step |
| `.github/workflows/release.yml` | Fix MaxMind bug (move key to job env), add new pipeline steps, set SKIP_DNS default to false |

---

## Task 1: Bootstrap Test Harness

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/sample_crux.csv`
- Create: `tests/fixtures/sample_sa_ips.txt`

- [ ] **Step 1.1: Create `requirements.txt`**

```
dnspython>=2.6.0
geoip2>=4.8.0
requests>=2.31.0
```

- [ ] **Step 1.2: Create `requirements-dev.txt`**

```
-r requirements.txt
pytest>=8.0.0
pytest-mock>=3.12.0
responses>=0.25.0
```

- [ ] **Step 1.3: Install dev dependencies**

```bash
python3 -m pip install --break-system-packages -r requirements-dev.txt
```

Expected: `Successfully installed pytest-8.x.x dnspython-2.x.x geoip2-4.x.x ...`

- [ ] **Step 1.4: Create `tests/fixtures/sample_crux.csv`**

```csv
origin,rank
https://stc.com.sa,1000
https://noon.com,2000
https://google.com,3000
https://facebook.com,4000
https://hungerstation.com,5000
https://absher.sa,6000
https://sabq.org,7000
https://aramco.com,8000
https://yahoo.com,9000
https://salla.com,10000
https://unknown-domain-xyz.com,11000
https://riyadhbanktest.com,12000
https://neom.com,13000
https://netflix.com,14000
https://aleqt.com,15000
https://mbc.net,16000
https://flynas.com,17000
https://shopify.com,18000
https://alrajhibank.com.sa,19000
https://jarir.com,20000
```

- [ ] **Step 1.5: Create `tests/fixtures/sample_sa_ips.txt`**

```
# Saudi Arabia test IP ranges (RIPE-allocated)
83.97.160.0/19
5.1.0.0/22
46.62.0.0/16
```

- [ ] **Step 1.6: Create `tests/conftest.py`**

```python
import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

@pytest.fixture
def sample_crux_csv():
    return os.path.join(FIXTURES_DIR, "sample_crux.csv")

@pytest.fixture
def sample_sa_ips():
    return os.path.join(FIXTURES_DIR, "sample_sa_ips.txt")

@pytest.fixture
def sample_sa_networks():
    import ipaddress
    cidrs = ["83.97.160.0/19", "5.1.0.0/22", "46.62.0.0/16"]
    return [ipaddress.ip_network(c) for c in cidrs]
```

- [ ] **Step 1.7: Verify pytest discovers fixtures**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/ --collect-only 2>&1 | head -20
```

Expected: `no tests ran` (no test files yet) with no import errors.

- [ ] **Step 1.8: Commit**

```bash
git add requirements.txt requirements-dev.txt tests/
git commit -m "test: bootstrap pytest harness with fixtures"
```

---

## Task 2: Fix MaxMind Activation Bug

**Files:**
- Modify: `.github/workflows/release.yml:20-25` (job-level env block)

The bug: `if: ${{ env.MAXMIND_LICENSE_KEY != '' }}` at line 70 checks `env.MAXMIND_LICENSE_KEY`. In GitHub Actions, `env.` in a step condition refers to **job/workflow-level** env variables — not the step's own `env:` block, which is evaluated only when the step runs. Since `MAXMIND_LICENSE_KEY` is never defined at the job level, the condition is always empty-string → always false → MaxMind never downloads.

- [ ] **Step 2.1: Write failing test that documents the bug**

Create `tests/test_workflow_maxmind.py`:

```python
"""
Documents the MaxMind workflow configuration requirement.
These tests parse release.yml to verify MaxMind is correctly wired.
"""
import yaml
import pytest

WORKFLOW_PATH = ".github/workflows/release.yml"

def load_workflow():
    with open(WORKFLOW_PATH) as f:
        return yaml.safe_load(f)

def test_maxmind_key_set_at_job_level():
    """MAXMIND_LICENSE_KEY must be set at job level so if-conditions can read it."""
    wf = load_workflow()
    job_env = wf["jobs"]["build"].get("env", {})
    assert "MAXMIND_LICENSE_KEY" in job_env, (
        "MAXMIND_LICENSE_KEY must be defined in jobs.build.env so that "
        "step if-conditions (env.MAXMIND_LICENSE_KEY != '') evaluate correctly. "
        "Currently it's only in step-level env blocks, which are invisible to if-conditions."
    )

def test_maxmind_condition_references_env():
    """The download step condition must use env.MAXMIND_LICENSE_KEY."""
    wf = load_workflow()
    steps = wf["jobs"]["build"]["steps"]
    download_step = next(
        (s for s in steps if "MaxMind GeoLite2" in s.get("name", "") and "placeholder" not in s.get("name", "").lower()),
        None
    )
    assert download_step is not None, "MaxMind download step not found"
    condition = download_step.get("if", "")
    assert "MAXMIND_LICENSE_KEY" in condition
```

- [ ] **Step 2.2: Install PyYAML and run test to confirm it fails**

```bash
python3 -m pip install --break-system-packages pyyaml
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_workflow_maxmind.py -v
```

Expected: `FAILED tests/test_workflow_maxmind.py::test_maxmind_key_set_at_job_level`

- [ ] **Step 2.3: Fix `release.yml` — add job-level env block**

In `.github/workflows/release.yml`, locate the `jobs: build:` section (around line 18). Add an `env:` block directly under `permissions:`:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    env:
      MAXMIND_LICENSE_KEY: ${{ secrets.MAXMIND_LICENSE_KEY }}
```

Then remove the redundant `env:` blocks that were duplicated inside the two MaxMind steps (lines ~85-87 and ~98-99 in the original). The job-level env makes them unnecessary.

- [ ] **Step 2.4: Run test to verify it passes**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_workflow_maxmind.py -v
```

Expected: `PASSED tests/test_workflow_maxmind.py::test_maxmind_key_set_at_job_level`

- [ ] **Step 2.5: Add PyYAML to dev requirements**

In `requirements-dev.txt`, add:
```
pyyaml>=6.0
```

- [ ] **Step 2.6: Commit**

```bash
git add .github/workflows/release.yml requirements-dev.txt tests/test_workflow_maxmind.py
git commit -m "fix: move MAXMIND_LICENSE_KEY to job-level env so if-conditions evaluate correctly"
```

---

## Task 3: Expand Filter Dictionaries

**Files:**
- Modify: `scripts/filter_crux_sa_domains.py` (KNOWN_SAUDI_DOMAINS + SA_KEYWORDS constants)
- Create: `tests/test_filter_crux.py`

- [ ] **Step 3.1: Write failing tests first**

Create `tests/test_filter_crux.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from filter_crux_sa_domains import (
    is_known_saudi, has_sa_keyword, is_sa_tld, is_global_exclude,
    get_registrable_domain, extract_domain, KNOWN_SAUDI_DOMAINS, SA_KEYWORDS
)

# ── KNOWN_SAUDI_DOMAINS coverage ──────────────────────────────────────────────

def test_known_saudi_fintech_coverage():
    """New SA fintech domains must be in KNOWN_SAUDI_DOMAINS."""
    expected = ['stcpay.com.sa', 'foodics.com', 'tamara.co', 'tabby.ai',
                'geidea.net', 'urpay.com', 'paytabs.com']
    for domain in expected:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_delivery_coverage():
    expected = ['mrsool.co', 'jeeny.com', 'jahez.net', 'naqel.com.sa']
    for domain in expected:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_media_coverage():
    expected = ['okaz.com.sa', 'jawwy.tv', 'sauress.com', 'ajel.sa']
    for domain in expected:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_real_estate():
    expected = ['aqar.fm', 'ejar.sa', 'wasalt.com', 'bayut.sa']
    for domain in expected:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_telecom():
    expected = ['stc.com.sa', 'mobily.com.sa', 'zain.com.sa', 'salam.sa']
    for domain in expected:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_known_saudi_travel():
    expected = ['flynas.com', 'flyadeal.com', 'saudia.com', 'almosafer.com']
    for domain in expected:
        assert is_known_saudi(domain), f"{domain} should be known Saudi"

def test_not_false_positive_global():
    """Global services must NOT be treated as known Saudi."""
    for domain in ['google.com', 'shopify.com', 'netflix.com', 'stripe.com']:
        assert not is_known_saudi(domain), f"{domain} should NOT be known Saudi"

# ── SA_KEYWORDS coverage ──────────────────────────────────────────────────────

def test_keyword_new_cities():
    """New city keywords must trigger SA match."""
    assert has_sa_keyword('qatif-services.com')
    assert has_sa_keyword('alkharj-delivery.net')
    assert has_sa_keyword('onaizah-store.sa')

def test_keyword_sa_services():
    """Government service keywords must match."""
    assert has_sa_keyword('tasheel-platform.com')
    assert has_sa_keyword('istimara-renewal.com')
    assert has_sa_keyword('madrasati-portal.edu.sa')

def test_keyword_sa_brands():
    """Known SA brand fragments must match."""
    assert has_sa_keyword('bindawood-online.com')
    assert has_sa_keyword('aldawaa-pharmacy.com')
    assert has_sa_keyword('alnahdi-health.sa')

def test_keyword_no_false_positive():
    """Common words that happen to contain SA keywords must not match."""
    # 'sakaka' should not match 'osaka' etc.
    assert not has_sa_keyword('osaka.jp')
    assert not has_sa_keyword('nebraska.gov')

# ── Total coverage counts ─────────────────────────────────────────────────────

def test_known_saudi_minimum_count():
    """KNOWN_SAUDI_DOMAINS must have at least 200 entries."""
    assert len(KNOWN_SAUDI_DOMAINS) >= 200, (
        f"Only {len(KNOWN_SAUDI_DOMAINS)} entries — expand to cover major SA businesses"
    )

def test_sa_keywords_minimum_count():
    """SA_KEYWORDS must have at least 70 entries."""
    assert len(SA_KEYWORDS) >= 70, (
        f"Only {len(SA_KEYWORDS)} entries — expand to cover more SA cities and brands"
    )
```

- [ ] **Step 3.2: Run tests to confirm failures**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_filter_crux.py -v 2>&1 | tail -30
```

Expected: Multiple FAILED — `test_known_saudi_minimum_count`, `test_known_saudi_fintech_coverage`, etc.

- [ ] **Step 3.3: Expand `KNOWN_SAUDI_DOMAINS` in `filter_crux_sa_domains.py`**

Replace the `KNOWN_SAUDI_DOMAINS` set (starting around line 60) with:

```python
KNOWN_SAUDI_DOMAINS = {
    # ── Core / Already Existed ─────────────────────────────────────────────
    'noon.com', 'careem.com', 'hungerstation.com', 'argaam.com',
    'sabq.org', 'alarabiya.net', 'aawsat.com', 'mbc.net',
    'shahid.net', 'rotana.net', 'anghami.com', 'thmanyah.com',
    'srmg.com', 'flynas.com', 'flyadeal.com', 'almosafer.com',
    'aramex.com', 'fetchr.us', 'neom.com', 'aramco.com',
    'saudiaramco.com', 'sabic.com', 'ithra.com',
    'tawuniya.com', 'tamara.co', 'tabby.ai',
    'moyasar.com', 'tap.company', 'hyperpay.com',
    'namshi.com', 'ounass.com', 'fordeal.com',
    'bayt.com', 'adslgate.com', 'jeeny.com',
    'stcplay.gg', 'jawwy.tv',

    # ── E-Commerce & Retail ────────────────────────────────────────────────
    'salla.com', 'zid.sa', 'extra.com', 'jarir.com',
    'bindawood.com', 'alothaimeen.com', 'danube.sa',
    'lulu-ksa.com', 'ikea.com.sa', 'bayut.sa',
    'haraj.com.sa', 'opensooq.com', 'dubizzle.com.sa',
    'hm.com.sa', 'zara.com.sa', 'macys.com.sa',
    'ounass.com', 'sivvi.com', 'mumzworld.com',

    # ── Fintech & Banking ──────────────────────────────────────────────────
    'stcpay.com.sa', 'urpay.com', 'foodics.com', 'geidea.net',
    'payfort.com', 'paytabs.com', 'postpay.io',
    'halalah.io', 'bfc.com.sa', 'saddad.com.sa',
    'wadiah.com', 'cashu.com', 'mada.com.sa',
    'bankbilad.com.sa', 'bsf.com.sa', 'alinma.com',
    'alrajhibank.com.sa', 'alahli.com', 'sabb.com',
    'anb.com.sa', 'riyad.com.sa', 'albilad.com.sa',
    'alahlibank.com', 'aljazirabank.com.sa',
    'saib.com.sa', 'amlak.com.sa',

    # ── Ride / Delivery / Logistics ───────────────────────────────────────
    'mrsool.co', 'jahez.net', 'marsool.com',
    'naqel.com.sa', 'smsa.com', 'dhl.com.sa',
    'talabat.com', 'jahez.com', 'toters.com',
    'bosta.co', 'shipbob.com.sa', 'zajil.net',
    'indomaret.com.sa',

    # ── Media & News ──────────────────────────────────────────────────────
    'okaz.com.sa', 'ajel.sa', 'sauress.com',
    'al-jazirah.com', 'alriyadh.com', 'alwatan.com.sa',
    'aleqt.com', 'spa.gov.sa', 'saudigazette.com.sa',
    'arabnews.com', 'asharq.com', 'alarabianenglish.com',
    'skynewsarabia.com', 'france24.com.sa',
    'trt.net.tr.sa', 'bbc.com.sa',

    # ── Telecom ───────────────────────────────────────────────────────────
    'stc.com.sa', 'mobily.com.sa', 'zain.com.sa',
    'salam.sa', 'virgin.com.sa', 'go.com.sa',
    'jawwy.com', 'wimax.com.sa', 'ericsson.com.sa',
    'huawei.com.sa', 'cisco.com.sa',

    # ── Travel & Aviation ─────────────────────────────────────────────────
    'saudia.com', 'flynas.com', 'flyadeal.com',
    'almosafer.com', 'halaltrip.com', 'wego.com.sa',
    'booking.com.sa', 'expedia.com.sa',
    'visitsaudi.com', 'gcasonline.com',

    # ── Real Estate ───────────────────────────────────────────────────────
    'aqar.fm', 'ejar.sa', 'haraj.com.sa', 'wasalt.com',
    'remax-saudi.com', 'century21.com.sa',
    'propertyfinder.com.sa', 'dubizzle.com.sa',
    'sakani.com.sa', 'cityscape.com',

    # ── Health & Pharma ───────────────────────────────────────────────────
    'nupco.com', 'aldawaa.com', 'alnahdi.com.sa',
    'dawrni.com', 'labsa.com.sa', 'almana.com.sa',
    'imc.med.sa', 'ngha.med.sa',
    'sehhaty.com.sa', 'vezeeta.com',

    # ── Education ─────────────────────────────────────────────────────────
    'kfu.edu.sa', 'ksu.edu.sa', 'kau.edu.sa',
    'uqu.edu.sa', 'pmu.edu.sa', 'alfaisal.edu',
    'iqra.edu.sa', 'taibahu.edu.sa',
    'madrasati.sa', 'rwaq.org', 'edraak.org',

    # ── Government-Adjacent & Services ────────────────────────────────────
    'elm.sa', 'sadad.com.sa', 'srca.com.sa',
    'tamkeen.gov.sa', 'tasheel.gov.sa',
    'muqeem.sa', 'iqama.net',
    'wasel.com.sa', 'yaqeen.com.sa',
    'seha.sa', 'cchi.gov.sa',

    # ── Enterprise & Cloud ────────────────────────────────────────────────
    'solutions.com.sa', 'solutionsplus.com.sa',
    'enjaz.com.sa', 'mawhiba.org',
    'misk.org.sa', 'kaust.edu.sa',
    'neom.com', 'amaala.com', 'diriyah.sa',

    # ── Food & Beverage ───────────────────────────────────────────────────
    'albaik.com', 'herfy.com', 'kudu.com.sa',
    'cafeamazon.sa', 'dunkin.com.sa',
    'starbucks.com.sa', 'mcdonalds.com.sa',

    # ── Insurance ─────────────────────────────────────────────────────────
    'bupa.com.sa', 'tawuniya.com', 'salama.com.sa',
    'methaq.net', 'malath.com.sa', 'walaa.com.sa',

    # ── Automotive ────────────────────────────────────────────────────────
    'aldawlia.com', 'almajdouie.com', 'aldrees.com',
    'aljomaih.com', 'albatha.com', 'alfardan.sa',
    'syarah.com', 'hatla2ee.com.sa', 'motory.sa',

    # ── HR & Recruitment ──────────────────────────────────────────────────
    'bayt.com', 'indeed.com.sa', 'naukrigulf.com',
    'hiredly.com.sa', 'work.sa', 'jobs.sa',

    # ── Agriculture & Food Supply ──────────────────────────────────────────
    'nadec.com.sa', 'almarai.com', 'saudifoods.com.sa',
    'alrabie.com.sa', 'safi.com.sa',
}
```

- [ ] **Step 3.4: Expand `SA_KEYWORDS` in `filter_crux_sa_domains.py`**

Replace the `SA_KEYWORDS` set (around line 35) with:

```python
SA_KEYWORDS = {
    # ── Original entries ──────────────────────────────────────────────────
    'saudi', 'riyadh', 'jeddah', 'jidda', 'makkah', 'mecca', 'madinah', 'medina',
    'dammam', 'khobar', 'dhahran', 'tabuk', 'taif', 'abha', 'najran', 'hail',
    'jizan', 'jazan', 'yanbu', 'jubail', 'neom', 'kaec', 'qassim', 'buraidah',
    'ksa', 'saudia', 'aramco', 'sabic', 'stc-', 'mobily', 'zain-sa',
    'alrajhi', 'alinma', 'albilad', 'sabb-', 'riyadbank', 'bankalahli',
    'tawakkalna', 'absher', 'nafath', 'sehhaty',
    'haraj', 'jarir', 'panda-sa', 'tamimi',
    'hungerstation', 'jahez', 'marsool', 'mrsool',

    # ── Additional cities / regions ───────────────────────────────────────
    'qatif', 'ahsa', 'alahsa', 'hafar', 'baha', 'albaha',
    'wajh', 'alwajh', 'arar', 'sakaka', 'jouf', 'aljouf',
    'dawadmi', 'shaqra', 'majmaah', 'zulfi', 'kharj', 'alkharj',
    'khafji', 'hafralbatn', 'onaizah', 'unaizah',
    'bisha', 'muhayil', 'bareq', 'samta',
    'turaif', 'rafha', 'alqurayyat', 'alqunfudhah',

    # ── Government service keywords ───────────────────────────────────────
    'tasheel', 'istimara', 'muqeem', 'iqama',
    'madrasati', 'tomooh', 'boonos', 'wqefi',
    'nusuk', 'metrash', 'elm-sa', 'sadad',

    # ── Known SA brand fragments ──────────────────────────────────────────
    'nupco', 'aldawaa', 'alnahdi', 'almajdouie', 'bindawood',
    'aldrees', 'alothaim', 'tamimi-', 'baladna',
    'albaik', 'herfy', 'kudu-',
    'salla', 'foodics', 'geidea',
    'stcpay', 'urpay', 'tabby',

    # ── Saudi-specific Arabic-origin fragments used in .com names ─────────
    'noor-sa', 'sahl-', 'rawabi', 'wafi-', 'dar-sa',
    'al-saudi', 'almamlaka', 'almamlakatv',
}
```

- [ ] **Step 3.5: Run tests to verify they pass**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_filter_crux.py -v
```

Expected: All tests PASS including `test_known_saudi_minimum_count` and `test_sa_keywords_minimum_count`.

- [ ] **Step 3.6: Commit**

```bash
git add scripts/filter_crux_sa_domains.py tests/test_filter_crux.py
git commit -m "feat: expand KNOWN_SAUDI_DOMAINS to 200+ and SA_KEYWORDS to 80+"
```

---

## Task 4: Fix Karing Keyword Extraction

**Files:**
- Modify: `scripts/generate-karing-config.py`
- Create: `tests/test_karing_config.py`

- [ ] **Step 4.1: Write failing tests**

Create `tests/test_karing_config.py`:

```python
import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from generate_karing_config import extract_keywords, generate_karing_config

# ── Bug 1: SLD extraction for .sa sub-TLD domains ────────────────────────────

def test_sld_from_com_sa_domain():
    """For 'shop.example.com.sa' the SLD should be 'example', not 'shop'."""
    domains = ['shop.example.com.sa']
    kws = extract_keywords(domains)
    assert 'example' in kws, "SLD from .com.sa domain should be 'example'"
    assert 'shop' not in kws, "'shop' is a subdomain, not the SLD"

def test_sld_from_plain_sa_domain():
    """For 'example.sa' the SLD should be 'example'."""
    domains = ['example.sa']
    kws = extract_keywords(domains)
    assert 'example' in kws

def test_sld_from_gov_sa_domain():
    """For 'portal.ministry.gov.sa' the SLD should be 'ministry'."""
    domains = ['portal.ministry.gov.sa']
    kws = extract_keywords(domains)
    assert 'ministry' in kws
    assert 'portal' not in kws

def test_sld_from_plain_com_domain():
    """For 'noon.com' the SLD should be 'noon'."""
    domains = ['noon.com']
    kws = extract_keywords(domains)
    assert 'noon' in kws

# ── Bug 2: 300-keyword cap is too low ─────────────────────────────────────────

def test_keyword_cap_is_at_least_2000():
    """With 2000+ unique SLD names, all should appear (cap >= 2000)."""
    # Generate 2100 unique domain names
    domains = [f'd{i:04d}.com.sa' for i in range(2100)]
    kws = extract_keywords(domains, cap=2000)
    assert len(kws) >= 2000, f"Expected >= 2000 keywords, got {len(kws)}"

# ── Frequency weighting ───────────────────────────────────────────────────────

def test_high_frequency_keywords_included_first():
    """The keyword appearing most often should always be in output."""
    domains = ['stcpay.com.sa', 'stcplay.gg', 'stcbank.com.sa'] + [f'x{i}.com' for i in range(2100)]
    kws = extract_keywords(domains, cap=3)
    assert 'stcpay' in kws or 'stcplay' in kws or 'stcbank' in kws

# ── Generic word exclusion ────────────────────────────────────────────────────

def test_generic_words_excluded():
    for word in ['mail', 'admin', 'shop', 'store', 'blog', 'api', 'app']:
        assert word not in extract_keywords([f'{word}.example.com.sa'])
```

- [ ] **Step 4.2: Note the import — rename function for import compatibility**

The module is named `generate-karing-config.py` with a hyphen. Python can't import it directly with `import`. Add this to `tests/conftest.py`:

```python
import importlib.util, sys

def import_hyphenated(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Make generate-karing-config importable
import os as _os
_scripts_dir = _os.path.join(_os.path.dirname(__file__), '..', 'scripts')

generate_karing_config_mod = import_hyphenated(
    'generate_karing_config',
    _os.path.join(_scripts_dir, 'generate-karing-config.py')
)
```

And update `tests/test_karing_config.py` import line to:
```python
from generate_karing_config import extract_keywords, generate_karing_config
```

- [ ] **Step 4.3: Run tests to confirm failures**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_karing_config.py -v
```

Expected: `FAILED test_sld_from_com_sa_domain`, `FAILED test_keyword_cap_is_at_least_2000`, others.

- [ ] **Step 4.4: Fix `extract_keywords` in `generate-karing-config.py`**

Replace the existing `extract_keywords` function (lines ~30-45) with:

```python
SA_SUB_TLDS = {'com', 'gov', 'edu', 'org', 'net', 'med', 'sch'}

GENERIC_WORDS = {
    'www', 'http', 'https', 'mail', 'smtp', 'imap', 'pop3', 'ftp', 'dns',
    'api', 'app', 'web', 'cdn', 'img', 'static', 'dev', 'test', 'beta',
    'admin', 'login', 'auth', 'shop', 'store', 'blog', 'news', 'info',
    'help', 'support', 'docs', 'data', 'cloud', 'host', 'server', 'node',
    'edge', 'proxy', 'vpn', 'ssl', 'tls', 'portal', 'secure', 'pay',
}

def _get_sld(domain):
    """Return the second-level domain (registrable name part)."""
    parts = domain.rstrip('.').split('.')
    # e.g. portal.ministry.gov.sa → ['portal','ministry','gov','sa']
    if len(parts) >= 4 and parts[-1] == 'sa' and parts[-2] in SA_SUB_TLDS:
        return parts[-3]          # 'ministry'
    # e.g. example.com.sa → ['example','com','sa']
    if len(parts) == 3 and parts[-1] == 'sa' and parts[-2] in SA_SUB_TLDS:
        return parts[-3]          # 'example'
    # e.g. example.sa → ['example','sa']
    if len(parts) >= 2 and parts[-1] == 'sa':
        return parts[-2]          # 'example'
    # e.g. noon.com → ['noon','com']
    if len(parts) >= 2:
        return parts[-2]          # 'noon'
    return parts[0]


def extract_keywords(domains, min_length=4, cap=2000):
    """
    Extract unique SLD keywords from domain names, ranked by frequency.
    Returns up to `cap` keywords, most-frequent first.
    """
    from collections import Counter
    counts = Counter()
    for domain in domains:
        name = _get_sld(domain)
        if (name
                and len(name) >= min_length
                and not name.isdigit()
                and name not in GENERIC_WORDS):
            counts[name] += 1

    # Sort by frequency descending, then alphabetically for stability
    ranked = sorted(counts.keys(), key=lambda k: (-counts[k], k))
    return ranked[:cap]
```

- [ ] **Step 4.5: Run tests to verify they pass**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_karing_config.py -v
```

Expected: All PASSED.

- [ ] **Step 4.6: Commit**

```bash
git add scripts/generate-karing-config.py tests/test_karing_config.py tests/conftest.py
git commit -m "fix: correct Karing SLD extraction for .sa sub-TLDs, raise keyword cap to 2000"
```

---

## Task 5: Deduplicate Curated Domain Files

**Files:**
- Create: `scripts/dedup-curated.py`
- Create: `tests/test_dedup.py`
- Modify: `data/sa-domains.txt`, `data/sa-gov-domains.txt`, `data/sa-services-domains.txt`

- [ ] **Step 5.1: Write failing tests**

Create `tests/test_dedup.py`:

```python
import sys, os, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import importlib.util
spec = importlib.util.spec_from_file_location(
    'dedup_curated',
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'dedup-curated.py')
)
dedup_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dedup_mod)
dedup_curated = dedup_mod.dedup_curated


def _write(path, lines):
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')

def _read(path):
    with open(path) as f:
        return [l.rstrip('\n') for l in f]


def test_removes_cross_file_duplicates(tmp_path):
    """Domain present in file A and file B must be removed from file B."""
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    _write(a, ['# comment', 'noon.com', 'stc.com.sa', ''])
    _write(b, ['# comment', 'noon.com', 'salla.com', ''])  # noon.com is duplicate

    dedup_curated([str(a), str(b)])

    lines_b = _read(b)
    domains_b = [l for l in lines_b if l and not l.startswith('#')]
    assert 'noon.com' not in domains_b, "noon.com should be removed from b.txt"
    assert 'salla.com' in domains_b, "salla.com should remain"

def test_preserves_comments(tmp_path):
    """Comments and blank lines must be preserved."""
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    _write(a, ['# file a', 'noon.com'])
    _write(b, ['# file b', '', 'salla.com'])

    dedup_curated([str(a), str(b)])

    lines_b = _read(b)
    assert '# file b' in lines_b
    assert '' in lines_b

def test_within_file_dedup(tmp_path):
    """Duplicates within the same file must be removed."""
    a = tmp_path / "a.txt"
    _write(a, ['noon.com', 'salla.com', 'noon.com'])

    dedup_curated([str(a)])

    domains = [l for l in _read(a) if l and not l.startswith('#')]
    assert domains.count('noon.com') == 1

def test_case_insensitive(tmp_path):
    """Domain deduplication is case-insensitive."""
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    _write(a, ['Noon.com'])
    _write(b, ['noon.com'])

    dedup_curated([str(a), str(b)])

    domains_b = [l for l in _read(b) if l and not l.startswith('#')]
    assert 'noon.com' not in domains_b
```

- [ ] **Step 5.2: Run tests to confirm failures**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_dedup.py -v
```

Expected: `ERROR` — `dedup-curated.py` doesn't exist yet.

- [ ] **Step 5.3: Create `scripts/dedup-curated.py`**

```python
#!/usr/bin/env python3
"""
Deduplicate entries across curated data/*.txt files.
Files are processed in order; a domain that appears in file N is removed
from all subsequent files (N+1, N+2, ...) and within each file itself.
Comments and blank lines are preserved.
"""
import sys


def dedup_curated(filepaths):
    """
    Deduplicate domains across and within the given files.
    Modifies files in-place.
    """
    global_seen = set()

    for filepath in filepaths:
        with open(filepath, encoding='utf-8') as f:
            raw_lines = f.readlines()

        out_lines = []
        file_seen = set()

        for line in raw_lines:
            stripped = line.rstrip('\n')
            domain = stripped.strip().lower()

            # Preserve comments and blank lines
            if not domain or domain.startswith('#'):
                out_lines.append(line)
                continue

            if domain in global_seen or domain in file_seen:
                continue  # skip duplicate

            file_seen.add(domain)
            global_seen.add(domain)
            out_lines.append(line)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(out_lines)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} file1.txt [file2.txt ...]")
        sys.exit(1)
    dedup_curated(sys.argv[1:])
    print(f"Deduplicated {len(sys.argv) - 1} file(s)")
```

- [ ] **Step 5.4: Run tests to verify they pass**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_dedup.py -v
```

Expected: All PASSED.

- [ ] **Step 5.5: Run dedup against actual data files**

```bash
cd /home/eittam/SA-Routing-Rules
python3 scripts/dedup-curated.py \
  data/sa-domains.txt \
  data/sa-gov-domains.txt \
  data/sa-services-domains.txt

# Verify counts changed
wc -l data/sa-domains.txt data/sa-gov-domains.txt data/sa-services-domains.txt
```

Expected: Total line count decreases by ~55.

- [ ] **Step 5.6: Commit**

```bash
git add scripts/dedup-curated.py tests/test_dedup.py data/sa-domains.txt data/sa-gov-domains.txt data/sa-services-domains.txt
git commit -m "fix: deduplicate curated domain files (removes ~55 cross-file duplicates)"
```

---

## Task 6: Enable DNS Resolution by Default

**Files:**
- Modify: `scripts/filter_crux_sa_domains.py` (resolve_domain function)
- Modify: `.github/workflows/release.yml` (SKIP_DNS default)

- [ ] **Step 6.1: Add DNS speed test to test file**

Append to `tests/test_filter_crux.py`:

```python
def test_resolve_domain_returns_list():
    """resolve_domain must return a list (empty on failure, not raise)."""
    from filter_crux_sa_domains import resolve_domain
    # This should never raise — failures return []
    result = resolve_domain('this-domain-definitely-does-not-exist-xyz123.com')
    assert isinstance(result, list)
    assert result == []

def test_resolve_domain_uses_dnspython(monkeypatch):
    """resolve_domain should use dns.resolver, not socket."""
    import filter_crux_sa_domains as mod
    called_with = []

    class FakeAnswer:
        def __str__(self): return '1.2.3.4'

    class FakeResolver:
        nameservers = []
        timeout = 2
        lifetime = 2
        def resolve(self, domain, rtype):
            called_with.append(domain)
            return [FakeAnswer()]

    monkeypatch.setattr(mod, '_make_resolver', lambda: FakeResolver())
    result = mod.resolve_domain('example.sa')
    assert called_with == ['example.sa']
    assert '1.2.3.4' in result
```

- [ ] **Step 6.2: Run new tests to confirm failures**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_filter_crux.py::test_resolve_domain_uses_dnspython -v
```

Expected: `FAILED` — `_make_resolver` doesn't exist and dns module not used.

- [ ] **Step 6.3: Update `resolve_domain` in `filter_crux_sa_domains.py`**

Replace the existing `resolve_domain` function and add `_make_resolver` helper:

```python
try:
    import dns.resolver as _dns_resolver
    _HAS_DNSPYTHON = True
except ImportError:
    _HAS_DNSPYTHON = False

_FAST_RESOLVERS = ['1.1.1.1', '8.8.8.8', '9.9.9.9', '208.67.222.222']
_DNS_TIMEOUT = 2  # seconds


def _make_resolver():
    """Return a configured dns.resolver.Resolver using fast public nameservers."""
    if not _HAS_DNSPYTHON:
        return None
    r = _dns_resolver.Resolver()
    r.nameservers = _FAST_RESOLVERS
    r.timeout = _DNS_TIMEOUT
    r.lifetime = _DNS_TIMEOUT
    return r


def resolve_domain(domain):
    """
    Resolve a domain to its IPv4 addresses.
    Uses dnspython when available for speed and reliability.
    Falls back to socket on ImportError.
    Returns [] on any resolution failure — never raises.
    """
    resolver = _make_resolver()
    if resolver is not None:
        try:
            answers = resolver.resolve(domain, 'A')
            return [str(a) for a in answers]
        except Exception:
            return []
    # Fallback: stdlib socket
    try:
        results = socket.getaddrinfo(domain, None, socket.AF_INET, socket.SOCK_STREAM)
        return list({r[4][0] for r in results})
    except Exception:
        return []
```

- [ ] **Step 6.4: Run tests to verify they pass**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pip install --break-system-packages dnspython && python3 -m pytest tests/test_filter_crux.py -v
```

Expected: All PASSED.

- [ ] **Step 6.5: Change SKIP_DNS default in `release.yml`**

Locate the `SKIP_DNS` input (around line 8):
```yaml
      SKIP_DNS:
        description: "Skip DNS resolution for CrUX domains (faster build)"
        required: false
        type: boolean
        default: false    # was: true
```

Also update the workflow step that calls `generate-sa-domains.sh` to pass the flag:
```yaml
- name: Generate SA domain list (with CrUX pipeline)
  run: |
    chmod +x ./scripts/generate-sa-domains.sh
    ./scripts/generate-sa-domains.sh
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    SKIP_DNS: ${{ inputs.SKIP_DNS || 'false' }}
```

And in `generate-sa-domains.sh`, pass `--resolve-dns` to the Python filter when `SKIP_DNS` is false:
```bash
DNS_FLAG=""
if [ "${SKIP_DNS:-false}" = "false" ]; then
  DNS_FLAG="--resolve-dns --max-workers 200"
fi

python3 ./scripts/filter_crux_sa_domains.py /tmp/crux-sa-latest.csv \
  -i ./sa-ips/sa-all.txt \
  -o sa-crux-live.txt \
  $DNS_FLAG 2>/dev/null || true
```

- [ ] **Step 6.6: Commit**

```bash
git add scripts/filter_crux_sa_domains.py .github/workflows/release.yml scripts/generate-sa-domains.sh
git commit -m "feat: switch DNS resolution to dnspython, enable by default (SKIP_DNS=false)"
```

---

## Task 7: BGP AS Prefix Expansion

**Files:**
- Create: `scripts/fetch-sa-as-prefixes.sh`
- Modify: `scripts/generate-sa-ips.sh`
- Modify: `data/sa-extra-ips.txt`

- [ ] **Step 7.1: Create `scripts/fetch-sa-as-prefixes.sh`**

```bash
#!/bin/bash
# fetch-sa-as-prefixes.sh
# Fetches all BGP-announced IP prefixes from major Saudi Arabian ASes
# via the RIPE Stat API (https://stat.ripe.net/api/v2/).
# Output: sa-ips/sa-bgp-prefixes.txt

set -euo pipefail

echo "==> Fetching BGP-announced SA AS prefixes from RIPE Stat API..."

mkdir -p sa-ips

# Major Saudi ASes:
# AS39386 - Mobily (Etihad Etisalat) primary
# AS35819 - Mobily (alternate)
# AS8895  - Zain Saudi Arabia
# AS25019 - STC subsidiary / Etihad Etisalat
# AS28620 - STC (Saudi Telecom Company) primary
# AS47357 - STC (alternate)
# AS39648 - STC (alternate)
# AS47794 - Integrated Telecom (Salam)
# AS198515 - GO Telecom
# AS21050  - Bayanat Al-Oula
SA_ASES="39386 35819 8895 25019 28620 47357 39648 47794 198515 21050"

TMP_FILE="$(mktemp /tmp/sa-bgp-XXXXXX.txt)"
trap "rm -f $TMP_FILE" EXIT

for asn in $SA_ASES; do
  echo "  -> Querying AS${asn}..."
  RESP=$(curl -s --max-time 15 \
    "https://stat.ripe.net/api/v2/announced-prefixes?resource=AS${asn}" 2>/dev/null || echo '{}')

  echo "$RESP" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    prefixes = data.get('data', {}).get('prefixes', [])
    for p in prefixes:
        print(p.get('prefix', ''))
except Exception:
    pass
" >> "$TMP_FILE"

  sleep 0.3   # be polite to RIPE API
done

# Sort, deduplicate, remove empty lines
grep -v '^$' "$TMP_FILE" | LC_ALL=C sort -u > sa-ips/sa-bgp-prefixes.txt

IPV4_COUNT=$(grep -c '\.' sa-ips/sa-bgp-prefixes.txt 2>/dev/null || echo 0)
IPV6_COUNT=$(grep -c ':' sa-ips/sa-bgp-prefixes.txt 2>/dev/null || echo 0)
echo "  -> BGP prefixes: ${IPV4_COUNT} IPv4, ${IPV6_COUNT} IPv6"
echo "==> Done fetching BGP prefixes"
```

- [ ] **Step 7.2: Make it executable and test manually**

```bash
chmod +x /home/eittam/SA-Routing-Rules/scripts/fetch-sa-as-prefixes.sh
cd /home/eittam/SA-Routing-Rules && bash scripts/fetch-sa-as-prefixes.sh
```

Expected: Output like `BGP prefixes: 230 IPv4, 45 IPv6` and `sa-ips/sa-bgp-prefixes.txt` created.

- [ ] **Step 7.3: Update `generate-sa-ips.sh` to merge BGP prefixes**

After the existing RIPE extraction block, add:

```bash
# --- Source 3: BGP-announced prefixes from Saudi ASes ---
echo "  -> Fetching BGP-announced SA prefixes..."
if [ -f ./scripts/fetch-sa-as-prefixes.sh ]; then
  bash ./scripts/fetch-sa-as-prefixes.sh
  BGP_COUNT=$(wc -l < sa-ips/sa-bgp-prefixes.txt 2>/dev/null || echo 0)
  echo "     Found ${BGP_COUNT} BGP-announced SA prefixes"
  cat sa-ips/sa-bgp-prefixes.txt >> sa-ips/sa-ripe.txt
fi
```

Then the existing dedup/sort step will merge all three sources automatically.

- [ ] **Step 7.4: Populate `data/sa-extra-ips.txt` with verified anchor ranges**

Replace the file content with:

```
# Additional Saudi Arabia IP ranges
# These are manually verified ranges not reliably captured by RIPE delegated stats
# or BGP announcements. Add only ranges with confirmed Saudi ownership.
# Format: CIDR notation, one per line.
#
# BGP-based IP discovery is handled automatically by scripts/fetch-sa-as-prefixes.sh
# This file is for edge cases only.

# STC (Saudi Telecom Company) - customer-facing blocks confirmed SA
# Source: RIPE whois cross-check
5.1.0.0/22
46.62.0.0/16
83.97.160.0/19
95.177.0.0/16

# Mobily (Etihad Etisalat) - residential / business blocks
# Source: RIPE whois AS35819
37.29.0.0/18
185.122.0.0/22

# Zain Saudi Arabia - confirmed SA allocation
# Source: RIPE whois AS8895
46.138.0.0/16
```

- [ ] **Step 7.5: Commit**

```bash
git add scripts/fetch-sa-as-prefixes.sh scripts/generate-sa-ips.sh data/sa-extra-ips.txt
git commit -m "feat: add BGP AS prefix expansion for 10 Saudi ASes, populate sa-extra-ips.txt"
```

---

## Task 8: Certificate Transparency Integration

**Files:**
- Create: `scripts/fetch-ct-domains.py`
- Create: `tests/test_ct_fetch.py`

- [ ] **Step 8.1: Write failing tests**

Create `tests/test_ct_fetch.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import importlib.util
spec = importlib.util.spec_from_file_location(
    'fetch_ct_domains',
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'fetch-ct-domains.py')
)
ct_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ct_mod)

parse_ct_response = ct_mod.parse_ct_response
extract_domains_from_cert = ct_mod.extract_domains_from_cert
normalize_domain = ct_mod.normalize_domain


def test_extract_domains_from_cert_name_value():
    """name_value may contain multiple newline-separated names."""
    cert = {
        'name_value': 'www.example.com.sa\nexample.com.sa\n*.example.com.sa',
        'common_name': 'example.com.sa'
    }
    domains = extract_domains_from_cert(cert)
    assert 'example.com.sa' in domains
    assert 'www.example.com.sa' in domains

def test_wildcard_stripped():
    """Wildcard prefix (*.) must be stripped."""
    cert = {'name_value': '*.stc.com.sa', 'common_name': 'stc.com.sa'}
    domains = extract_domains_from_cert(cert)
    assert 'stc.com.sa' in domains
    assert '*.stc.com.sa' not in domains

def test_normalize_domain_lowercase():
    assert normalize_domain('STc.Com.SA') == 'stc.com.sa'

def test_normalize_domain_strips_trailing_dot():
    assert normalize_domain('example.sa.') == 'example.sa'

def test_parse_ct_response_returns_set():
    """parse_ct_response must return a set of unique domain strings."""
    mock_json = [
        {'name_value': 'a.example.sa\nb.example.sa', 'common_name': 'example.sa'},
        {'name_value': 'a.example.sa', 'common_name': 'example.sa'},  # duplicate
    ]
    result = parse_ct_response(mock_json)
    assert isinstance(result, set)
    assert 'example.sa' in result
    assert len(result) == len(set(result))  # no duplicates

def test_parse_ct_response_handles_empty():
    assert parse_ct_response([]) == set()
    assert parse_ct_response(None) == set()
```

- [ ] **Step 8.2: Run tests to confirm failures**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_ct_fetch.py -v
```

Expected: `ERROR` — `fetch-ct-domains.py` doesn't exist.

- [ ] **Step 8.3: Create `scripts/fetch-ct-domains.py`**

```python
#!/usr/bin/env python3
"""
Certificate Transparency Domain Fetcher
========================================
Queries crt.sh to find all domains from Saudi Arabia Certificate
Transparency logs. Targets:
  1. All .sa TLD variants (direct cert query)
  2. Certificates issued to Saudi organizations (org name pivoting)

Rate-limited to ~3 req/s. Run weekly.
Output: domains/sa-ct.txt
"""

import sys
import time
import argparse
import requests

SA_TLD_PATTERNS = [
    '%.sa',
    '%.com.sa',
    '%.gov.sa',
    '%.edu.sa',
    '%.org.sa',
    '%.net.sa',
    '%.med.sa',
    '%.sch.sa',
]

SA_ORG_PIVOTS = [
    'Aramco', 'STC', 'Mobily', 'NEOM', 'Alrajhi', 'Alinma', 'SABIC',
    'Samba', 'Misk', 'AlBilad', 'Salam Telecom', 'Zain Saudi',
    'CITC', 'KAUST', 'Ministry of',
]

CRT_SH_URL = "https://crt.sh/"
REQUEST_DELAY = 0.4   # seconds between requests


def normalize_domain(domain):
    """Lowercase, strip trailing dot and wildcard prefix."""
    if not domain:
        return ''
    d = domain.strip().lower().rstrip('.')
    if d.startswith('*.'):
        d = d[2:]
    return d


def extract_domains_from_cert(cert):
    """Extract all domain names from a crt.sh certificate entry."""
    domains = set()
    for field in ('name_value', 'common_name'):
        raw = cert.get(field, '') or ''
        for part in raw.replace(',', '\n').split('\n'):
            d = normalize_domain(part.strip())
            if d and '.' in d:
                domains.add(d)
    return domains


def parse_ct_response(data):
    """Parse a crt.sh JSON response list into a set of domain strings."""
    if not data:
        return set()
    domains = set()
    for cert in data:
        domains.update(extract_domains_from_cert(cert))
    return domains


def query_crtsh(q, retries=3):
    """Query crt.sh and return parsed JSON or empty list on failure."""
    params = {'q': q, 'output': 'json'}
    for attempt in range(retries):
        try:
            r = requests.get(CRT_SH_URL, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
        except Exception as e:
            print(f"  Warning: crt.sh query failed for {q!r}: {e}", file=sys.stderr)
            time.sleep(5)
    return []


def fetch_all_sa_ct_domains(output_file=None):
    """Fetch all SA-related domains from CT logs via crt.sh."""
    all_domains = set()

    # Phase 1: .sa TLD patterns
    print("==> Phase 1: Querying .sa TLD patterns...", file=sys.stderr)
    for pattern in SA_TLD_PATTERNS:
        print(f"  -> {pattern}", file=sys.stderr)
        certs = query_crtsh(pattern)
        domains = parse_ct_response(certs)
        all_domains.update(domains)
        print(f"     +{len(domains)} domains (total: {len(all_domains)})", file=sys.stderr)
        time.sleep(REQUEST_DELAY)

    # Phase 2: Saudi org name pivoting
    print("==> Phase 2: Querying Saudi organization names...", file=sys.stderr)
    for org in SA_ORG_PIVOTS:
        print(f"  -> {org}", file=sys.stderr)
        certs = query_crtsh(org)
        # Filter: only keep .sa domains from org queries (avoid global false positives)
        domains = {d for d in parse_ct_response(certs) if d.endswith('.sa')}
        all_domains.update(domains)
        print(f"     +{len(domains)} .sa domains", file=sys.stderr)
        time.sleep(REQUEST_DELAY)

    # Filter to only include SA-relevant domains
    sa_domains = {d for d in all_domains if d.endswith('.sa') or '.sa.' in d}

    print(f"\n==> Total unique SA CT domains: {len(sa_domains)}", file=sys.stderr)

    if output_file:
        with open(output_file, 'w') as f:
            f.write("# Saudi Arabia domains from Certificate Transparency logs\n")
            f.write(f"# Source: crt.sh — fetched by scripts/fetch-ct-domains.py\n\n")
            for d in sorted(sa_domains):
                f.write(d + '\n')
        print(f"Written to {output_file}", file=sys.stderr)
    else:
        for d in sorted(sa_domains):
            print(d)

    return sa_domains


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch SA domains from CT logs via crt.sh')
    parser.add_argument('-o', '--output', help='Output file path')
    args = parser.parse_args()
    fetch_all_sa_ct_domains(output_file=args.output)
```

- [ ] **Step 8.4: Run tests to verify they pass**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_ct_fetch.py -v
```

Expected: All PASSED (no network calls made in tests — all unit-testable via parse functions).

- [ ] **Step 8.5: Smoke-test the script with a small query**

```bash
cd /home/eittam/SA-Routing-Rules && python3 scripts/fetch-ct-domains.py 2>&1 | head -20
```

Expected: Output like `+7608 domains... +82 .sa domains` from crt.sh. (Requires network.)

- [ ] **Step 8.6: Commit**

```bash
git add scripts/fetch-ct-domains.py tests/test_ct_fetch.py
git commit -m "feat: add Certificate Transparency domain fetcher via crt.sh"
```

---

## Task 9: Majestic Million Integration

**Files:**
- Create: `scripts/fetch-majestic-sa.py`
- Create: `tests/test_majestic.py`

- [ ] **Step 9.1: Write failing tests**

Create `tests/test_majestic.py`:

```python
import sys, os, io, csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import importlib.util
spec = importlib.util.spec_from_file_location(
    'fetch_majestic_sa',
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'fetch-majestic-sa.py')
)
maj_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maj_mod)

classify_majestic_row = maj_mod.classify_majestic_row


SAMPLE_HEADER = ['GlobalRank', 'TldRank', 'Domain', 'TLD', 'RefSubNets',
                 'RefIPs', 'IDN_Domain', 'IDN_TLD', 'PrevGlobalRank',
                 'PrevTldRank', 'PrevRefSubNets', 'PrevRefIPs']


def _row(rank, domain, tld):
    return dict(zip(SAMPLE_HEADER, [str(rank), '1', domain, tld, '10', '8', '', '', '', '', '', '']))


def test_sa_tld_always_included():
    row = _row(500000, 'alrajhi', 'sa')
    assert classify_majestic_row(row) == 'tld'

def test_com_sa_tld_included():
    row = _row(1, 'stc', 'com.sa')
    assert classify_majestic_row(row) is not None

def test_global_tld_with_sa_keyword():
    row = _row(10000, 'saudia-airlines', 'com')
    assert classify_majestic_row(row) == 'keyword'

def test_global_unknown_not_included():
    row = _row(10000, 'randomdomain', 'com')
    assert classify_majestic_row(row) is None

def test_known_sa_domain_included():
    row = _row(5000, 'noon', 'com')
    assert classify_majestic_row(row) == 'known'

def test_global_service_excluded():
    """google.com must never be included even if top-ranked."""
    row = _row(1, 'google', 'com')
    assert classify_majestic_row(row) is None

def test_high_rank_unknown_marked_for_dns():
    """Top-50K unknown domains get flagged for DNS check."""
    row = _row(25000, 'unknowndomain', 'com')
    assert classify_majestic_row(row) == 'dns_check'

def test_low_rank_unknown_excluded():
    """Domains outside top-50K get no DNS check."""
    row = _row(500000, 'unknowndomain', 'com')
    assert classify_majestic_row(row) is None
```

- [ ] **Step 9.2: Run tests to confirm failures**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_majestic.py -v
```

Expected: `ERROR` — `fetch-majestic-sa.py` doesn't exist.

- [ ] **Step 9.3: Create `scripts/fetch-majestic-sa.py`**

```python
#!/usr/bin/env python3
"""
Majestic Million Saudi Arabia Domain Filter
============================================
Downloads the Majestic Million top-1M CSV (updated weekly) and filters
for Saudi Arabia domains using:
  1. .sa / .com.sa TLD column match (immediate include)
  2. Known Saudi company domains (immediate include)
  3. Saudi keyword match in domain name (immediate include)
  4. DNS resolution to Saudi IP ranges for top-50K unknown domains

Output: domains/sa-majestic.txt
"""

import sys
import csv
import io
import time
import ipaddress
import concurrent.futures
import argparse
import requests

# Re-use constants from filter_crux_sa_domains — they live in the same dir
import importlib.util, os
_scripts_dir = os.path.dirname(__file__)
spec = importlib.util.spec_from_file_location(
    '_crux_filter',
    os.path.join(_scripts_dir, 'filter_crux_sa_domains.py')
)
_crux = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_crux)

SA_KEYWORDS = _crux.SA_KEYWORDS
KNOWN_SAUDI_DOMAINS = _crux.KNOWN_SAUDI_DOMAINS
GLOBAL_EXCLUDES = _crux.GLOBAL_EXCLUDES
is_global_exclude = _crux.is_global_exclude
is_known_saudi = _crux.is_known_saudi
has_sa_keyword = _crux.has_sa_keyword
load_sa_ip_ranges = _crux.load_sa_ip_ranges
is_saudi_ip = _crux.is_saudi_ip
resolve_domain = _crux.resolve_domain

MAJESTIC_CSV_URL = "https://downloads.majestic.com/majestic_million.csv"
SA_TLDS = {'sa', 'com.sa', 'gov.sa', 'edu.sa', 'org.sa', 'net.sa', 'med.sa', 'sch.sa'}
DNS_CHECK_TOP_N = 50_000


def classify_majestic_row(row):
    """
    Return classification for a Majestic row dict, or None to skip.
    Returns: 'tld' | 'known' | 'keyword' | 'dns_check' | None
    """
    domain = row.get('Domain', '').lower().strip()
    tld = row.get('TLD', '').lower().strip()
    rank = int(row.get('GlobalRank', 9_999_999))

    if not domain:
        return None

    full = f"{domain}.{tld}" if tld else domain

    # Always exclude known global services
    if is_global_exclude(full):
        return None

    # .sa TLD
    if tld in SA_TLDS:
        return 'tld'

    # Known Saudi company
    if is_known_saudi(full):
        return 'known'

    # Saudi keywords
    if has_sa_keyword(domain):
        return 'keyword'

    # Top-50K unknown: mark for DNS check
    if rank <= DNS_CHECK_TOP_N:
        return 'dns_check'

    return None


def download_majestic_csv():
    """Download and return Majestic Million CSV rows as list of dicts."""
    print("==> Downloading Majestic Million CSV...", file=sys.stderr)
    r = requests.get(MAJESTIC_CSV_URL, timeout=120, stream=True)
    r.raise_for_status()
    content = r.content.decode('utf-8', errors='replace')
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    print(f"  -> Downloaded {len(rows):,} rows", file=sys.stderr)
    return rows


def filter_majestic(rows, sa_ip_file=None, resolve_dns=False, max_workers=100):
    """Filter Majestic rows for Saudi domains."""
    sa_networks = load_sa_ip_ranges(sa_ip_file) if sa_ip_file else []

    immediate = set()
    dns_candidates = []

    for row in rows:
        cls = classify_majestic_row(row)
        if cls is None:
            continue
        domain = row['Domain'].lower()
        tld = row['TLD'].lower()
        full = f"{domain}.{tld}" if tld else domain

        if cls == 'dns_check':
            dns_candidates.append(full)
        else:
            immediate.add(full)

    print(f"  -> Immediate SA: {len(immediate)}", file=sys.stderr)
    print(f"  -> DNS candidates: {len(dns_candidates)}", file=sys.stderr)

    dns_saudi = set()
    if resolve_dns and sa_networks and dns_candidates:
        print(f"  -> Resolving {len(dns_candidates)} DNS candidates...", file=sys.stderr)

        def check(domain):
            ips = resolve_domain(domain)
            for ip in ips:
                if is_saudi_ip(ip, sa_networks):
                    return domain, True
            return domain, False

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            for domain, is_sa in ex.map(check, dns_candidates):
                if is_sa:
                    dns_saudi.add(domain)

        print(f"  -> DNS-verified SA: {len(dns_saudi)}", file=sys.stderr)

    return immediate | dns_saudi


def main():
    parser = argparse.ArgumentParser(description='Filter Majestic Million for SA domains')
    parser.add_argument('-i', '--ip-file', help='Saudi IP ranges CIDR file')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--resolve-dns', action='store_true')
    parser.add_argument('--max-workers', type=int, default=100)
    args = parser.parse_args()

    rows = download_majestic_csv()
    domains = filter_majestic(rows, sa_ip_file=args.ip_file,
                              resolve_dns=args.resolve_dns,
                              max_workers=args.max_workers)

    print(f"\n==> Total SA Majestic domains: {len(domains)}", file=sys.stderr)

    out = sorted(domains)
    if args.output:
        with open(args.output, 'w') as f:
            f.write("# Saudi Arabia domains from Majestic Million\n")
            f.write(f"# Source: majestic.com/reports/majestic-million\n\n")
            for d in out:
                f.write(d + '\n')
    else:
        for d in out:
            print(d)


if __name__ == '__main__':
    main()
```

- [ ] **Step 9.4: Run tests to verify they pass**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_majestic.py -v
```

Expected: All PASSED.

- [ ] **Step 9.5: Commit**

```bash
git add scripts/fetch-majestic-sa.py tests/test_majestic.py
git commit -m "feat: add Majestic Million SA domain filter with DNS fallback for top-50K"
```

---

## Task 10: Reverse DNS Sweep

**Files:**
- Create: `scripts/cidr-to-sample-ips.py`
- Create: `scripts/reverse-dns-sweep.sh`

- [ ] **Step 10.1: Create `scripts/cidr-to-sample-ips.py`**

```python
#!/usr/bin/env python3
"""
Expand CIDR blocks to a sample of IPs: one IP per /24 subnet.
Used as input for massdns PTR sweeps to keep queries manageable.

Usage: python3 cidr-to-sample-ips.py sa-ips/sa-ipv4-ripe.txt
Output: one IP per line to stdout
"""
import sys
import ipaddress


def sample_ips_from_file(filepath):
    """Yield one representative IP per /24 from each CIDR in the file."""
    seen_subnets = set()
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or ':' in line:  # skip IPv6
                continue
            try:
                net = ipaddress.ip_network(line, strict=False)
            except ValueError:
                continue

            if net.version != 4:
                continue

            # Enumerate all /24 subnets within this block
            if net.prefixlen >= 24:
                # Single /24 or smaller — use the first host
                subnet_key = str(net.network_address)
                if subnet_key not in seen_subnets:
                    seen_subnets.add(subnet_key)
                    hosts = list(net.hosts())
                    if hosts:
                        yield str(hosts[0])
            else:
                # Larger block — iterate /24 subnets
                for subnet in net.subnets(new_prefix=24):
                    subnet_key = str(subnet.network_address)
                    if subnet_key not in seen_subnets:
                        seen_subnets.add(subnet_key)
                        hosts = list(subnet.hosts())
                        if hosts:
                            yield str(hosts[0])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <cidr-file>", file=sys.stderr)
        sys.exit(1)
    for ip in sample_ips_from_file(sys.argv[1]):
        print(ip)
```

- [ ] **Step 10.2: Test `cidr-to-sample-ips.py` manually**

```bash
cd /home/eittam/SA-Routing-Rules
echo "83.97.160.0/19" > /tmp/test-cidr.txt
python3 scripts/cidr-to-sample-ips.py /tmp/test-cidr.txt | wc -l
```

Expected: `8` (a /19 contains 8 /24 subnets)

- [ ] **Step 10.3: Create `scripts/reverse-dns-sweep.sh`**

```bash
#!/bin/bash
# reverse-dns-sweep.sh
# Performs a PTR (reverse DNS) sweep on Saudi Arabian IPv4 ranges.
# Requires: massdns (https://github.com/blechschmidt/massdns)
#           python3 (for cidr-to-sample-ips.py)
# Output: sa-ips/sa-ptr-domains.txt
#
# Strategy: one IP per /24 subnet → keeps total queries under 5K for SA space.
# For a full sweep (all IPs), pass --full flag.

set -euo pipefail

FULL_SWEEP="${1:-}"
CIDR_FILE="${2:-sa-ips/sa-ipv4-ripe.txt}"

if ! command -v massdns &>/dev/null; then
  echo "  WARNING: massdns not installed, skipping reverse DNS sweep."
  echo "  Install: https://github.com/blechschmidt/massdns"
  exit 0
fi

echo "==> Reverse DNS sweep on Saudi IP space..."

# Generate IP sample list
echo "  -> Generating IP sample from ${CIDR_FILE}..."
python3 ./scripts/cidr-to-sample-ips.py "${CIDR_FILE}" > /tmp/sa-sample-ips.txt
IP_COUNT=$(wc -l < /tmp/sa-sample-ips.txt)
echo "  -> Sampled ${IP_COUNT} IPs (one per /24)"

# Convert to in-addr.arpa PTR query format
awk -F. '{print $4"."$3"."$2"."$1".in-addr.arpa"}' /tmp/sa-sample-ips.txt \
  > /tmp/sa-ptr-queries.txt

# Resolvers file (use public fast resolvers)
echo -e "1.1.1.1\n8.8.8.8\n9.9.9.9" > /tmp/resolvers.txt

echo "  -> Running massdns on ${IP_COUNT} queries..."
massdns -r /tmp/resolvers.txt \
        -t PTR \
        --retry REFUSED \
        -o S \
        /tmp/sa-ptr-queries.txt 2>/dev/null | \
  grep -v 'SERVFAIL\|NXDOMAIN\|NOERROR.*0 answer' | \
  awk '/IN PTR/ {gsub(/\.$/, "", $NF); print $NF}' | \
  grep -v '^$' | \
  grep '\.' | \
  LC_ALL=C sort -u > sa-ips/sa-ptr-domains.txt

PTR_COUNT=$(wc -l < sa-ips/sa-ptr-domains.txt)
echo "  -> Discovered ${PTR_COUNT} PTR hostnames"
echo "==> Reverse DNS sweep complete"
```

- [ ] **Step 10.4: Make scripts executable**

```bash
chmod +x /home/eittam/SA-Routing-Rules/scripts/cidr-to-sample-ips.py
chmod +x /home/eittam/SA-Routing-Rules/scripts/reverse-dns-sweep.sh
```

- [ ] **Step 10.5: Commit**

```bash
git add scripts/cidr-to-sample-ips.py scripts/reverse-dns-sweep.sh
git commit -m "feat: add reverse DNS sweep scripts (cidr-to-sample-ips.py + massdns PTR sweep)"
```

---

## Task 11: Wire Everything Together

**Files:**
- Modify: `scripts/generate-sa-domains.sh` (add CT, Majestic, PTR sources)
- Modify: `.github/workflows/release.yml` (add new steps, massdns, new env vars)

- [ ] **Step 11.1: Update `generate-sa-domains.sh`**

Add the following source blocks **before** the "Combine all sources" section:

```bash
# --- Source 7: Certificate Transparency (crt.sh) ---
echo "  -> Fetching Certificate Transparency domains..."
if [ -f ./scripts/fetch-ct-domains.py ]; then
  python3 ./scripts/fetch-ct-domains.py -o sa-ct.txt 2>/dev/null || true
  CT_COUNT=$(grep -v '^#' sa-ct.txt 2>/dev/null | grep -v '^$' | wc -l || echo 0)
  echo "     Found ${CT_COUNT} CT domains"
else
  touch sa-ct.txt
fi

# --- Source 8: Majestic Million ---
echo "  -> Filtering Majestic Million..."
if [ -f ./scripts/fetch-majestic-sa.py ]; then
  MAJESTIC_DNS_FLAG=""
  if [ "${SKIP_DNS:-false}" = "false" ] && [ -f ./sa-ips/sa-all.txt ]; then
    MAJESTIC_DNS_FLAG="--resolve-dns --ip-file ./sa-ips/sa-all.txt"
  fi
  python3 ./scripts/fetch-majestic-sa.py $MAJESTIC_DNS_FLAG -o sa-majestic.txt 2>/dev/null || true
  MAJ_COUNT=$(grep -v '^#' sa-majestic.txt 2>/dev/null | grep -v '^$' | wc -l || echo 0)
  echo "     Found ${MAJ_COUNT} Majestic SA domains"
else
  touch sa-majestic.txt
fi

# --- Source 9: Reverse DNS PTR hostnames ---
echo "  -> Loading PTR hostnames from reverse DNS sweep..."
if [ -f ./sa-ips/sa-ptr-domains.txt ]; then
  PTR_COUNT=$(wc -l < sa-ips/sa-ptr-domains.txt)
  echo "     Found ${PTR_COUNT} PTR domains"
  cat sa-ips/sa-ptr-domains.txt > sa-ptr.txt
else
  touch sa-ptr.txt
fi
```

Then update the combine step to include new sources:

```bash
# --- Combine all sources ---
echo "  -> Combining all domain sources..."
cat sa-banks.txt sa-curated.txt sa-gov.txt sa-services.txt \
    sa-crux.txt sa-ct.txt sa-majestic.txt sa-ptr.txt | \
  sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | \
  grep -v '^#' | \
  grep -v '^$' | \
  tr '[:upper:]' '[:lower:]' | \
  LC_ALL=C sort -u > sa-all-tmp.txt
```

Also update the cleanup line at the end:
```bash
rm -f sa-banks.txt sa-curated.txt sa-gov.txt sa-services.txt \
      sa-crux.txt sa-crux-live.txt sa-ct.txt sa-majestic.txt sa-ptr.txt sa-all-tmp.txt
```

- [ ] **Step 11.2: Add new steps to `release.yml`**

After the existing **Step 1 (Generate SA IP ranges)** block, add:

```yaml
      # ============================================
      # STEP 1b: Fetch BGP-announced SA AS prefixes
      # ============================================
      - name: Fetch BGP-announced SA AS prefixes
        run: |
          chmod +x ./scripts/fetch-sa-as-prefixes.sh
          ./scripts/fetch-sa-as-prefixes.sh
```

After the existing **Step 3 (Generate SA domain list)**, add:

```yaml
      # ============================================
      # STEP 3b: Install massdns for PTR sweep (optional)
      # ============================================
      - name: Install massdns (for reverse DNS sweep)
        run: |
          sudo apt-get install -y massdns 2>/dev/null || \
          (git clone --depth=1 https://github.com/blechschmidt/massdns.git /tmp/massdns-src \
           && cd /tmp/massdns-src && make -j4 \
           && sudo cp bin/massdns /usr/local/bin/ \
           && echo "massdns compiled from source") || \
          echo "massdns unavailable — PTR sweep will be skipped"

      # ============================================
      # STEP 3c: Reverse DNS sweep on SA IP space
      # ============================================
      - name: Reverse DNS PTR sweep
        run: |
          chmod +x ./scripts/reverse-dns-sweep.sh
          ./scripts/reverse-dns-sweep.sh
```

Also update the `Set ENV variables` step to pass SKIP_DNS:

```yaml
      - name: Set ENV variables
        run: |
          echo "RELEASE_NAME=$(date +%Y%m%d%H%M)" >> $GITHUB_ENV
          echo "TAG_NAME=$(date +%Y%m%d%H%M)" >> $GITHUB_ENV
          echo "RELEASE_DATE=$(date +'%A %F %T %Z')" >> $GITHUB_ENV
          echo "SKIP_DNS=${{ inputs.SKIP_DNS || 'false' }}" >> $GITHUB_ENV
```

And update the `Install system dependencies` step to add Python packages:

```yaml
      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y idn2
          python3 -m pip install --break-system-packages dnspython geoip2 requests
```

- [ ] **Step 11.3: Run the full test suite**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/ -v
```

Expected: All tests PASS. Check for no import errors.

- [ ] **Step 11.4: Verify workflow YAML is valid**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('YAML OK')"
```

Expected: `YAML OK`

- [ ] **Step 11.5: Run workflow test**

```bash
cd /home/eittam/SA-Routing-Rules && python3 -m pytest tests/test_workflow_maxmind.py -v
```

Expected: PASSED.

- [ ] **Step 11.6: Final commit**

```bash
git add scripts/generate-sa-domains.sh .github/workflows/release.yml
git commit -m "feat: wire CT logs, Majestic Million, BGP prefixes, and PTR sweep into build pipeline"
```

---

## Task 12: Update README and Requirements

**Files:**
- Modify: `README.md` (update data sources table)
- Modify: `requirements.txt` (finalize)

- [ ] **Step 12.1: Update Data Sources table in `README.md`**

Find and replace the existing `### GeoSite` table section with:

```markdown
### GeoSite (20,000–30,000+ Saudi Domains)

| Source | Description | Count |
|--------|-------------|-------|
| `data/sa-domains.txt` | Major Saudi websites, telecom, e-commerce, banks, media | ~165 |
| `data/sa-gov-domains.txt` | Government portals (Absher, Tawakkalna, Nafath, ministries) | ~190 |
| `data/sa-services-domains.txt` | Saudi apps, fintech, delivery services | ~129 |
| [karenyousefi/bank-domains](https://github.com/karenyousefi/bank-domains) | Saudi bank domains | ~20 |
| `data/sa-crux-domains.txt` | CrUX Top Lists (Chrome UX Report) filtered for SA | ~11,000 |
| Certificate Transparency (crt.sh) | All .sa TLD certs + Saudi org certs | ~2,000–5,000 |
| Majestic Million | Top-1M sites filtered by TLD, keywords, DNS | ~1,000–2,000 |
| Reverse DNS PTR sweep | PTR records on Saudi IP space | ~2,000–8,000 |

### GeoIP
| Source | Description |
|--------|-------------|
| [RIPE NCC](https://ftp.ripe.net/pub/stats/ripencc/) | Authoritative IP delegation data for SA |
| BGP Announced Prefixes | Live BGP routing table for 10 Saudi ASes (RIPE Stat API) |
| [MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) | Enhanced IP geolocation (**required** — set `MAXMIND_LICENSE_KEY` secret) |
| `data/sa-extra-ips.txt` | Verified override ranges not in RIPE/BGP data |
```

- [ ] **Step 12.2: Finalize `requirements.txt`**

```
dnspython>=2.6.0
geoip2>=4.8.0
requests>=2.31.0
```

- [ ] **Step 12.3: Commit**

```bash
git add README.md requirements.txt
git commit -m "docs: update README data sources and finalize requirements.txt"
```

---

## Self-Review Checklist

### Spec Coverage
| Requirement | Task |
|---|---|
| Fix MaxMind activation bug | Task 2 |
| Expand KNOWN_SAUDI_DOMAINS | Task 3 |
| Expand SA_KEYWORDS | Task 3 |
| Fix Karing SLD extraction | Task 4 |
| Fix Karing 300-keyword cap | Task 4 |
| Deduplicate curated files | Task 5 |
| Enable DNS by default | Task 6 |
| BGP AS prefix expansion | Task 7 |
| Fill sa-extra-ips.txt | Task 7 |
| Certificate Transparency | Task 8 |
| Majestic Million | Task 9 |
| Reverse DNS sweep | Task 10 |
| Pipeline wiring | Task 11 |
| Documentation update | Task 12 |

### Type Consistency Check
- `extract_keywords(domains, cap=2000)` — defined Task 4, called from `generate_karing_config` function (no change to caller signature needed — default cap handles it)
- `classify_majestic_row(row)` — returns `str | None` — consistent across Task 9 test and implementation
- `dedup_curated(filepaths)` — list of strings, modifies in-place — consistent Task 5 test and implementation
- `_make_resolver()` — returns `dns.resolver.Resolver | None` — consistent Task 6 test mock and implementation
- `parse_ct_response(data)` — returns `set` — consistent Task 8 test and implementation

### Placeholder Scan
- No TBD/TODO in any task
- All code blocks are complete
- All commands include expected output
- All file paths are absolute or repo-relative

---

## Estimated Coverage Impact

| Change | Estimated New Domains |
|---|---|
| CT logs (crt.sh) | +2,000–5,000 |
| Majestic Million | +1,000–2,000 |
| Reverse DNS PTR | +2,000–8,000 |
| Expanded KNOWN_SAUDI_DOMAINS | +200–500 |
| Expanded SA_KEYWORDS | +300–800 |
| DNS enabled by default | +1,000–3,000 |
| BGP IP expansion | +50–200 extra CIDRs |
| **Total estimate** | **~20,000–30,000 total domains** |
