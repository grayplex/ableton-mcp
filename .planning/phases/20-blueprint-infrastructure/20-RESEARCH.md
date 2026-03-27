# Phase 20: Blueprint Infrastructure - Research

**Researched:** 2026-03-26
**Phase:** 20-blueprint-infrastructure
**Goal:** A validated schema and catalog system exists, proven end-to-end with a complete house genre blueprint

## 1. Existing Codebase Patterns

### Data Definition Pattern (scales.py, progressions.py)
- `SCALE_CATALOG` in `scales.py`: dict keyed by scale name, each entry has `intervals`, `category`, `music21_class`, `aliases`
- `PROGRESSION_CATALOG` in `progressions.py`: list of dicts, each with `name`, `genre`, `numerals`
- Both are module-level constants, imported directly by other modules
- Pattern: define data as Python dicts, logic functions reference the data

### Lazy Import Pattern (chords.py)
- music21 submodules loaded lazily via `_get_*_module()` functions
- Global `_*_module = None` with first-use import
- Genres package won't need this (no music21 dependency — pure data)

### Package Structure
- `MCP_Server/theory/` — 7 modules, barrel exports from `__init__.py`
- `MCP_Server/tools/` — 15 domain modules, `__init__.py` imports all to trigger `@mcp.tool()` registration
- New `MCP_Server/genres/` package follows same pattern

### Test Pattern
- `tests/test_theory.py` — standalone, direct imports from `MCP_Server.theory`
- Unit tests (library functions) + integration tests (MCP tool calls via `mcp_server` fixture)
- Genre tests will be pure unit tests (no MCP tools in this phase)

### Supported Theory Types (for blueprint cross-validation)
- **26 chord qualities** in `_QUALITY_MAP`: maj, min, dim, aug, maj7, min7, dom7, 7, dim7, hdim7, min7b5, sus2, sus4, add9, 9, min9, maj9, 11, min11, 13, min13, 7b5, 7#5, 7b9, 7#9, 7#11
- **38 scales** in `SCALE_CATALOG`: major, natural_minor, chromatic, ionian, dorian, phrygian, lydian, mixolydian, aeolian, locrian, harmonic_minor, melodic_minor, major_pentatonic, minor_pentatonic, blues, + 23 more
- Blueprints must only reference names from these sets (QUAL-02 in Phase 24)

## 2. Schema Design

### TypedDict Approach
Per CONTEXT.md D-06, use TypedDict for schema definition. Structure:

```python
from typing import TypedDict, List, Optional

class InstrumentationSection(TypedDict):
    roles: List[str]  # ["kick", "bass", "pad", "lead", "hi-hats"]

class HarmonySection(TypedDict):
    scales: List[str]  # Must match SCALE_CATALOG keys
    chord_types: List[str]  # Must match _QUALITY_MAP keys
    common_progressions: List[List[str]]  # Roman numeral sequences

class RhythmSection(TypedDict):
    time_signature: str  # "4/4"
    bpm_range: List[int]  # [120, 130]
    # Claude's discretion: drum pattern, swing, groove details

class ArrangementSection(TypedDict):
    sections: List[dict]  # [{"name": "intro", "bars": 16}, ...]

class MixingSection(TypedDict):
    # Claude's discretion for internal structure

class ProductionTipsSection(TypedDict):
    # Claude's discretion for internal structure

class GenreBlueprint(TypedDict):
    name: str
    id: str  # canonical identifier, e.g., "house"
    bpm_range: List[int]
    aliases: List[str]
    instrumentation: InstrumentationSection
    harmony: HarmonySection
    rhythm: RhythmSection
    arrangement: ArrangementSection
    mixing: MixingSection
    production_tips: ProductionTipsSection
    subgenres: Optional[dict]  # or separate export
```

### Validation Function
Per CONTEXT.md D-07 and D-08:
- `validate_blueprint(data: dict) -> None` raises `ValueError` on malformed data
- Checks: required top-level keys, required keys per section, type checks on values
- Called by catalog during auto-discovery
- Catalog catches ValueError per genre, logs error, excludes bad genre — server starts with valid genres

## 3. Catalog Auto-Discovery

### Recommended Approach: Package Scanning
```python
# MCP_Server/genres/catalog.py
import importlib
import pkgutil
import MCP_Server.genres as genres_package

def _discover_genres():
    """Auto-discover all genre modules in the genres package."""
    registry = {}
    for importer, modname, ispkg in pkgutil.iter_modules(genres_package.__path__):
        if modname.startswith('_') or modname in ('catalog', 'schema'):
            continue  # skip private/infrastructure modules
        try:
            module = importlib.import_module(f'MCP_Server.genres.{modname}')
            # Extract genre data from module
            # Convention: module exports GENRE (base dict) and SUBGENRES (dict of overrides)
        except Exception as e:
            logger.error(f"Failed to load genre module '{modname}': {e}")
            continue
    return registry
```

This matches INFR-02: "discovers and indexes genre modules at import time without manual registration."

### Alternative: Explicit `__init__.py` imports
Like `tools/__init__.py` which imports all modules. Simpler but requires manual update when adding genres. Not recommended since it defeats auto-discovery (INFR-02).

## 4. Alias Resolution

### Recommended Approach: Built from genre data
Each genre file declares its own aliases. Catalog builds a reverse lookup:
```python
# During discovery:
alias_map = {}
for genre_id, genre_data in registry.items():
    for alias in genre_data.get('aliases', []):
        alias_map[alias.lower().replace(' ', '_')] = genre_id
    # Also add the canonical name
    alias_map[genre_id] = genre_id
```

Handles INFR-03: "deep house" → normalize to "deep_house" → resolve to house subgenre.

Key normalization: lowercase, replace spaces/hyphens with underscores.

## 5. Subgenre Merge

Per INFR-04 and CONTEXT.md D-05: shallow merge with subgenre overriding parent.

```python
def get_blueprint(genre_id, subgenre=None):
    base = registry[genre_id].copy()
    if subgenre and subgenre in base.get('subgenres', {}):
        sub_data = base['subgenres'][subgenre]
        for key, value in sub_data.items():
            base[key] = value  # shallow override
    return base
```

## 6. House Genre Content (GENR-01)

The house blueprint needs all six dimensions. Research-informed content structure:

### Instrumentation
- Roles: kick, bass, hi-hats, clap/snare, pad, stab, lead, vocal_chop, percussion, FX/riser

### Harmony
- Scales: minor, dorian, natural_minor, major (less common)
- Chord types: min7, maj7, dom7, min9, sus4, add9
- Common progressions: [["i", "iv"], ["i", "bVII", "iv"], ["ii", "V", "I"], ["i", "bVI", "bVII"]]

### Rhythm
- Time signature: 4/4
- BPM range: [120, 130]
- Straight 16ths hi-hats, four-on-the-floor kick, offbeat claps

### Arrangement
- Sections: intro (16 bars), buildup (8), drop/main (32), breakdown (16), buildup2 (8), drop2 (32), outro (16)

### Mixing
- Frequency ranges, sidechain compression, stereo field conventions

### Production Tips
- Genre-specific techniques, common sound design approaches

### Subgenres (deep, tech, progressive, acid)
Each overrides relevant dimensions:
- Deep house: slower (118-124 BPM), more jazzy chords (min9, maj9), lush pads
- Tech house: more percussive, minimal harmony, groovy basslines
- Progressive house: longer builds, cinematic arrangement, wider BPM (124-132)
- Acid house: TB-303 bass, resonance sweeps, raw/repetitive

## 7. File Organization

```
MCP_Server/genres/
├── __init__.py          # Barrel exports: get_blueprint, list_genres, etc.
├── schema.py            # TypedDict definitions + validate_blueprint()
├── catalog.py           # Auto-discovery, alias resolution, subgenre merge
└── house.py             # HOUSE dict + HOUSE_SUBGENRES dict (GENR-01)
```

Phase 22-23 will add: techno.py, hip_hop_trap.py, ambient.py, drum_and_bass.py, dubstep.py, trance.py, neo_soul_rnb.py, synthwave.py, lo_fi.py, future_bass.py, disco_funk.py

## 8. Testing Strategy

### Unit Tests (tests/test_genres.py)
1. **Schema validation**: valid blueprint passes, missing keys raise ValueError, wrong types raise ValueError
2. **Catalog discovery**: house genre auto-discovered and indexed
3. **Alias resolution**: "house", "deep house", "deep_house" all resolve correctly
4. **Subgenre merge**: deep house = house base + deep overrides, override keys replaced
5. **Blueprint completeness**: house blueprint has all 6 required dimensions
6. **Content validity**: all chord_types in house blueprint exist in `_QUALITY_MAP`, all scales exist in `SCALE_CATALOG`

### Validation Architecture

**Coverage mapping:**
| Requirement | Test Approach |
|-------------|---------------|
| INFR-01 | Verify house blueprint has all 6 dimension keys with non-empty values |
| INFR-02 | Verify catalog auto-discovers house.py without explicit registration |
| INFR-03 | Verify alias normalization and resolution for multiple input formats |
| INFR-04 | Verify shallow merge produces correct subgenre data |
| INFR-05 | Verify malformed dict raises ValueError; valid dict passes |
| GENR-01 | Verify house + 4 subgenres all pass validation with complete data |

## 9. Risk Assessment

### Low Risk
- Schema definition (TypedDict is straightforward)
- House genre content (well-documented genre)
- Validation function (simple key/type checking)

### Medium Risk
- Auto-discovery mechanism (pkgutil pattern needs testing with the package structure)
- Alias resolution edge cases (abbreviations, typos — keep it simple, exact match after normalization)

### No Risk
- No Ableton Remote Script changes needed
- No existing code modified (new package only)
- No new external dependencies

## RESEARCH COMPLETE
