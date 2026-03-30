# Domain Pitfalls: v1.4 Mix/Master Intelligence

**Domain:** Device parameter catalog, mix recipes, gain staging, spectrum analysis, and master bus processing for an existing Ableton MCP server
**Researched:** 2026-03-28
**Confidence:** HIGH (codebase-verified) / MEDIUM (Ableton API behavior from community sources)

## Critical Pitfalls

### Pitfall 1: Parameter Name Mismatch Between Catalog and Live API

**What goes wrong:**
A device parameter catalog stores human-readable names like "Frequency", "Gain", "Q" for EQ Eight bands. But the actual `DeviceParameter.name` returned by the Ableton LOM is `"1 Frequency A"`, `"1 Gain A"`, `"1 Resonance A"` (not "Q"). The catalog's `set_device_parameter(parameter_name="Frequency")` call fails because the case-insensitive first-match lookup (see `devices.py` line 130-137) finds no match. The existing error message lists all available parameter names, but by then the recipe has already failed mid-application.

**Why it happens:**
Ableton's built-in devices use internal parameter naming conventions that differ from their GUI labels. EQ Eight shows "Freq" in the GUI but the API name is `"1 Frequency A"` (band-prefixed, channel-suffixed). Compressor shows "Threshold" in the GUI but the API name is `"Threshold"` (no prefix). There is no consistent naming pattern across devices. Developers build catalogs from the GUI labels or documentation, not from actual `get_device_parameters` output.

Known naming traps:
- EQ Eight: Band parameters are `"{N} {Param} A"` where N=1-8 and A=channel. "Resonance" not "Q".
- Compressor: `"Threshold"`, `"Ratio"`, `"Attack"`, `"Release"` match GUI, but `"Output Gain"` not "Makeup" or "Gain".
- Glue Compressor: Different parameter names than Compressor despite similar function.
- Utility: `"Gain"` is the main parameter, but there is also a `"Left"` and `"Right"` for mid/side.
- Channel EQ: Completely different naming from EQ Eight (e.g., `"Low Gain"`, `"Mid Gain"`, `"High Gain"`).

**How to avoid:**
Do NOT hand-author the parameter catalog from documentation or GUI labels. Instead:
1. Build the catalog by querying `get_device_parameters` on actual loaded devices in a live Ableton session.
2. Store the exact `param.name` strings returned by the API as the canonical keys.
3. Add a `display_name` field for human readability, but NEVER use it for API calls.
4. Include a `verify_catalog` test that loads each device in Ableton and checks that all catalog parameter names match actual API names.
5. The existing `set_device_parameter` already does case-insensitive first-match lookup -- use that, but ensure catalog entries use exact API names.

**Warning signs:**
- Catalog entries like `{"name": "Frequency", "min": 20, "max": 20000}` without band prefixes
- Any catalog entry where `name` does not exactly match a string from `get_device_parameters` output
- Recipe application silently failing with "Parameter 'X' not found" errors
- Recipes that work for Compressor but fail for EQ Eight (because Compressor names happen to match GUI labels)

**Phase to address:**
Device parameter catalog phase (FIRST). Must be built from live Ableton queries, not hand-authored. The catalog is the foundation -- if names are wrong, every recipe fails.

---

### Pitfall 2: Normalized vs. Absolute Value Confusion

**What goes wrong:**
The Ableton LOM stores ALL device parameter values in a normalized range defined by `param.min` and `param.max`. For many parameters, this is NOT the human-readable range. EQ Eight frequency is stored as a normalized float (approximately 0.0 to 1.0) that maps logarithmically to 20Hz-20kHz. A recipe that sets `"1 Frequency A"` to `200` (meaning 200Hz) actually sets it to the maximum value (clamped to `param.max` which is ~1.0), resulting in 20kHz. The existing `set_device_parameter` handler (line 158-164) silently clamps out-of-range values and logs a warning, but the recipe author never sees the warning.

**Why it happens:**
Different Ableton devices use different value semantics:
- **Normalized 0-1 mapped to range:** EQ Eight frequency (0.0-1.0 -> 20Hz-20kHz logarithmic), Q/Resonance (0.0-1.0 -> 0.1-18.0)
- **Direct values in natural units:** Compressor Threshold (-inf to 0 dB, stored as dB), Compressor Ratio (1.0 to inf)
- **Quantized integer enums:** Filter type (0=LP, 1=HP, 2=BP...), Compressor model
- **Boolean-like 0/1:** Band on/off, device on/off

There is NO flag on the parameter that tells you which semantic applies. The only clue is `param.min`, `param.max`, and `param.is_quantized`. A developer who writes recipes in "human units" (Hz, dB, ms) discovers the mismatch only at runtime.

**How to avoid:**
The parameter catalog MUST store the actual `min` and `max` values from the API alongside each parameter. Recipe values must be specified in API units, not human units. If human-readable recipes are desired:
1. Add conversion functions per parameter type: `hz_to_normalized(hz, min, max)` using logarithmic scaling for frequency params.
2. Store the conversion type in the catalog: `{"name": "1 Frequency A", "min": 0.0, "max": 1.0, "unit": "log_hz", "human_range": [20, 20000]}`.
3. The recipe application tool converts human values to API values BEFORE calling `set_device_parameter`.
4. Never pass human-unit values directly to `set_device_parameter`.

Key conversion formulas:
- **Log frequency:** `normalized = (log10(hz) - log10(20)) / (log10(20000) - log10(20))`
- **Linear dB:** Usually direct (param range is already in dB)
- **Quantized:** Direct integer values

**Warning signs:**
- Recipe sets EQ frequency to "200" and gets max frequency instead
- All frequency-based parameters sound wrong (extreme high or low)
- Recipe works for Compressor threshold (direct dB) but fails for EQ frequency (normalized)
- `param.max` is 1.0 but recipe specifies values in the hundreds

**Phase to address:**
Device parameter catalog phase. Value semantics must be documented per parameter. The apply-recipe tool must handle conversion.

---

### Pitfall 3: Recipe Application Ordering -- Load Device THEN Set Parameters

**What goes wrong:**
A mix recipe tool tries to load an EQ Eight onto a track and set its parameters in the same operation. But `load_browser_item` is asynchronous at the Ableton level -- the device is not fully instantiated when the command returns. The subsequent `set_device_parameter` calls fail because the device either does not exist yet, has a different `device_index` than expected, or has not finished initializing its parameters.

**Why it happens:**
The existing `load_browser_item` handler (in `browser.py`) loads the device and returns a result that includes `"loaded": True` and the device list. But Ableton's internal loading is not atomic -- there can be a brief delay before the device's parameter list is fully populated. In the Remote Script running on the main thread via `schedule_message()`, commands are serialized, but the device initialization may span multiple message cycles.

Additionally, when loading a device, the `device_index` of the newly loaded device depends on where Ableton inserts it (usually at the end of the chain, but not always -- e.g., instruments go before effects). If the recipe assumes `device_index=0`, it may be setting parameters on a different device.

**How to avoid:**
The apply-recipe tool MUST be a single Remote Script command that:
1. Loads the device (or verifies it is already present by `class_name` match).
2. Waits for the device to be fully initialized (check `len(device.parameters) > 0`).
3. Resolves the device index by scanning the track's device chain for the expected `class_name`, NOT by assuming a fixed index.
4. Sets all parameters in sequence within the same handler call.
5. Returns the actual parameter values after setting (read-back verification).

Do NOT implement this as separate MCP tool calls from Claude: `load_instrument_or_effect` -> `get_device_parameters` -> `set_device_parameter` x N. That is 10+ tool calls per device and fragile.

**Warning signs:**
- "Device index X out of range" errors after loading a device
- Parameters set on the wrong device (e.g., setting EQ params on the instrument)
- Intermittent failures where the same recipe sometimes works and sometimes fails
- Recipe tool design that requires Claude to chain load + multiple set calls

**Phase to address:**
Apply-recipe tool phase. Must be a single atomic command in the Remote Script.

---

### Pitfall 4: MIDI Tracks Without Instruments Have No Meaningful Mixer Levels

**What goes wrong:**
A gain staging check tool reads `track.mixer_device.volume.value` on all tracks to assess levels. On a MIDI track without an instrument loaded, this call succeeds (the `mixer_device` exists) but the volume value is meaningless -- there is no audio signal flowing through the mixer. The gain staging tool reports "Track 3 (Bass): volume 0.85 = -1.4dB" which looks like a valid level, but the track produces no audio. The AI suggests EQ and compression for a track that has no sound.

**Why it happens:**
As documented in project memory: "MIDI tracks without an instrument/device have NO volume fader -- only a MIDI input meter." The `mixer_device.volume` property EXISTS on all tracks (it is always part of the Track LOM), but on instrumentless MIDI tracks it controls nothing. The volume value is a stored setting that will take effect once an instrument is loaded, but it does not reflect actual audio levels.

The v1.3 `get_arrangement_progress` tool already flags tracks without instruments, but a new gain staging tool may not reuse this check.

**How to avoid:**
Every mixing/mastering tool that reads or writes mixer parameters MUST first check if the track has audio output capability:
1. Check `len(track.devices) > 0` -- if no devices, skip for MIDI tracks.
2. Better: check `track.has_audio_output` (LOM property) if available in Live 12.
3. Best: reuse the existing pattern from `get_arrangement_progress` (Phase 28) that checks for instrumentless tracks.

The gain staging tool should categorize tracks:
- **Audio tracks:** Always have valid mixer levels.
- **MIDI tracks with instruments:** Have valid mixer levels.
- **MIDI tracks without instruments:** Flag as "no audio output -- load instrument first." Do NOT report volume/pan as valid mixing data.
- **Return tracks:** Always have valid mixer levels.
- **Master track:** Always has valid mixer level.

**Warning signs:**
- Gain staging report includes MIDI tracks with no instruments showing non-zero levels
- Mix recipes applied to tracks that produce no sound
- AI suggests "lower the bass track volume by 3dB" when the bass track has no instrument

**Phase to address:**
Gain staging check phase. The instrument-presence check from v1.3 must be reused, not reimplemented.

---

### Pitfall 5: Master Bus Device Chain -- Insert Order and Monitoring Disruption

**What goes wrong:**
A master bus recipe loads a Limiter, then an EQ Eight, then a Glue Compressor onto the master track. The devices end up in the wrong signal flow order. Signal flows through devices from index 0 to index N in Ableton. Loading Limiter first puts it at position 0 (first in signal chain), which means audio hits the limiter BEFORE the EQ and compressor. This is backwards for mastering.

**Why it happens:**
1. **Device insertion order:** `load_browser_item` appends devices to the END of the chain by default. If you load in the order Limiter, EQ, Compressor, the chain becomes [Limiter, EQ, Compressor] -- signal hits Limiter first. The correct mastering order is [EQ, Compressor, Limiter].

2. **No "insert at position" API:** The LOM's `load_browser_item` does not support an `insert_index` parameter. Devices always append. To get the right order, you must load in the correct sequence (EQ first, then Compressor, then Limiter).

3. **Master track sensitivity:** The master track processes ALL audio. Adding/removing devices on it while audio is playing can cause clicks. There is no "bypass all" atomic operation to prevent this.

**How to avoid:**
1. **Load devices in signal-flow order:** EQ -> Compressor -> Limiter. Document the expected insertion order in the recipe definition.
2. **Verify chain order after loading:** Read `track.devices` and check that `class_name` values match the expected order. If not, the recipe should fail with a clear error rather than silently leaving devices in wrong order.
3. **Consider building a master chain in an Audio Effect Rack:** Load a single rack and configure chains within it. This is one device insertion (less disruption) and chain order is controlled within the rack.
4. **Recommend stopping transport before applying master bus recipes:** The apply tool should warn or auto-stop transport before modifying the master chain.

**Warning signs:**
- Limiter before EQ in the master chain (limiting un-EQ'd signal)
- Audio glitches when applying master bus recipe during playback
- Device order in Ableton does not match recipe specification
- Master bus recipe works in empty session but causes issues in sessions with audio playing

**Phase to address:**
Master bus recipe phase. Signal flow order must be specified in the recipe and verified after application.

---

### Pitfall 6: Sidechain Routing Setup Is Session-Dependent and Fragile

**What goes wrong:**
A mix recipe specifies "sidechain bass compressor from kick track." The existing `set_compressor_sidechain` tool (line 1218 in `devices.py`) requires `routing_type_index` and `routing_channel_index`, which are opaque integer indices into Ableton's routing lists. These indices are SESSION-DEPENDENT -- they change based on the number and order of tracks in the session. A recipe that hardcodes `routing_type_index=3` works in one session but routes to the wrong track in another.

**Why it happens:**
Ableton's sidechain routing uses a two-level selection: first a routing type (e.g., "Post FX" from a specific track), then a routing channel within that type (e.g., "Pre FX", "Post FX", "Post Mixer"). The available routing types depend on what tracks exist in the session. Track 0 might be routing_type_index 2 in one session and index 5 in another if return tracks or groups are present.

The existing `get_compressor_sidechain` tool returns the available routing types with their display names, but the recipe system would need to resolve "kick track" to the correct routing_type_index at apply time, not at catalog time.

**How to avoid:**
Sidechain recipes must specify the SOURCE by semantic name (e.g., "kick" or track role), not by routing index. The apply-recipe tool must:
1. Resolve the source track by name or role (find the track named "Kick" or tagged as kick role).
2. Call `get_compressor_sidechain` to get available routing types for the target compressor.
3. Match the source track name against the routing type display names.
4. Set the sidechain using the matched index.

This is a minimum 3-step process within a single Remote Script command. It CANNOT be hardcoded in the catalog.

**Warning signs:**
- Sidechain recipes with hardcoded routing indices
- Sidechain routing that works in the scaffolded session but breaks when user adds/removes tracks
- "routing_type_index out of range" errors

**Phase to address:**
Apply-recipe tool phase or a dedicated sidechain setup phase. The routing resolution logic is complex enough to warrant its own handler.

---

## Moderate Pitfalls

### Pitfall 7: Spectrum Analyzer Data Is NOT Accessible via LOM

**What goes wrong:**
The v1.4 feature list includes "Spectrum analysis (frequency snapshot if LOM exposes it)." A developer adds a Spectrum device to a track and tries to read frequency bin data via the LOM. There is no API for this. The Spectrum device has the standard `DeviceParameter` properties (on/off, range, etc.) but does NOT expose its frequency analysis data through any LOM property.

**Why it happens:**
The Spectrum device is a visualization-only device in Ableton. Its frequency display is rendered by the GUI, not by the LOM. The LOM exposes device parameters (knobs, sliders, toggles) but not visual output data like spectrum graphs, waveform displays, or meter readings. This is a fundamental LOM limitation, not a bug.

The only audio level data available via LOM is `Track.output_meter_left` and `Track.output_meter_right`, which provide peak level values (and only when meters are visible in the UI in some implementations).

**How to avoid:**
Accept that frequency-domain analysis is NOT possible through the LOM/Remote Script path. Alternative approaches:
1. **Use `output_meter_left/right`** for peak level monitoring (gain staging). This is available and useful, but it is amplitude only, not frequency.
2. **Use EQ Three as a crude frequency splitter:** Load an EQ Three, read the individual band output levels. This is a hack but provides rough 3-band frequency information.
3. **Defer spectrum analysis to a future milestone** that uses Max for Live (which CAN access audio signals via `plugin~` or `plugsend~/plugreceive~`). This is out of scope for v1.4.
4. **Document the limitation clearly** in the feature spec. The "if LOM exposes it" qualifier in the PROJECT.md is the right hedge.

**Warning signs:**
- Any code that tries to read properties beyond standard `DeviceParameter` on a Spectrum device
- Feature planning that depends on frequency-domain data
- Sprint plans that include "read spectrum data" as a task without research validation

**Phase to address:**
Should be resolved in architecture/planning. Mark spectrum analysis as OUT OF SCOPE for v1.4. The gain staging check should use `output_meter_left/right` instead.

---

### Pitfall 8: EQ Eight Has 8 Bands x Multiple Parameters = 40+ Parameters

**What goes wrong:**
A recipe for "high-pass filter at 80Hz on bass track" tries to set a single EQ Eight parameter. But EQ Eight has 8 bands, each with: Filter On, Frequency, Gain, Resonance, Filter Type -- plus global parameters (Scale, Output Gain, Adaptive Q). That is 40+ parameters. Setting just "1 Frequency A" without also setting "1 Filter On A" to 1 (enabled), "1 Filter Type A" to the correct type (1=High Pass), "1 Gain A" to 0.0, and "1 Resonance A" to the desired Q means the filter either does not turn on, is the wrong type, or has unexpected gain.

**Why it happens:**
Developers think of EQ as "set frequency and done." But in Ableton's EQ Eight, each band is independently togglable and typed. The default state of a freshly loaded EQ Eight has bands 1, 3, and 8 enabled with specific default types. A recipe that only sets frequency without configuring the full band state produces unpredictable results depending on the device's current state.

**How to avoid:**
EQ recipes must specify the COMPLETE state of every band they use:
```python
# GOOD: Complete band specification
{"band": 1, "on": True, "type": "highpass_12", "freq_hz": 80, "gain_db": 0.0, "q": 0.71}

# BAD: Partial specification
{"param": "1 Frequency A", "value": 80}
```

The apply-recipe tool for EQ Eight should:
1. Accept band-level specifications (band number, on/off, type, freq, gain, Q).
2. Convert human values to API values (Hz to normalized, type name to enum).
3. Set ALL parameters for each specified band in one operation.
4. Leave unspecified bands in their current state (do not reset them).

Consider a dedicated `apply_eq_recipe` Remote Script command rather than generic `set_device_parameter` calls.

**Warning signs:**
- Recipe that sets frequency but not filter type (gets random type from default state)
- EQ band that is set to 80Hz but remains disabled (`Filter On A = 0`)
- Recipes specified as flat parameter lists instead of per-band objects

**Phase to address:**
Device parameter catalog phase (EQ needs structured representation) and apply-recipe tool phase (EQ needs band-aware application).

---

### Pitfall 9: Compressor Parameter Ranges Are Not Uniform

**What goes wrong:**
A recipe applies Compressor settings using values from production guides: "Threshold -20dB, Ratio 4:1, Attack 10ms, Release 100ms." The Compressor's `Threshold` parameter stores values in dB (direct), `Ratio` is stored as a direct float, but `Attack` and `Release` are stored in MILLISECONDS as normalized values that map to a non-linear range. Setting `Attack` to `10` (meaning 10ms) when the parameter range is 0.0-1.0 results in clamping to max (slowest attack).

**Why it happens:**
Ableton's Compressor has parameter ranges that vary per parameter (approximate, must be verified in live session):
- Threshold: dB range -- direct values
- Ratio: direct float but may use non-linear scaling
- Attack: likely stored as normalized 0-1 with non-linear mapping to ms
- Release: likely stored as normalized 0-1 with non-linear mapping to ms
- Output Gain / Makeup: dB range -- direct
- Knee: 0.0 to 1.0 -- normalized

Each parameter has a different value domain. Recipes that assume all values are in natural units will fail for some parameters.

**How to avoid:**
The parameter catalog must record the actual `min`, `max`, and mapping type for EVERY parameter. The apply-recipe tool must convert recipe values to API values using parameter-specific conversion functions. Do not assume any parameter uses natural units until verified.

**Warning signs:**
- Attack/release values clamped to min or max
- Compressor with "correct" settings sounds completely wrong
- Some parameters in a recipe work while others are wildly off

**Phase to address:**
Device parameter catalog phase. Every parameter's min/max/mapping must be captured from a live Ableton session.

---

### Pitfall 10: Device class_name Varies and Is Not Intuitive

**What goes wrong:**
A recipe specifies loading "Compressor" but the catalog uses `class_name: "Compressor2"` (the actual Live 12 class name). Or a recipe checks if a device is an EQ Eight by `class_name == "Eq8"` but the actual class name is `"FilterEQ8"` or `"ChannelEq"` (for Channel EQ). The recipe loader cannot find the expected device on the track.

**Why it happens:**
Ableton's internal `class_name` values are not always intuitive:
- Simpler is `"OriginalSimpler"` (as seen in existing test at `test_devices.py` line 116)
- Compressor, EQ Eight, Glue Compressor class names need verification from live session
- Different device variants (e.g., Compressor vs. Multiband Dynamics) have different class names

The existing codebase uses `device.class_name` for type detection (see `devices.py` line 859, 861) but only checks broad categories ("audio_effect" in class_name), not specific device types.

**How to avoid:**
1. Build a `class_name` lookup table from a live Ableton session: load each target device and record its `class_name`.
2. Use `class_name` for definitive device identification, not `device.name` (which users can rename).
3. Include `class_name` in the parameter catalog as the canonical device identifier.
4. When checking if a device is present on a track, match by `class_name`, not by display name.

**Warning signs:**
- "Device not found" errors when the device IS on the track but has a different name
- Catalog entries with assumed class names that were never verified
- Tests that mock `class_name` with guessed values

**Phase to address:**
Device parameter catalog phase. Class names must be captured from live Ableton queries.

---

### Pitfall 11: Existing Genre Blueprint `mixing` Section Is Prose, Not Parameters

**What goes wrong:**
A developer tries to generate mix recipes from the existing genre blueprint `mixing` section. But the current schema stores mixing data as prose strings: `"frequency_focus": "sub-bass 40-80Hz, kick presence 100-200Hz"`, `"compression_style": "heavy sidechain on bass and pads from kick"`. These are human-readable descriptions, not actionable parameter values. There is no machine-parseable path from "sub-bass 40-80Hz" to `{"device": "EQ Eight", "band_1_freq": 40, "band_1_type": "highpass"}`.

**Why it happens:**
The v1.2 genre blueprints were designed as reference documents for Claude, not as machine-executable specifications. The `MixingSection` schema (see `schema.py` lines 63-68) stores `frequency_focus`, `stereo_field`, `common_effects`, and `compression_style` as strings/lists -- useful for Claude's reasoning but not for automated recipe application.

**How to avoid:**
The v1.4 mix recipe system must be a NEW data layer, not an extension of the existing blueprint mixing section. Two options:

1. **Separate recipe files** (recommended): Create `MCP_Server/recipes/` with per-genre recipe files that contain exact device parameters. The genre blueprint's `mixing` section remains as-is for Claude's reference. Recipes reference blueprints but are not part of them.

2. **Extend blueprint schema:** Add a `mixing_recipes` section to blueprints with structured parameter data. This is riskier because it changes the existing schema and inflates blueprint size.

Option 1 is safer because it does not modify the working v1.2/v1.3 code.

**Warning signs:**
- Attempts to parse prose strings into parameter values
- Recipe system that extends `MixingSection` TypedDict with dozens of new fields
- Blueprint token counts doubling or tripling after adding recipe data

**Phase to address:**
Architecture design phase (first). Decide on recipe storage before building the catalog or apply tool.

---

## Minor Pitfalls

### Pitfall 12: Return Tracks Need Different Recipe Treatment

**What goes wrong:**
Mix recipes include "add reverb to return track A." But return tracks are accessed with `track_type="return"` and `track_index=0`, while regular tracks use `track_type="track"`. A recipe that does not specify `track_type` defaults to `"track"` and applies reverb to the wrong track. The existing `set_device_parameter` handler correctly supports `track_type`, but recipe definitions may omit it.

**How to avoid:**
Recipe definitions must include `track_type` for every operation. Return track recipes should be distinct from regular track recipes. The apply-recipe tool should validate `track_type` against the target track.

**Phase to address:**
Apply-recipe tool phase. Recipe schema must require `track_type` or infer it from context.

---

### Pitfall 13: get_device_parameters Returns ALL Parameters Including Internal Ones

**What goes wrong:**
When building the parameter catalog by querying `get_device_parameters`, the result includes internal parameters that should not be in recipes (e.g., `"Device On"` at index 0 for every device). Recipes that iterate all parameters and set them might accidentally disable the device by setting parameter 0 to 0.

**How to avoid:**
Filter out `"Device On"` (index 0) from recipe parameters. The catalog should flag parameters as "internal" vs. "user-facing." Never include `"Device On"` in mix recipes unless explicitly toggling device bypass.

**Phase to address:**
Device parameter catalog phase. Mark parameter 0 as internal/excluded.

---

### Pitfall 14: Multiple Devices of Same Type on One Track

**What goes wrong:**
A track has two EQ Eight devices (one for low-cut, one for presence boost). The recipe targets "EQ Eight on track 3" but `device_index` is ambiguous. The apply-recipe tool picks the first one (index 0), but the user's intent was the second one.

**How to avoid:**
Recipes should reference devices by chain position purpose, not by type alone. For v1.4 MVP, recipes should assume they are loading devices onto clean tracks (no pre-existing devices of the same type). The apply-recipe tool should check for existing devices of the same `class_name` and either skip (device already present) or warn.

**Phase to address:**
Apply-recipe tool phase. Handle "device already exists" gracefully.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hand-author parameter catalog from docs | No Ableton session needed | Names and ranges wrong, every recipe fails | Never -- must query live Ableton |
| Store recipe values in human units (Hz, dB, ms) | Readable recipes | Conversion bugs at apply time | Only if conversion layer is built and tested |
| Use `device_index=0` assumption in recipes | Simpler recipe format | Breaks when device is not at position 0 | Never for master bus (multiple devices) |
| Skip instrument-presence check in gain staging | Simpler gain staging tool | Reports meaningless levels for empty MIDI tracks | Never -- reuse v1.3 check |
| Hardcode sidechain routing indices | Works in scaffolded sessions | Breaks when user modifies track layout | Never -- must resolve at apply time |
| Include spectrum analysis in scope | Feature-complete spec | Unimplementable via LOM, wasted sprint | Never -- document as out of scope |
| Extend existing MixingSection for recipes | No new files/modules | Bloats blueprints, breaks existing tests | Never -- keep recipes separate |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Recipe catalog + existing `get_device_parameters` | Catalog duplicates parameter enumeration logic | Catalog IS a cache of `get_device_parameters` output. Use the same data format. |
| Apply-recipe + existing `load_browser_item` | Recipe tool loads device then calls separate set_parameter commands | Single Remote Script command: load + verify + set all params atomically |
| Gain staging + existing `set_track_volume` | Gain staging reads volumes then separately calls set_volume to adjust | Read and adjust should be separate tools. Gain staging is read-only analysis. Adjustment is a separate deliberate action. |
| Master bus recipe + existing mixer tools | Recipe sets device params but forgets to set master track volume/pan | Master bus recipe should include volume/limiter ceiling as part of the recipe, applied via existing `set_track_volume(track_type="master")` |
| Mix recipes + v1.3 scaffold tracks | Recipe references tracks by name ("Kick") but scaffold may have created tracks with different names | Recipe resolution must use the same track-name lookup as scaffold. Consider a shared track-role resolver. |
| Sidechain setup + existing `set_compressor_sidechain` | Recipe hardcodes routing indices discovered during development | Must call `get_compressor_sidechain` at apply time to resolve indices dynamically |
| New recipe module + existing conftest.py | New `MCP_Server/tools/recipes.py` imports `get_ableton_connection` but conftest does not patch it | Add new module to `_GAC_PATCH_TARGETS` in `conftest.py` -- easy to forget, causes all recipe tests to fail |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Per-parameter tool calls for recipes | 10+ parameters x 3 devices = 30 tool calls per track | Single atomic apply-recipe command per device | Immediately -- 30 tool calls is unacceptable |
| Gain staging reads every track sequentially | 2-3 second response for 20+ track sessions | Single Remote Script command that reads all track levels in one pass | At 15+ tracks |
| Loading catalog from Ableton on every recipe apply | 500ms+ per device parameter query | Cache catalog server-side. Catalog is static for a given Ableton version. | At first recipe application |
| Master bus recipe applies during playback | Audio glitches, pops, brief silence | Stop transport before master chain modification | Always during playback |

## Testing Approaches for Device Parameter Recipes Without Ableton Running

### What Works

1. **Schema/structure tests (no Ableton needed):**
   - Recipe dict structure validation (required keys, types, ranges)
   - Recipe-to-parameter mapping (recipe band spec -> list of set_device_parameter calls)
   - Conversion function unit tests (Hz to normalized, dB to API value)
   - Existing mock pattern from `conftest.py` -- mock `send_command` return values

2. **Catalog integrity tests (no Ableton needed, but catalog built FROM Ableton):**
   - All recipes reference parameters that exist in the catalog
   - All recipe values are within catalog min/max ranges
   - No recipe sets "Device On" (index 0) accidentally
   - All EQ band recipes specify complete band state (on, type, freq, gain, Q)

3. **Integration test with mocked Ableton (existing pattern):**
   - Mock `send_command` to return canned device parameter lists
   - Verify recipe tool calls `set_device_parameter` with correct parameter names and values
   - Verify load-then-set ordering in atomic commands

### What Requires Live Ableton (UAT)

4. **Catalog verification:** Load each target device, run `get_device_parameters`, compare against catalog. This MUST be run at least once to build/validate the catalog.

5. **End-to-end recipe application:** Apply a recipe to a track, read back parameters, verify values match.

6. **Master bus recipe:** Apply full master chain, verify device order and parameter values.

7. **Sidechain routing:** Verify routing indices resolve correctly in a multi-track session.

### Testing Strategy

The v1.3 codebase established the pattern: unit tests with `mock_connection` for logic, live UAT scripts for Ableton-dependent verification (see `tests/live_uat_07.py`). v1.4 should follow the same pattern:
- Automated tests: recipe structure, conversion functions, tool registration, command dispatch
- Manual UAT: catalog verification, end-to-end recipe application, master bus, sidechain

---

## "Looks Done But Isn't" Checklist

- [ ] **Parameter catalog:** Names match EXACTLY what `get_device_parameters` returns from a live Ableton session (not GUI labels, not documentation)
- [ ] **Value ranges:** Catalog stores actual `param.min`/`param.max` from Ableton, not assumed human ranges
- [ ] **Conversion functions:** Hz-to-normalized tested for EQ Eight across full frequency range (20Hz, 200Hz, 1kHz, 10kHz, 20kHz)
- [ ] **EQ recipes:** Specify complete band state (on/off, type, freq, gain, Q) not just frequency
- [ ] **Gain staging:** Skips MIDI tracks without instruments (reuses v1.3 instrument-presence check)
- [ ] **Master bus order:** Devices inserted in correct signal-flow order (EQ -> Comp -> Limiter)
- [ ] **Sidechain routing:** Resolves source track by name at apply time, not by hardcoded index
- [ ] **Spectrum analysis:** Marked as out of scope, not silently dropped or left as TODO
- [ ] **conftest.py updated:** New tool module(s) added to `_GAC_PATCH_TARGETS`
- [ ] **Recipe values in API units:** No recipe passes human-readable values (Hz, ms) directly to `set_device_parameter` without conversion

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong parameter names in catalog | HIGH | Must re-query all devices from live Ableton, rebuild catalog, rewrite all recipes |
| Normalized value confusion | MEDIUM | Add conversion layer, update recipes to specify unit type, retest |
| Device load ordering failure | LOW | Restructure as atomic command, retest. No session state to clean up. |
| Gain staging on empty MIDI tracks | LOW | Add instrument-presence filter. Results were wrong but no damage to session. |
| Master bus wrong device order | MEDIUM | Delete devices from master, reload in correct order. May need manual cleanup. |
| Sidechain routing with hardcoded indices | MEDIUM | Refactor to dynamic resolution. Must retest in different session configurations. |
| Spectrum analysis attempted | LOW | Remove code, mark as out of scope. No user-facing impact. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Parameter name mismatch | Device parameter catalog (FIRST phase) | UAT: query live Ableton, compare catalog names |
| Normalized value confusion | Device parameter catalog (FIRST phase) | Unit test: conversion functions for all parameter types |
| Recipe application ordering | Apply-recipe tool phase | Integration test: load device + set params atomically |
| MIDI tracks without instruments | Gain staging check phase | Unit test: mock track with no devices, verify skip |
| Master bus device order | Master bus recipe phase | UAT: verify device chain order in live Ableton |
| Sidechain routing fragility | Apply-recipe or dedicated sidechain phase | UAT: test in sessions with different track counts |
| Spectrum data inaccessible | Architecture/planning (FIRST phase) | Document as out of scope in requirements |
| EQ Eight incomplete band state | Device parameter catalog + apply-recipe | Unit test: recipe specifies all 5 band parameters |
| Compressor parameter ranges | Device parameter catalog | UAT: set all compressor params, read back, verify |
| Device class_name variation | Device parameter catalog | UAT: load each device, record class_name |
| Blueprint mixing is prose | Architecture/planning (FIRST phase) | Recipes stored separately from blueprints |
| Return track routing | Apply-recipe tool | Unit test: recipe for return tracks uses track_type="return" |
| Internal parameters in recipes | Device parameter catalog | Unit test: no recipe sets parameter index 0 |
| Duplicate devices on track | Apply-recipe tool | Unit test: handle "device already exists" case |

## Sources

- Existing codebase: `AbletonMCP_Remote_Script/handlers/devices.py` -- current `set_device_parameter` implementation (case-insensitive name lookup, value clamping)
- Existing codebase: `MCP_Server/tools/devices.py` -- current device tool surface (load, get params, set params, EQ8, compressor sidechain)
- Existing codebase: `MCP_Server/genres/schema.py` -- current `MixingSection` schema (prose strings, not parameters)
- Existing codebase: `tests/conftest.py` -- mock pattern with `_GAC_PATCH_TARGETS`
- Existing codebase: `tests/test_devices.py` line 116 -- `class_name: "OriginalSimpler"` confirms non-obvious class names
- Project memory: "MIDI tracks without an instrument/device have NO volume fader"
- [Remotify Device Parameter Reference](https://remotify.io/device-parameters/device_params_live10.html) -- EQ Eight band naming pattern
- [Cycling '74 LOM Documentation](https://docs.cycling74.com/max8/vignettes/live_object_model) -- DeviceParameter properties, LOM limitations
- [Ableton Forum: Spectrum analyzer](https://forum.ableton.com/viewtopic.php?t=125206) -- Spectrum device is visualization-only
- [Ableton Forum: MIDI Track Volume](https://forum.ableton.com/viewtopic.php?t=17973) -- MIDI tracks without instruments have no volume fader
- [Ableton Live 12 Reference Manual: Routing](https://www.ableton.com/en/manual/routing-and-i-o/) -- Sidechain routing structure
- [Ableton Live API Documentation](https://nsuspray.github.io/Live_API_Doc/) -- DeviceParameter properties reference
- [Another Ableton MCP: Device Parameter Control Guide](https://glama.ai/mcp/servers/@itsuzef/ableton-mcp/blob/7a0216f58180507167b9c1a4e97ee2aec407b39b/docs/device_parameter_control.md) -- Normalized value conversion patterns
- [Cycling '74 Forum: Parameter order mismatch](https://cycling74.com/forums/ableton-control-surface-script-not-in-the-same-order-as-device-parameters) -- Device parameter ordering inconsistencies
- [Ableton DeviceParameter Class Reference](https://ricardomatias.net/ableton-live/classes/DeviceParameter.html) -- Property listing

---
*Pitfalls research for: v1.4 Mix/Master Intelligence*
*Researched: 2026-03-28*
