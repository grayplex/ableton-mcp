---
phase: quick
plan: 260319-tmm
type: execute
wave: 1
depends_on: []
files_modified:
  - AbletonMCP_Remote_Script/handlers/devices.py
  - MCP_Server/tools/devices.py
  - tests/test_devices.py
  - tests/test_registry.py
  - tests/conftest.py
autonomous: true
requirements: [LOM-GAPS]
must_haves:
  truths:
    - "AI can browse/select wavetables and configure modulation matrix on Wavetable device"
    - "AI can set sidechain routing on Compressor device"
    - "AI can manage rack macro variations (store/recall/delete)"
    - "AI can configure drum chain note assignment and choke groups"
    - "AI can check/re-enable parameter automation state"
    - "AI can control Drift modulation matrix, Looper device, EQ8 modes, Spectral Resonator modes"
    - "AI can read/set chain mute/solo/color directly"
    - "AI can access take lanes and tuning system"
  artifacts:
    - path: "AbletonMCP_Remote_Script/handlers/devices.py"
      provides: "All new Remote Script command handlers"
    - path: "MCP_Server/tools/devices.py"
      provides: "All new MCP tool functions"
    - path: "tests/test_devices.py"
      provides: "Smoke tests for new tools"
    - path: "tests/test_registry.py"
      provides: "Updated registry count"
  key_links:
    - from: "MCP_Server/tools/devices.py"
      to: "AbletonMCP_Remote_Script/handlers/devices.py"
      via: "send_command wire protocol"
      pattern: "send_command\\(\"(get_|set_|looper_|re_enable_)"
---

<objective>
Implement 12 unimplemented LOM objects as Remote Script commands + MCP tools: WavetableDevice, RackDevice (extended), CompressorDevice, DrumChain, DeviceParameter (extended), DriftDevice, LooperDevice, SpectralResonatorDevice, TakeLane, Eq8Device, TuningSystem, and Chain (direct control).

Purpose: Close the remaining LOM coverage gaps identified in the gap analysis (260319-t3s), adding ~35 new commands and ~35 new MCP tools following established project patterns.

Output: Extended devices.py handler + tools, updated tests.
</objective>

<execution_context>
@C:/Users/ksthu/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/ksthu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/quick/260319-t3s-analyze-mcp-server-feature-gaps-vs-ablet/LOM-GAP-ANALYSIS.md

<interfaces>
<!-- Existing patterns the executor MUST follow -->

From AbletonMCP_Remote_Script/registry.py:
```python
from AbletonMCP_Remote_Script.registry import command

# Read command (runs on socket thread):
@command("get_something")
def _get_something(self, params):
    ...
    return {"key": "value"}

# Write command (scheduled on main thread):
@command("set_something", write=True)
def _set_something(self, params):
    ...
    return {"key": "value"}
```

From AbletonMCP_Remote_Script/handlers/devices.py:
```python
class DeviceHandlers:
    def _resolve_device(self, params):
        """Returns (device, track) tuple. Supports chain navigation."""
    def _resolve_drum_pad(self, device, note):
        """Find drum pad by MIDI note. Raises ValueError if not found."""
    def _get_device_type(self, device):
        """Returns device type string."""

    # Device type detection pattern:
    # hasattr(device, "playback_mode") -> Simpler
    # hasattr(device, "presets") -> Plugin (VST/AU)
    # device.can_have_drum_pads -> Drum Rack
    # device.can_have_chains -> Rack
```

From MCP_Server/tools/devices.py:
```python
import json
from mcp.server.fastmcp import Context
from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp

@mcp.tool()
def some_tool(ctx: Context, track_index: int, device_index: int = 0, track_type: str = "track") -> str:
    try:
        ableton = get_ableton_connection()
        params = {"track_index": track_index, "device_index": device_index, "track_type": track_type}
        result = ableton.send_command("some_command", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error("Failed to ...", detail=str(e), suggestion="...")
```

From AbletonMCP_Remote_Script/__init__.py:
```python
# Mixin MRO order (add new handlers before BrowserHandlers):
class AbletonMCP(
    BaseHandlers, TransportHandlers, TrackHandlers, ClipHandlers,
    NoteHandlers, DeviceHandlers, MixerHandlers, SceneHandlers,
    AutomationHandlers, RoutingHandlers, AudioClipHandlers,
    GrooveHandlers, BrowserHandlers, ControlSurface,
): ...
```

From tests/conftest.py:
```python
# Must add new module patch targets to _GAC_PATCH_TARGETS if creating new tool modules
_GAC_PATCH_TARGETS = [
    "MCP_Server.tools.devices.get_ableton_connection",
    # ... other modules
]
```

From tests/test_registry.py:
```python
# Registry count must be updated:
assert len(registered) == 144  # Update to new count
# Expected set must include all new command names
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add Remote Script handlers for all 12 LOM objects</name>
  <files>AbletonMCP_Remote_Script/handlers/devices.py</files>
  <action>
Add the following command handlers to DeviceHandlers class in devices.py, appended after the existing `compare_ab` handler. Follow established patterns exactly (use `_resolve_device`, try/except with `self.log_message`, `@command` decorator, hasattr guards for device type detection).

**WavetableDevice (6 commands):**

1. `get_wavetable_info` (read) - Get Wavetable device info including oscillator wavetable categories, current category/index for osc 1+2, effect modes, filter_routing, mono_poly, poly_voices, unison_mode, unison_voice_count. Detect via `hasattr(device, 'oscillator_wavetable_categories')`. Return dict with all properties. Also include `oscillator_1_wavetables` and `oscillator_2_wavetables` as lists (the available wavetables in current category) and `visible_modulation_target_names` as list.

2. `set_wavetable_oscillator` (write) - Set oscillator wavetable selection. Params: standard device addressing + `oscillator` (1 or 2), optional `category` (int index), optional `index` (int wavetable index). Validate oscillator is 1 or 2. Access via `device.oscillator_1_wavetable_category` / `device.oscillator_2_wavetable_category` and `device.oscillator_1_wavetable_index` / `device.oscillator_2_wavetable_index`. Return current state after set.

3. `set_wavetable_voice_config` (write) - Set voice config. Params: standard device addressing + optional `mono_poly` (int), `poly_voices` (int), `unison_mode` (int), `unison_voice_count` (int), `filter_routing` (int). Only set non-None params. Also support `oscillator_1_effect_mode` and `oscillator_2_effect_mode` (int). Return updated values.

4. `add_wavetable_modulation` (write) - Add parameter to modulation matrix. Params: standard device addressing + `parameter_name` (str) or `parameter_index` (int). Call `device.add_parameter_to_modulation_matrix(param)`. Return confirmation with parameter name.

5. `set_wavetable_modulation_value` (write) - Set modulation amount. Params: standard device addressing + `parameter_name`/`parameter_index` (to identify the target param), `modulation_target` (str from visible_modulation_target_names), `value` (float). Call `device.set_modulation_value(param, target, value)`. Return confirmation.

6. `get_wavetable_modulation_value` (read) - Get modulation value. Params: standard device addressing + `parameter_name`/`parameter_index`, `modulation_target` (str). Call `device.get_modulation_value(param, target)`. Also expose `device.is_parameter_modulatable(param)` and `device.get_modulation_target_parameter_name(target)`. Return value + metadata.

**CompressorDevice (2 commands):**

7. `get_compressor_sidechain` (read) - Get sidechain routing info. Detect via `hasattr(device, 'available_input_routing_types')` AND `device.class_name == 'Compressor'` (or just hasattr check). Return `available_input_routing_types` (list of .display_name), `available_input_routing_channels` (list of .display_name), current `input_routing_type.display_name`, current `input_routing_channel.display_name`.

8. `set_compressor_sidechain` (write) - Set sidechain source. Params: standard device addressing + `routing_type_index` (int, optional), `routing_channel_index` (int, optional). Set `device.input_routing_type = device.available_input_routing_types[index]` and similarly for channel. Validate indices. Return updated routing state.

**RackDevice extended (5 commands):**

9. `get_rack_variations` (read) - Get macro variation info. Guard with `hasattr(device, 'variation_count')`. Return `variation_count`, `selected_variation_index`, `visible_macro_count`. Only works on rack devices (device.can_have_chains and not device.can_have_drum_pads).

10. `rack_variation_action` (write) - Manage variations. Params: standard device addressing + `action` ('store', 'recall', 'recall_last', 'delete'). Optional `index` for recall/delete. Actions: 'store' calls `device.store_variation()`, 'recall' calls `device.recall_selected_variation()` after setting `device.selected_variation_index = index`, 'recall_last' calls `device.recall_last_used_variation()`, 'delete' calls `device.delete_selected_variation()` after setting index. Return updated state.

11. `rack_macro_action` (write) - Manage macros. Params: standard device addressing + `action` ('add', 'remove', 'randomize'). 'add' calls `device.add_macro()`, 'remove' calls `device.remove_macro()`, 'randomize' calls `device.randomize_macros()`. Return `visible_macro_count`.

12. `insert_rack_chain` (write) - Insert a new chain. Guard with `device.can_have_chains`. Call `device.insert_chain(index)` where index is from params (default len(device.chains)). Return updated chain list.

13. `copy_drum_pad` (write) - Copy drum pad content. Guard with `device.can_have_drum_pads`. Params: standard device addressing + `source_note` (int MIDI note), `target_note` (int MIDI note). Call `device.copy_pad(source_note, target_note)`. Return confirmation.

**DrumChain (2 commands):**

14. `get_drum_chain_config` (read) - Get drum chain's in_note, out_note, choke_group. Resolve device, then access specific chain via `chain_index` param. Check `hasattr(chain, 'in_note')` to verify it's a DrumChain. Return `in_note`, `out_note`, `choke_group`, `name`.

15. `set_drum_chain_config` (write) - Set drum chain properties. Params: standard device addressing + `chain_index`, optional `in_note` (int), `out_note` (int), `choke_group` (int). Only set non-None params. Return updated values.

**DeviceParameter extended (2 commands):**

16. `get_parameter_automation_state` (read) - Get parameter automation state. Params: standard device addressing + `parameter_name`/`parameter_index`. Resolve parameter (same pattern as set_device_parameter). Return `automation_state` (int -- 0=none, 1=playing, 2=overridden), `default_value`, `is_enabled`, `state` (int). Use hasattr guards for each property since older Live versions may not have them all.

17. `re_enable_parameter_automation` (write) - Re-enable overridden automation. Params: standard device addressing + `parameter_name`/`parameter_index`. Resolve parameter, call `param.re_enable_automation()`. Return confirmation with param name and new automation_state.

**DriftDevice (2 commands):**

18. `get_drift_mod_matrix` (read) - Get Drift modulation matrix state. Detect via `hasattr(device, 'mod_matrix_1_source_index')`. Return all 8 mod matrix slots (1-8): for each slot, return `source_index`, `source_list` (as list of strings), `target_index`, `target_list` (as list of strings). Build dict dynamically using `getattr(device, f'mod_matrix_{i}_source_index')` etc for i in 1..8. Note: some slots may have less properties -- LOM shows 24 properties which is 8 slots * 3 props each (source_index, source_list, target_index -- but verify target_list exists too).

19. `set_drift_mod_matrix` (write) - Set Drift modulation matrix slot. Params: standard device addressing + `slot` (1-8), optional `source_index` (int), `target_index` (int). Validate slot 1-8. Set via `setattr(device, f'mod_matrix_{slot}_source_index', source_index)` etc. Return updated slot state.

**LooperDevice (3 commands):**

20. `get_looper_info` (read) - Get Looper device state. Detect via `hasattr(device, 'overdub_after_record')`. Return `loop_length`, `overdub_after_record`, `record_length_index`, `record_length_list` (as list), `tempo`.

21. `looper_action` (write) - Execute Looper action. Params: standard device addressing + `action` ('record', 'overdub', 'play', 'stop', 'clear', 'undo', 'double_speed', 'half_speed', 'double_length', 'half_length'). Call the corresponding method on device. Return action confirmation.

22. `looper_export_to_clip_slot` (write) - Export Looper content to a clip slot. Params: standard device addressing + `scene_index` (int). Call `device.export_to_clip_slot(track.clip_slots[scene_index])`. Return confirmation.

**SpectralResonatorDevice (2 commands):**

23. `get_spectral_resonator_info` (read) - Get SpectralResonator config. Detect via `hasattr(device, 'frequency_dial_mode')`. Return `frequency_dial_mode`, `midi_gate`, `mod_mode`, `mono_poly`, `pitch_mode`, `pitch_bend_range`, `polyphony`.

24. `set_spectral_resonator_config` (write) - Set SpectralResonator properties. Params: standard device addressing + optional params for each property. Only set non-None. Return updated state.

**Eq8Device (2 commands):**

25. `get_eq8_info` (read) - Get EQ8 processing modes. Detect via `hasattr(device, 'edit_mode')` AND device class_name check. Return `edit_mode`, `global_mode`, `oversample`.

26. `set_eq8_mode` (write) - Set EQ8 modes. Params: standard device addressing + optional `edit_mode` (int), `global_mode` (int), `oversample` (bool). Only set non-None. Return updated state.

**TakeLane (3 commands):**

27. `get_take_lanes` (read) - Get take lanes for a track. Params: track_index, track_type. Access `track.take_lanes` (hasattr guard). Return list of lanes with `name` and clip count.

28. `get_take_lane_clips` (read) - Get arrangement clips in a take lane. Params: track_index, track_type, `lane_index`. Access `track.take_lanes[lane_index].arrangement_clips`. Return clip info list.

29. `create_take_lane_clip` (write) - Create a clip in a take lane. Params: track_index, track_type, `lane_index`, `start_time` (float), `length` (float), `clip_type` ('midi' or 'audio'). Call `lane.create_midi_clip(start_time, length)` or `lane.create_audio_clip(start_time, length)`. Return clip info.

**TuningSystem (2 commands):**

30. `get_tuning_system` (read) - Get tuning system info. Access via `self._song.tuning_system` (hasattr guard). Return `name`, `pseudo_octave_in_cents`, `lowest_note`, `highest_note`, `reference_pitch`, `note_tunings` (as list of cent offsets for all notes).

31. `set_tuning_system` (write) - Set tuning system properties. Params: optional `reference_pitch` (float), `note_tunings` (list of floats). Only set non-None. Return updated state. Note: `name` is read-only.

**Chain direct control (3 commands):**

32. `set_chain_mute_solo` (write) - Mute or solo a chain within a rack. Params: standard device addressing + `chain_index`, optional `mute` (bool), `solo` (bool). Set on `device.chains[chain_index]`. Return chain name, mute, solo state.

33. `set_chain_name_color` (write) - Set chain name or color. Params: standard device addressing + `chain_index`, optional `name` (str), `color_index` (int). Return updated chain info.

34. `get_chain_info` (read) - Get detailed chain info. Params: standard device addressing + `chain_index`. Return name, color, color_index, mute, solo, is_auto_colored, mixer_device info (volume, panning, sends), device count.

Total: 34 new commands. Follow the exact pattern: @command decorator, params extraction, _resolve_device, hasattr guards, try/except with log_message, return dict.
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -c "import sys; sys.modules['_Framework'] = type(sys)('_Framework'); sys.modules['_Framework.ControlSurface'] = type(sys)('_Framework.ControlSurface'); sys.modules['_Framework.ControlSurface'].ControlSurface = type('ControlSurface', (), {}); import AbletonMCP_Remote_Script.handlers; from AbletonMCP_Remote_Script.registry import CommandRegistry; registered = {e[0] for e in CommandRegistry._entries}; new_cmds = {'get_wavetable_info','set_wavetable_oscillator','set_wavetable_voice_config','add_wavetable_modulation','set_wavetable_modulation_value','get_wavetable_modulation_value','get_compressor_sidechain','set_compressor_sidechain','get_rack_variations','rack_variation_action','rack_macro_action','insert_rack_chain','copy_drum_pad','get_drum_chain_config','set_drum_chain_config','get_parameter_automation_state','re_enable_parameter_automation','get_drift_mod_matrix','set_drift_mod_matrix','get_looper_info','looper_action','looper_export_to_clip_slot','get_spectral_resonator_info','set_spectral_resonator_config','get_eq8_info','set_eq8_mode','get_take_lanes','get_take_lane_clips','create_take_lane_clip','get_tuning_system','set_tuning_system','set_chain_mute_solo','set_chain_name_color','get_chain_info'}; missing = new_cmds - registered; assert not missing, f'Missing commands: {missing}'; print(f'All {len(new_cmds)} new commands registered. Total: {len(registered)}')"</automated>
  </verify>
  <done>All 34 new command handlers exist in devices.py, import cleanly, and register in CommandRegistry. Total registered commands increases from 144 to 178.</done>
</task>

<task type="auto">
  <name>Task 2: Add MCP tools for all 12 LOM objects + update tests</name>
  <files>MCP_Server/tools/devices.py, tests/test_devices.py, tests/test_registry.py</files>
  <action>
**Part A: Add MCP tools to MCP_Server/tools/devices.py**

Add 34 new MCP tool functions to the end of devices.py, following the exact established pattern. Each tool:
- Uses `@mcp.tool()` decorator
- Takes `ctx: Context` as first param, then typed parameters
- Uses `get_ableton_connection()` + `send_command()`
- Returns `json.dumps(result, indent=2)`
- Has try/except returning `format_error()` on failure
- Has clear docstring with Parameters section

Create tools matching each of the 34 commands from Task 1. Use the same parameter names. For optional parameters, use `| None = None` type hints. For parameters with defaults, provide defaults.

Group tools with comment sections:

```python
# --- WavetableDevice ---
# (6 tools: get_wavetable_info, set_wavetable_oscillator, set_wavetable_voice_config,
#  add_wavetable_modulation, set_wavetable_modulation_value, get_wavetable_modulation_value)

# --- CompressorDevice ---
# (2 tools: get_compressor_sidechain, set_compressor_sidechain)

# --- RackDevice Extended ---
# (5 tools: get_rack_variations, rack_variation_action, rack_macro_action,
#  insert_rack_chain, copy_drum_pad)

# --- DrumChain ---
# (2 tools: get_drum_chain_config, set_drum_chain_config)

# --- DeviceParameter Extended ---
# (2 tools: get_parameter_automation_state, re_enable_parameter_automation)

# --- DriftDevice ---
# (2 tools: get_drift_mod_matrix, set_drift_mod_matrix)

# --- LooperDevice ---
# (3 tools: get_looper_info, looper_action, looper_export_to_clip_slot)

# --- SpectralResonatorDevice ---
# (2 tools: get_spectral_resonator_info, set_spectral_resonator_config)

# --- Eq8Device ---
# (2 tools: get_eq8_info, set_eq8_mode)

# --- TakeLane ---
# (3 tools: get_take_lanes, get_take_lane_clips, create_take_lane_clip)

# --- TuningSystem ---
# (2 tools: get_tuning_system, set_tuning_system)

# --- Chain Direct Control ---
# (3 tools: set_chain_mute_solo, set_chain_name_color, get_chain_info)
```

Key patterns per tool:
- Standard device addressing: `track_index: int, device_index: int = 0, track_type: str = "track"`
- Chain addressing adds: `chain_index: int | None = None, chain_device_index: int | None = None`
- Conditional param building: only add non-None params to the command dict
- Suggestion text should reference related tools (e.g., "Use get_wavetable_info to see available categories")

For TakeLane tools, params are `track_index: int, track_type: str = "track", lane_index: int` (no device_index).
For TuningSystem tools, no track/device params needed -- song-level access.

**Part B: Update tests/test_devices.py**

1. Update `test_device_tools_registered` to include ALL new tool names in the expected set. The test currently checks for 5 tools -- update to check for 5 + 34 = 39 core tools (note: some existing tools like insert_device, move_device, simpler tools, etc. are NOT in the expected set but are registered. Keep the test structure -- just add the 34 new tool names to the expected set).

Actually, the current test checks for a subset (5 original tools). Add ALL 34 new tool names to the expected set.

2. Add one representative smoke test for each device category (6 total smoke tests):

```python
async def test_get_wavetable_info(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {"device_name": "Wavetable", "oscillator_wavetable_categories": ["Basic Shapes"]}
    result = await mcp_server.call_tool("get_wavetable_info", {"track_index": 0, "device_index": 0})
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_name"] == "Wavetable"

async def test_get_compressor_sidechain(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {"device_name": "Compressor", "input_routing_type": "Post FX"}
    result = await mcp_server.call_tool("get_compressor_sidechain", {"track_index": 0, "device_index": 0})
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_name"] == "Compressor"

async def test_get_rack_variations(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {"device_name": "Instrument Rack", "variation_count": 3}
    result = await mcp_server.call_tool("get_rack_variations", {"track_index": 0, "device_index": 0})
    text = result[0][0].text
    data = json.loads(text)
    assert data["variation_count"] == 3

async def test_get_drift_mod_matrix(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {"device_name": "Drift", "slots": []}
    result = await mcp_server.call_tool("get_drift_mod_matrix", {"track_index": 0, "device_index": 0})
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_name"] == "Drift"

async def test_get_looper_info(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {"device_name": "Looper", "loop_length": 4.0}
    result = await mcp_server.call_tool("get_looper_info", {"track_index": 0, "device_index": 0})
    text = result[0][0].text
    data = json.loads(text)
    assert data["device_name"] == "Looper"

async def test_get_tuning_system(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {"name": "12-TET", "reference_pitch": 440.0}
    result = await mcp_server.call_tool("get_tuning_system", {})
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "12-TET"
```

**Part C: Update tests/test_registry.py**

1. Change the count assertion from 144 to 178 (144 + 34 new commands).
2. Add all 34 new command names to the `expected` set in `test_all_commands_registered`, with a comment section `# Quick Task: LOM gaps`.
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/test_devices.py tests/test_registry.py -x -q 2>&1 | tail -10</automated>
  </verify>
  <done>All 34 MCP tools are registered and callable. test_devices.py passes with new smoke tests. test_registry.py passes with updated count of 178 commands. All existing tests still pass.</done>
</task>

</tasks>

<verification>
```bash
cd I:/ableton-mcp && python -m pytest tests/ -x -q
```
All 198+ tests pass (existing 198 + ~6 new smoke tests).

```bash
cd I:/ableton-mcp && python -c "from MCP_Server.server import mcp; import asyncio; tools = asyncio.run(mcp.list_tools()); print(f'{len(tools)} tools registered')"
```
Tool count increases from 141 to 175 (141 + 34 new tools).
</verification>

<success_criteria>
- 34 new Remote Script commands registered (total 178)
- 34 new MCP tools registered (total 175)
- All existing tests pass unchanged
- New smoke tests pass for representative tools from each LOM object category
- Code follows established patterns (decorator, error handling, JSON responses)
</success_criteria>

<output>
After completion, create `.planning/quick/260319-tmm-implement-wavetabledevice-rackdevice-com/260319-tmm-SUMMARY.md`
</output>
