---
phase: quick
plan: 260402-lys
type: execute
wave: 1
depends_on: []
files_modified:
  - AbletonMCP_Remote_Script/handlers/devices.py
  - MCP_Server/orchestration/checkpoint.py
  - MCP_Server/orchestration/next_actions.py
  - tests/test_checkpoint.py
  - tests/test_next_actions.py
  - .planning/codebase/CONCERNS.md
autonomous: true
requirements: []
must_haves:
  truths:
    - "Checkpoint no longer serializes device parameters over the socket"
    - "Phase detection still works correctly (master short-circuit, mix/sound_design detection)"
    - "All existing checkpoint and next_actions tests pass with the new command"
  artifacts:
    - path: "AbletonMCP_Remote_Script/handlers/devices.py"
      provides: "get_device_classes RS command"
      contains: "@command(\"get_device_classes\")"
    - path: "MCP_Server/orchestration/checkpoint.py"
      provides: "Checkpoint using lightweight get_device_classes instead of get_mix_state"
      contains: "get_device_classes"
    - path: "MCP_Server/orchestration/next_actions.py"
      provides: "next_actions using get_device_classes instead of get_mix_state"
      contains: "get_device_classes"
  key_links:
    - from: "MCP_Server/orchestration/checkpoint.py"
      to: "AbletonMCP_Remote_Script/handlers/devices.py"
      via: "conn.send_command('get_device_classes')"
      pattern: "send_command.*get_device_classes"
---

<objective>
Replace the expensive `get_mix_state` call in checkpoint and next_actions with a lightweight `get_device_classes` RS command that returns only device class names (no parameter values).

Purpose: `get_mix_state` serializes all device parameters (~960 values for a typical 8-track session). Checkpoint and next_actions only need device class names to detect which plugins are loaded. This eliminates ~95% of the serialized data per checkpoint call.

Output: New RS command, updated checkpoint.py, updated next_actions.py, updated tests.
</objective>

<execution_context>
@.planning/quick/260402-lys-add-get-device-classes-rs-command-to-avo/260402-lys-PLAN.md
</execution_context>

<context>
@AbletonMCP_Remote_Script/handlers/devices.py (lines 2745-2791 — get_mix_state handler as pattern reference)
@AbletonMCP_Remote_Script/registry.py (CommandRegistry @command decorator)
@MCP_Server/orchestration/checkpoint.py (full file — the caller being optimized)
@MCP_Server/orchestration/next_actions.py (lines 238-255 — also calls get_mix_state)
@tests/test_checkpoint.py (full file — needs mock updates)
@tests/test_next_actions.py (lines 34-56 — _make_conn helper)

<interfaces>
<!-- From checkpoint.py — how mix_state result is consumed -->
<!-- Only these fields are used from mix_state: -->

checkpoint.py line 164:
```python
master_devices = mix_state.get("master_track", {}).get("devices", [])
```

_infer_completed_phases lines 51-53 (iterates tracks from arrangement_state):
```python
all_device_classes = set()
for t in tracks:
    for d in t.get("devices", []):
        all_device_classes.add(d.get("class_name", ""))
```

_build_session_stats lines 123-126 (same pattern):
```python
all_device_classes = set()
for t in tracks:
    for d in t.get("devices", []):
        all_device_classes.add(d.get("class_name", ""))
```

CRITICAL FINDING: `_infer_completed_phases` and `_build_session_stats` iterate `tracks` (from arrangement_state) looking for `devices[].class_name`. But real `get_arrangement_state` does NOT include a `devices` field — only `has_instrument` (bool). So `all_device_classes` is always empty in production. The tests inject `devices` into the fixture, masking this bug. The new `get_device_classes` command must provide per-track device class lists so checkpoint can merge them, fixing this latent bug.

From _infer_completed_phases, `all_device_classes` is used for:
- Line 58: master short-circuit `_COMPRESSOR in all_device_classes`
- Line 92: sound_design check `all_device_classes & effect_classes`
- Line 104: mix check `_COMPRESSOR in all_device_classes`

From _build_session_stats, `all_device_classes` is used for:
- Line 131: `has_mix_applied = _COMPRESSOR in all_device_classes`

<!-- From registry.py — the decorator pattern -->
```python
from AbletonMCP_Remote_Script.registry import command

@command("get_device_classes")
def _get_device_classes(self, params=None):
    ...
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add get_device_classes RS command</name>
  <files>AbletonMCP_Remote_Script/handlers/devices.py</files>
  <action>
Add a new `get_device_classes` read command in the DeviceHandlers class (near `_get_mix_state`, around line 2792). Use `@command("get_device_classes")` with `write=False` (default).

The command returns device class names only — no parameter values. Response shape:

```python
{
    "tracks": [
        {"index": 0, "name": "Kick", "device_classes": ["Compressor2", "Eq8"]},
        {"index": 1, "name": "Bass", "device_classes": ["Analog", "AutoFilter"]},
    ],
    "return_tracks": [
        {"index": 0, "name": "A-Reverb", "device_classes": ["Reverb"]},
    ],
    "master_track": {
        "name": "Master",
        "device_classes": ["GlueCompressor", "Limiter2"]
    }
}
```

Implementation:
```python
@command("get_device_classes")
def _get_device_classes(self, params=None):
    """Get device class names for all tracks (no parameters).

    Lightweight alternative to get_mix_state for code that only needs
    to know which device types are loaded (e.g., checkpoint phase detection).

    Returns:
        tracks: list of {index, name, device_classes}
        return_tracks: list of {index, name, device_classes}
        master_track: {name, device_classes}
    """
    try:
        result = {"tracks": [], "return_tracks": [], "master_track": {}}

        for i, track in enumerate(self._song.tracks):
            result["tracks"].append({
                "index": i,
                "name": track.name,
                "device_classes": [d.class_name for d in track.devices],
            })

        for i, track in enumerate(self._song.return_tracks):
            result["return_tracks"].append({
                "index": i,
                "name": track.name,
                "device_classes": [d.class_name for d in track.devices],
            })

        master = self._song.master_track
        result["master_track"] = {
            "name": master.name,
            "device_classes": [d.class_name for d in master.devices],
        }
        return result
    except Exception as e:
        self.log_message(f"Error getting device classes: {e}")
        raise
```

Place this method immediately after `_get_mix_state` (before `_get_track_meters`).
  </action>
  <verify>
    <automated>cd /home/user/ableton-mcp && grep -n "get_device_classes" AbletonMCP_Remote_Script/handlers/devices.py | head -5</automated>
  </verify>
  <done>New `get_device_classes` RS command registered, returns only class name lists per track, no parameters serialized.</done>
</task>

<task type="auto">
  <name>Task 2: Replace get_mix_state with get_device_classes in checkpoint and next_actions</name>
  <files>MCP_Server/orchestration/checkpoint.py, MCP_Server/orchestration/next_actions.py</files>
  <action>
**checkpoint.py** — Replace `get_mix_state` with `get_device_classes` in `get_checkpoint()`. Change lines 158 and 162-164:

Before:
```python
mix_state = conn.send_command("get_mix_state")
...
master_devices = mix_state.get("master_track", {}).get("devices", [])
```

After:
```python
device_classes = conn.send_command("get_device_classes")
...
master_device_classes = device_classes.get("master_track", {}).get("device_classes", [])
```

Then update ALL consumers of `master_devices` and `all_device_classes` to use the new shape. The `device_classes` response provides `device_classes: [str]` (list of class name strings) not `devices: [{class_name: str}]` (list of dicts).

**Key changes in checkpoint.py:**

1. In `get_checkpoint()` (line 158): `conn.send_command("get_device_classes")` instead of `get_mix_state`.

2. Build `master_devices` as a simple list of class name strings (not list of dicts):
   ```python
   master_class_names = set(device_classes.get("master_track", {}).get("device_classes", []))
   ```

3. Build per-track device classes from `device_classes["tracks"]` and merge into arrangement tracks. After getting `tracks` from `arrangement_state` and `device_classes` from `get_device_classes`:
   ```python
   # Merge device class names into arrangement tracks for phase detection
   dc_by_name = {}
   for dc_track in device_classes.get("tracks", []):
       dc_by_name[dc_track["name"]] = dc_track.get("device_classes", [])
   for t in tracks:
       t["device_classes"] = dc_by_name.get(t["name"], [])
   ```

4. Update `_infer_completed_phases` signature: replace `master_devices: list` with `master_class_names: set, all_device_classes: set`. Compute `all_device_classes` from the merged track data BEFORE calling the function, and pass it in. This avoids the function needing to understand the data shape.

   Actually, simpler approach: keep the function signature but change how it builds `all_device_classes` and `master_class_names`:

   ```python
   # In _infer_completed_phases, lines 50-53 become:
   all_device_classes = set()
   for t in tracks:
       for cn in t.get("device_classes", []):
           all_device_classes.add(cn)

   # Lines 56 become:
   master_class_names = set(master_devices)  # now a list of strings, not list of dicts
   ```

   And at every call site, pass `master_devices` as a list of class name strings:
   ```python
   master_devices = device_classes.get("master_track", {}).get("device_classes", [])
   ```

5. Update `_build_session_stats` the same way — it also iterates `devices` on tracks (lines 123-126) and `master_devices` (lines 126-133). Change to use `device_classes` field on tracks and treat `master_devices` as list of strings:
   ```python
   all_device_classes = set()
   for t in tracks:
       for cn in t.get("device_classes", []):
           all_device_classes.add(cn)
   master_class_names = set(master_devices)  # list of strings now
   ```

6. In `_infer_completed_phases` line 106, the local `master_class_names` re-computation also changes:
   ```python
   master_class_names = set(master_devices)  # was {d.get("class_name", "") for d in master_devices}
   ```

**next_actions.py** — Same pattern. Change line 245:
```python
device_classes = conn.send_command("get_device_classes")
```

Line 250:
```python
master_devices = device_classes.get("master_track", {}).get("device_classes", [])
```

And in `_phase_complete` (line 30-44), apply the same changes as `_infer_completed_phases`:
- `all_device_classes` built from `t.get("device_classes", [])` (list of strings)
- `master_class_names = set(master_devices)` (list of strings, not list of dicts)

Also merge device classes into tracks in `get_transition_guidance` the same way as in checkpoint:
```python
# After line 253 (clips_by_track), add:
dc_by_name = {}
for dc_track in device_classes.get("tracks", []):
    dc_by_name[dc_track["name"]] = dc_track.get("device_classes", [])
for t in tracks:
    t["device_classes"] = dc_by_name.get(t["name"], [])
```

IMPORTANT: The pre-fetched data path in `get_transition_guidance` (line 238) takes `master_devices` as a kwarg. When pre-fetched, the caller may still pass the old format. Update the kwarg contract: `master_devices` is now expected to be a list of class name strings (not list of dicts). Check all callers of `get_transition_guidance` with `master_devices=` to confirm they pass the right format.
  </action>
  <verify>
    <automated>cd /home/user/ableton-mcp && python -m pytest tests/test_checkpoint.py tests/test_next_actions.py -x -q 2>&1 | tail -20</automated>
  </verify>
  <done>checkpoint.py and next_actions.py use `get_device_classes` instead of `get_mix_state`. Device class names merged into arrangement tracks for phase detection. `master_devices` is now a list of strings throughout.</done>
</task>

<task type="auto">
  <name>Task 3: Update tests and CONCERNS.md</name>
  <files>tests/test_checkpoint.py, tests/test_next_actions.py, .planning/codebase/CONCERNS.md</files>
  <action>
**tests/test_checkpoint.py:**

1. Update `_make_conn` helper (line 52) to mock `get_device_classes` instead of `get_mix_state`. The `mix_state` parameter becomes `device_classes_state`. Build the mock response in the new shape:
   ```python
   def _make_conn(arrangement_state, device_classes_state, clips_by_track=None):
   ```
   Where `device_classes_state` has shape:
   ```python
   {"tracks": [{"index": 0, "name": "Kick", "device_classes": ["Compressor2"]}],
    "return_tracks": [],
    "master_track": {"name": "Master", "device_classes": ["GlueCompressor", "Limiter2"]}}
   ```

   In `send_command` side_effect, change `"get_mix_state"` to `"get_device_classes"`.

2. Update all fixture data that currently uses `EMPTY_MIX`:
   ```python
   EMPTY_DEVICE_CLASSES = {"tracks": [], "return_tracks": [], "master_track": {"name": "Master", "device_classes": []}}
   ```

3. Update `master_devices` in test fixtures from `[{"class_name": "GlueCompressor"}, ...]` to just the `device_classes` list: `["GlueCompressor", "Limiter2"]`.

4. Update the `_make_track` helper: change `devices` kwarg to `device_classes` defaulting to `[]`. The track dict should have `"device_classes": device_classes` instead of `"devices": devices`.

5. Update `test_no_per_track_clip_queries` (line 257): the expected commands should be `["get_arrangement_state", "get_device_classes"]` not `["get_arrangement_state", "get_mix_state"]`.

6. Ensure test_master_complete fixture has `device_classes=["Compressor2"]` on the Kick track (was `devices=[{"class_name": "Compressor2"}]`).

7. Ensure test_arrangement_multi_section_clips_complete has `device_classes=["AutoFilter"]` on the Synth track (was `devices=[{"class_name": "AutoFilter"}]`).

**tests/test_next_actions.py:**

1. Update `_make_conn` helper (line 34): change `mix_state` to `device_classes_state` with the new shape. `master_devices` parameter becomes a list of strings:
   ```python
   def _make_conn(tracks, master_device_classes=None, clips_by_track=None):
       master_device_classes = master_device_classes or []
       ...
       device_classes_state = {
           "tracks": [{"index": i, "name": t["name"],
                        "device_classes": t.get("device_classes", [])}
                       for i, t in enumerate(enriched_tracks)],
           "return_tracks": [],
           "master_track": {"name": "Master", "device_classes": master_device_classes}
       }
   ```
   And in `send_command`: `"get_device_classes"` instead of `"get_mix_state"`.

2. Update all test call sites that pass `master_devices=[{"class_name": "X"}]` to pass `master_device_classes=["X"]` (or whatever the kwarg is named).

3. For `get_transition_guidance` calls that pass `master_devices=`, update to pass list of strings.

**CONCERNS.md:**

Remove the resolved performance concern at line 47-50 (`get_mix_state serializes full parameter lists`). Replace with a one-line note:
```
**`get_mix_state` serializes full parameter lists — expensive for large sessions:** RESOLVED (260402-lys) -- Checkpoint and next_actions now use lightweight `get_device_classes` RS command (class names only, no parameters).
```
  </action>
  <verify>
    <automated>cd /home/user/ableton-mcp && python -m pytest tests/test_checkpoint.py tests/test_next_actions.py -x -q 2>&1 | tail -20</automated>
  </verify>
  <done>All tests pass with the new `get_device_classes` mock shape. CONCERNS.md updated to mark the performance concern as resolved.</done>
</task>

</tasks>

<verification>
1. `python -m pytest tests/test_checkpoint.py tests/test_next_actions.py -x -q` -- all tests pass
2. `grep -r "get_mix_state" MCP_Server/orchestration/` returns NO matches (checkpoint and next_actions no longer use it)
3. `grep "get_device_classes" AbletonMCP_Remote_Script/handlers/devices.py` confirms the new RS command exists
4. `grep "RESOLVED.*260402-lys" .planning/codebase/CONCERNS.md` confirms concern is marked resolved
</verification>

<success_criteria>
- New `get_device_classes` RS command registered and returns `{tracks: [{index, name, device_classes}], return_tracks: [...], master_track: {name, device_classes}}`
- checkpoint.py calls `get_device_classes` instead of `get_mix_state`
- next_actions.py calls `get_device_classes` instead of `get_mix_state`
- Per-track device class names are merged into arrangement tracks for `_infer_completed_phases` and `_build_session_stats` (fixing the latent bug where `all_device_classes` was always empty)
- All existing checkpoint and next_actions tests pass
- CONCERNS.md performance entry marked as resolved
</success_criteria>

<output>
After completion, create `.planning/quick/260402-lys-add-get-device-classes-rs-command-to-avo/260402-lys-SUMMARY.md`
</output>
