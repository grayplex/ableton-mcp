# Phase 35: Package Skeleton and First Profile - Research

**Researched:** 2026-03-31
**Domain:** Python package structure, pkgutil auto-discovery, instrument profile data modeling
**Confidence:** HIGH

## Summary

This phase creates `MCP_Server/sounds/` as a new peer package mirroring the established `genres/` and `mixing/` patterns. The project already has two working examples of pkgutil auto-discovery catalogs (genres/catalog.py and mixing/catalog.py) with alias normalization, lazy initialization, and module-level registries. The sounds package follows the identical pattern with a simpler data shape (no subgenres, no schema validation in this phase per D-02).

The Wavetable profile is the first instrument profile, serving as the reference implementation. Its browser path (`Instruments/Wavetable`) must be validated against a live Ableton session using the existing `get_browser_items_at_path` MCP tool. Per D-06, validation failure logs a warning but does not block -- profiles work without live Ableton.

**Primary recommendation:** Clone the genres/catalog.py discovery pattern exactly, simplify by removing subgenre/schema logic, and add a `get_profile()` public API that returns None for unknown instruments (D-09).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Descriptor affinities use a two-axis dict structure: `{"role": {"pad": 0.9, "lead": 0.6}, "character": {"warm": 0.8, "evolving": 0.9}}` with 0.0-1.0 weights per tag
- **D-02:** No schema version or type marker -- minimal PROFILE dict constant (like GENRE/RECIPE), add validation later if needed
- **D-03:** Strengths and weaknesses are short phrase lists: `["lush evolving pads", "wavetable morphing", "complex textures"]`
- **D-04:** Sonic character is a single string paragraph describing the instrument's identity
- **D-05:** Browser paths stored as root path + categories dict: `{"root": "Instruments/Wavetable", "categories": {"pad": "Pads", "lead": "Leads", "bass": "Bass"}}`
- **D-06:** Validation failure logs a warning but keeps the path -- profiles work without live Ableton
- **D-07:** Only the instrument root path is validated against live Ableton; category sub-paths are best-effort hints (vary by Live edition/installed packs)
- **D-08:** Short abbreviations supported via aliases list in each profile (e.g., `["wavetable", "wt"]`), same pattern as genre blueprints
- **D-09:** `catalog.get_profile()` returns `None` for unknown instrument names -- matches mixing/catalog pattern
- **D-10:** Display names accepted via normalization (case-insensitive, whitespace/hyphen to underscore) -- `"Wavetable"`, `"wavetable"`, `"wave table"` all resolve

### Claude's Discretion
No areas explicitly deferred to Claude's discretion in this phase.

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PKG-01 | `sounds/` peer package with pkgutil auto-discovery catalog (mirrors `genres/` and `mixing/` structure) -- zero-registration, one file per instrument | genres/catalog.py and mixing/catalog.py provide exact patterns to clone; _discover_profiles() follows _discover_genres() structure |
| INST-01 | Claude can retrieve the Wavetable instrument profile -- sonic character, strengths/weaknesses, descriptor affinities, and browser category paths validated against live Ableton | Profile data shape defined by D-01 through D-05; browser validation uses existing get_browser_items_at_path tool; D-06/D-07 define graceful degradation |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `pkgutil` | 3.11 | Auto-discovery of profile modules | Already used by genres/ and mixing/ catalogs |
| Python stdlib `importlib` | 3.11 | Dynamic import of discovered modules | Already used by genres/ and mixing/ catalogs |
| Python stdlib `logging` | 3.11 | Warning on browser path validation failure | Already used project-wide |

### Supporting
No additional libraries needed. This phase is pure Python data + stdlib.

**Installation:**
```bash
# No new dependencies required
```

## Architecture Patterns

### Recommended Project Structure
```
MCP_Server/sounds/
    __init__.py        # Package init with public API re-exports
    catalog.py         # Auto-discovery, alias resolution, get_profile()
    wavetable.py       # First instrument profile (PROFILE dict constant)
```

### Pattern 1: pkgutil Auto-Discovery (clone from genres/catalog.py)
**What:** On first access, scan the package directory for Python modules, import each, extract the `PROFILE` dict constant, and register it in a module-level `_registry` dict keyed by instrument ID.
**When to use:** Every catalog in this project uses this pattern.
**Example:**
```python
# Source: MCP_Server/genres/catalog.py (lines 35-85)
import importlib
import pkgutil
import MCP_Server.sounds as sounds_package

_registry: dict[str, dict] = {}
_alias_map: dict[str, str] = {}
_initialized = False
_SKIP_MODULES = {"catalog"}

def _normalize(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")

def _discover_profiles() -> None:
    global _initialized
    for finder, modname, ispkg in pkgutil.iter_modules(sounds_package.__path__):
        if modname.startswith("_") or modname in _SKIP_MODULES:
            continue
        try:
            mod = importlib.import_module(f"MCP_Server.sounds.{modname}")
        except Exception:
            logger.error("Failed to import profile module '%s'", modname, exc_info=True)
            continue
        profile = getattr(mod, "PROFILE", None)
        if profile is None:
            logger.warning("Profile module '%s' has no PROFILE constant, skipping", modname)
            continue
        inst_id = profile["id"]
        _registry[inst_id] = profile
        _alias_map[_normalize(inst_id)] = inst_id
        for alias in profile.get("aliases", []):
            _alias_map[_normalize(alias)] = inst_id
    _initialized = True
```

### Pattern 2: PROFILE Dict Constant (data module)
**What:** Each instrument file exports a single `PROFILE` dict with all profile data. No classes, no functions.
**When to use:** Every data module in genres/ and mixing/ uses this pattern.
**Example:**
```python
# MCP_Server/sounds/wavetable.py
PROFILE = {
    "id": "wavetable",
    "name": "Wavetable",
    "aliases": ["wavetable", "wt"],
    "sonic_character": "Wavetable is Ableton's modern wavetable synthesizer...",
    "strengths": ["lush evolving pads", "wavetable morphing", "complex textures"],
    "weaknesses": ["less suited for simple analog-style sounds", "..."],
    "descriptor_affinities": {
        "role": {"pad": 0.9, "lead": 0.6, "bass": 0.5, "texture": 0.85},
        "character": {"warm": 0.8, "evolving": 0.9, "bright": 0.6, "dark": 0.5},
    },
    "browser": {
        "root": "Instruments/Wavetable",
        "categories": {"pad": "Pads", "lead": "Leads", "bass": "Bass"},
    },
}
```

### Pattern 3: Package __init__.py (public API re-exports)
**What:** The `__init__.py` re-exports public functions from catalog.py, matching genres/ and mixing/ patterns.
**Example:**
```python
# MCP_Server/sounds/__init__.py
"""Instrument profile library: sonic character and browser paths for Ableton instruments."""

from .catalog import get_profile, list_profiles

__all__ = ["get_profile", "list_profiles"]
```

### Anti-Patterns to Avoid
- **Adding schema validation in this phase:** D-02 explicitly defers this. Keep it simple -- just a dict constant.
- **Using classes for profiles:** The project convention is pure dicts (D-01 through D-04).
- **Hardcoding profiles in catalog.py:** The whole point of pkgutil discovery is zero-registration. One file per instrument.
- **Raising exceptions for unknown instruments:** D-09 says return None, matching mixing/catalog pattern.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Module discovery | Manual import list | `pkgutil.iter_modules` | Automatic, zero-registration, proven in genres/ and mixing/ |
| Alias normalization | Custom regex parser | `str.lower().replace()` chain | Simple, already used in `_normalize_alias()` in genres/catalog.py |
| Browser path validation | Custom HTTP client | Existing `get_browser_items_at_path` MCP tool | Already implemented in tools/browser.py, talks to Ableton |

**Key insight:** This phase creates zero new patterns -- it clones two existing catalogs with a different data shape.

## Common Pitfalls

### Pitfall 1: Forgetting pyproject.toml packages list
**What goes wrong:** If `MCP_Server.sounds` is added to `[tool.setuptools] packages`, it breaks consistency since `MCP_Server.genres`, `MCP_Server.mixing`, and `MCP_Server.devices` are also NOT listed there. The project works in development mode without explicit package listing for sub-packages.
**Why it happens:** Instinct to register every package.
**How to avoid:** Do NOT add to pyproject.toml packages list. The existing genres/mixing/devices packages are not listed and work fine.
**Warning signs:** If you edit pyproject.toml, something is wrong.

### Pitfall 2: Browser path format mismatch
**What goes wrong:** The browser path string format passed to `get_browser_items_at_path` does not match what Ableton expects.
**Why it happens:** Ableton's browser uses forward-slash-separated paths, but the exact root category name matters (e.g., "Instruments" vs "instruments" vs "Sounds").
**How to avoid:** Validate the root path against live Ableton (D-07). The `get_browser_items_at_path` tool returns available categories on error, which reveals the correct names.
**Warning signs:** Error response with "available_categories" in the result.

### Pitfall 3: Registry state leaking between tests
**What goes wrong:** Module-level `_registry`, `_alias_map`, `_initialized` persist across test runs, causing test ordering dependencies.
**Why it happens:** Python module globals survive across test functions.
**How to avoid:** Either test against the already-initialized state (how test_genres.py and test_mixing.py do it -- they test the real discovered data) or add a `_reset()` function for testing. The existing tests do NOT reset state; they test the real registry.
**Warning signs:** Tests pass individually but fail in suite.

### Pitfall 4: Circular imports from __init__.py
**What goes wrong:** If `__init__.py` imports from `catalog.py` which imports the package itself via `import MCP_Server.sounds as sounds_package`, it can cause issues.
**Why it happens:** Python import machinery resolves package `__init__.py` before submodules.
**How to avoid:** Follow the exact same import pattern as genres/catalog.py line 8: `import MCP_Server.sounds as sounds_package`. This works because pkgutil only needs `__path__` which is set early in `__init__.py` processing. The genres/ and mixing/ packages prove this works.

## Code Examples

### Complete catalog.py structure (verified from genres/catalog.py and mixing/catalog.py)
```python
"""Instrument profile catalog: auto-discovery and alias resolution.

Per PKG-01: Auto-discovers profile modules via pkgutil.iter_modules.
Per D-08/D-10: Normalizes aliases (case-insensitive, whitespace/hyphen-tolerant).
"""

import importlib
import logging
import pkgutil
from typing import Dict, List, Optional

import MCP_Server.sounds as sounds_package

logger = logging.getLogger("AbletonMCPServer")

_registry: Dict[str, dict] = {}
_alias_map: Dict[str, str] = {}
_initialized = False
_SKIP_MODULES = {"catalog"}


def _normalize(name: str) -> str:
    """Normalize a name for lookup: lowercase, underscores for spaces/hyphens."""
    return name.lower().replace(" ", "_").replace("-", "_")


def _discover_profiles() -> None:
    """Scan sounds package for profile modules and register them."""
    global _initialized
    for finder, modname, ispkg in pkgutil.iter_modules(sounds_package.__path__):
        if modname.startswith("_") or modname in _SKIP_MODULES:
            continue
        try:
            mod = importlib.import_module(f"MCP_Server.sounds.{modname}")
        except Exception:
            logger.error("Failed to import profile module '%s'", modname, exc_info=True)
            continue
        profile = getattr(mod, "PROFILE", None)
        if profile is None:
            logger.warning("Profile module '%s' has no PROFILE constant, skipping", modname)
            continue
        inst_id = profile["id"]
        _registry[inst_id] = profile
        _alias_map[_normalize(inst_id)] = inst_id
        for alias in profile.get("aliases", []):
            _alias_map[_normalize(alias)] = inst_id
    _initialized = True


def _ensure_initialized() -> None:
    if not _initialized:
        _discover_profiles()


def get_profile(name: str) -> Optional[dict]:
    """Return instrument profile by name/alias, or None if not found."""
    _ensure_initialized()
    normalized = _normalize(name)
    inst_id = _alias_map.get(normalized)
    if inst_id is None:
        return None
    return _registry.get(inst_id)


def list_profiles() -> List[dict]:
    """Return summary metadata for all discovered instrument profiles."""
    _ensure_initialized()
    return [
        {"id": p["id"], "name": p["name"], "aliases": p.get("aliases", [])}
        for p in _registry.values()
    ]
```

### PROFILE dict shape (from decisions D-01 through D-05)
```python
PROFILE = {
    "id": "wavetable",
    "name": "Wavetable",
    "aliases": ["wavetable", "wt"],
    "sonic_character": "A single string paragraph...",
    "strengths": ["phrase 1", "phrase 2"],
    "weaknesses": ["phrase 1", "phrase 2"],
    "descriptor_affinities": {
        "role": {"pad": 0.9, "lead": 0.6},
        "character": {"warm": 0.8, "evolving": 0.9},
    },
    "browser": {
        "root": "Instruments/Wavetable",
        "categories": {"pad": "Pads", "lead": "Leads", "bass": "Bass"},
    },
}
```

### Browser path validation pattern
```python
# In a live UAT or manual test -- call via MCP tool
# get_browser_items_at_path(path="Instruments/Wavetable")
# Success: returns list of presets/categories
# Failure: returns error with available_categories list

# Per D-06: log warning but keep the path
import logging
logger = logging.getLogger("AbletonMCPServer")

def validate_browser_path(root_path: str) -> bool:
    """Validate browser path against live Ableton. Returns True if valid."""
    # This is a MANUAL validation step, not automated code
    # Run: get_browser_items_at_path(path=root_path) via MCP
    # If it returns items, the path is valid
    # If it returns error, log warning per D-06
    pass
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual import registration | pkgutil.iter_modules auto-discovery | Project v1.0 (genres/) | Zero-touch adding of new instruments -- just add a .py file |

**Deprecated/outdated:**
- Nothing -- this is all established project patterns, not external dependencies.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/test_sounds.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-01 | pkgutil discovers wavetable module | unit | `pytest tests/test_sounds.py::TestAutoDiscovery -x` | No -- Wave 0 |
| PKG-01 | catalog skips infrastructure modules | unit | `pytest tests/test_sounds.py::TestAutoDiscovery::test_skip_modules -x` | No -- Wave 0 |
| INST-01 | get_profile("wavetable") returns complete dict | unit | `pytest tests/test_sounds.py::TestGetProfile -x` | No -- Wave 0 |
| INST-01 | alias normalization (case, whitespace, abbreviation) | unit | `pytest tests/test_sounds.py::TestAliasResolution -x` | No -- Wave 0 |
| INST-01 | PROFILE has all required keys (sonic_character, strengths, weaknesses, descriptor_affinities, browser) | unit | `pytest tests/test_sounds.py::TestProfileShape -x` | No -- Wave 0 |
| INST-01 | descriptor_affinities has role and character axes with 0.0-1.0 weights | unit | `pytest tests/test_sounds.py::TestProfileShape::test_affinity_weights_range -x` | No -- Wave 0 |
| INST-01 | get_profile returns None for unknown instrument | unit | `pytest tests/test_sounds.py::TestGetProfile::test_unknown_returns_none -x` | No -- Wave 0 |
| INST-01 | browser root path validated against live Ableton | manual-only | Manual: call `get_browser_items_at_path("Instruments/Wavetable")` via MCP | N/A |

### Sampling Rate
- **Per task commit:** `pytest tests/test_sounds.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_sounds.py` -- covers PKG-01 and INST-01 (auto-discovery, profile shape, alias resolution, get_profile API)
- [ ] No new conftest fixtures needed -- sounds/ catalog is pure data, no MCP mock required

## Open Questions

1. **Exact Ableton browser root path for Wavetable**
   - What we know: Likely `Instruments/Wavetable` based on Ableton Live Suite conventions
   - What's unclear: The exact string Ableton returns -- could be `Instruments/Wavetable` or `Sounds/Instruments/Wavetable` or similar
   - Recommendation: Validate against live Ableton during implementation. Per D-06, if validation fails, log warning and keep the assumed path. The `get_browser_items_at_path` error response reveals available categories.

2. **Wavetable preset category names**
   - What we know: Common categories include Pads, Leads, Bass, Keys, etc.
   - What's unclear: Exact category folder names in the browser (varies by Live edition and installed packs)
   - Recommendation: Per D-07, sub-categories are best-effort hints. Use standard names and accept they may vary.

## Sources

### Primary (HIGH confidence)
- `MCP_Server/genres/catalog.py` -- Complete pkgutil auto-discovery pattern, alias normalization, lazy init
- `MCP_Server/genres/__init__.py` -- Package init re-export pattern
- `MCP_Server/genres/techno.py` -- Data module structure (GENRE dict constant)
- `MCP_Server/mixing/catalog.py` -- Second auto-discovery catalog implementation, confirms pattern
- `MCP_Server/mixing/__init__.py` -- Second package init, confirms pattern
- `MCP_Server/tools/browser.py` -- `get_browser_items_at_path` implementation for path validation
- `tests/test_genres.py` -- Test patterns for catalog auto-discovery
- `tests/test_mixing.py` -- Test patterns for catalog auto-discovery with mocking
- `pyproject.toml` -- Build config, test config, linting rules

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- No external dependencies, pure Python stdlib already used in project
- Architecture: HIGH -- Exact pattern cloned from two working catalogs (genres/, mixing/)
- Pitfalls: HIGH -- All pitfalls derived from direct code inspection of existing patterns
- Profile data shape: HIGH -- All decisions locked in CONTEXT.md (D-01 through D-10)
- Browser path validation: MEDIUM -- Exact path strings depend on live Ableton session

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable -- pure Python patterns, no external dependencies)
