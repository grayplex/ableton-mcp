# Phase 30: Core Mix Recipes - Research

**Researched:** 2026-03-28
**Domain:** Static mix recipe data + MCP tool + pkgutil auto-discovery
**Confidence:** HIGH

## Summary

Phase 30 is a pure data + query tool phase with no Remote Script changes. The work consists of: (1) creating a `MCP_Server/mixing/` package with one recipe file per genre, (2) a catalog module mirroring the genres auto-discovery pattern, (3) a single MCP tool `get_mix_recipe`, and (4) validation tests ensuring all recipe parameter names exist in the device catalog.

The 4 genres (house, techno, ambient, drum_and_bass) each need 9 role entries, and each role maps to a subset of the 12 catalog devices with natural-unit parameter values. The data volume is significant (4 genres x 9 roles x variable devices per role) but the architecture is straightforward -- it mirrors the established `MCP_Server/genres/` pattern exactly.

**Primary recommendation:** Mirror the genres package structure verbatim -- one `RECIPE` constant per genre file, `catalog.py` with pkgutil discovery, `__init__.py` exposing `get_recipe()`. Validate every recipe parameter name against `CATALOG` at import time or test time.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Parameter values stored in natural units (Hz, dB, ms, %), not normalized 0.0-1.0
- D-02: Recipes cover all sound-shaping parameters; exclude Device On, LegacyMode, model selectors, and non-sound-shaping housekeeping params
- D-03: All 9 roles authored for every genre; non-typical combos get safe generic values
- D-04: When a role/genre doesn't use a device, omit that device entirely from the recipe (no None markers)
- D-05: Auto-discovery via pkgutil pattern matching genres; one file per genre with RECIPE constant
- D-06: One new MCP tool: get_mix_recipe(role, genre) returning JSON; supports role/genre aliases

### Claude's Discretion
- Which catalog parameters are "sound-shaping" vs. "housekeeping" per device
- Exact natural-unit values for each role/genre combination
- Whether RECIPE lives in recipes/ subdirectory or directly in MCP_Server/mixing/
- Internal structure of mixing catalog (validation on import vs. query time)
- Whether get_mix_recipe returns full device spec or summary

### Deferred Ideas (OUT OF SCOPE)
- list_mix_recipes() MCP tool
- Master bus recipes (MSTR-01) -- Phase 34
- Recipe quality gate / token budget check
- Sidechain routing hints in recipes
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RECIP-01 | User can retrieve a role x genre mix recipe for any of the 4 core genres (house, techno, ambient, DnB) -- returns EQ, compression, reverb/delay, panning, and dynamics parameter values for the specified role | Mixing catalog with pkgutil discovery, get_recipe() API, get_mix_recipe MCP tool, 4 genre recipe files with 9 roles each |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib pkgutil | 3.10+ | Auto-discovery of recipe modules | Same pattern as genres/catalog.py; zero dependencies |
| Python stdlib importlib | 3.10+ | Dynamic import of discovered recipe modules | Same pattern as genres/catalog.py |
| Python stdlib json | 3.10+ | Serialize recipe output in MCP tool | Same as all other MCP tools |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | existing | Validate recipe param names against CATALOG | Test suite |
| mcp.server.fastmcp | existing | @mcp.tool() decorator for get_mix_recipe | MCP tool registration |

No new packages needed. This phase uses only existing project dependencies.

## Architecture Patterns

### Recommended Project Structure
```
MCP_Server/
  mixing/
    __init__.py          # Public API: get_recipe(), list_recipes()
    catalog.py           # pkgutil auto-discovery, alias resolution, registry
    house.py             # RECIPE constant for house genre
    techno.py            # RECIPE constant for techno genre
    ambient.py           # RECIPE constant for ambient genre
    drum_and_bass.py     # RECIPE constant for DnB genre
  tools/
    mixing.py            # get_mix_recipe MCP tool (new file)
    __init__.py          # Updated to import mixing module
```

**Rationale for `MCP_Server/mixing/` (not `MCP_Server/mixing/recipes/` subdirectory):** Placing recipe files directly in `mixing/` mirrors the `genres/` package exactly. The genres package has `genres/house.py`, `genres/techno.py` etc. -- mixing should have `mixing/house.py`, `mixing/techno.py`. An extra `recipes/` subdirectory adds nesting without benefit.

### Pattern 1: Recipe Data Module
**What:** Each genre file exports a single `RECIPE` dict constant
**When to use:** Every genre recipe file
**Example:**
```python
# MCP_Server/mixing/house.py
# Source: mirrors MCP_Server/genres/house.py pattern (GENRE constant)

RECIPE = {
    "kick": {
        "Eq8": {
            "1 Filter On A": 1,      # Enable band 1
            "1 Filter Type A": 3,    # Bell
            "1 Frequency A": 60,     # Hz - boost fundamental
            "1 Gain A": 2.0,         # dB
            "1 Resonance A": 0.7,
            "2 Filter On A": 1,
            "2 Filter Type A": 1,    # Low cut
            "2 Frequency A": 30,     # Hz - remove sub rumble
        },
        "Compressor2": {
            "Threshold": -18,        # dB
            "Ratio": 4.0,
            "Attack": 10,            # ms
            "Release": 80,           # ms
            "Makeup": 0,             # dB - use Output Gain if needed
            "Dry/Wet": 1.0,          # 100%
            "Knee": 0.5,
        },
        "StereoGain": {
            "Gain": 0,               # dB
            "Stereo Width": 0.0,     # Mono for kick
            "Bass Mono": 1,
            "Bass Freq": 120,        # Hz
        },
    },
    "bass": {
        # ... device params ...
    },
    # ... 7 more roles ...
}
```

### Pattern 2: Auto-Discovery Catalog (mirror genres/catalog.py)
**What:** Module-level registry populated on first access via pkgutil
**When to use:** `MCP_Server/mixing/catalog.py`
**Example:**
```python
# Source: mirrors MCP_Server/genres/catalog.py

import importlib
import logging
import pkgutil
from typing import Dict, List, Optional

import MCP_Server.mixing as mixing_package

logger = logging.getLogger("AbletonMCPServer")

_registry: Dict[str, dict] = {}  # genre_id -> RECIPE dict
_alias_map: Dict[str, str] = {}  # normalized alias -> genre_id
_initialized = False
_SKIP_MODULES = {"catalog"}

# Role aliases: "kick drum" -> "kick", etc.
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

# Genre aliases
_GENRE_ALIASES: Dict[str, str] = {
    "drum_and_bass": "drum_and_bass",
    "dnb": "drum_and_bass",
    "d_n_b": "drum_and_bass",
    "d&b": "drum_and_bass",
    "jungle": "drum_and_bass",
}

def _normalize(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_").replace("&", "_")

def _discover_recipes() -> None:
    global _initialized
    for finder, modname, ispkg in pkgutil.iter_modules(mixing_package.__path__):
        if modname.startswith("_") or modname in _SKIP_MODULES:
            continue
        try:
            mod = importlib.import_module(f"MCP_Server.mixing.{modname}")
        except Exception:
            logger.error("Failed to import recipe module '%s'", modname, exc_info=True)
            continue
        recipe_data = getattr(mod, "RECIPE", None)
        if recipe_data is None:
            logger.warning("Recipe module '%s' has no RECIPE constant, skipping", modname)
            continue
        _registry[modname] = recipe_data
        _alias_map[modname] = modname
    _initialized = True

def _ensure_initialized() -> None:
    if not _initialized:
        _discover_recipes()

def get_recipe(role: str, genre: str) -> Optional[dict]:
    _ensure_initialized()
    # resolve genre alias
    norm_genre = _normalize(genre)
    genre_id = _alias_map.get(norm_genre) or _GENRE_ALIASES.get(norm_genre)
    if genre_id is None or genre_id not in _registry:
        return None
    # resolve role alias
    norm_role = _normalize(role)
    resolved_role = _ROLE_ALIASES.get(norm_role, norm_role)
    recipe = _registry[genre_id]
    return recipe.get(resolved_role)
```

### Pattern 3: MCP Tool (mirror tools/catalog.py)
**What:** Single tool wrapping the catalog API
**When to use:** `MCP_Server/tools/mixing.py`
**Example:**
```python
# Source: mirrors MCP_Server/tools/catalog.py pattern

import json
from mcp.server.fastmcp import Context
from MCP_Server.connection import format_error
from MCP_Server.server import mcp
from MCP_Server.mixing.catalog import get_recipe

@mcp.tool()
def get_mix_recipe(ctx: Context, role: str, genre: str) -> str:
    """Get mix recipe for a role in a genre. Returns device parameter values
    (EQ, compression, reverb/delay, panning, dynamics) in natural units.

    Parameters:
    - role: Mixing role (kick, bass, lead, pad, chords, vocal, atmospheric, return, master)
    - genre: Genre (house, techno, ambient, dnb/drum_and_bass)
    """
    result = get_recipe(role, genre)
    if result is None:
        return format_error(
            f"No recipe found for role='{role}', genre='{genre}'",
            suggestion="Roles: kick, bass, lead, pad, chords, vocal, atmospheric, return, master. "
                       "Genres: house, techno, ambient, dnb",
        )
    return json.dumps(result, indent=2)
```

### Anti-Patterns to Avoid
- **Registering recipes manually:** Do not add recipe modules to a hardcoded list. pkgutil discovery handles this.
- **Normalized values in recipes:** All values MUST be in natural units per D-01. Phase 31 handles conversion.
- **None markers for omitted devices:** Per D-04, simply omit the device key. No `"Reverb": None`.
- **Including Device On in recipes:** Per D-02, Device On is housekeeping. Phase 31 sets it to 1 when loading a device.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Module auto-discovery | Manual registry of recipe files | pkgutil.iter_modules (same as genres) | Zero-registration pattern already proven in codebase |
| Alias normalization | Complex fuzzy matching | Simple lowercase + underscore normalization (same as genres) | Consistent with existing codebase pattern |
| Error formatting | Custom error strings | format_error() from connection.py | Consistent MCP error format |

## Sound-Shaping vs. Housekeeping Parameter Classification

This is Claude's Discretion per CONTEXT.md. Below is the recommended classification based on the catalog.

### Housekeeping Parameters (EXCLUDE from recipes)
These do not meaningfully affect audio output:

| Device | Parameters to Exclude |
|--------|-----------------------|
| ALL devices | `Device On` (index 0 on every device) |
| Compressor2 | `S/C Listen` (monitoring only), `Model` (visual/character but keep if it affects sound -- discretion), `Env Mode` |
| Reverb | `Freeze On`, `Flat On`, `Cut On` (these are momentary toggles, not recipe values) |
| Delay | `Delay Mode`, `Link`, `L Sync`, `R Sync`, `Freeze` |
| Gate | `S/C Listen`, `FlipMode`, `LookAhead` |
| Limiter | `Auto`, `Link`, `M/S Link`, `Lookahead`, `Routing`, `Mode`, `Maximize On` |
| AutoFilter2 | `LFO T Mode`, `LFO S Mode`, `LFO Q Mode`, `Env Hold On`, `Env S&H On`, `Soft Clip On` |
| MultibandDynamics | `Soft Knee On/Off`, `Peak/RMS Mode` |
| DrumBuss | `Boom Audition` (monitoring only) |
| MxDeviceAudioEffect | `Delay Mode`, `Sidechain` |

### Sound-Shaping Parameters (INCLUDE in recipes)
Everything else -- frequencies, gains, ratios, thresholds, times, wet/dry, widths, etc.

**Important notes on classification edge cases:**
- `Compressor2.Model` (Peak/Opto/etc): Affects sound character. Recommend INCLUDING.
- `Compressor2.Env Mode`: Peak vs. RMS detection -- affects compression behavior. Recommend INCLUDING.
- `Limiter.Mode`: Legacy vs. new algorithm -- affects sound. Could include; but master limiter is Phase 34.
- Filter Type/Slope params (Eq8 Filter Type, AutoFilter Type/Slope): These affect sound. INCLUDE.
- `S/C On`, `S/C Gain`, `S/C Mix`, `S/C EQ *`: Sidechain config -- defer to Phase 31 (SIDE-01). EXCLUDE from recipes.
- Band Activator params in MultibandDynamics: These enable/disable bands. INCLUDE because they define which bands are active.
- Filter On params in Eq8 (`1 Filter On A` etc.): These enable/disable bands. INCLUDE because they define which EQ bands are active.

### Per-Device Recipe Parameter Summary

| Device (class name) | Typical recipe params | Count |
|----------------------|----------------------|-------|
| Eq8 | Output Gain, Scale, Adaptive Q, N x (Filter On A, Filter Type A, Frequency A, Gain A, Resonance A) for used bands | ~5-25 per role (1-5 bands) |
| Compressor2 | Threshold, Ratio, Attack, Release, Output Gain, Makeup, Dry/Wet, Knee, Model, Env Mode, Expansion Ratio, Auto Release On/Off | ~8-12 |
| GlueCompressor | Threshold, Range, Makeup, Attack, Ratio, Release, Dry/Wet, Peak Clip In | ~6-8 |
| Reverb | Predelay, In Filter Freq, In Filter Width, ER Spin Rate/Amount, ER Shape, HiFilter Freq, HiShelf Gain, LowShelf Freq/Gain, Decay Time, Diffusion, Scale, Room Size, Stereo Image, Density, Reflect Level, Diffuse Level, Dry/Wet + filter on/off toggles | ~15-20 |
| Delay | L Time, R Time, L 16th, R 16th, L Offset, R Offset, Feedback, Filter Freq, Filter Width, Ping Pong, Mod Freq, Dly < Mod, Filter < Mod, Dry/Wet, Filter On | ~10-15 |
| StereoGain (Utility) | Gain, Stereo Width, Mono, Bass Mono, Bass Freq, Balance, Mute | ~5-7 |
| DrumBuss | Drive, Drive Type, Crunch, Damping Freq, Transients, Boom Freq, Boom Amt, Boom Decay, Trim, Output Gain, Dry/Wet, Compressor On | ~10-12 |
| MultibandDynamics | Crossovers, Amount, Time Scaling, Output/Input Gains per band, Band Activators, Above/Below Thresholds + Ratios per band, Attack/Release per band, Master Output | ~30+ |
| Gate | Threshold, Attack, Hold, Release, Return, Floor | ~6 |
| Limiter | Input Gain, Ceiling, Release, Threshold, Output | ~4-5 |
| AutoFilter2 | Frequency, Resonance, Morph, Type, Slope, Circuit, Drive, LFO Amount/Wave/Freq/Phase/Offset, Env Amount/Attack/Release, Output, Dry/Wet | ~12-18 |

## Common Pitfalls

### Pitfall 1: Catalog Parameter Name Mismatch
**What goes wrong:** Recipe specifies `"Frequency"` but EQ Eight's param is `"1 Frequency A"`. Or uses `"Compressor"` as device key instead of `"Compressor2"`.
**Why it happens:** Ableton's API names are not intuitive. The catalog uses exact class names and param names from the Live Object Model.
**How to avoid:** Import CATALOG in tests and validate every recipe param name against it. This is SC #2.
**Warning signs:** Test failures on param name validation.

### Pitfall 2: Missing Roles in a Genre
**What goes wrong:** A genre recipe file has 7 roles instead of 9.
**Why it happens:** Author forgets non-typical roles (e.g., ambient kick).
**How to avoid:** Test that every genre's RECIPE dict has exactly the 9 canonical ROLES as keys.
**Warning signs:** KeyError when Phase 31 tries to apply a recipe.

### Pitfall 3: Normalized Values Sneaking In
**What goes wrong:** Values like `0.5` for a frequency parameter (should be in Hz).
**Why it happens:** Ableton's API uses normalized 0-1 internally; easy to confuse.
**How to avoid:** For params with `conversion` metadata, validate that recipe values fall within `natural_min`-`natural_max` range.
**Warning signs:** Recipe values between 0 and 1 for parameters that should be in Hz, dB, or ms.

### Pitfall 4: Auto-Discovery Not Registering Genre Aliases
**What goes wrong:** `get_mix_recipe(role="kick", genre="dnb")` returns None because only `"drum_and_bass"` is registered.
**Why it happens:** The genre file is `drum_and_bass.py` but user says "dnb".
**How to avoid:** Catalog must register standard aliases. Genre files could optionally export an `ALIASES` list, or the catalog maintains a hardcoded alias map for the 4 core genres.
**Warning signs:** Tool returns error for common genre abbreviations.

### Pitfall 5: EQ Band B Parameters
**What goes wrong:** Recipes set A-channel EQ params but forget EQ Eight has A+B channels (mid/side or stereo).
**Why it happens:** Most mixing uses only the A channel. B channel is for mid/side processing.
**How to avoid:** Recipes should only set A-channel params (the standard stereo EQ). B-channel params are for advanced mid/side which is out of scope.
**Warning signs:** Unused B-channel params cluttering recipes.

## Code Examples

### Test: Validate All Recipe Param Names Against CATALOG
```python
# Source: project convention from test_catalog.py

import pytest
from MCP_Server.devices.catalog import CATALOG
from MCP_Server.mixing.catalog import _ensure_initialized, _registry

def _get_device_param_names(device_class: str) -> set:
    """Get all parameter names for a device from the catalog."""
    entry = CATALOG.get(device_class)
    if entry is None:
        return set()
    return {p["name"] for p in entry["parameters"]}

class TestRecipeParameterNames:
    """Every param name in every recipe must exist in the device CATALOG."""

    @pytest.fixture(autouse=True)
    def init_registry(self):
        _ensure_initialized()

    def test_all_recipe_params_in_catalog(self):
        for genre_id, recipe in _registry.items():
            for role, devices in recipe.items():
                for device_class, params in devices.items():
                    assert device_class in CATALOG, (
                        f"{genre_id}/{role}: device '{device_class}' not in CATALOG"
                    )
                    valid_names = _get_device_param_names(device_class)
                    for param_name in params:
                        assert param_name in valid_names, (
                            f"{genre_id}/{role}/{device_class}: "
                            f"param '{param_name}' not in catalog"
                        )
```

### Test: Every Genre Has All 9 Roles
```python
from MCP_Server.devices.catalog import ROLES

class TestRecipeCompleteness:
    def test_all_genres_have_all_roles(self):
        _ensure_initialized()
        for genre_id, recipe in _registry.items():
            for role in ROLES:
                assert role in recipe, (
                    f"Genre '{genre_id}' missing role '{role}'"
                )
```

### MCP Mock Pattern for Tool Tests
```python
# Source: tests/test_catalog.py pattern
import sys
import types
from unittest.mock import MagicMock

# Must be set up before importing tool modules
_mock_mcp = types.ModuleType("mcp")
_mock_fastmcp = types.ModuleType("mcp.server.fastmcp")
_mock_server = types.ModuleType("mcp.server")
_mock_fastmcp.Context = type("Context", (), {})
_mock_mcp.server = _mock_server
_mock_server.fastmcp = _mock_fastmcp
sys.modules.setdefault("mcp", _mock_mcp)
sys.modules.setdefault("mcp.server", _mock_server)
sys.modules.setdefault("mcp.server.fastmcp", _mock_fastmcp)

if "MCP_Server.server" not in sys.modules:
    _mock_app_server = types.ModuleType("MCP_Server.server")
    _mcp_instance = MagicMock()
    _mcp_instance.tool.return_value = lambda fn: fn
    _mock_app_server.mcp = _mcp_instance
    sys.modules["MCP_Server.server"] = _mock_app_server
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_mixing.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RECIP-01a | Recipe data structure valid for all 4 genres | unit | `pytest tests/test_mixing.py::TestRecipeData -x` | No -- Wave 0 |
| RECIP-01b | All recipe param names exist in device CATALOG | unit | `pytest tests/test_mixing.py::TestRecipeParameterNames -x` | No -- Wave 0 |
| RECIP-01c | All 9 roles present in every genre recipe | unit | `pytest tests/test_mixing.py::TestRecipeCompleteness -x` | No -- Wave 0 |
| RECIP-01d | pkgutil auto-discovery finds all 4 genre recipes | unit | `pytest tests/test_mixing.py::TestAutoDiscovery -x` | No -- Wave 0 |
| RECIP-01e | get_recipe() returns correct data for valid role/genre | unit | `pytest tests/test_mixing.py::TestGetRecipe -x` | No -- Wave 0 |
| RECIP-01f | get_recipe() resolves aliases (dnb, kick drum) | unit | `pytest tests/test_mixing.py::TestAliasResolution -x` | No -- Wave 0 |
| RECIP-01g | get_mix_recipe MCP tool returns JSON for valid input | unit | `pytest tests/test_mixing.py::TestMixRecipeTool -x` | No -- Wave 0 |
| RECIP-01h | get_mix_recipe MCP tool returns error for invalid input | unit | `pytest tests/test_mixing.py::TestMixRecipeTool -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_mixing.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_mixing.py` -- covers all RECIP-01 sub-requirements
- [ ] MCP mock setup (reuse pattern from test_catalog.py)

## Typical Device Usage by Role

This table guides which devices to include per role (Claude's discretion on exact values).

| Role | Eq8 | Compressor2 | GlueCompressor | DrumBuss | Reverb | Delay | StereoGain | Gate | AutoFilter2 | MultibandDynamics | Limiter |
|------|-----|-------------|-----------------|----------|--------|-------|------------|------|-------------|-------------------|---------|
| kick | Yes | Yes | - | Yes (house/techno) | - | - | Yes | - | - | - | - |
| bass | Yes | Yes | - | - | - | - | Yes | - | - | - | - |
| lead | Yes | Yes | - | - | Yes | Yes | Yes | - | - | - | - |
| pad | Yes | Yes | - | - | Yes | - | Yes | - | - | - | - |
| chords | Yes | Yes | - | - | Yes | Yes | Yes | - | - | - | - |
| vocal | Yes | Yes | - | - | Yes | Yes | Yes | Gate? | - | - | - |
| atmospheric | Yes | - | - | - | Yes | Yes | Yes | - | - | - | - |
| return | - | - | - | - | Yes | Yes | Yes | - | - | - | - |
| master | Yes | - | Yes | - | - | - | Yes | - | - | Yes | Yes |

**Notes:**
- Master recipes are deferred to Phase 34 (MSTR-01) but the data structure should support them. For Phase 30, master gets a minimal recipe (Eq8 + StereoGain only, or safe generic values).
- DrumBuss is genre-dependent: house/techno kicks benefit, ambient kicks do not.
- AutoFilter2 is optional and genre-dependent (e.g., techno acid bass).
- Return recipes focus on send effects (Reverb, Delay) with Utility for level.
- The exact device set per role/genre is Claude's discretion.

## Genre-Specific Mixing Characteristics

### House
- Four-on-the-floor kick: tight low-end EQ, moderate compression, mono bass
- Sidechain-style compression on bass (values only -- actual routing is Phase 31)
- Warm reverb on pads/chords, subtle delay on leads
- Wide stereo field for pads, narrow for kick/bass

### Techno
- Harder kick processing: more aggressive EQ, heavier compression, DrumBuss saturation
- Minimal reverb, more delay-based effects
- Tighter, more controlled dynamics overall
- Filter-heavy approach (AutoFilter on some roles)

### Ambient
- Gentle compression, long reverb tails
- Wide stereo imaging on most elements
- Subtle EQ -- less aggressive cuts/boosts
- Longer attack/release times on compressors
- Non-typical roles (kick, bass) get very gentle processing

### Drum and Bass
- Fast, punchy compression on drums (short attack/release)
- Sub-bass emphasis with tight low-end control
- Aggressive high-pass on non-bass elements
- Moderate reverb, rhythmic delay on some elements

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-authored param names | CATALOG-validated names | Phase 29 (v1.4) | Recipe param names must match exactly |
| Normalized 0-1 values | Natural units (Hz, dB, ms) | D-01 (Phase 30) | Human-readable recipes, conversion at apply time |

## Open Questions

1. **Master role in Phase 30 vs Phase 34**
   - What we know: MSTR-01 is Phase 34 scope. Master is one of the 9 ROLES. D-03 says all 9 roles authored for every genre.
   - What's unclear: Should Phase 30 master recipes be minimal stubs or substantial?
   - Recommendation: Provide safe, minimal master recipes (Eq8 gentle curve + StereoGain at unity). Phase 34 will author the full GlueCompressor + MultibandDynamics + Limiter master chain.

2. **Natural unit values for params without conversion metadata**
   - What we know: Many params have `conversion: None` (Resonance, Dry/Wet, Ratio, etc.). These are either already in natural units or are normalized 0-1 with no conversion formula.
   - What's unclear: For params like `Resonance` (0.0-1.0, no conversion), should recipes use the raw 0-1 value?
   - Recommendation: Yes. When a param has no conversion metadata, its raw min/max range IS its natural range. Use those values directly. Document this convention.

3. **Quantized params (filter types, slopes, etc.)**
   - What we know: Params like `1 Filter Type A` are quantized (min=0, max=5, integer values meaning different filter types).
   - What's unclear: Should recipes use numeric values (3) or named constants ("Bell")?
   - Recommendation: Use numeric values matching the catalog's range. Add a comment in the recipe file mapping numbers to names for readability. Phase 31 sends the numeric value directly.

## Sources

### Primary (HIGH confidence)
- `MCP_Server/devices/catalog.py` -- 327 live-validated parameters across 12 devices; all param names and ranges verified
- `MCP_Server/genres/catalog.py` -- pkgutil auto-discovery pattern to mirror
- `MCP_Server/genres/house.py` -- genre module pattern (GENRE constant)
- `MCP_Server/tools/catalog.py` -- MCP tool pattern (@mcp.tool(), format_error)
- `MCP_Server/tools/__init__.py` -- tool registration via import
- `tests/test_catalog.py` -- test patterns including MCP mock setup
- `MCP_Server/devices/__init__.py` -- public API pattern (get_catalog_entry, get_roles)

### Secondary (MEDIUM confidence)
- Device parameter names and ranges from CATALOG -- verified by bootstrap script against live Ableton

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- uses only existing project patterns and stdlib
- Architecture: HIGH -- direct mirror of genres/ package, no design ambiguity
- Pitfalls: HIGH -- based on verified catalog data and established patterns
- Musical values: MEDIUM -- exact parameter values are subjective/artistic; reasonable defaults based on mixing conventions

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable -- pure data module, no external dependencies)
