from erp.security_hardening import safe_run, safe_call, safe_popen
import pathlib
import shutil
import subprocess
import pytest


@pytest.mark.accessibility
def test_base_template_pa11y():
    pa11y = shutil.which("pa11y")
    if not pa11y:
        pytest.skip("pa11y not installed")
    template = pathlib.Path(__file__).resolve().parents[1] / "templates" / "base.html"
    result = safe_run([pa11y, template.as_uri()], capture_output=True, text=True)
    assert result.returncode == 0



