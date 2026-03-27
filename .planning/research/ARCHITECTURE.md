# Architecture Patterns: v1.2 Genre/Style Blueprint Integration

**Domain:** Genre blueprint reference system for Ableton MCP server
**Researched:** 2026-03-25
**Confidence:** HIGH (architecture follows established codebase patterns)

## Recommended Architecture

### Overview

Genre blueprints are **static reference documents** that provide Claude with curated knowledge about electronic music conventions. They integrate into the existing MCP server as a new domain alongside the theory engine, following the same architectural patterns: a library package (`MCP_Server/blueprints/`) exposes data, and a tool module (`MCP_Server/tools/blueprints.py`) wraps it for MCP access.

The key architectural decision: use **MCP tools (not resources)** as the delivery mechanism. Tools are model-controlled -- Claude decides when to fetch blueprint data based on conversation context. MCP resources require the client application to explicitly select them, which creates friction and is inconsistent across MCP clients.

### Proposed File Structure

```
MCP_Server/
  blueprints/                    # NEW: Blueprint library (parallel to theory/)
    __init__.py                  # Public API: get_blueprint, list_genres, search_blueprints
    catalog.py                   # Blueprint registry, lookup, search, subgenre merging
    schema.py                    # Blueprint validation (TypedDict or runtime checks)
    genres/                      # Blueprint data files (one per genre)
      __init__.py                # Imports all genre modules
      house.py                   # House + subgenres (deep, tech, progressive, etc.)
      techno.py                  # Techno + subgenres (minimal, industrial, melodic, etc.)
      drum_and_bass.py           # DnB + subgenres (liquid, neurofunk, jungle, etc.)
      dubstep.py                 # Dubstep + subgenres (brostep, riddim, melodic, etc.)
      trance.py                  # Trance + subgenres (progressive, uplifting, psytrance, etc.)
      ambient.py                 # Ambient + subgenres (dark ambient, drone, etc.)
      hip_hop.py                 # Hip-hop/trap + subgenres
      neo_soul.py                # Neo-soul/R&B
      synthwave.py               # Synthwave/retrowave
      lo_fi.py                   # Lo-fi hip-hop/chill
      future_bass.py             # Future bass
      disco_funk.py              # Disco/nu-disco/funk
  tools/
    blueprints.py                # NEW: MCP tool wrappers (parallel to theory.py)
tests/
  test_blueprints.py             # NEW: Blueprint library + tool tests
```

### Why This Structure

**Parallel to theory engine.** The theory engine established the pattern: `MCP_Server/theory/` is the library, `MCP_Server/tools/theory.py` is the tool layer. Blueprints follow identically: `MCP_Server/blueprints/` is the library, `MCP_Server/tools/blueprints.py` is the tool layer. Anyone who understands theory/ understands blueprints/ immediately.

**One file per genre.** Each blueprint is substantial (80-120 lines of structured data). With 12 genres, a single file would be 1000-1400 lines. Separate files make individual genres easy to review, edit, and test.

**Python dicts, not JSON/YAML/Markdown.** Three reasons:
1. The theory engine uses Python catalogs (`PROGRESSION_CATALOG`, `RHYTHM_CATALOG`, `SCALE_CATALOG`). Consistency.
2. No file I/O at runtime. Python modules load once at import time. The existing server has zero runtime file reads.
3. Malformed Python fails at import with a clear traceback. Malformed YAML/JSON fails at runtime.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `blueprints/genres/*.py` | Define individual genre blueprint data as dicts | Imported by `genres/__init__.py` |
| `blueprints/genres/__init__.py` | Re-export all genre modules | Imported by `catalog.py` |
| `blueprints/catalog.py` | Blueprint registry, lookup by genre/subgenre, listing, subgenre merge logic | Imported by `blueprints/__init__.py` |
| `blueprints/schema.py` | Blueprint structure validation (ensure required keys exist) | Used by `catalog.py` at import |
| `blueprints/__init__.py` | Public API surface (`get_blueprint`, `list_genres`) | Imported by `tools/blueprints.py` |
| `tools/blueprints.py` | MCP tool wrappers with `@mcp.tool()` | Imports from `blueprints/` and `theory/`, registered on `mcp` |

### What Does NOT Change

| Component | Why No Change |
|-----------|--------------|
| Remote Script | Blueprints are pure server-side reference data (same as theory engine) |
| `MCP_Server/connection.py` | No socket protocol changes needed |
| `MCP_Server/server.py` | Tool registration via existing import chain |
| `MCP_Server/theory/*.py` | No modifications. Blueprints reference theory concepts by name, not by import |
| Existing tool modules | No modifications to any of the 17 existing tool files |

## Data Flow

### Primary Flow: User Mentions a Genre

```
User: "Help me make a deep house track"
         |
    [Claude recognizes genre context from conversation]
         |
    Claude calls get_genre_blueprint(genre="house", subgenre="deep_house")
         |
    tools/blueprints.py
      → blueprints.get_blueprint("house", "deep_house")
        → catalog.py looks up GENRE_CATALOG["house"]
        → merges subgenre overrides from house.BLUEPRINT["subgenres"]["deep_house"]
        → returns merged dict
      → json.dumps(result)
         |
    Returns JSON: instrumentation, harmony, rhythm, arrangement, mixing conventions
         |
    Claude uses blueprint data to inform all subsequent tool calls:
      - set_tempo(bpm=122)  (from bpm_range)
      - create_midi_track() + load_instrument("Operator")  (from ableton_tips)
      - build_chord(root="D", quality="min7")  (from harmony.chord_types)
      - generate_progression(key="C", genre="rnb")  (from harmony conventions)
```

### Secondary Flow: Genre Discovery

```
User: "What genres can you help me produce?"
         |
    Claude calls list_genre_blueprints()
         |
    Returns: [{genre: "house", display_name: "House", subgenres: [...], description: "..."},
              {genre: "techno", ...}, ...]
```

### Tertiary Flow: Theory Cross-Reference via Palette Tool

```
User: "Set up a neo-soul session for me"
         |
    Claude calls get_genre_palette(genre="neo_soul", key="Eb")
         |
    tools/blueprints.py:
      1. Loads blueprint: blueprints.get_blueprint("neo_soul")
      2. Reads harmony section: chord_types=["maj7","min7","dom9"], scales=["dorian","mixolydian"]
      3. Calls theory functions at RUNTIME (not import time):
         - theory.build_chord("Eb", "maj7") → {midi: [55,59,62,65], ...}
         - theory.build_chord("Eb", "min7") → {midi: [55,58,62,65], ...}
         - theory.get_scale_pitches("Eb", "dorian") → {pitches: [...], ...}
         - theory.generate_progression("Eb", genre="rnb") → {chords: [...], ...}
      4. Assembles combined result
         |
    Returns JSON: key-resolved chords, scales, progressions + rhythm feel + BPM range
```

**Critical design principle:** Blueprints do NOT import or call theory functions. They store **convention names** (e.g., `"chord_types": ["min7", "dom9"]`). Only the `get_genre_palette` tool bridges the gap at runtime, keeping the two systems decoupled.

## Blueprint Data Schema

Each genre blueprint is a Python dict following this canonical structure:

```python
BLUEPRINT = {
    # === Identity ===
    "genre": "house",                          # Machine key (used in lookups)
    "display_name": "House",                   # Human-readable name
    "description": "Four-on-the-floor...",     # 1-2 sentence overview
    "bpm_range": [118, 130],                   # [min, max] BPM
    "time_signature": "4/4",                   # Primary time signature

    # === Subgenres (optional overrides) ===
    "subgenres": {
        "deep_house": {
            "bpm_range": [118, 124],           # Override parent BPM
            "description": "Warm, jazzy...",
            "distinguishing_features": ["jazz chords", "warm pads"],
            # Any key from parent can be overridden here
        },
    },

    # === Instrumentation ===
    "instrumentation": {
        "drums": {
            "kick": {"role": "foundation", "pattern": "four-on-the-floor", "notes": "..."},
            "snare_clap": {"role": "backbeat", "pattern": "2 and 4", "notes": "..."},
            "hi_hats": {"role": "groove", "pattern": "offbeat 8ths", "notes": "..."},
            "percussion": {"role": "texture", "elements": ["shaker", "rim", "conga"]},
        },
        "bass": {
            "type": "synth bass",
            "role": "groove + harmony",
            "characteristics": ["driving", "syncopated"],
            "octave_range": [1, 3],
        },
        "keys_pads": {
            "types": ["electric piano", "analog pad"],
            "role": "harmony + atmosphere",
            "characteristics": ["warm", "filtered"],
        },
        "other": [],  # Additional instruments specific to genre
    },

    # === Harmony ===
    "harmony": {
        "key_preferences": ["minor", "dorian"],          # Preferred key/mode types
        "chord_types": ["min7", "maj7", "dom9"],          # Chord quality names (theory engine compatible)
        "common_progressions": [                           # Named progressions with Roman numerals
            {"name": "Classic House", "numerals": ["i", "iv", "v", "i"]},
        ],
        "scales": ["natural_minor", "dorian"],             # Scale names (theory engine compatible)
        "harmonic_rhythm": "1-2 chords per 4 bars",
        "notes": "Harmony is sparse; chords filtered or evolving.",
    },

    # === Rhythm ===
    "rhythm": {
        "feel": "straight with swing on hats",
        "grid": "16th note",
        "swing_amount": "0-15%",
        "syncopation": "moderate on bass, heavy on percussion",
        "notes": "Ghost notes on hats create shuffle feel.",
    },

    # === Arrangement ===
    "arrangement": {
        "structure": ["intro", "buildup", "drop", "breakdown", "drop", "outro"],
        "section_lengths": {"intro": "16-32 bars", "buildup": "8-16 bars", "drop": "32 bars"},
        "techniques": ["filter sweeps", "gradual layering", "energy curves"],
        "total_length": "5-8 minutes",
        "notes": "Additive/subtractive -- layers enter and exit gradually.",
    },

    # === Mixing ===
    "mixing": {
        "frequency_balance": "bass-heavy with clear high-end",
        "key_frequencies": {"sub_bass": "30-60 Hz", "kick_fundamental": "60-100 Hz"},
        "stereo_image": "kick/bass/snare center, hats/pads wide",
        "effects": ["sidechain compression on bass from kick", "reverb on claps"],
        "loudness_target": "-6 to -8 LUFS",
        "notes": "Sidechain compression is essential to the pumping feel.",
    },

    # === Ableton-Specific Tips ===
    "ableton_tips": {
        "instruments": ["Operator for bass", "Wavetable for pads", "Drum Rack for drums"],
        "effects": ["Compressor (sidechain)", "Auto Filter", "Reverb"],
        "workflow_tips": ["Start with 8-bar loop", "Use Session View for jamming"],
    },
}
```

### Schema Rationale

| Section | Maps To | Purpose |
|---------|---------|---------|
| `instrumentation` | Track/device tools (create tracks, load instruments) | What to build |
| `harmony` | Theory tools (chord types, scales, progressions by name) | What notes to use |
| `rhythm` | Rhythm pattern selection, groove settings | How notes feel |
| `arrangement` | Arrangement tools, scene management | Song structure |
| `mixing` | Mixer tools (volume, pan, effects, sends) | How it sounds |
| `ableton_tips` | Browser/device tools (specific Ableton instruments) | DAW-specific guidance |

### Subgenre Merge Strategy

Subgenres override parent values at the top level. A shallow merge -- subgenre keys replace parent keys entirely (no deep dict merging) to keep behavior predictable:

```python
def get_blueprint(genre: str, subgenre: str | None = None) -> dict:
    base = GENRE_CATALOG[genre].copy()
    if subgenre and subgenre in base.get("subgenres", {}):
        overrides = base["subgenres"][subgenre]
        for key, value in overrides.items():
            base[key] = value
    # Remove subgenres dict from output (not needed by caller)
    base.pop("subgenres", None)
    return base
```

## MCP Delivery: Tools vs Resources Decision

### Why Tools, Not Resources

| Factor | Tools (`@mcp.tool`) | Resources (`@mcp.resource`) |
|--------|---------------------|----------------------------|
| Control | Model-controlled (Claude decides when to fetch) | Application-controlled (user must select in client UI) |
| Client support | Universal across all MCP clients | Inconsistent -- some clients hide or poorly support resources |
| Existing pattern | All 197 existing capabilities are tools | Zero resources in the codebase |
| Discovery | Claude sees tool descriptions, calls when genre is mentioned | User must know to browse and attach a resource before chatting |
| Dynamic params | Supports genre/subgenre/sections naturally | URI templates are less expressive |
| Autonomy | Claude proactively loads relevant genre info | Breaks if user forgets to select the resource |

**Decision: Tools.** Resources would require users to manually attach genre context before every conversation. With tools, Claude autonomously fetches blueprint data when a user mentions "make me a techno track." This is the natural UX.

### Tool Design (3 Tools)

Following the project's granular tool philosophy (23 theory tools, each doing one thing):

```python
@mcp.tool()
def list_genre_blueprints(ctx: Context, category: str | None = None) -> str:
    """List available genre/style blueprints. Returns genre names, subgenres, BPM ranges,
    and brief descriptions. Use this to discover what genres are available before
    fetching a full blueprint.

    Parameters:
    - category: Optional filter (e.g., "electronic", "urban", "ambient")
    """

@mcp.tool()
def get_genre_blueprint(ctx: Context, genre: str, subgenre: str | None = None,
                         sections: list[str] | None = None) -> str:
    """Get a genre/style blueprint with production conventions covering instrumentation,
    harmony, rhythm, arrangement, and mixing. Use this when producing music in a
    specific genre to get authoritative guidance on conventions.

    Parameters:
    - genre: Genre identifier (e.g., "house", "techno", "drum_and_bass")
    - subgenre: Optional subgenre (e.g., "deep_house", "minimal_techno")
    - sections: Optional list of sections to return (e.g., ["harmony", "rhythm"]).
                Returns all sections if omitted. Useful to save tokens.
    """

@mcp.tool()
def get_genre_palette(ctx: Context, genre: str, key: str = "C",
                       subgenre: str | None = None) -> str:
    """Get a ready-to-use harmonic palette for a genre: chords, scales, and progressions
    resolved to a specific musical key. Bridges genre conventions with the theory engine.

    Parameters:
    - genre: Genre identifier (e.g., "house", "techno", "neo_soul")
    - key: Musical key to resolve to (e.g., "C", "Eb", "F#")
    - subgenre: Optional subgenre for more specific conventions
    """
```

### The `get_genre_palette` Bridge

This is the one place where blueprints and theory intersect at the code level. It reads a blueprint's harmony conventions and calls theory functions to produce concrete output:

```python
# tools/blueprints.py (simplified)
from MCP_Server.theory import build_chord, get_scale_pitches, generate_progression

@mcp.tool()
def get_genre_palette(ctx, genre, key="C", subgenre=None):
    blueprint = _get_blueprint(genre, subgenre)
    harmony = blueprint["harmony"]

    chords = []
    for quality in harmony["chord_types"][:6]:
        try:
            chords.append(build_chord(key, quality))
        except Exception:
            pass  # Skip unsupported qualities gracefully

    scales = []
    for scale_type in harmony["scales"][:3]:
        try:
            scales.append(get_scale_pitches(key, scale_type))
        except Exception:
            pass

    return json.dumps({
        "key": key, "genre": genre,
        "suggested_chords": chords,
        "suggested_scales": scales,
        "bpm_range": blueprint["bpm_range"],
        "rhythm_feel": blueprint["rhythm"]["feel"],
    }, indent=2)
```

## Patterns to Follow

### Pattern 1: Python Catalog (from Theory Engine)

Module-level dicts, registered in a central catalog, exposed through a clean public API. This is exactly how `PROGRESSION_CATALOG`, `RHYTHM_CATALOG`, and `SCALE_CATALOG` work.

### Pattern 2: Thin Tool Wrappers (from Theory Tools)

Every tool in `tools/theory.py` follows: validate input, call library function, `json.dumps()` result, catch exceptions with `format_error()`. Blueprint tools follow identically.

### Pattern 3: Section Filtering for Token Economy

A full blueprint is 2000+ tokens. The `sections` parameter on `get_genre_blueprint` lets Claude request only what it needs (e.g., just `["harmony"]` when building chords). This avoids flooding context with irrelevant mixing tips when the user is focused on chord progressions.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Markdown Blob Blueprints
Storing blueprints as markdown and returning raw text. Unstructured text cannot be filtered by section, cannot be programmatically cross-referenced, and is harder for Claude to parse reliably than JSON.

### Anti-Pattern 2: Blueprint-Theory Tight Coupling
Having blueprint modules import theory functions at load time or embed MIDI data. Creates circular dependency risk and makes blueprints fragile to theory changes. Blueprints store convention **names**; only `get_genre_palette` bridges at runtime.

### Anti-Pattern 3: Single Mega-File
All genres in one 1400-line `catalog.py`. Impossible to review or maintain. One file per genre.

### Anti-Pattern 4: MCP Resources
Using `@mcp.resource("blueprint://house")`. Resources are application-controlled, not model-controlled. Claude cannot autonomously fetch blueprints when it recognizes a genre. Also introduces a new primitive type the codebase has never used.

### Anti-Pattern 5: Deep Dict Merging for Subgenres
Recursive dict merging where subgenre partially overrides nested dicts. Behavior becomes unpredictable. Shallow merge (subgenre key replaces parent key entirely) is simple and sufficient.

## Integration Points: New vs Modified

### New Components (to build)

| Component | Lines (est.) | Dependencies |
|-----------|-------------|--------------|
| `MCP_Server/blueprints/__init__.py` | ~30 | None |
| `MCP_Server/blueprints/catalog.py` | ~80 | Genre modules |
| `MCP_Server/blueprints/schema.py` | ~40 | None |
| `MCP_Server/blueprints/genres/__init__.py` | ~15 | Genre modules |
| `MCP_Server/blueprints/genres/*.py` (12 files) | ~80-120 each | None |
| `MCP_Server/tools/blueprints.py` | ~120 | `blueprints/`, `theory/`, `server.mcp` |
| `tests/test_blueprints.py` | ~200 | `blueprints/` |
| **Total new code** | **~1500-2000** | |

### Modified Components (2 files, minimal changes)

| Component | Change | Lines Changed |
|-----------|--------|--------------|
| `MCP_Server/tools/__init__.py` | Add `blueprints` to import list | 1 line |
| `pyproject.toml` | Add `MCP_Server.blueprints`, `MCP_Server.blueprints.genres` to packages | 2 lines |

## Suggested Build Order

| Order | Phase | What | Why This Order |
|-------|-------|------|----------------|
| 1 | Schema + Catalog | `schema.py`, `catalog.py`, `genres/__init__.py` | Foundation everything else depends on |
| 2 | First Genre | `genres/house.py` (canonical example) | Validates schema with real data |
| 3 | Core Tools | `tools/blueprints.py` with `list_genre_blueprints`, `get_genre_blueprint` | End-to-end validation: data -> API |
| 4 | Tests | `test_blueprints.py` for catalog + tools | Regression safety before scaling |
| 5 | Remaining Genres | 11 more `genres/*.py` files | Schema validated, now scale content |
| 6 | Palette Bridge | `get_genre_palette` tool | Requires both blueprints and theory; build last |
| 7 | Integration | Wire into `tools/__init__.py`, update `pyproject.toml` | Final wiring (trivial, but last to avoid import issues during dev) |

**Rationale:** Front-load architectural decisions (schema, catalog, tools) and validate with one genre before committing to content for all 12. The palette bridge tool depends on both blueprints and theory being stable, so it comes last.

## Sources

- Existing codebase: `MCP_Server/theory/progressions.py` (PROGRESSION_CATALOG), `MCP_Server/theory/rhythm.py` (RHYTHM_CATALOG), `MCP_Server/tools/theory.py` (tool wrapper pattern), `MCP_Server/server.py` (FastMCP setup), `MCP_Server/tools/__init__.py` (import-based registration)
- [MCP Resources vs Tools](https://medium.com/@laurentkubaski/mcp-resources-explained-and-how-they-differ-from-mcp-tools-096f9d15f767) -- Resources are application-controlled, tools are model-controlled
- [MCP Features Guide](https://workos.com/blog/mcp-features-guide) -- Tools, Resources, Prompts interaction patterns
- [FastMCP Resource/Prompt docs](https://gofastmcp.com/servers/prompts) -- Decorator syntax and usage
- [FastMCP Tutorial](https://gofastmcp.com/tutorials/create-mcp-server) -- Server patterns

---
*Architecture research for: v1.2 Genre/Style Blueprints*
*Researched: 2026-03-25*
