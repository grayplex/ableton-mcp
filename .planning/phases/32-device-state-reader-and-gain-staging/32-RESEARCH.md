# Phase 32: Device State Reader and Gain Staging - Research

**Researched:** 2026-03-28
**Domain:** Ableton LOM meter reading, session-wide device state snapshot, gain staging analysis
**Confidence:** HIGH

## Summary

Phase 32 adds two read-only MCP tools: `get_mix_state` (session-wide device parameter snapshot) and `check_gain_staging` (per-track dBFS estimate vs. role-based targets). Both tools are purely analytical — no parameter writes.

The codebase already has a near-complete template: `get_session_state` (RS command, `devices.py` line 2266) iterates all tracks/return_tracks/master_track with optional `detailed=True` mode that includes full device parameters. The new `get_mix_state` RS handler is a focused variant of this pattern — device params only, no mixer state, no clips. The `check_gain_staging` tool needs a new RS command (`get_track_meters`) to read `output_meter_level` for all tracks in one round-trip, plus a `_meter_to_db()` helper in `mixer_helpers.py`.

**Primary recommendation:** One new RS command (`get_mix_state`) plus one new RS command (`get_track_meters`), both modeled on the existing `get_session_state` loop. Two MCP tools in a new `MCP_Server/tools/analysis.py`. Gain targets in `MCP_Server/devices/gain_targets.py` adjacent to `ROLES`.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Include all track types: regular tracks + return tracks + master track. Full session snapshot.

**D-02:** Each track entry contains device params only — no mixer state (volume, pan, sends).

**D-03:** Use `output_meter_level` for per-track dBFS estimates (0.0–1.0 normalized peak, actual signal).

**D-04:** When all meters read 0.0 (session not playing), warn with "All meters are 0 — play the session to get live meter readings". Report raw values regardless; don't abort.

**D-05:** Role is inferred from track name via case-insensitive substring match against ROLES list. First match wins. Examples: `"KICK_01"` → `kick`, `"bass_synth"` → `bass`.

**D-06:** Tracks with no role match are included with their meter level but marked `"role": null`. They are excluded from flag comparison (no target available).

**D-07:** MIDI tracks with no instrument loaded are excluded from gain staging analysis entirely. Identify by `len(track.devices) == 0` on the RS side.

### Claude's Discretion

- Exact dBFS target ranges per role
- Where gain targets live: `MCP_Server/devices/gain_targets.py` or inline in the analysis module
- How `output_meter_level` maps to dBFS (formula for non-zero values)
- Whether `get_mix_state` skips tracks with zero devices or includes them with empty `devices: []`
- New RS command name(s) for reading all-track device state in one round-trip

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STATE-01 | User can retrieve current device parameters for every device on every track in a single MCP tool call — returns a complete snapshot of the session's mix state without N sequential reads | RS `get_mix_state` command loops `self._song.tracks`, `return_tracks`, `master_track`; device param loop from `_get_device_parameters` pattern |
| GAIN-01 | User can run a gain staging check — returns per-track dBFS estimates from track meter levels, compares to role-based targets, flags tracks significantly above or below target | RS `get_track_meters` command reads `output_meter_level`; `_meter_to_db()` helper; `GAIN_TARGETS` dict in `gain_targets.py`; role inference via substring match on ROLES |
| GAIN-02 | Gain staging check excludes MIDI tracks with no instrument loaded from analysis — no false-positive flags on empty scaffold tracks | `len(track.devices) == 0` guard confirmed by `scaffold.py` pattern (line 70: `"has_devices": len(track.devices) > 0`) |
</phase_requirements>

---

## RS Handler Design for get_mix_state

**Confidence: HIGH** — verified by reading the codebase.

### Key finding: get_session_state already does this

`get_session_state` (RS command registered at `devices.py` line 2266) already performs the exact iteration needed:

```python
# Regular tracks
for i, track in enumerate(self._song.tracks):
    track_state = build_track_state(track)
    ...

# Return tracks
for i, track in enumerate(self._song.return_tracks):
    track_state = build_track_state(track, "return")
    ...

# Master track
result["master_track"] = build_track_state(self._song.master_track, "master")
```

When called with `detailed=True`, `build_track_state` already includes full device parameters:

```python
if detailed:
    dev_info["parameters"] = [
        {"name": p.name, "value": p.value, "min": p.min, "max": p.max}
        for p in d.parameters
    ]
```

### Recommended approach: new focused command, not reuse of get_session_state

`get_session_state` with `detailed=True` returns a large payload including mixer state, mute/solo/arm, clips, and sends. Phase 33 only needs device params. A dedicated `get_mix_state` RS command is preferred because:

1. Smaller response payload — device params only, no clips, no mixer state, no sends
2. Clear semantics for Phase 33 consumer — `get_mix_state` output maps 1:1 to recipe diff
3. `get_session_state` is already a public command — changes to its shape risk breaking existing callers

**New RS command: `get_mix_state`**

Response shape (matches CONTEXT.md specification):

```python
{
    "tracks": [
        {
            "index": i,
            "name": track.name,
            "type": "midi" | "audio" | "group",
            "devices": [
                {
                    "index": di,
                    "class_name": d.class_name,
                    "device_name": d.name,
                    "parameters": [
                        {"name": p.name, "value": p.value}
                        for p in d.parameters
                    ]
                }
            ]
        }
    ],
    "return_tracks": [...],
    "master_track": {...}
}
```

### Discretion decision: include tracks with zero devices

Include tracks with `devices: []` — excluding them would hide MIDI scaffold tracks from the snapshot. Phase 33 needs to know these tracks exist (even if deviceless) to avoid suggesting recipe application to empty tracks. The empty list signals "no devices to diff."

### One RS command or two (STATE-01)?

**One new RS command** (`get_mix_state`). The alternative — calling `get_device_parameters` per-track in a loop from the MCP side — would require N sequential socket round-trips (one per track). STATE-01 explicitly requires "without N sequential reads." The single-command loop is the correct pattern, already proven by `get_session_state` and `get_all_tracks`.

---

## output_meter_level to dBFS Conversion

**Confidence: HIGH** — confirmed by prior v1.4 research (STACK.md) and standard audio engineering.

### LOM meter properties

From prior research (STACK.md line 84-86, confirmed HIGH confidence):

- `track.output_meter_level` — peak hold value, 0.0–1.0 range, 1-second hold (max of L/R channels)
- `track.output_meter_left` — smoothed momentary peak, left channel, 0.0–1.0
- `track.output_meter_right` — smoothed momentary peak, right channel, 0.0–1.0

The gain staging check uses `output_meter_level` (D-03, locked decision).

### Conversion formula

Ableton's normalized meter is a linear amplitude scale (0.0 = silence = −∞ dBFS, 1.0 = full scale = 0 dBFS). Standard peak meter dBFS conversion:

```python
import math

def _meter_to_db(value: float) -> float | None:
    """Convert normalized 0.0-1.0 peak meter reading to dBFS.

    Returns None for zero (silence / -inf dBFS).
    """
    if value <= 0.0:
        return None  # -inf, do not attempt log10(0)
    return 20.0 * math.log10(value)
```

This is confirmed by STACK.md line 120: "Conversion to dBFS for meters: `20 * math.log10(meter_value)` where meter_value > 0"

### Edge cases and floor handling

| Input value | dBFS result | Meaning |
|-------------|-------------|---------|
| 0.0 | None / −∞ | Silence or session not playing |
| 0.001 | −60.0 dBFS | Very quiet signal |
| 0.316 | −10.0 dBFS | Moderate signal |
| 1.0 | 0.0 dBFS | Full scale (clipping threshold) |
| > 1.0 | Not possible | LOM clamps at 1.0 |

**Zero guard:** `value <= 0.0` returns `None` (not a string "−inf") so the caller can distinguish "no signal" from a very quiet signal. The check_gain_staging tool should surface this as `"meter_db": null` and status `"no_signal"` rather than attempting a comparison.

**All-zero warning:** When all `output_meter_level` values across all tracks are 0.0, the response must include a top-level `"warning": "All meters are 0 — play the session to get live meter readings"` (D-04). Check the aggregate across all returned tracks before building the warning.

### Where the helper lives

Add `_meter_to_db(value)` to `AbletonMCP_Remote_Script/handlers/mixer_helpers.py` — adjacent to `_to_db()`. This keeps all dB math in one module. The RS handler for `get_track_meters` calls it inline without needing to import it separately (same as `_to_db` is called in `build_track_state`).

Alternatively, the conversion can be done on the MCP Server side in `analysis.py` using stdlib `math`, since the RS handler can return raw float values and let the Python server convert them. **Recommended: do the conversion on the MCP Server side.** Reasons:

1. The RS handler runs in Ableton's Python environment; returning raw floats is simpler and faster
2. The MCP Server can apply the floor guard and all-zero detection in one place
3. `mixer_helpers.py` already separates concerns from the RS handlers

---

## Gain Staging Target Ranges

**Confidence: MEDIUM** — based on widely-cited mixing conventions from multiple sources; these are guidelines not hard rules. Exact values are Claude's discretion per CONTEXT.md.

### Industry context

Gain staging targets are expressed as dBFS (decibels relative to full scale). In modern digital mixing:
- Peaks are measured at the track output meter (post-fader, post-effects chain)
- "Headroom" is preserved to avoid inter-sample peaks and clipping downstream
- Typical individual track peaks: −18 to −6 dBFS depending on role and density
- Mix bus overhead: −6 dBFS or more before master bus processing
- Final master output: −1 to −0.1 dBFS peak after limiting

### Per-role target ranges

These targets represent healthy individual track peaks for electronic music production. The ranges are intentionally wide (6 dB) to accommodate different performance intensity levels.

```python
# MCP_Server/devices/gain_targets.py

GAIN_TARGETS = {
    "kick": (-10, -4),        # Punchy transient; hottest element in most EDM
    "bass": (-14, -8),        # Sustained sub energy; needs more headroom than kick
    "lead": (-14, -8),        # Melodic lead; similar headroom to bass
    "pad": (-18, -12),        # Background texture; sits lower to preserve space
    "chords": (-16, -10),     # Mid-density harmonic content
    "vocal": (-14, -6),       # Expressive range; varies with performance
    "atmospheric": (-20, -12), # Ambient elements; lowest priority in mix
    "return": (-18, -6),      # Return buses vary widely (reverb tail vs. saturation)
    "master": (-6, -1),       # Master output peak; after limiting chain
}
# Tuple format: (low_dBFS, high_dBFS)
# "too_quiet": meter_db < low
# "too_hot": meter_db > high
# "ok": low <= meter_db <= high
```

### Rationale per role

**kick (-10, -4):** The kick is the rhythmic anchor in EDM genres. It regularly sits near the top of the mix with intentional loudness. A peak of −6 dBFS is typical for a well-compressed kick in house/techno. Below −10 dBFS suggests either the kick is buried or the session is not playing at performance level.

**bass (-14, -8):** Bass elements carry sustained energy (not just transients), so they need more headroom than the kick to avoid cumulative clipping when summed. −8 dBFS peak is the hot end for an active bass line.

**lead (-14, -8):** Lead synths and melodic instruments typically sit just below the kick and bass. Same headroom range as bass.

**pad (-18, -12):** Pads are textural background elements. Sitting too hot (above −12) will mask leads and vocals. Below −18 dBFS and the pad becomes inaudible in the mix context.

**chords (-16, -10):** Chord stabs and harmonic mid-layer elements. More presence than pads but not as hot as leads.

**vocal (-14, -6):** Vocals need presence but their level varies significantly with performance dynamics. A wide range of −14 to −6 accommodates both intimate and energetic passages.

**atmospheric (-20, -12):** Atmospheric elements (risers, FX, ambience) live at the bottom of the mix. If they exceed −12, they are competing with primary mix elements.

**return (-18, -6):** Return buses are extremely variable. A reverb return might sit at −20, while a saturation/distortion return might be at −6. The wide range avoids false-positive flags on return tracks.

**master (-6, -1):** The master output after limiting should be approaching 0 dBFS but not hitting it. Below −6 is under-utilized. Above −1 risks true-peak clipping in export.

### Placement: gain_targets.py vs. inline

**Recommendation: new `MCP_Server/devices/gain_targets.py`** file adjacent to `catalog.py`.

Reasons:
1. `ROLES` already lives in `catalog.py` (line 2242) — gain targets are a natural companion
2. Phase 33 `suggest_mix_adjustments` may also need to reference gain targets; a shared module avoids duplication
3. Keeps `analysis.py` focused on tool logic, not data constants
4. Easy to test independently (import and assert target shapes)

```python
# MCP_Server/devices/gain_targets.py
GAIN_TARGETS: dict[str, tuple[float, float]] = {
    "kick": (-10.0, -4.0),
    "bass": (-14.0, -8.0),
    "lead": (-14.0, -8.0),
    "pad": (-18.0, -12.0),
    "chords": (-16.0, -10.0),
    "vocal": (-14.0, -6.0),
    "atmospheric": (-20.0, -12.0),
    "return": (-18.0, -6.0),
    "master": (-6.0, -1.0),
}
```

---

## Module Placement (mixing.py vs analysis.py)

**Confidence: HIGH** — based on file size measurement and module purpose analysis.

### Current mixing.py size

`MCP_Server/tools/mixing.py` is **114 lines**. It contains:
- `get_mix_recipe` — recipe lookup tool
- `apply_mix_recipe` — recipe application tool
- `apply_master_recipe` — master bus recipe tool
- `set_sidechain_source` — sidechain routing tool

### Recommendation: new `MCP_Server/tools/analysis.py`

Add `get_mix_state` and `check_gain_staging` to a new `analysis.py` module rather than appending to `mixing.py`. Reasons:

1. **Conceptual separation:** `mixing.py` contains write/apply tools; `analysis.py` contains read/inspect tools. The distinction matches Phase 32's explicit constraint: "This phase does NOT modify any device parameters."

2. **Size management:** `mixing.py` at 114 lines is clean. Adding two more tools with their supporting logic would push it to ~200+ lines without logical grouping.

3. **Phase 33 alignment:** `suggest_mix_adjustments` (Phase 33, INTEL-01) is also an analysis tool — it belongs in `analysis.py` alongside `get_mix_state` and `check_gain_staging`.

4. **Existing pattern:** Other tools are split by concern — `mixer.py` (volume/pan/sends), `devices.py` (device CRUD), `mixing.py` (recipe application). `analysis.py` continues this pattern cleanly.

5. **Test organization:** `test_mixing.py` already has 47 tests. A separate `test_analysis.py` keeps test files focused.

### conftest.py update required

`conftest.py` patches `get_ableton_connection` for all tool modules in `_GAC_PATCH_TARGETS`. When `analysis.py` is added, its patch target must be registered:

```python
"MCP_Server.tools.analysis.get_ableton_connection",
```

This is a Wave 0 task (test infrastructure).

---

## MIDI Track Instrument Detection

**Confidence: HIGH** — confirmed by two independent locations in the codebase.

### Confirmation: `len(track.devices) == 0`

This exact check is already used in `scaffold.py` line 70:

```python
"has_devices": len(track.devices) > 0,
```

The inverse (`len(track.devices) == 0`) correctly identifies tracks with no instrument or effect devices. This works for both MIDI and audio tracks, but the gain staging exclusion targets MIDI scaffold tracks specifically.

### Should the check also filter on track type?

**Recommendation: filter on both MIDI type AND zero devices.**

A MIDI track with an instrument loaded should still appear in gain staging (it produces audio output). An audio track with zero devices is unusual but valid — an audio track may have no effects chain and still pass audio. The gain staging check should:

1. Detect track type using the same `track.has_midi_input` check as `_get_track_type_str`
2. Skip only MIDI tracks with zero devices

```python
# On the RS side in get_track_meters:
is_midi = hasattr(track, "has_midi_input") and track.has_midi_input
if is_midi and len(track.devices) == 0:
    continue  # GAIN-02: exclude empty MIDI scaffold tracks
```

This matches D-07 exactly: "MIDI tracks with no instrument loaded (GAIN-02) are excluded from gain staging analysis entirely. Identify by checking `len(track.devices) == 0`."

### Alternative: filter on MCP Server side

The RS handler for `get_track_meters` could include a flag `"excluded": true` in the response for MIDI/no-device tracks, and let the MCP Server `check_gain_staging` tool apply the filtering. This preserves symmetry (RS provides data, MCP applies business logic). However, given the RS side already knows track type via `track.has_midi_input`, filtering at the RS level is simpler and avoids transmitting unnecessary data.

**Recommendation: filter at RS level.** Exclude empty MIDI tracks from the `get_track_meters` response entirely. The MCP tool does not need to implement this guard separately.

---

## Architecture Patterns

### Pattern 1: Session-wide loop (from get_session_state)

Both new RS handlers follow this three-section loop:

```python
@command("get_mix_state")
def _get_mix_state(self, params=None):
    try:
        result = {"tracks": [], "return_tracks": [], "master_track": {}}

        def build_track_device_state(track, track_type_hint=None):
            type_str = _get_track_type_str(track, track_type_hint=track_type_hint)
            devices = []
            for di, d in enumerate(track.devices):
                devices.append({
                    "index": di,
                    "class_name": d.class_name,
                    "device_name": d.name,
                    "parameters": [
                        {"name": p.name, "value": p.value}
                        for p in d.parameters
                    ],
                })
            return {"name": track.name, "type": type_str, "devices": devices}

        for i, track in enumerate(self._song.tracks):
            state = build_track_device_state(track)
            state["index"] = i
            result["tracks"].append(state)

        for i, track in enumerate(self._song.return_tracks):
            state = build_track_device_state(track, "return")
            state["index"] = i
            result["return_tracks"].append(state)

        master = build_track_device_state(self._song.master_track, "master")
        result["master_track"] = master
        return result
    except Exception as e:
        self.log_message(f"Error getting mix state: {e}")
        raise
```

### Pattern 2: MCP tool with single RS command (from apply_mix_recipe)

```python
@mcp.tool()
def get_mix_state(ctx: Context) -> str:
    """Get current device parameters for every device on every track.

    Returns a snapshot of the session's mix state (STATE-01).
    """
    conn = get_ableton_connection()
    result = conn.send_command("get_mix_state", {})
    return json.dumps(result, indent=2)
```

### Pattern 3: Role inference (new, for check_gain_staging)

```python
from MCP_Server.devices.catalog import ROLES

def _infer_role(track_name: str) -> str | None:
    """Infer mixing role from track name via case-insensitive substring match."""
    name_lower = track_name.lower()
    for role in ROLES:
        if role in name_lower:
            return role
    return None
```

The `ROLES` list is `['kick', 'bass', 'lead', 'pad', 'chords', 'vocal', 'atmospheric', 'return', 'master']` (catalog.py line 2242). Substring match means `"KICK_01"` → `kick`, `"bass_synth"` → `bass`, `"pad_atmo"` → `pad` (first match wins — `pad` before `atmospheric`).

**Important:** `"pad"` will match before `"atmospheric"` for a track named `"pad_atmo"` because iteration is ordered. Alphabetically `atmospheric` comes before `pad`, but ROLES is ordered by mix convention, not alphabet. The current list has `pad` at index 3 and `atmospheric` at index 6, so `pad` would match first on `"pad_atmo"`. This is acceptable behavior.

### Anti-patterns to avoid

- **Calling `get_device_parameters` in a loop from MCP side:** Requires N socket round-trips. Use the new `get_mix_state` RS command instead (STATE-01 requirement).
- **Using `_to_db()` for meter conversion:** `_to_db()` is calibrated for Ableton's fader (non-linear mapping). Meter levels are linear amplitude — use `20 * log10(value)` directly.
- **Returning string `"-inf dB"` from `_meter_to_db()`:** Return `None` for zero. The MCP tool must distinguish "no signal" from a measurable level to set status correctly.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| dBFS conversion | Custom calibration table | `20 * math.log10(value)` | Standard formula; peak meters are linear amplitude |
| fader-to-dB | Custom linear formula | Existing `_to_db()` in mixer_helpers | Already calibrated to 77 live data points |
| Track iteration | Sequential get_device_parameters calls | New `get_mix_state` RS command | Single round-trip; existing pattern in get_session_state |
| Role inference | Regex or fuzzy matching | Exact substring match on ROLES list | ROLES list is small and canonical; substring is sufficient |
| Gain target data | Genre-specific lookups | Flat `GAIN_TARGETS` dict | Role targets are genre-independent for gain staging |

---

## Common Pitfalls

### Pitfall 1: Using _to_db() for meter levels

**What goes wrong:** `_to_db()` is a two-piece piecewise formula fitted to Ableton's volume fader curve (non-linear). It produces incorrect results for linear amplitude meter values.

**Why it happens:** Both fader values and meter values are 0.0–1.0 normalized. It is tempting to reuse `_to_db()`.

**How to avoid:** Use `20 * math.log10(value)` for meter levels only. Document this in `_meter_to_db()` docstring.

**Warning signs:** Gain staging check reports kick at −30 dBFS when it should be −6 dBFS.

### Pitfall 2: math.log10(0) → ValueError

**What goes wrong:** `math.log10(0.0)` raises `ValueError: math domain error` in Python.

**Why it happens:** Session not playing, meter reads 0.0, conversion is called naively.

**How to avoid:** Guard with `if value <= 0.0: return None` before calling log10. The check_gain_staging tool treats `None` as "no_signal" status.

### Pitfall 3: get_track_meters GUI load caveat

**What goes wrong:** LOM docs note that accessing `output_meter_level/left/right` adds load to Live's GUI and meters may only update when visible in the interface. In practice, meters may read stale values if the Mixer view is not active.

**Why it happens:** Ableton's meter properties are tied to the GUI rendering pipeline.

**How to avoid:** The D-04 warning ("All meters are 0 — play the session") partially covers this. Document in tool docstring that users should have the Mixer view open and session playing when calling `check_gain_staging`.

### Pitfall 4: Applying gain staging to empty MIDI tracks

**What goes wrong:** An empty MIDI scaffold track reads `output_meter_level = 0.0`, produces `meter_db = None`, which would flag as "no_signal" or "too_quiet" — false positive.

**Why it happens:** v1.3 scaffold tracks may have MIDI tracks without instruments waiting to be set up.

**How to avoid:** GAIN-02 guard: check `has_midi_input and len(track.devices) == 0` on the RS side and exclude these tracks from `get_track_meters` response entirely.

### Pitfall 5: Role substring collision

**What goes wrong:** A track named `"pad_atmospheric"` matches `"pad"` before `"atmospheric"` because ROLES iteration order puts `pad` (index 3) ahead of `atmospheric` (index 6). This may not be the user's intended role.

**Why it happens:** Substring first-match traverses ROLES in order.

**How to avoid:** This is acceptable per D-05 ("first match wins"). Document in `_infer_role()` docstring. If needed in a future phase, longest-match or explicit role tags could be added, but D-05 locks first-match for Phase 32.

---

## Module Placement Summary

| Artifact | Location | Notes |
|----------|----------|-------|
| `get_mix_state` RS handler | `AbletonMCP_Remote_Script/handlers/devices.py` | Adjacent to `get_session_state` (line 2266) |
| `get_track_meters` RS handler | `AbletonMCP_Remote_Script/handlers/devices.py` | New handler; reads `output_meter_level` |
| `_meter_to_db()` helper | `MCP_Server/tools/analysis.py` (or `mixer_helpers.py`) | Recommended: in `analysis.py` as private helper; conversion done MCP side |
| `get_mix_state` MCP tool | `MCP_Server/tools/analysis.py` | New module |
| `check_gain_staging` MCP tool | `MCP_Server/tools/analysis.py` | New module |
| `GAIN_TARGETS` constant | `MCP_Server/devices/gain_targets.py` | New file adjacent to `catalog.py` |
| `_infer_role()` function | `MCP_Server/tools/analysis.py` | Private helper within analysis module |

---

## Plan Split Recommendation

**Recommendation: 2 plans.**

| Plan | Name | Contents | Dependencies |
|------|------|----------|--------------|
| 32-01 | RS handlers and data layer | `get_mix_state` RS command, `get_track_meters` RS command, `GAIN_TARGETS` in `gain_targets.py` | None — pure additions |
| 32-02 | MCP tools | `analysis.py` with `get_mix_state` and `check_gain_staging` tools, `test_analysis.py`, conftest.py update | Requires 32-01 RS commands to exist |

**Why 2 plans:**

1. **RS side changes and MCP side changes are independent work units.** The RS handler loop (32-01) can be reviewed and verified before the MCP tool layer (32-02) is built against it.

2. **Test strategy differs by plan:** 32-01 RS changes are tested via the existing RS handler test pattern (mock Song/Track objects). 32-02 MCP tools are tested via `unittest.mock.patch` of `get_ableton_connection` (same pattern as `test_mixing.py`).

3. **`gain_targets.py` belongs in 32-01** as it is pure data with no dependencies — it can be authored and tested (import + assert shape) before the MCP tool logic in 32-02.

4. **The split mirrors the existing phase 31 pattern** (31-01: RS batch handler; 31-02: RS apply_recipe + MCP tools).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (inferred from `tests/` structure and `conftest.py`) |
| Config file | None detected — invoked via `python -m pytest` |
| Quick run command | `python -m pytest tests/test_mixing.py tests/test_analysis.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STATE-01 | `get_mix_state` returns tracks/return_tracks/master_track with device params | unit | `pytest tests/test_analysis.py::TestGetMixState -x` | No — Wave 0 |
| STATE-01 | Response includes device class_name, device_name, parameters list | unit | `pytest tests/test_analysis.py::TestGetMixStateResponse -x` | No — Wave 0 |
| GAIN-01 | `check_gain_staging` calls `get_track_meters` RS command | unit | `pytest tests/test_analysis.py::TestCheckGainStaging -x` | No — Wave 0 |
| GAIN-01 | dBFS conversion: `meter_value=0.316` → approximately −10.0 dBFS | unit | `pytest tests/test_analysis.py::TestMeterToDb -x` | No — Wave 0 |
| GAIN-01 | All-zero warning included when all meters read 0.0 | unit | `pytest tests/test_analysis.py::TestAllZeroWarning -x` | No — Wave 0 |
| GAIN-01 | Role inference: "KICK_01" → "kick", "bass_synth" → "bass" | unit | `pytest tests/test_analysis.py::TestInferRole -x` | No — Wave 0 |
| GAIN-01 | Track with no role match → `role: null`, no flag comparison | unit | `pytest tests/test_analysis.py::TestUnknownRole -x` | No — Wave 0 |
| GAIN-02 | MIDI track with 0 devices excluded from gain staging output | unit | `pytest tests/test_analysis.py::TestMidiExclusion -x` | No — Wave 0 |
| GAIN-01 | GAIN_TARGETS covers all 9 ROLES | unit | `pytest tests/test_analysis.py::TestGainTargets -x` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_analysis.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_analysis.py` — all test classes above; covers STATE-01, GAIN-01, GAIN-02
- [ ] `conftest.py` — add `"MCP_Server.tools.analysis.get_ableton_connection"` to `_GAC_PATCH_TARGETS`
- [ ] `MCP_Server/devices/gain_targets.py` — data file; can be authored in Wave 0 with import test
- [ ] `MCP_Server/tools/analysis.py` — stub with `get_mix_state` and `check_gain_staging` function signatures

---

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified — all changes are pure Python additions within the existing project stack; no new libraries, databases, or CLI tools required).

---

## Sources

### Primary (HIGH confidence)

- `AbletonMCP_Remote_Script/handlers/devices.py` (lines 2266–2397) — `get_session_state` all-track iteration pattern and `build_track_state` with detailed device params; verified by direct code read
- `AbletonMCP_Remote_Script/handlers/devices.py` (lines 82–119) — `_get_device_parameters` pattern for device param loop; verified by direct code read
- `AbletonMCP_Remote_Script/handlers/mixer_helpers.py` — `_to_db()` implementation; confirms fader conversion is non-linear and NOT appropriate for meter levels
- `AbletonMCP_Remote_Script/handlers/scaffold.py` (line 70) — `len(track.devices) > 0` pattern; confirms GAIN-02 check is already used in codebase
- `AbletonMCP_Remote_Script/handlers/tracks.py` (lines 107–126) — `_get_track_type_str()` implementation; `track.has_midi_input` is the correct MIDI type check
- `MCP_Server/devices/catalog.py` (line 2242) — `ROLES` list canonical definition
- `MCP_Server/tools/mixing.py` — 114 lines total; confirms new analysis module is appropriate
- `.planning/research/STACK.md` (lines 84–128) — v1.4 prior research confirming `output_meter_level` LOM properties and `20 * log10` formula (HIGH confidence from prior research session)
- `tests/test_mixing.py` + `tests/conftest.py` — confirmed test infrastructure pattern for new `test_analysis.py`

### Secondary (MEDIUM confidence)

- Industry mixing convention knowledge (gain staging target ranges) — widely cited in audio engineering sources; specific values are guidelines not specification

### Tertiary (LOW confidence)

- LOM GUI load caveat for meter properties — from prior research STACK.md, originally from community sources; not independently verified against Ableton LOM documentation in this session

---

## Metadata

**Confidence breakdown:**
- RS handler design: HIGH — get_session_state template directly reusable; confirmed by code read
- dBFS conversion formula: HIGH — standard audio math confirmed by prior research
- Gain target ranges: MEDIUM — mixing convention guidelines; inherently approximate
- Module placement: HIGH — size measured, existing pattern is clear
- MIDI track detection: HIGH — two independent codebase locations confirm `len(track.devices) == 0`
- Plan split: HIGH — matches phase 31 precedent and clean separation of concerns

**Research date:** 2026-03-28
**Valid until:** 2026-05-28 (stable domain — Ableton LOM and Python stdlib)
