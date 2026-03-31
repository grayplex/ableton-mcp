"""Instrument profile catalog: auto-discovery and alias resolution.

Auto-discovers instrument profile modules via pkgutil.iter_modules.
Each module exposes a PROFILE dict constant with instrument data.
Normalizes and resolves aliases (spaces, hyphens, case).
"""

import importlib
import logging
import pkgutil
import string
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


def list_descriptors() -> dict:
    """Return all supported descriptor tags grouped by axis.

    Tags are derived from the union of all registered instrument profiles'
    affinity keys. Both axes (role and character) are returned as sorted lists.

    Returns:
        Dict with keys 'role' and 'character', each containing a sorted list
        of descriptor tag strings.
    """
    _ensure_initialized()
    role_tags: set = set()
    character_tags: set = set()
    for profile in _registry.values():
        affinities = profile.get("descriptor_affinities", {})
        role_tags.update(affinities.get("role", {}).keys())
        character_tags.update(affinities.get("character", {}).keys())
    return {
        "role": sorted(role_tags),
        "character": sorted(character_tags),
    }


def recommend(descriptor: str) -> Optional[dict]:
    """Recommend the best-matching instrument for a descriptor string.

    Tokenizes the descriptor by whitespace, looks up each token in all
    instrument profiles' role and character affinities, sums matched weights,
    and returns the top-ranked instrument with browser path and reasoning.

    Args:
        descriptor: Natural-language descriptor, e.g. "warm pad" or "punchy kick"

    Returns:
        Dict with id, name, score, browser_path, category_hint, reasoning,
        or None if all instruments score 0 or no profiles are loaded.
    """
    _ensure_initialized()
    if not descriptor or not descriptor.strip():
        return None

    # Tokenize: lowercase, strip punctuation, split on whitespace
    tokens = [
        t.strip(string.punctuation)
        for t in descriptor.lower().split()
    ]
    tokens = [t for t in tokens if t]
    if not tokens:
        return None

    # Score each instrument by summing matched affinity weights
    scored: List[tuple] = []
    for profile_id, profile in _registry.items():
        total = 0.0
        affinities = profile.get("descriptor_affinities", {})
        role_aff = affinities.get("role", {})
        char_aff = affinities.get("character", {})
        for token in tokens:
            total += role_aff.get(token, 0.0)
            total += char_aff.get(token, 0.0)
        scored.append((total, profile_id))

    # Sort by score descending, then by id ascending for stable tie-breaking
    scored.sort(key=lambda x: (-x[0], x[1]))
    best_score, best_id = scored[0]

    if best_score == 0.0:
        return None

    profile = _registry[best_id]
    browser = profile.get("browser", {})
    browser_root = browser.get("root", "")
    categories = browser.get("categories", {})

    # Derive category hint from first role token that has a mapping
    category_hint = ""
    for token in tokens:
        if token in categories:
            category_hint = categories[token]
            break
    if not category_hint and categories:
        category_hint = next(iter(categories.values()))

    # Build reasoning string
    strengths = profile.get("strengths", [])
    top_strength = strengths[0] if strengths else profile.get("name", best_id)
    reasoning = (
        f"Best match for '{descriptor}': {profile['name']} scores "
        f"{best_score:.2f} — {top_strength}"
    )

    return {
        "id": best_id,
        "name": profile["name"],
        "score": best_score,
        "browser_path": browser_root,
        "category_hint": category_hint,
        "reasoning": reasoning,
    }
