"""Device parameter catalog and mixing role taxonomy."""

from .catalog import CATALOG, ROLES


def get_catalog_entry(device_name: str):
    """Look up a device by class name or display name. Returns dict or None."""
    entry = CATALOG.get(device_name)
    if entry is not None:
        return entry
    for class_name, data in CATALOG.items():
        if data["display_name"].lower() == device_name.lower():
            return data
    return None


def get_roles():
    """Return the canonical role list."""
    return list(ROLES)


__all__ = ["CATALOG", "ROLES", "get_catalog_entry", "get_roles"]
