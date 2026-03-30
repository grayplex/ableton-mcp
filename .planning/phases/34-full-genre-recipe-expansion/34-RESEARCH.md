# Phase 34: Full Genre Recipe Expansion - Research

**Researched:** 2026-03-30
**Domain:** Music production mixing recipe data authoring (pure data, no new tools)
**Confidence:** HIGH

## Summary

Phase 34 is a pure data-authoring phase: create 8 new genre recipe files in `MCP_Server/mixing/`, add genre aliases to `catalog.py`, and update 4 tool docstrings. No new MCP tools, no new Remote Script handlers. The existing auto-discovery system (`pkgutil.iter_modules`) means new `.py` files with `RECIPE` and `MASTER_RECIPE` constants are automatically registered at runtime.

The existing 4 genre files (house, techno, ambient, drum_and_bass) establish a rigid pattern: comment header referencing D-01..D-04, `RECIPE` dict keyed by 9 roles, each role mapping device class names to parameter dicts, followed by `MASTER_RECIPE` with GlueCompressor + MultibandDynamics + Limiter. Every parameter name must exist in the CATALOG. The existing test suite (`tests/test_mixing.py`) dynamically iterates `_registry.items()`, so new genres are automatically validated for schema correctness, role completeness, and catalog-verified parameter names.

**Primary recommendation:** Mirror the exact structure of `house.py` for all 8 new files. The `_MASTER_GENRES` hardcoded list in tests must be updated to include all 12 genres. Add D-08 aliases to `_GENRE_ALIASES` in `catalog.py`. Update 4 tool docstrings per D-09.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Recipe values in natural units (Hz, dB, ms, %, not normalized 0.0-1.0)
- **D-02:** Sound-shaping params only -- no `Device On`, `LegacyMode`, or housekeeping params
- **D-03:** All 9 roles authored for every genre (kick, bass, lead, pad, chords, vocal, atmospheric, return, master)
- **D-04:** Omit inapplicable devices entirely -- no None markers
- **D-05:** One file per genre in `MCP_Server/mixing/`, pkgutil auto-discovery, zero registration code
- **D-07:** Two plans split by genre family: Plan 34-01 (electronic: synthwave, dubstep, trance, future_bass) and Plan 34-02 (groove/organic: hip_hop_trap, disco_funk, neo_soul_rnb, lo_fi). Each plan includes MASTER_RECIPE for its 4 genres.
- **D-08:** Minimal alias set: `hip-hop` -> `hip_hop_trap`, `hip_hop` -> `hip_hop_trap`, `r_b` -> `neo_soul_rnb`, `disco_funk` already canonical. Added to `_GENRE_ALIASES` in `catalog.py`.
- **D-09:** After Phase 34, all four mixing tools must replace hardcoded genre lists with reference to `list_recipes()`.

### Claude's Discretion
- Exact natural-unit parameter values for each role/genre combination (musical authoring)
- Which devices are present per role in each genre (omit inapplicable per D-04)
- Non-typical role/genre pairings receive safe generic values (per D-03)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RECIP-02 | User can retrieve a role x genre mix recipe for all 12 genres -- extends RECIP-01 to synthwave, hip-hop/trap, dubstep, trance, lo-fi, future bass, disco/funk, and neo-soul/R&B | 8 new recipe files following existing house.py pattern; auto-discovery handles registration; existing tests validate schema |
| MSTR-01 | User can retrieve a master bus recipe for any of the 12 genres -- returns Glue Compressor + Multiband Dynamics + Limiter chain appropriate to that genre's loudness and tonal conventions | MASTER_RECIPE constant at bottom of each new file; 3 devices with catalog-verified param names; genre-appropriate loudness settings |
</phase_requirements>

## Architecture Patterns

### File Structure (mirror exactly)
```
MCP_Server/mixing/
  __init__.py           # existing, no changes
  catalog.py            # add D-08 aliases only
  house.py              # existing reference
  techno.py             # existing reference
  ambient.py            # existing reference
  drum_and_bass.py      # existing reference
  synthwave.py          # NEW (Plan 34-01)
  dubstep.py            # NEW (Plan 34-01)
  trance.py             # NEW (Plan 34-01)
  future_bass.py        # NEW (Plan 34-01)
  hip_hop_trap.py       # NEW (Plan 34-02)
  disco_funk.py         # NEW (Plan 34-02)
  neo_soul_rnb.py       # NEW (Plan 34-02)
  lo_fi.py              # NEW (Plan 34-02)
```

### Recipe File Template
Every new file MUST follow this exact structure (derived from house.py):

```python
# {Genre} genre mix recipe
# Per D-01: All values in natural units (Hz, dB, ms, %, 0-1 for raw params)
# Per D-02: Sound-shaping params only (no Device On, S/C Listen, etc.)
# Per D-03: All 9 roles present
# Per D-04: Omit devices not applicable (no None markers)
#
# Structure: RECIPE[role][device_class][param_name] = value
# Device class names match CATALOG keys exactly.
# Param names match CATALOG entries exactly.
#
# Eq8 Filter Types: 0=48dB/oct, 1=12dB/oct, 2=Low Shelf, 3=Bell, 4=Notch,
#                   5=High Shelf, 6=LP (12dB), 7=HP (12dB)
# Compressor2 Model: 0=Peak, 1=RMS, 2=Expand
# DrumBuss Drive Type: 0=Soft, 1=Medium, 2=Hard

RECIPE = {
    "kick": { ... },
    "bass": { ... },
    "lead": { ... },
    "pad": { ... },
    "chords": { ... },
    "vocal": { ... },
    "atmospheric": { ... },
    "return": { ... },
    "master": { ... },
}

# ---------------------------------------------------------------------------
# Master bus recipe: GlueCompressor -> MultibandDynamics -> Limiter
# {Genre description} -- {genre} master chain
# All values in natural units; converted to normalized by devices.convert
# Param names match CATALOG keys exactly
# ---------------------------------------------------------------------------

MASTER_RECIPE = {
    "GlueCompressor": { ... },
    "MultibandDynamics": { ... },
    "Limiter": { ... },
}
```

### Device Classes Available (from CATALOG)
These are the only valid device class keys:
- `Eq8` -- EQ (used in every role)
- `Compressor2` -- Compressor (most roles)
- `DrumBuss` -- Drum Bus (kick, sometimes bass)
- `Reverb` -- Reverb (lead, pad, chords, vocal, atmospheric, return)
- `Delay` -- Delay (lead, chords, vocal, atmospheric, return)
- `Gate` -- Gate (vocal, sometimes kick)
- `AutoFilter` -- Auto Filter (atmospheric, sometimes lead/pad)
- `StereoGain` -- Utility (every role for gain/width/mono)
- `GlueCompressor` -- Glue Compressor (MASTER_RECIPE only)
- `MultibandDynamics` -- Multiband Dynamics (MASTER_RECIPE only)
- `Limiter` -- Limiter (MASTER_RECIPE only)

### Canonical Roles (all 9, every genre)
`kick`, `bass`, `lead`, `pad`, `chords`, `vocal`, `atmospheric`, `return`, `master`

### MASTER_RECIPE Parameter Template
All 8 new genres need this exact parameter set (values vary by genre):

```python
MASTER_RECIPE = {
    "GlueCompressor": {
        "Threshold": ...,        # dB (-40 to 0)
        "Ratio": ...,            # 0-2 range
        "Attack": ...,           # 0-6 raw range
        "Release": ...,          # 0-6 raw range
        "Makeup": ...,           # dB (-15 to 15)
        "Dry/Wet": 100.0,        # % always 100
        "Peak Clip In": 0,       # off
        "Range": ...,            # 0-70 raw range
    },
    "MultibandDynamics": {
        "Master Output": 0.0,
        "Band Activator (High)": 1,
        "Band Activator (Mid)": 1,
        "Band Activator (Low)": 1,
        "Above Threshold (Low)": ...,    # dB
        "Above Ratio (Low)": ...,        # -1 to 1
        "Above Threshold (Mid)": ...,
        "Above Ratio (Mid)": ...,
        "Above Threshold (High)": ...,
        "Above Ratio (High)": ...,
        "Input Gain (Low)": 0.0,
        "Input Gain (Mid)": 0.0,
        "Input Gain (High)": 0.0,
    },
    "Limiter": {
        "Input Gain": ...,       # dB (-15 to 15)
        "Ceiling": ...,          # 0-1 raw
        "Link": 1.0,
        "Lookahead": 1,          # 0=off, 1=1ms, 2=6ms
    },
}
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Genre registration | Manual import/register code | pkgutil auto-discovery in catalog.py | D-05: zero registration code |
| Parameter validation | Custom validation logic | Existing test_mixing.py dynamic iteration | Tests already iterate _registry.items() |
| Alias resolution | Hardcoded if/else chains | _GENRE_ALIASES dict + _normalize() | Existing pattern handles spaces, hyphens, case |

## Common Pitfalls

### Pitfall 1: Wrong Parameter Names
**What goes wrong:** Using parameter names that don't exactly match CATALOG entries causes silent recipe failures.
**Why it happens:** Param names are case-sensitive and use specific formatting (e.g., parenthesized format for MultibandDynamics: `Above Threshold (Low)`).
**How to avoid:** Copy parameter names verbatim from existing recipe files. Run `pytest tests/test_mixing.py` after each file -- the `test_all_recipe_params_in_catalog` test catches mismatches immediately.
**Warning signs:** Test failures mentioning "param X not in catalog."

### Pitfall 2: Compressor2 Ratio Uses 0.0-1.0 Range
**What goes wrong:** Writing ratio as `4` meaning 4:1 instead of `0.6` (the normalized 0-1 value the CATALOG expects).
**Why it happens:** Natural instinct is to write compression ratios as 2:1, 4:1, etc.
**How to avoid:** Compressor2 `Ratio` is stored as 0.0-1.0 in the CATALOG. Reference existing files: 0.35 = ~2:1, 0.4 = ~2.5:1, 0.5 = ~3:1, 0.55 = ~3.5:1, 0.6 = ~4:1, 0.8 = ~8:1.
**Warning signs:** Unreasonably crushed audio.

### Pitfall 3: Missing Roles
**What goes wrong:** Forgetting one of the 9 roles in a genre file.
**Why it happens:** Some roles feel inapplicable to certain genres (e.g., "vocal" in dubstep).
**How to avoid:** D-03 mandates all 9 roles. Non-typical pairings get safe generic values. Test `test_all_genres_have_all_roles` catches this.
**Warning signs:** Test failure mentioning "Genre X missing role Y."

### Pitfall 4: Hardcoded _MASTER_GENRES in Tests
**What goes wrong:** New genres pass dynamic recipe validation but master recipe tests still only check the original 4 genres.
**Why it happens:** `_MASTER_GENRES` in `tests/test_mixing.py` line 319 is hardcoded to `["house", "techno", "ambient", "drum_and_bass"]`.
**How to avoid:** Update `_MASTER_GENRES` to include all 12 genres, or better, replace with dynamic `list(_master_registry.keys())`.
**Warning signs:** Master recipe tests pass but new genres' MASTER_RECIPE is never validated.

### Pitfall 5: GlueCompressor Dry/Wet Is 100.0 Not 1.0
**What goes wrong:** Writing `"Dry/Wet": 1.0` instead of `"Dry/Wet": 100.0` for the GlueCompressor.
**Why it happens:** Confusing normalized (0-1) with natural (0-100%) units.
**How to avoid:** D-01 specifies natural units. All existing MASTER_RECIPE files use `100.0` for Dry/Wet.
**Warning signs:** GlueCompressor doing almost nothing (1% wet).

### Pitfall 6: Tool Docstring Suggestion Lines Still Hardcode Genres
**What goes wrong:** Error messages in `format_error()` calls within `mixing.py` and `intelligence.py` still list "house, techno, ambient, dnb" even after adding 8 new genres.
**Why it happens:** D-09 only mentions docstrings, but the `suggestion=` kwargs in `format_error()` calls also hardcode genre lists.
**How to avoid:** Update both the docstrings AND the `suggestion=` strings in `format_error()` calls to reference `list_recipes()` dynamically.
**Warning signs:** Error messages showing only 4 genres when 12 exist.

## Code Integration Points

### Files to Create (8 new recipe files)
| File | Genre | Plan |
|------|-------|------|
| `MCP_Server/mixing/synthwave.py` | synthwave | 34-01 |
| `MCP_Server/mixing/dubstep.py` | dubstep | 34-01 |
| `MCP_Server/mixing/trance.py` | trance | 34-01 |
| `MCP_Server/mixing/future_bass.py` | future_bass | 34-01 |
| `MCP_Server/mixing/hip_hop_trap.py` | hip_hop_trap | 34-02 |
| `MCP_Server/mixing/disco_funk.py` | disco_funk | 34-02 |
| `MCP_Server/mixing/neo_soul_rnb.py` | neo_soul_rnb | 34-02 |
| `MCP_Server/mixing/lo_fi.py` | lo_fi | 34-02 |

### Files to Modify
| File | Change | Plan |
|------|--------|------|
| `MCP_Server/mixing/catalog.py` | Add D-08 aliases to `_GENRE_ALIASES` | 34-01 (or 34-02) |
| `MCP_Server/tools/mixing.py` | Update docstrings + `suggestion=` for `get_mix_recipe`, `apply_mix_recipe`, `apply_master_recipe` per D-09 | 34-02 |
| `MCP_Server/tools/intelligence.py` | Update `suggest_mix_adjustments` docstring + `suggestion=` per D-09 | 34-02 |
| `tests/test_mixing.py` | Update `_MASTER_GENRES` to include all 12 genres | 34-02 |

### Genre-Specific Mixing Guidance (Claude's Discretion)

These are musical guidelines for parameter authoring -- exact values are at implementer's discretion:

**Electronic/Synth-Heavy (Plan 34-01):**
- **Synthwave:** Warm, lush, 80s analog aesthetic. Heavy reverb on leads/pads, chorus-like stereo width, gentle compression. Master: moderate loudness, warm low end.
- **Dubstep:** Aggressive bass, heavy sub, distorted mids. DrumBuss on kick/bass, aggressive compression (0.7-0.8 ratio). Master: loud, heavy limiting, strong low band compression.
- **Trance:** Driving, euphoric, wide stereo pads. Long reverb tails on pads/leads, ping-pong delays, moderate compression. Master: loud, punchy, clean high end.
- **Future Bass:** Heavy sidechain feel, lush chords, wide stereo. Aggressive chord compression, reverb-heavy pads. Master: loud but not crushed, wide stereo image.

**Groove/Organic (Plan 34-02):**
- **Hip-Hop/Trap:** Hard-hitting kick/808, crisp vocals, dry mix overall. Gate on vocals, minimal reverb except on vocals/atmospheric. Master: very loud, heavy limiting.
- **Disco/Funk:** Groovy, warm, dynamic. Less compression than electronic genres (preserve dynamics), warm EQ, moderate reverb. Master: moderate loudness, preserve dynamics.
- **Neo-Soul/R&B:** Smooth, warm, vocal-forward. Gentle compression, warm low-shelf EQ boosts, intimate reverb. Master: moderate loudness, warm character.
- **Lo-Fi:** Deliberately imperfect, warm, filtered. High-shelf cuts for muffled sound, DrumBuss for warmth, short reverb. Master: gentle limiting, lo-fi character.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pytest.ini` or default |
| Quick run command | `pytest tests/test_mixing.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RECIP-02 | All 12 genres have 9-role recipes with catalog-verified params | unit | `pytest tests/test_mixing.py::TestRecipeParameterNames -x` | Exists (dynamic, auto-covers new genres) |
| RECIP-02 | All 12 genres have all 9 roles | unit | `pytest tests/test_mixing.py::TestRecipeCompleteness -x` | Exists (dynamic) |
| MSTR-01 | All 12 genres have MASTER_RECIPE with 3 devices | unit | `pytest tests/test_mixing.py::TestMasterRecipeData -x` | Exists but _MASTER_GENRES hardcoded to 4 |
| MSTR-01 | Master recipe params in CATALOG | unit | `pytest tests/test_mixing.py::TestMasterRecipeData::test_all_master_recipe_params_in_catalog -x` | Exists but scope limited to 4 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_mixing.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_mixing.py` -- update `_MASTER_GENRES` from hardcoded 4-genre list to all 12 (or dynamic `list(_master_registry.keys())`)

## Sources

### Primary (HIGH confidence)
- `MCP_Server/mixing/house.py` -- reference RECIPE + MASTER_RECIPE structure (683 lines)
- `MCP_Server/mixing/drum_and_bass.py` -- reference for aggressive genre patterns
- `MCP_Server/mixing/techno.py` -- reference MASTER_RECIPE values
- `MCP_Server/mixing/catalog.py` -- auto-discovery, alias resolution, _GENRE_ALIASES
- `MCP_Server/devices/__init__.py` -- CATALOG, ROLES
- `MCP_Server/tools/mixing.py` -- 3 tool docstrings to update
- `MCP_Server/tools/intelligence.py` -- 1 tool docstring to update
- `tests/test_mixing.py` -- test infrastructure, _MASTER_GENRES hardcoded list

### Secondary (MEDIUM confidence)
- Genre-specific mixing conventions are musical knowledge, not code-verified

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, pure data files following established pattern
- Architecture: HIGH -- pattern is rigid and well-documented across 4 existing files
- Pitfalls: HIGH -- verified by reading test code and identifying hardcoded vs dynamic validation

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable -- no external dependency changes expected)
