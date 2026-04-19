import os
import pytest
import importlib.util
import sys
import ipaddress

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

@pytest.fixture
def sample_crux_csv():
    return os.path.join(FIXTURES_DIR, "sample_crux.csv")

@pytest.fixture
def sample_sa_ips():
    return os.path.join(FIXTURES_DIR, "sample_sa_ips.txt")

@pytest.fixture
def sample_sa_networks():
    cidrs = ["83.97.160.0/19", "5.1.0.0/22", "46.62.0.0/16"]
    return [ipaddress.ip_network(c) for c in cidrs]


def import_hyphenated(name, path):
    """Import a Python module with a hyphenated filename."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')

# Pre-import hyphenated modules so tests can use them
try:
    generate_karing_config_mod = import_hyphenated(
        'generate_karing_config',
        os.path.join(_scripts_dir, 'generate-karing-config.py')
    )
except (FileNotFoundError, ImportError):
    generate_karing_config_mod = None
