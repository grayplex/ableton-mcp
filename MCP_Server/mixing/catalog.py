"""Mixing recipe catalog: auto-discovery, alias resolution, and recipe lookup.

Per D-05: Auto-discovers recipe modules via pkgutil.iter_modules.
Per D-06: Resolves role and genre aliases (spaces, hyphens, case).
"""

import importlib
import logging
import pkgutil
from typing import Dict, List, Optional

import MCP_Server.mixing as mixing_package

logger = logging.getLogger("AbletonMCPServer")

# Module-level registry populated on first access
_registry: Dict[str, dict] = {}  # genre_id -> RECIPE dict
_master_registry: Dict[str, dict] = {}  # genre_id -> MASTER_RECIPE dict
_alias_map: Dict[str, str] = {}  # normalized genre alias -> genre_id
_initialized = False

# Infrastructure modules to skip during discovery
_SKIP_MODULES = {"catalog"}

# Role aliases: common alternative names -> canonical role
_ROLE_ALIASES: Dict[str, str] = {
    "kick_drum": "kick",
    "bass_line": "bass",
    "bassline": "bass",
    "synth_lead": "lead",
    "synth_pad": "pad",
    "chord": "chords",
    "vox": "vocal",
    "vocals": "vocal",
    "atmo": "atmospheric",
    "atmosphere": "atmospheric",
    "fx": "atmospheric",
    "bus": "return",
    "send": "return",
    "master_bus": "master",
}

# Genre aliases: common abbreviations -> canonical genre_id
_GENRE_ALIASES: Dict[str, str] = {
    "dnb": "drum_and_bass",
    "d_n_b": "drum_and_bass",
    "d&b": "drum_and_bass",
    "jungle": "drum_and_bass",
    "hip_hop": "hip_hop_trap",
    "r_b": "neo_soul_rnb",
}


def _normalize(name: str) -> str:
    """Normalize a name for lookup: lowercase, underscores for spaces/hyphens."""
    return name.lower().replace(" ", "_").replace("-", "_").replace("&", "_")


def _discover_recipes() -> None:
    """Scan mixing package for recipe modules and register them.

    Skips modules starting with '_' and infrastructure modules.
    Logs and skips any module that fails to import or lacks RECIPE.
    """
    global _initialized

    for finder, modname, ispkg in pkgutil.iter_modules(mixing_package.__path__):
        if modname.startswith("_") or modname in _SKIP_MODULES:
            continue

        try:
            mod = importlib.import_module(f"MCP_Server.mixing.{modname}")
        except Exception:
            logger.error(
                "Failed to import recipe module '%s'", modname, exc_info=True
            )
            continue

        recipe_data = getattr(mod, "RECIPE", None)
        if recipe_data is None:
            logger.warning(
                "Recipe module '%s' has no RECIPE constant, skipping", modname
            )
            continue

        _registry[modname] = recipe_data
        _alias_map[modname] = modname

        # Also check for MASTER_RECIPE (master bus chain)
        master_data = getattr(mod, "MASTER_RECIPE", None)
        if master_data is not None:
            _master_registry[modname] = master_data

    _initialized = True


def _ensure_initialized() -> None:
    """Trigger auto-discovery if not yet done."""
    if not _initialized:
        _discover_recipes()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_recipe(role: str, genre: str) -> Optional[dict]:
    """Get a mix recipe for a role in a genre.

    Args:
        role: Mixing role (kick, bass, lead, etc.) or alias.
        genre: Genre ID (house, techno, etc.) or alias.

    Returns:
        Dict of device_class -> param_dict for the role, or None if not found.
    """
    _ensure_initialized()

    # Resolve genre: try alias_map first (discovered genres), then hardcoded aliases
    norm_genre = _normalize(genre)
    genre_id = _alias_map.get(norm_genre) or _GENRE_ALIASES.get(norm_genre)
    if genre_id is None or genre_id not in _registry:
        return None

    # Resolve role alias
    norm_role = _normalize(role)
    resolved_role = _ROLE_ALIASES.get(norm_role, norm_role)

    recipe = _registry[genre_id]
    return recipe.get(resolved_role)


def get_master_recipe(genre: str) -> Optional[dict]:
    """Get master bus recipe for a genre.

    Args:
        genre: Genre ID (house, techno, etc.) or alias.

    Returns:
        Dict of device_class -> param_dict, or None if not found.
    """
    _ensure_initialized()
    norm_genre = _normalize(genre)
    genre_id = _alias_map.get(norm_genre) or _GENRE_ALIASES.get(norm_genre)
    if genre_id is None or genre_id not in _master_registry:
        return None
    return _master_registry[genre_id]


def list_recipes() -> List[str]:
    """Return sorted list of discovered genre recipe IDs."""
    _ensure_initialized()
    return sorted(_registry.keys())
