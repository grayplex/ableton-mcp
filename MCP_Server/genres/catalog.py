"""Genre catalog: auto-discovery, alias resolution, and subgenre merge.

Per INFR-02: Auto-discovers genre modules via pkgutil.iter_modules.
Per INFR-03: Normalizes and resolves aliases (spaces, hyphens, case).
Per INFR-04: Shallow merge of subgenre overrides onto base genre.
Per D-08: Malformed genres logged and skipped, not a server crash.
"""

import copy
import importlib
import logging
import pkgutil
from typing import Any, Dict, List, Optional, Tuple, Union

import MCP_Server.genres as genres_package
from MCP_Server.genres.schema import validate_blueprint

logger = logging.getLogger("AbletonMCPServer")

# Module-level registry populated on first access
_registry: Dict[str, dict] = {}
_alias_map: Dict[str, Union[str, Tuple[str, str]]] = {}
_subgenres: Dict[str, Dict[str, dict]] = {}
_initialized = False

# Infrastructure modules to skip during discovery
_SKIP_MODULES = {"catalog", "schema"}


def _normalize_alias(alias: str) -> str:
    """Normalize an alias for lookup: lowercase, underscores for spaces/hyphens."""
    return alias.lower().replace(" ", "_").replace("-", "_")


def _discover_genres() -> None:
    """Scan genres package for genre modules, validate, and register them.

    Skips modules starting with '_' and infrastructure modules (catalog, schema).
    Logs and skips any module that fails validation.
    """
    global _initialized

    for finder, modname, ispkg in pkgutil.iter_modules(genres_package.__path__):
        if modname.startswith("_") or modname in _SKIP_MODULES:
            continue

        try:
            mod = importlib.import_module(f"MCP_Server.genres.{modname}")
        except Exception:
            logger.error("Failed to import genre module '%s'", modname, exc_info=True)
            continue

        genre_data = getattr(mod, "GENRE", None)
        if genre_data is None:
            logger.warning("Genre module '%s' has no GENRE constant, skipping", modname)
            continue

        try:
            validate_blueprint(genre_data)
        except ValueError as exc:
            logger.error(
                "Genre module '%s' failed validation: %s", modname, exc
            )
            continue

        genre_id = genre_data["id"]
        _registry[genre_id] = genre_data

        # Register base genre aliases
        _alias_map[_normalize_alias(genre_id)] = genre_id
        for alias in genre_data.get("aliases", []):
            _alias_map[_normalize_alias(alias)] = genre_id

        # Register subgenres
        subgenres_data = getattr(mod, "SUBGENRES", None)
        if subgenres_data and isinstance(subgenres_data, dict):
            _subgenres[genre_id] = subgenres_data
            for sub_id, sub_data in subgenres_data.items():
                # Map subgenre ID itself
                _alias_map[_normalize_alias(sub_id)] = (genre_id, sub_id)
                # Map subgenre aliases
                for alias in sub_data.get("aliases", []):
                    _alias_map[_normalize_alias(alias)] = (genre_id, sub_id)

    _initialized = True


def _ensure_initialized() -> None:
    """Trigger auto-discovery if not yet done."""
    if not _initialized:
        _discover_genres()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_genres() -> List[dict]:
    """Return metadata for all discovered genres.

    Each entry has: id, name, bpm_range, subgenres (list of subgenre IDs).
    Does NOT return full blueprint data.
    """
    _ensure_initialized()
    result = []
    for genre_id, genre_data in _registry.items():
        entry: Dict[str, Any] = {
            "id": genre_data["id"],
            "name": genre_data["name"],
            "bpm_range": genre_data["bpm_range"],
            "subgenres": list(_subgenres.get(genre_id, {}).keys()),
        }
        result.append(entry)
    return result


def resolve_alias(alias: str) -> Optional[dict]:
    """Resolve a genre or subgenre alias to its canonical IDs.

    Returns:
        {"genre_id": str} for a base genre match, or
        {"genre_id": str, "subgenre_id": str} for a subgenre match, or
        None if not found.
    """
    _ensure_initialized()
    normalized = _normalize_alias(alias)
    match = _alias_map.get(normalized)
    if match is None:
        return None
    if isinstance(match, tuple):
        return {"genre_id": match[0], "subgenre_id": match[1]}
    return {"genre_id": match}


def get_blueprint(
    genre_id: str, subgenre: Optional[str] = None
) -> Optional[dict]:
    """Return a full genre blueprint, optionally merged with a subgenre.

    Args:
        genre_id: Canonical ID or alias (e.g., "house", "deep house").
        subgenre: Optional subgenre ID (e.g., "deep_house"). If genre_id
            is itself a subgenre alias, the subgenre is auto-resolved.

    Returns:
        Complete blueprint dict with all 6 dimensions, or None if not found.
        Subgenre merge is shallow: each top-level key in the subgenre override
        replaces the base value entirely.
    """
    _ensure_initialized()

    # Try alias resolution first
    resolved = resolve_alias(genre_id)
    if resolved is None:
        return None

    base_genre_id = resolved["genre_id"]
    if subgenre is None and "subgenre_id" in resolved:
        subgenre = resolved["subgenre_id"]

    base = _registry.get(base_genre_id)
    if base is None:
        return None

    # Copy base to avoid mutating the registry
    result = copy.copy(base)
    result = {k: v for k, v in result.items()}

    if subgenre is not None:
        sub_overrides = _subgenres.get(base_genre_id, {}).get(subgenre)
        if sub_overrides is not None:
            for key, value in sub_overrides.items():
                result[key] = value

    return result
