# Architecture Patterns

**Domain:** Sound Selection Intelligence for Ableton MCP (v1.5)
**Researched:** 2026-03-30
**Confidence:** HIGH -- all recommendations derived from existing codebase patterns; no external dependencies introduced

## Recommended Architecture

### Overview

v1.5 adds a new `MCP_Server/sounds/` peer package (alongside `genres/`, `mixing/`, `theory/`) containing instrument profile data and descriptor-matching logic. A new `MCP_Server/tools/sounds.py` tool module exposes three MCP tools. No Remote Script changes. No genre coupling.

```
MCP_Server/
  sounds/                    # NEW peer package
    __init__.py              # Public API: get_profile, list_descriptors, recommend
    catalog.py               # Auto-discovery registry + matching engine
    wavetable.py             # INSTRUMENT profile dict
    analog.py                # INSTRUMENT profile dict
    operator.py              # INSTRUMENT profile dict
    drift.py                 # INSTRUMENT profile dict
    simpler.py               # INSTRUMENT profile dict
    drum_rack.py             # INSTRUMENT profile dict
  tools/
    sounds.py                # NEW tool module (3 MCP tools)
    __init__.py              # MODIFIED: add sounds import
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `sounds/wavetable.py` (etc.) | Static instrument profile data -- sonic character, strengths, weaknesses, descriptor affinities, preset category map | `sounds/catalog.py` reads INSTRUMENT constant |
| `sounds/catalog.py` | Auto-discovers profiles via pkgutil; descriptor registry; weighted scoring engine for descriptor-to-instrument matching | `sounds/*.py` profile modules |
| `sounds/__init__.py` | Public API surface: `get_profile()`, `list_descriptors()`, `recommend()` | Delegates to `catalog.py` |
| `tools/sounds.py` | MCP tool definitions: `get_instrument_profile`, `list_sound_descriptors`, `get_sound_recommendation` | Imports from `sounds/` package; uses `MCP_Server.server.mcp` for registration |

### Data Flow

**Recommendation request flow:**
```
Claude calls get_sound_recommendation(descriptor="warm evolving pad")
  -> tools/sounds.py parses descriptor string into tags
  -> sounds.catalog.recommend(tags) called
  -> catalog iterates all discovered INSTRUMENT profiles
  -> for each instrument, computes weighted affinity score against tags
  -> returns top match(es) with instrument name, browser_path, reasoning
  -> tools/sounds.py formats as JSON string, returns to Claude
```

**Profile lookup flow:**
```
Claude calls get_instrument_profile(instrument="Wavetable")
  -> tools/sounds.py delegates to sounds.catalog.get_profile("wavetable")
  -> catalog returns the full INSTRUMENT dict for that instrument
  -> tools/sounds.py formats as JSON string
```

**Descriptor listing flow:**
```
Claude calls list_sound_descriptors()
  -> tools/sounds.py delegates to sounds.catalog.list_descriptors()
  -> catalog aggregates all descriptor tags across all profiles
  -> returns deduplicated, categorized list
```

## Integration Points with Existing Tools

### Browser Tools (browser.py)

`get_sound_recommendation` returns a `browser_path` field (e.g., `"Instruments/Wavetable/Pads/Warm Pad"`). Claude uses this path with the existing `get_browser_items_at_path` tool to navigate and load a preset. The sounds package does NOT call browser tools directly -- it returns data that guides Claude's next action.

**Why no direct integration:** Keeping sounds as pure data/computation (like theory/) means no socket calls, no Remote Script dependency, and easier testing. Claude orchestrates the workflow: recommend -> browse -> load.

### Genre Tools (genres.py)

No coupling. The milestone spec explicitly says "no genre dependency." Genre-awareness (e.g., "house bass" vs "dubstep bass") is a future enhancement, not v1.5 scope. The sounds package is self-contained.

### Mix Recipe Tools (mixing.py)

No coupling for v1.5. A future milestone could bridge sounds and mixing (e.g., "load instrument then apply role recipe"), but that is out of scope.

### Device/Load Tools (devices.py)

The existing `load_instrument_by_path` tool in devices.py handles loading browser items onto tracks. The recommendation flow is: `get_sound_recommendation` -> returns browser path -> Claude calls `load_instrument_by_path` with that path. No modification to devices.py needed.

## New vs. Modified Files

### New Files (8)

| File | Type | Purpose |
|------|------|---------|
| `MCP_Server/sounds/__init__.py` | Package init | Public API exports |
| `MCP_Server/sounds/catalog.py` | Core logic | Auto-discovery, descriptor registry, matching engine |
| `MCP_Server/sounds/wavetable.py` | Data | Wavetable instrument profile |
| `MCP_Server/sounds/analog.py` | Data | Analog instrument profile |
| `MCP_Server/sounds/operator.py` | Data | Operator instrument profile |
| `MCP_Server/sounds/drift.py` | Data | Drift instrument profile |
| `MCP_Server/sounds/simpler.py` | Data | Simpler instrument profile |
| `MCP_Server/sounds/drum_rack.py` | Data | Drum Rack instrument profile |
| `MCP_Server/tools/sounds.py` | Tool module | 3 MCP tool definitions |

### Modified Files (1)

| File | Change |
|------|--------|
| `MCP_Server/tools/__init__.py` | Add `sounds` to the import list |

### Unchanged Files

Everything else. No Remote Script changes. No genre/mixing/theory modifications.

## Instrument Profile Data Structure

Use plain Python dicts (matching genres/ convention per D-01, D-02). Each profile module exports an `INSTRUMENT` constant.

### Recommended Schema

```python
INSTRUMENT = {
    # Identity
    "name": "Wavetable",                    # Display name (matches Ableton)
    "id": "wavetable",                      # Canonical ID for lookup
    "aliases": ["wavetable synth"],          # Alternative names
    "type": "synthesizer",                   # synthesizer | sampler | drum_machine

    # Sonic character -- what this instrument sounds like / is good at
    "character": {
        "description": "Modern wavetable synth with morphing capabilities...",
        "strengths": [
            "evolving textures",
            "rich pads",
            "modern digital leads",
            "morphing timbres",
        ],
        "weaknesses": [
            "raw analog warmth",
            "simple classic waveforms",
        ],
    },

    # Descriptor affinities -- the matching engine core
    # Keys are descriptor tags; values are affinity weights 0.0-1.0
    # Only include descriptors where this instrument has meaningful affinity (>= 0.3)
    "descriptors": {
        # Texture descriptors
        "warm": 0.6,
        "bright": 0.8,
        "dark": 0.5,
        "evolving": 0.95,
        "static": 0.3,
        "gritty": 0.6,
        "clean": 0.7,
        "lush": 0.9,
        # Role descriptors
        "pad": 0.9,
        "lead": 0.8,
        "bass": 0.7,
        "pluck": 0.7,
        "keys": 0.4,
        "arp": 0.8,
        # Character descriptors
        "analog": 0.4,
        "digital": 0.9,
        "acoustic": 0.1,
        "cinematic": 0.8,
        "aggressive": 0.7,
        "soft": 0.7,
        "punchy": 0.6,
    },

    # Browser category map -- where to find presets in Ableton's browser
    # Maps descriptor combinations to specific browser paths
    "browser_paths": {
        "pad": "Instruments/Wavetable/Pad",
        "lead": "Instruments/Wavetable/Lead",
        "bass": "Instruments/Wavetable/Bass",
        "keys": "Instruments/Wavetable/Keys",
        "pluck": "Instruments/Wavetable/Pluck",
        "arp": "Instruments/Wavetable/Rhythmic",
        "_default": "Instruments/Wavetable",
    },
}
```

### Why This Structure

1. **Plain dicts, not dataclasses:** Matches the established D-01/D-02 convention from genres/. Every data module in this codebase uses dicts. Consistency matters more than type safety here -- the catalog validates on discovery.

2. **Affinity weights (0.0-1.0), not boolean tags:** A boolean "supports pad: yes/no" loses the critical nuance that Wavetable is excellent for pads (0.9) while Operator is decent (0.6). Weighted scoring enables the matching engine to rank instruments, not just filter them.

3. **Sparse descriptors (only >= 0.3):** Instruments only list descriptors they have meaningful affinity for. Absence = 0.0 affinity. This keeps profiles lean and makes it obvious what each instrument is NOT good at.

4. **browser_paths keyed by role descriptor:** After the matching engine picks an instrument, it needs to tell Claude WHERE in the browser to look. The role descriptor (pad, lead, bass) maps to a specific browser category. The `_default` key handles cases where no specific path exists.

5. **Separate character.strengths/weaknesses from descriptors:** Strengths/weaknesses are human-readable text for the `get_instrument_profile` tool (Claude reads these to explain its choice). Descriptors are machine-readable weights for the matching engine. Different audiences, different formats.

## Descriptor Matching Algorithm

### Recommended: Weighted Sum Scoring

**Not keyword matching** (too brittle -- "warm pad" would only match instruments tagged with both exact strings).

**Not ML/embeddings** (overkill for 6 instruments and ~30 descriptors; adds dependencies; opaque reasoning).

**Weighted sum scoring** because it is transparent, debuggable, and sufficient for the problem size:

```python
def recommend(tags: list[str]) -> list[dict]:
    """Score all instruments against descriptor tags, return ranked results."""
    results = []
    for inst_id, profile in _registry.items():
        affinities = profile["descriptors"]
        score = 0.0
        matched_tags = []
        unmatched_tags = []

        for tag in tags:
            normalized = tag.lower().strip()
            weight = affinities.get(normalized, 0.0)
            score += weight
            if weight > 0:
                matched_tags.append((normalized, weight))
            else:
                unmatched_tags.append(normalized)

        if score > 0:
            # Determine best browser path from role-type tags
            browser_path = _resolve_browser_path(profile, tags)
            results.append({
                "instrument": profile["name"],
                "score": round(score, 2),
                "browser_path": browser_path,
                "matched": matched_tags,
                "unmatched": unmatched_tags,
                "reasoning": _build_reasoning(profile, matched_tags),
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results
```

### Tag Parsing

The descriptor input from Claude is a free-form string like `"warm evolving pad"`. Parse by splitting on spaces and stripping punctuation. Each word becomes a tag. This is intentionally simple -- Claude already knows the valid descriptors (from `list_sound_descriptors`) and will use them correctly.

### Browser Path Resolution

After scoring picks an instrument, resolve the browser path:
1. Check tags for role descriptors (pad, lead, bass, keys, pluck, arp)
2. If found, use `browser_paths[role]`
3. If not found, use `browser_paths["_default"]`
4. If multiple role descriptors, prefer the one with highest affinity weight

### Reasoning Generation

Build a one-liner explaining why this instrument was chosen. Template:
`"{instrument} excels at {top_matched_descriptors} (scored {score})"`. This helps Claude explain its recommendation to the user.

## Catalog / Auto-Discovery Pattern

Follow the exact pattern from `genres/catalog.py` and `mixing/catalog.py`:

```python
# sounds/catalog.py

import importlib
import logging
import pkgutil
from typing import Dict, List, Optional

import MCP_Server.sounds as sounds_package

logger = logging.getLogger("AbletonMCPServer")

_registry: Dict[str, dict] = {}      # inst_id -> INSTRUMENT dict
_descriptor_index: Dict[str, list] = {}  # descriptor -> [(inst_id, weight)]
_initialized = False
_SKIP_MODULES = {"catalog"}


def _discover_instruments() -> None:
    global _initialized
    for finder, modname, ispkg in pkgutil.iter_modules(sounds_package.__path__):
        if modname.startswith("_") or modname in _SKIP_MODULES:
            continue
        try:
            mod = importlib.import_module(f"MCP_Server.sounds.{modname}")
        except Exception:
            logger.error("Failed to import sound module '%s'", modname, exc_info=True)
            continue

        inst_data = getattr(mod, "INSTRUMENT", None)
        if inst_data is None:
            logger.warning("Sound module '%s' has no INSTRUMENT constant", modname)
            continue

        # Validate required keys
        required = {"name", "id", "type", "character", "descriptors", "browser_paths"}
        missing = required - set(inst_data.keys())
        if missing:
            logger.error("Sound module '%s' missing keys: %s", modname, missing)
            continue

        inst_id = inst_data["id"]
        _registry[inst_id] = inst_data

        # Build descriptor reverse index
        for desc, weight in inst_data["descriptors"].items():
            _descriptor_index.setdefault(desc, []).append((inst_id, weight))

    _initialized = True


def _ensure_initialized() -> None:
    if not _initialized:
        _discover_instruments()
```

### Key Design Decisions

1. **`INSTRUMENT` constant name** (not `PROFILE` or `SOUND`): Parallels `GENRE` in genres/ and `RECIPE` in mixing/. Noun that describes what the dict IS.

2. **`_descriptor_index` reverse index**: Built at discovery time. Maps each descriptor to a list of (instrument_id, weight) tuples. Enables O(1) lookup per tag during scoring, and powers `list_descriptors()` trivially.

3. **Validation at discovery time**: Missing required keys logged and skipped, matching the D-08 pattern from genres/catalog.py. Fail gracefully, never crash the server.

## Patterns to Follow

### Pattern 1: Peer Package with pkgutil Auto-Discovery
**What:** New `sounds/` package sits alongside `genres/` and `mixing/`. Each instrument is a separate Python file exporting a dict constant. The catalog discovers them via `pkgutil.iter_modules`.
**When:** Always -- this is the established pattern for all data packages in this codebase.
**Why:** Zero-registration. Add a new instrument file, it appears automatically. Proven in genres/ (12 files) and mixing/ (12 files).

### Pattern 2: Tool Module Imports Data Package
**What:** `tools/sounds.py` imports from `sounds/` package and defines `@mcp.tool()` functions. Tool module handles formatting, error messages, and JSON serialization. Data package handles logic.
**When:** Always -- every tool module follows this separation (tools/genres.py imports genres/, tools/mixing.py imports mixing/, tools/catalog.py imports devices/).
**Why:** Separation of concerns. Data/logic is testable without MCP. Tools are thin wrappers.

### Pattern 3: format_error for User-Facing Errors
**What:** Use `MCP_Server.connection.format_error()` for structured error responses in tool functions.
**When:** Any tool function that can fail (invalid instrument name, empty descriptor, etc.).
**Why:** Consistent error format across all 100+ tools.

### Pattern 4: JSON Serialization in Tool Layer Only
**What:** Tool functions call `json.dumps()` on the data returned by the data package. The data package returns Python dicts/lists, never JSON strings.
**When:** Always -- every tool module does this.
**Why:** Data package stays testable with plain Python assertions. JSON is a presentation concern.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Genre Coupling
**What:** Making sound recommendations depend on genre context.
**Why bad:** Violates the milestone spec ("no genre dependency"). Adds complexity. If Claude wants genre-aware recommendations, it can call genre tools separately and combine the information itself.
**Instead:** Pure descriptor-based matching. Genre awareness is a future milestone.

### Anti-Pattern 2: Embedding/ML Matching
**What:** Using sentence embeddings or ML models to match descriptors to instruments.
**Why bad:** Adds heavy dependencies (torch, sentence-transformers) to a project that currently has zero ML deps beyond music21. Opaque reasoning. 6 instruments do not warrant ML.
**Instead:** Weighted sum scoring with hand-tuned affinity values. Transparent, debuggable, zero new dependencies.

### Anti-Pattern 3: Static Lookup Table
**What:** A giant if/elif chain or flat dict mapping exact descriptor strings to instruments.
**Why bad:** Brittle. "warm pad" works but "lush warm pad" doesn't. No ranking. Adding new descriptors requires modifying the lookup table rather than just instrument profiles.
**Instead:** Weighted scoring over individual tags. Naturally handles multi-tag queries and provides ranked results.

### Anti-Pattern 4: Remote Script Changes
**What:** Adding any command handlers to the Ableton Remote Script.
**Why bad:** Unnecessary. Sound selection is pure computation -- no Ableton API calls needed. Same principle as theory/ (server-side only, per the project's established pattern).
**Instead:** All new code is MCP_Server-side only.

### Anti-Pattern 5: Dataclass/Pydantic Profiles
**What:** Defining instrument profiles as dataclasses or Pydantic models.
**Why bad:** Breaks established convention. Genres use dicts (D-01). Mixing uses dicts. Devices use dicts. Adding a different data representation for one package creates inconsistency.
**Instead:** Plain Python dicts with validation in the catalog discovery step.

## Suggested Build Order

Build order follows dependency chain: data first, then logic, then tools, then registration.

### Phase 1: Package Skeleton + First Profile
1. Create `MCP_Server/sounds/__init__.py` with public API stubs
2. Create `MCP_Server/sounds/catalog.py` with auto-discovery + `get_profile()` + `list_descriptors()`
3. Create `MCP_Server/sounds/wavetable.py` with full INSTRUMENT profile
4. Write tests for catalog discovery and profile lookup

### Phase 2: Remaining Profiles
5. Create `analog.py`, `operator.py`, `drift.py`, `simpler.py`, `drum_rack.py`
6. Test all 6 profiles discovered and queryable

### Phase 3: Matching Engine
7. Add `recommend()` function to `catalog.py` with weighted scoring
8. Add `_resolve_browser_path()` helper
9. Add `_build_reasoning()` helper
10. Write tests for scoring, ranking, browser path resolution

### Phase 4: MCP Tools
11. Create `MCP_Server/tools/sounds.py` with 3 tool functions
12. Modify `MCP_Server/tools/__init__.py` to import sounds module
13. Integration test: tools return valid JSON with expected fields

**Rationale:** Profiles must exist before the catalog can discover them. Catalog must work before matching engine can score. Matching engine must work before tools can expose it. Each phase is independently testable.

## Scalability Considerations

| Concern | At 6 instruments (v1.5) | At 20 instruments (future) | At 50+ instruments (far future) |
|---------|------------------------|---------------------------|-------------------------------|
| Discovery time | Instant (<10ms) | Instant (<50ms) | Still fast -- pkgutil is O(n) |
| Scoring time | Trivial -- 6 instruments x ~5 tags | Trivial -- 20 x 5 | Still trivial -- 50 x 10 = 500 multiplies |
| Profile maintenance | Manual, manageable | Manual, needs conventions doc | Consider YAML/JSON data files |
| Descriptor sprawl | ~30 descriptors, easy to reason about | ~50, needs categorization | Needs hierarchy or taxonomy |
| Browser paths | Hardcoded per instrument, fine | Per-instrument hardcoding still works | May need browser API verification |

The weighted scoring approach scales well up to hundreds of instruments. The bottleneck will be profile authoring quality, not computation.

## Sources

- Codebase analysis: `MCP_Server/genres/catalog.py` (pkgutil auto-discovery pattern)
- Codebase analysis: `MCP_Server/mixing/catalog.py` (pkgutil auto-discovery pattern)
- Codebase analysis: `MCP_Server/tools/__init__.py` (tool registration pattern)
- Codebase analysis: `MCP_Server/genres/house.py` (dict-based data module pattern, D-01/D-02)
- Codebase analysis: `MCP_Server/tools/genres.py` (tool-imports-package pattern)
- Codebase analysis: `MCP_Server/tools/mixing.py` (tool-imports-package, format_error pattern)
- Codebase analysis: `MCP_Server/tools/browser.py` (browser path navigation, integration point)
- Codebase analysis: `MCP_Server/devices/__init__.py` (public API delegation pattern)
- Project spec: `.planning/PROJECT.md` (v1.5 requirements, architecture constraints)
