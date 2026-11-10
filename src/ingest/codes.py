"""Shared helper for Jolpica driver identity."""


def driver_code(driver: dict) -> str:
    """Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper when `code` is missing."""
    return driver.get("code") or driver["familyName"][:3].upper()
