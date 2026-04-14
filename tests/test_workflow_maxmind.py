"""
Verifies that MAXMIND_LICENSE_KEY is correctly wired in release.yml
so that the MaxMind download step actually runs when the secret is set.
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


def test_maxmind_download_step_has_condition():
    """The MaxMind download step must have an if-condition referencing MAXMIND_LICENSE_KEY."""
    wf = load_workflow()
    steps = wf["jobs"]["build"]["steps"]
    download_step = next(
        (s for s in steps
         if "MaxMind" in s.get("name", "") and "placeholder" not in s.get("name", "").lower()),
        None
    )
    assert download_step is not None, "MaxMind download step not found"
    condition = download_step.get("if", "")
    assert "MAXMIND_LICENSE_KEY" in condition
