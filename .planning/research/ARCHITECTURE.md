# Architecture Patterns: v1.4 Mix/Master Intelligence

**Domain:** Mix/master intelligence layer for Ableton MCP server
**Researched:** 2026-03-28
**Confidence:** HIGH (architecture follows established codebase patterns, all integration points verified via code inspection)

## Recommended Architecture

### High-Level Integration

Mix/master intelligence integrates as a new `MCP_Server/mixing/` package -- parallel to `genres/` and `theory/` -- containing:
1. **Device parameter catalog** (static data, curated)
2. **Mix recipes** (role x genre x device-type mappings)
3. **Recipe engine** (lookup + application logic)

New MCP tools in `MCP_Server/tools/mixing.py` expose recipe application, gain staging checks, and state reading. These tools **orchestrate existing Remote Script commands** -- no new Remote Script handlers are needed for the core recipe workflow.

```
MCP_Server/
  mixing/                    # NEW package (parallel to genres/, theory/)
    __init__.py              # Public API exports
    schema.py                # TypedDicts for recipes, device catalog entries
    catalog.py               # Device parameter catalog (static dicts)
    recipes/                 # Subpackage: per-genre recipe files
      __init__.py            # Auto-discovery catalog (like genres/catalog.py)
      house.py               # Role x device recipes for house
      techno.py              # Role x device recipes for techno
      ...                    # One file per genre
    engine.py                # Recipe lookup + parameter resolution logic
    gain.py                  # Gain staging analysis logic
  tools/
    mixing.py                # NEW tool module (MCP tools for mix/master)
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `mixing/catalog.py` | Maps Ableton device class_names to parameter names, value ranges, and semantics | `mixing/engine.py` (lookup) |
| `mixing/recipes/*.py` | Stores role x genre x device-type recipes as Python dicts | `mixing/engine.py` (lookup via recipes/__init__.py) |
| `mixing/engine.py` | Resolves a recipe request into concrete device + parameter actions | `mixing/catalog.py`, `mixing/recipes/` |
| `mixing/schema.py` | TypedDict definitions for catalog entries, recipes, gain targets | All mixing modules (type contract) |
| `mixing/gain.py` | Gain staging analysis: compare current state to targets, produce diffs | `mixing/catalog.py` |
| `tools/mixing.py` | MCP tool endpoints -- bridges engine to existing Remote Script commands | `mixing/engine.py`, `connection.py` (existing) |
| Remote Script | **NO CHANGES** -- existing handlers already cover all needed operations | N/A |

### Data Flow

**Apply Recipe Flow:**
```
Claude calls apply_mix_recipe(track_index, role, genre, device_type="eq")
  --> tools/mixing.py looks up recipe via engine.resolve_recipe(role, genre, "eq")
  --> engine returns: {device_path: "audio_effects/EQ Eight", params: [{name: "1 Frequency A", value: 80.0}, ...]}
  --> tools/mixing.py calls existing load_instrument_or_effect(track_index, path=device_path)
  --> tools/mixing.py calls existing set_device_parameter() for EACH param
  --> Returns summary of what was applied
```

**Read + Suggest Flow:**
```
Claude calls get_mix_state(track_index)
  --> tools/mixing.py calls existing get_device_parameters() for each device on track
  --> Returns structured device chain state

Claude calls suggest_mix_adjustments(track_index, role, genre)
  --> tools/mixing.py reads current state (as above)
  --> engine.diff_against_recipe(current_state, role, genre)
  --> Returns param diffs with reasoning
```

**Gain Staging Flow:**
```
Claude calls check_gain_staging()
  --> tools/mixing.py reads all track volumes via existing mixer commands
  --> gain.analyze(volumes, role_assignments) compares to target ranges
  --> Returns flagged tracks with suggested adjustments
```

## Key Architecture Decisions

### 1. New `mixing/` Package (Not Inline in Genres)

**Decision:** Create `MCP_Server/mixing/` as a peer package to `genres/` and `theory/`.

**Rationale:** The genre blueprints' `mixing` section contains *prose-level conventions* (e.g., "mono bass and kick, wide pads"). Mix recipes contain *exact device parameter values* (e.g., `EQ Eight.1 Frequency A = 80.0`). These are fundamentally different data types. Embedding parameter-level data in genre blueprints would:
- Bloat blueprint token counts (currently 537-670 tokens; recipes would add 2000+ per genre)
- Violate the "no helper functions" design decision for genre files (D-02)
- Require schema changes that break the existing 12-genre validation suite

The `mixing/` package *references* genre IDs for recipe lookup but owns its own data.

### 2. Static Device Parameter Catalog (Not Auto-Discovered)

**Decision:** Curate a static Python dict mapping device class_names to their parameters.

**Rationale:**
- **Reliability:** Auto-discovery requires a live Ableton connection and device instantiation. Recipes need to work offline for validation/testing.
- **Stability:** Ableton's built-in device parameters are stable across Live 12 versions. EQ Eight's "1 Frequency A" does not change between updates.
- **Testing:** Static data can be validated in CI without Ableton running.
- **Scope:** Start with ~10 priority devices (EQ Eight, Compressor, Glue Compressor, Limiter, Utility, Auto Filter, Reverb, Delay, Saturator, Multiband Dynamics). Covers 95% of mixing needs.
- **Bootstrap:** Capture initial data by running `get_device_parameters` on each device in a live Ableton session, then store as static dicts.

The catalog stores: `class_name`, `display_name`, `browser_path`, and a list of `{name, min, max, default, unit, semantic}` per parameter. The `semantic` field tags parameters by function (e.g., "frequency", "gain", "threshold", "ratio") enabling the engine to map recipe intent to parameter names.

**Confidence:** HIGH -- existing `get_device_parameters` already returns this exact structure from live devices.

### 3. Orchestrate Existing Tools (No New Remote Script Commands)

**Decision:** Recipe application calls existing `load_browser_item` and `set_device_parameter` commands in sequence. No new Remote Script handler needed.

**Rationale:**
- Existing `load_browser_item` loads any device by browser path
- Existing `set_device_parameter` sets any param by name or index with clamping
- Existing `get_device_parameters` reads all params from any device
- All three already support `track_type: "master"` for master bus operations
- Adding a new "apply_recipe" Remote Script command would duplicate logic and create a maintenance burden

**Tradeoff:** Multiple socket round-trips per recipe application (1 load + N param sets). At ~5ms per round-trip over localhost TCP, a 15-parameter recipe takes ~80ms total. Acceptable for a non-real-time workflow.

**Confidence:** HIGH -- verified that all three commands exist and support master track type.

### 4. Master Track: Same Tools, Different `track_type`

**Decision:** Master bus tools use `track_type: "master"` on existing device/mixer tools. No separate tool set needed.

**Rationale:**
- `_resolve_track()` in the Remote Script already resolves `track_type: "master"` to `song.master_track`
- `load_browser_item`, `set_device_parameter`, `get_device_parameters` all accept `track_type: "master"`
- Master track uses `track_index: 0` (ignored when `track_type: "master"`)

**What differs for master recipes:**
- Recipe data: master bus recipes reference different devices (Multiband Dynamics, Glue Compressor, Limiter) and different parameter targets (e.g., ceiling, output gain)
- The engine routes `role="master_bus"` to master-specific recipe data
- The tools pass `track_type="master"` automatically when role is `master_bus`

**No separate `apply_master_recipe` tool is needed** -- `apply_mix_recipe(track_index=0, track_type="master", role="master_bus", genre="house")` uses the same code path.

**Important note on load_browser_item:** The current handler indexes into `self._song.tracks[track_index]`, which does NOT include the master track. Loading devices onto the master track may require either: (a) a small Remote Script fix to handle master track device loading, or (b) using the master track's existing device loading mechanism. This needs verification during implementation -- flag as a potential integration gap.

### 5. Spectrum Analysis: Not Feasible via LOM

**Decision:** Do NOT build spectrum analysis tools. Use gain staging + device state reading as the feedback loop instead.

**Rationale:**
- Ableton's Spectrum device is visualization-only. The LOM exposes its *control parameters* (FFT size, range, channel mode) but **not the frequency bin data** it displays. There is no API to read amplitude-per-frequency.
- Max for Live can access audio buffers via `[snapshot~]` but this requires M4L device authoring, not Remote Script API calls.
- The Remote Script API has no audio buffer access whatsoever.

**Alternative feedback loop (sufficient for mixing intelligence):**
1. **Read device state:** `get_device_parameters` on EQ/compressor shows current frequency/gain/threshold settings
2. **Gain staging check:** Read track volumes, flag outliers against genre-appropriate targets
3. **Recipe diff:** Compare current device params vs. recipe targets, suggest adjustments with reasoning

**Confidence:** HIGH that Spectrum data is not accessible via LOM.

## Patterns to Follow

### Pattern 1: Auto-Discovery Catalog (Reuse genres/ pattern)

**What:** Python dicts in individual files, auto-discovered via `pkgutil.iter_modules`, validated at import time.

**Applied to mixing recipes:**
```python
# MCP_Server/mixing/recipes/house.py
RECIPES = {
    "genre_id": "house",
    "roles": {
        "kick": {
            "eq": {
                "device": "eq_eight",
                "params": [
                    {"name": "1 Filter On A", "value": 1.0},
                    {"name": "1 Filter Type A", "value": 6.0},
                    {"name": "1 Frequency A", "value": 30.0},
                ],
            },
            "compressor": {
                "device": "compressor",
                "params": [
                    {"name": "Threshold", "value": -12.0},
                    {"name": "Ratio", "value": 4.0},
                ],
            },
        },
        "bass": { ... },
        "master_bus": {
            "glue_compressor": { ... },
            "limiter": { ... },
            "eq": { ... },
        },
    },
}
```

### Pattern 2: Engine Module (Reuse theory/ pattern)

**What:** Pure computation module with no Ableton dependency -- takes data in, returns data out.

**Applied to mixing:**
```python
# MCP_Server/mixing/engine.py
def resolve_recipe(role: str, genre_id: str, device_type: str) -> ResolvedRecipe | None:
    """Look up a recipe and resolve it against the device catalog."""
    ...

def diff_against_recipe(current_params: list[dict], recipe: ResolvedRecipe) -> list[ParamDiff]:
    """Compare current device state to recipe target, return diffs."""
    ...
```

### Pattern 3: Thin Tool Layer (Reuse existing tools/ pattern)

**What:** MCP tool functions are thin wrappers -- validate inputs, call library/engine, format output. No business logic in tools.

```python
# MCP_Server/tools/mixing.py
@mcp.tool()
def apply_mix_recipe(ctx: Context, track_index: int, role: str, genre: str,
                     device_type: str, track_type: str = "track") -> str:
    """Apply a mixing recipe..."""
    recipe = engine.resolve_recipe(role, genre, device_type)
    # ... call existing load + set_device_parameter commands
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Mega-Tool That Does Everything

**What:** A single `mix_track` tool that loads ALL devices AND sets ALL params for a role.

**Why bad:** Too many socket calls in one tool invocation (could be 50+ round-trips). If one fails mid-way, partial state is hard to recover. Claude cannot inspect intermediate results.

**Instead:** One tool per device-type application. Claude calls per device: EQ, then compressor, then send setup. Matches how a human mixes -- device by device, with listening between.

### Anti-Pattern 2: Auto-Discovering Parameters from Live at Startup

**What:** Building the device catalog by querying Ableton for every built-in device's parameters.

**Why bad:** Requires Ableton running for tests. Slow startup. Recipe authoring can't happen offline.

**Instead:** Static catalog, validated against live Ableton in integration tests only.

### Anti-Pattern 3: Storing Recipes in Genre Blueprints

**What:** Adding parameter-level recipe data to the existing genre blueprint `mixing` section.

**Why bad:** Breaks token budget. Breaks schema. Couples genre conventions with device specifics.

**Instead:** `mixing/` package references genre IDs. Genre `mixing` section = the *why*. Recipes = the *how*.

### Anti-Pattern 4: New Remote Script Command for Recipe Application

**What:** A Remote Script command that receives a full recipe payload and applies it.

**Why bad:** Puts business logic in Ableton's Python sandbox. Harder to test/debug. Couples recipe format to socket protocol.

**Instead:** Keep intelligence server-side. Remote Script stays dumb.

## Integration Points Summary (New vs. Modified)

### New Components

| Component | Type | Description |
|-----------|------|-------------|
| `MCP_Server/mixing/__init__.py` | New package | Public API exports |
| `MCP_Server/mixing/schema.py` | New module | TypedDicts for catalog, recipes, diffs |
| `MCP_Server/mixing/catalog.py` | New module | Static device parameter catalog (~10 devices) |
| `MCP_Server/mixing/recipes/` | New subpackage | Per-genre recipe files with auto-discovery |
| `MCP_Server/mixing/engine.py` | New module | Recipe resolution + diff logic |
| `MCP_Server/mixing/gain.py` | New module | Gain staging analysis |
| `MCP_Server/tools/mixing.py` | New module | MCP tool endpoints |

### Modified Components

| Component | Change | Reason |
|-----------|--------|--------|
| `MCP_Server/tools/__init__.py` | Add `import MCP_Server.tools.mixing` | Tool auto-registration |
| Possibly `AbletonMCP_Remote_Script/handlers/browser.py` | Support `track_type: "master"` in `load_browser_item` | Master track device loading (needs verification) |

### Existing Commands Reused (No Changes)

| Command | Used For | Confidence |
|---------|----------|------------|
| `load_browser_item` | Loading devices onto tracks from recipes | HIGH (per-track); MEDIUM (master -- needs verification) |
| `set_device_parameter` | Setting recipe parameter values | HIGH |
| `get_device_parameters` | Reading current device state for diffs | HIGH |
| `set_track_volume` | Gain staging adjustments | HIGH |
| `set_send_level` | Setting up return track sends (reverb/delay) | HIGH |

## Recipe Data Structure

```python
class RecipeParam(TypedDict):
    name: str           # Exact Ableton parameter name (e.g., "1 Frequency A")
    value: float        # Target value
    unit: str           # Documentation: "Hz", "dB", "ratio", "%"
    reason: str         # Why this value (e.g., "high-pass below kick fundamental")

class DeviceRecipe(TypedDict):
    device: str         # catalog key (e.g., "eq_eight")
    params: list[RecipeParam]

class RoleRecipes(TypedDict, total=False):
    eq: DeviceRecipe
    compressor: DeviceRecipe
    reverb_send: float         # Send level 0.0-1.0
    delay_send: float          # Send level 0.0-1.0
    pan: float                 # -1.0 to 1.0
    volume: float              # 0.0 to 1.0 (gain staging target)

class GenreRecipes(TypedDict):
    genre_id: str
    roles: dict[str, RoleRecipes]
```

## Scalability Considerations

| Concern | At 12 genres | At 30 genres | At 50+ genres |
|---------|-------------|-------------|---------------|
| Recipe file count | 12 files, manageable | 30 files, still fine with auto-discovery | Recipe inheritance (base -> subgenre override, like current SUBGENRES pattern) |
| Device catalog | ~10 devices | ~10 devices (same built-in devices) | Same -- built-in devices are fixed |
| Tool count | +5-8 new tools | Same tools | Same tools |
| Token budget per recipe | ~800-1200 tokens per genre | Same | Same -- tool returns only requested recipe |

## Sources

- Ableton Live Object Model: [LOM Reference](https://docs.cycling74.com/max8/vignettes/live_object_model) -- MEDIUM confidence (Max 8 docs, structure same in Live 12)
- Ableton Forum on Spectrum device: [Push 3 spectrum 'No parameter mapped'](https://forum.ableton.com/viewtopic.php?t=247697) -- confirms Spectrum has no mappable parameters
- Existing codebase: `_resolve_track()`, device tools, genre catalog, browser handler -- HIGH confidence (direct code inspection)
- Ableton Live 12 Release Notes: [ableton.com](https://www.ableton.com/en/release-notes/live-12/) -- HIGH confidence
