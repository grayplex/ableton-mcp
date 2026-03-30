---
phase: 33
name: Mix Adjustment Intelligence
status: context-ready
auto: true
---

# Phase 33 Context: Mix Adjustment Intelligence

## Domain Boundary

Deliver a single MCP tool — `suggest_mix_adjustments` — that diffs a track's current device state against the role×genre recipe and returns per-parameter suggestions with one-sentence reasoning. No parameters are changed; this is read-only analysis for review. No new Remote Script command is needed — the tool reads state via the existing `get_mix_state` infrastructure.

## Decisions

### 1. Tool Interface
**Decision:** `suggest_mix_adjustments(track_name: str, genre: str, role: str = None) -> str`

- `track_name` — matched against Ableton session tracks (case-insensitive substring, same pattern as `check_gain_staging`)
- `genre` — required; the recipe lookup key (house, techno, ambient, dnb)
- `role` — optional; inferred from track name via `_infer_role()` if absent; can be overridden

**Why:** Consistent with `check_gain_staging` interface (uses track name, infers role). `apply_mix_recipe` takes `track_index + role + genre` — this tool mirrors the analysis-side pattern, not the write-side pattern.

**Error cases:**
- Track name matches no track → error with message
- Role cannot be inferred and not provided → error: "Cannot infer role from track name '{name}'. Provide role= explicitly."
- No recipe for role×genre combo → error with suggestion

### 2. Diff Computation Strategy
**Decision:** Convert recipe natural-unit values → normalized 0.0–1.0 using existing `natural_to_normalized()` from `MCP_Server.devices.convert`, then compare against current normalized values from `get_mix_state`.

**Why:** `get_mix_state` returns raw normalized values (0.0–1.0) from the RS handler. The conversion module from Phase 31 already handles natural→normalized for all catalog-verified parameters. No inverse-conversion logic needed.

**Implementation path:**
1. Call `get_recipe(role, genre)` to get natural-unit recipe
2. For each device in recipe, iterate parameters
3. Find matching device on track by class name (from `get_mix_state` output)
4. For each parameter: `suggested_normalized = natural_to_normalized(device_class, param, recipe_value)`
5. Look up `current_normalized` from the track's device state
6. Compute delta; apply threshold filter

**Natural-unit reporting:** After computing normalized diff, convert `suggested_normalized` back to natural units for human-readable output. Use catalog `min`/`max` and `conversion` to produce approximate natural-unit values for display.

### 3. Diff Threshold
**Decision:** Skip suggestions where `abs(current_normalized - suggested_normalized) < 0.03`.

**Why:** Avoids noise from floating-point precision and recipe values already close to target. Threshold of 0.03 (~3% of parameter range) filters trivial diffs without missing real adjustments. Fixed constant — no config needed.

### 4. Unloaded Device Handling
**Decision:** If a recipe device is not found on the track's device chain, skip it silently. Do not suggest loading devices.

**Why:** `apply_mix_recipe` is the tool for loading devices + setting parameters. `suggest_mix_adjustments` is for fine-tuning an already-applied setup. Mixing concerns stays clean.

**Device matching:** Match by `class_name` from `get_mix_state` output. Recipe keys like `"EQ Eight"` → map to catalog class name (e.g. `"Eq8"`). Use catalog's existing class name mapping.

### 5. Output Structure
**Decision:** JSON grouped by device, with `total_suggestions` count at top level.

```json
{
  "track": "KICK_01",
  "role": "kick",
  "genre": "house",
  "total_suggestions": 4,
  "devices": {
    "EQ Eight": [
      {
        "parameter": "FreqA",
        "current_normalized": 0.23,
        "suggested_normalized": 0.31,
        "current_display": "~80 Hz",
        "suggested_display": "~120 Hz",
        "reason": "Low shelf frequency is below the recipe target; raising it reduces mud in the sub-bass region."
      }
    ]
  }
}
```

- `current_display` / `suggested_display` — approximate natural-unit strings (best-effort; omit if conversion not available for parameter)
- Devices with no suggestions are omitted from output
- When `total_suggestions` is 0, return `{"track": ..., "total_suggestions": 0, "devices": {}}` with a note: "Mix is close to recipe targets"

### 6. Implementation Scope
**MCP side only** — no Remote Script changes. The tool:
1. Calls `get_mix_state` (existing RS command via `conn.send_command("get_mix_state", {})`)
2. Calls `get_recipe(role, genre)` from catalog
3. Runs the diff computation inline
4. Returns JSON suggestions

**New file:** `MCP_Server/tools/intelligence.py` — follows the pattern of `analysis.py`, `mixing.py`, `catalog.py`

**Register in:** `MCP_Server/tools/__init__.py` (same pattern as all other tool modules)

## Canonical Refs

- `MCP_Server/tools/analysis.py` — `check_gain_staging`, `_infer_role()`, `get_mix_state` tool patterns
- `MCP_Server/tools/mixing.py` — `get_mix_recipe`, `apply_mix_recipe` interface patterns
- `MCP_Server/devices/convert.py` — `natural_to_normalized()` conversion infrastructure
- `MCP_Server/devices/catalog.py` — `CATALOG`, `ROLES` constants
- `MCP_Server/mixing/catalog.py` — `get_recipe()` function
- `MCP_Server/tools/__init__.py` — tool module registration pattern
- `.planning/REQUIREMENTS.md` — INTEL-01 spec

## Requirements Traceability

| Requirement | Decision |
|-------------|----------|
| INTEL-01: suggest_mix_adjustments returns param diffs with one-sentence reasons | Sec 5 output format with `reason` field per suggestion |
| INTEL-01: based on comparing current state against role×genre recipe | Sec 2 diff computation strategy |
| INTEL-01: suggestions for review only — no auto-apply | Sec 6 — read-only, no RS write commands |

## Deferred Ideas

- Whole-session suggestions (suggest for all tracks at once) — could be a Phase 35 tool built on this foundation
- Priority/impact ranking (sort suggestions by largest delta or most impactful parameter) — nice-to-have, add if low cost during implementation
