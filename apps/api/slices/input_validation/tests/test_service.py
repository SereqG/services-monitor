from __future__ import annotations

import pytest

from core.exceptions import InputValidationError, SSRFAttemptError
from slices.input_validation.service import validate_url


def test_valid_https_root_url():
    assert validate_url("https://example.com") == "https://example.com"


def test_valid_url_with_trailing_slash():
    assert validate_url("https://example.com/") == "https://example.com/"


def test_rejects_http():
    with pytest.raises(InputValidationError, match="HTTPS"):
        validate_url("http://example.com")


def test_rejects_subpage():
    with pytest.raises(InputValidationError) as exc:
        validate_url("https://example.com/about")
    assert exc.value.code == "SUBPAGE_NOT_ALLOWED"


def test_rejects_localhost():
    with pytest.raises(SSRFAttemptError) as exc:
        validate_url("https://localhost")
    assert exc.value.code == "SSRF_LOCALHOST"


def test_rejects_private_ip():
    with pytest.raises(SSRFAttemptError) as exc:
        validate_url("https://192.168.1.1")
    assert exc.value.code == "SSRF_PRIVATE_IP"


def test_rejects_internal_range():
    with pytest.raises(SSRFAttemptError):
        validate_url("https://10.0.0.1")


def test_rejects_cloud_metadata_ip():
    # 169.254.169.254 is the cloud metadata endpoint — link-local, must be blocked.
    with pytest.raises(SSRFAttemptError) as exc:
        validate_url("https://169.254.169.254")
    assert exc.value.code == "SSRF_PRIVATE_IP"


def test_rejects_cgnat_ip():
    with pytest.raises(SSRFAttemptError) as exc:
        validate_url("https://100.64.0.1")
    assert exc.value.code == "SSRF_PRIVATE_IP"


def test_rejects_url_too_long():
    long_url = "https://" + "a" * 200 + ".com"
    with pytest.raises(InputValidationError) as exc:
        validate_url(long_url)
    assert exc.value.code == "URL_TOO_LONG"
