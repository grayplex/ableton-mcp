"""Instrument profile catalog: auto-discovery and alias resolution.

Auto-discovers instrument profile modules via pkgutil.iter_modules.
Each module exposes a PROFILE dict constant with instrument data.
Normalizes and resolves aliases (spaces, hyphens, case).
"""

import importlib
import logging
import pkgutil
from typing import Dict, List, Optional

import MCP_Server.sounds as sounds_package

logger = logging.getLogger("AbletonMCPServer")

# Module-level registry populated on first access
_registry: Dict[str, dict] = {}
_alias_map: Dict[str, str] = {}
_initialized = False

# Infrastructure modules to skip during discovery
_SKIP_MODULES = {"catalog"}


def _normalize(name: str) -> str:
    """Normalize a name for lookup: lowercase, underscores for spaces/hyphens."""
    return name.lower().replace(" ", "_").replace("-", "_")


def _discover_profiles() -> None:
    """Scan sounds package for profile modules and register them.

    Skips modules starting with '_' and infrastructure modules.
    Logs and skips any module that fails to import or lacks a PROFILE constant.
    """
    global _initialized

    for finder, modname, ispkg in pkgutil.iter_modules(sounds_package.__path__):
        if modname.startswith("_") or modname in _SKIP_MODULES:
            continue

        try:
            mod = importlib.import_module(f"MCP_Server.sounds.{modname}")
        except Exception:
            logger.error("Failed to import sounds module '%s'", modname, exc_info=True)
            continue

        profile_data = getattr(mod, "PROFILE", None)
        if profile_data is None:
            logger.warning("Sounds module '%s' has no PROFILE constant, skipping", modname)
            continue

        profile_id = profile_data["id"]
        _registry[profile_id] = profile_data

        # Register canonical id
        _alias_map[_normalize(profile_id)] = profile_id
        # Register all aliases
        for alias in profile_data.get("aliases", []):
            _alias_map[_normalize(alias)] = profile_id

    _initialized = True


def _ensure_initialized() -> None:
    """Trigger auto-discovery if not yet done."""
    if not _initialized:
        _discover_profiles()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_profile(name: str) -> Optional[dict]:
    """Return full instrument profile by canonical id or alias.

    Normalizes the input name (lowercase, spaces/hyphens to underscores)
    and looks up in the alias map to find the canonical id.

    Returns:
        Profile dict if found, None otherwise.
    """
    _ensure_initialized()
    normalized = _normalize(name)
    canonical_id = _alias_map.get(normalized)
    if canonical_id is None:
        return None
    return _registry.get(canonical_id)


def list_profiles() -> List[dict]:
    """Return summary metadata for all discovered instrument profiles.

    Each entry has: id, name, aliases.
    """
    _ensure_initialized()
    return [
        {"id": p["id"], "name": p["name"], "aliases": p.get("aliases", [])}
        for p in _registry.values()
    ]
