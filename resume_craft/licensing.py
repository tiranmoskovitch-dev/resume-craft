"""
Licensing and tier management for Resume Craft.

Model:
- 30-day full-feature trial on first use
- After trial: Free tier (limited) + Premium (license key from Gumroad)
"""

import json
import os
import time
from pathlib import Path

PRODUCT_NAME = "resume-craft"
TRIAL_DAYS = 30
LICENSE_STORE = Path.home() / ".resume-craft" / "license.json"

# Tier limits
FREE_LIMITS = {
    "resume": True,
    "cover_letter": False,
    "linkedin_optimization": False,
    "ats_scoring": False,
    "templates": ["basic"],
}

PREMIUM_LIMITS = {
    "resume": True,
    "cover_letter": True,
    "linkedin_optimization": True,
    "ats_scoring": True,
    "templates": ["basic", "modern", "executive", "creative", "tech"],
}


def _ensure_store():
    LICENSE_STORE.parent.mkdir(parents=True, exist_ok=True)
    if not LICENSE_STORE.exists():
        data = {
            "first_run": time.time(),
            "license_key": None,
            "tier": "trial",
        }
        LICENSE_STORE.write_text(json.dumps(data, indent=2))
    return json.loads(LICENSE_STORE.read_text())


def _save_store(data):
    LICENSE_STORE.parent.mkdir(parents=True, exist_ok=True)
    LICENSE_STORE.write_text(json.dumps(data, indent=2))


def get_tier():
    """Return current tier: 'trial', 'free', or 'premium'."""
    data = _ensure_store()

    if data.get("license_key") and data.get("tier") == "premium":
        return "premium"

    first_run = data.get("first_run", time.time())
    elapsed_days = (time.time() - first_run) / 86400

    if elapsed_days <= TRIAL_DAYS:
        return "trial"

    return "free"


def get_limits():
    """Return the feature limits for the current tier."""
    tier = get_tier()
    if tier in ("trial", "premium"):
        return PREMIUM_LIMITS.copy()
    return FREE_LIMITS.copy()


def activate_license(key):
    """Activate a premium license key."""
    if not key or not key.strip():
        return False, "License key cannot be empty."

    # NOTE: needs real Gumroad license verification API call
    data = _ensure_store()
    data["license_key"] = key.strip()
    data["tier"] = "premium"
    _save_store(data)
    return True, "License activated. Premium features unlocked."


def deactivate_license():
    """Remove the current license key."""
    data = _ensure_store()
    data["license_key"] = None
    data["tier"] = "free"
    _save_store(data)
    return True, "License deactivated."


def get_status():
    """Return a dict with full licensing status."""
    data = _ensure_store()
    tier = get_tier()
    first_run = data.get("first_run", time.time())
    elapsed_days = (time.time() - first_run) / 86400
    trial_remaining = max(0, TRIAL_DAYS - elapsed_days)

    return {
        "product": PRODUCT_NAME,
        "tier": tier,
        "trial_days_remaining": round(trial_remaining, 1) if tier == "trial" else 0,
        "license_key": bool(data.get("license_key")),
        "limits": get_limits(),
    }


def check_limit(feature, value=None):
    """Check if a feature/value is allowed under the current tier."""
    limits = get_limits()

    if feature == "cover_letter":
        if not limits.get("cover_letter"):
            return False, (
                "Cover letter generation requires Premium. "
                "Upgrade: https://tirandev.gumroad.com"
            )

    if feature == "linkedin_optimization":
        if not limits.get("linkedin_optimization"):
            return False, (
                "LinkedIn optimization requires Premium. "
                "Upgrade: https://tirandev.gumroad.com"
            )

    if feature == "ats_scoring":
        if not limits.get("ats_scoring"):
            return False, (
                "ATS scoring requires Premium. "
                "Upgrade: https://tirandev.gumroad.com"
            )

    if feature == "template" and value is not None:
        allowed = limits.get("templates", [])
        if value not in allowed:
            return False, (
                f"Template '{value}' requires Premium. "
                f"Free tier supports: {', '.join(allowed)}. "
                f"Upgrade: https://tirandev.gumroad.com"
            )

    return True, "OK"
