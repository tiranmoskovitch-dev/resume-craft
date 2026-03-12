"""Tests for the licensing module."""

from unittest.mock import patch

import pytest

from resume_craft.licensing import (
    activate_license,
    check_limit,
    get_limits,
    get_status,
    get_tier,
)


@pytest.fixture(autouse=True)
def temp_license_store(tmp_path):
    store = tmp_path / "license.json"
    with patch("resume_craft.licensing.LICENSE_STORE", store):
        yield store


def test_first_run_is_trial():
    assert get_tier() == "trial"


def test_trial_has_premium_limits():
    limits = get_limits()
    assert limits["cover_letter"] is True
    assert limits["ats_scoring"] is True


def test_activate_license():
    ok, _ = activate_license("test-key")
    assert ok is True
    assert get_tier() == "premium"


def test_check_limit_cover_letter_free():
    with patch("resume_craft.licensing.get_tier", return_value="free"):
        allowed, msg = check_limit("cover_letter")
        assert allowed is False
        assert "premium" in msg.lower()


def test_check_limit_template_free():
    with patch("resume_craft.licensing.get_tier", return_value="free"):
        allowed, _ = check_limit("template", "basic")
        assert allowed is True
        allowed, _ = check_limit("template", "modern")
        assert allowed is False


def test_get_status():
    status = get_status()
    assert status["product"] == "resume-craft"
    assert "limits" in status
