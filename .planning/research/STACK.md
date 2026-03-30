# Technology Stack

**Project:** Ableton MCP v1.4 -- Mix/Master Intelligence
**Researched:** 2026-03-28

## Existing Stack (No Changes)

These are already in place and sufficient. Listed for context only.

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Remote Script runtime (Ableton-embedded) |
| Python | >=3.10 | MCP Server runtime |
| FastMCP (mcp[cli]) | >=1.3.0 | MCP server framework |
| music21 | >=9.0 | Theory engine |
| TCP socket | localhost:9877 | MCP Server <-> Remote Script IPC |

## New Stack Additions

### No New Dependencies Required

**This is the key finding.** The v1.4 milestone requires zero new Python package dependencies. Here is why:

1. **Device parameter catalog**: Pure Python data (dicts), following the same pattern as genre blueprints. No library exists for this -- Ableton device parameters are discoverable at runtime via the existing `get_device_parameters` tool, and the catalog is hand-authored reference data.

2. **Role x genre mix recipes**: Pure Python data (dicts), extending the genre blueprint pattern. No library needed.

3. **dB/gain calculations**: Already implemented in `mixer_helpers.py` (`_to_db()` function with calibrated two-piece formula). Extend with inverse `_from_db()` for target-based gain staging.

4. **LUFS measurement**: NOT feasible without audio file access. The MCP server controls Ableton -- it does not process audio streams. LUFS requires raw audio samples (pyloudnorm needs NumPy arrays of audio data). The Remote Script has no access to audio buffers. **Drop LUFS from scope.**

5. **Spectrum analysis**: NOT exposed via LOM. The Spectrum device is visual-only; its frequency bin data is not accessible through `Device.parameters` or any other LOM property. **Drop Spectrum frequency reading from scope.** However, Spectrum can still be loaded as a monitoring device via `insert_device`.

6. **Output metering**: Available via LOM Track properties `output_meter_level`, `output_meter_left`, `output_meter_right` (0.0-1.0 range). This requires a new Remote Script handler but no new libraries.

### Core Framework: None needed

| Category | Decision | Rationale |
|----------|----------|-----------|
| Device catalog | Pure Python dicts | Same pattern as genre blueprints; auto-discovery via pkgutil; no library exists |
| Mix recipes | Pure Python dicts | Extends genre blueprint schema; TypedDict validation |
| Gain math | Extend `mixer_helpers.py` | `_to_db()` already calibrated; add `_from_db()` inverse |
| Output meters | New Remote Script handler | LOM `track.output_meter_level` (0.0-1.0); no library needed |
| dBFS conversion | `20 * math.log10(value)` | Standard formula; `math` is stdlib |

### Database: None needed

Mix recipes and device catalogs are static reference data, same as genre blueprints. No database.

### Infrastructure: No changes

Same two-tier architecture: MCP Server <-> TCP socket <-> Remote Script.

### Supporting Libraries: None

| Considered | Decision | Why Not |
|------------|----------|---------|
| pyloudnorm | DO NOT ADD | Requires raw audio samples (NumPy arrays). MCP server has no audio access. Remote Script has no audio buffer access. LUFS measurement is architecturally impossible in this system. |
| numpy/scipy | DO NOT ADD | Only needed if doing DSP. We are not. Device parameters are set by value, not computed from audio. |
| PyAbleton | DO NOT ADD | Preset file manipulation library. We control live devices via LOM, not .adv files. |
| pylive | DO NOT ADD | OSC-based Ableton control. We already have a superior TCP socket protocol with 181 commands. |

## Detailed Technical Findings

### 1. No Existing Python Libraries for Ableton Device Parameter Catalogs

**Confidence: HIGH** (searched PyPI, GitHub, community forums)

No library provides a structured catalog of Ableton built-in device parameter names and value ranges. This is because:

- Parameter names and ranges are discoverable at runtime via `device.parameters[i].name`, `.min`, `.max`, `.is_quantized`
- The existing `get_device_parameters` handler already returns this data (lines 80-97 of Remote Script `devices.py`)
- What is missing is a **static reference** so Claude does not need to call `get_device_parameters` before every `set_device_parameter` call

**Approach:** Hand-author device parameter catalogs by querying Ableton Live once per device, capturing the parameter list, and storing it as Python dicts. Same pattern as genre blueprints.

### 2. Ableton LOM Spectrum Analyzer Data: NOT Accessible

**Confidence: HIGH** (verified via Cycling 74 LOM docs, forum searches, Max for Live documentation)

The Spectrum device (`class_name: "SpectrumAnalyzer"`) exposes only standard device parameters through the LOM (on/off, block size, channel, range, etc.). The actual frequency magnitude data displayed in the visual analyzer is rendered internally by the C++ audio engine and is NOT exposed to the Python LOM API.

**What IS accessible:**
- `track.output_meter_level` -- peak hold value, 0.0-1.0, 1-second hold (max of L/R)
- `track.output_meter_left` -- smoothed momentary peak, left channel, 0.0-1.0
- `track.output_meter_right` -- smoothed momentary peak, right channel, 0.0-1.0

These are per-track aggregate levels, not frequency-domain data. Sufficient for gain staging checks but not spectral analysis.

**Important caveat:** The LOM docs note that accessing output meter properties adds load to Live's GUI and meters may only update when visible in the interface.

### 3. Existing get_device_parameters / set_device_parameter Coverage

**Confidence: HIGH** (verified by reading source code)

The existing tooling covers ALL built-in device needs with one gap:

**Fully covered:**
- All device parameters via `device.parameters` enumeration (name, value, min, max, is_quantized)
- Parameter setting by name (case-insensitive) or index with automatic clamping
- Rack chain navigation (chain_index, chain_device_index)
- Master track device access (`track_type="master"`)
- Device insertion at position (`insert_device` / `track.insert_device()`)
- Device loading from browser (`load_browser_item`)
- Device deletion and moving
- Device A/B comparison

**Gap: No batch parameter setting.** Setting 10 parameters on a Compressor requires 10 separate `set_device_parameter` calls. For mix recipes (which set 5-15 parameters per device), a batch endpoint would reduce round-trips dramatically.

**Recommendation:** Add `set_device_parameters_batch` handler that accepts a list of `{parameter_name, value}` pairs and sets them all in one command. This is the single most impactful Remote Script addition for v1.4.

### 4. dBFS and Gain Staging

**Confidence: HIGH** (verified against existing code)

The existing `_to_db()` function converts normalized 0.0-1.0 volume to dB with high accuracy (RMS 0.13 dB error, calibrated against 77 Ableton Live data points). For gain staging:

- Track volumes are 0.0-1.0 normalized (LOM `mixer_device.volume.value`)
- Output meters are 0.0-1.0 normalized (LOM `track.output_meter_level`)
- Conversion to dBFS for meters: `20 * math.log10(meter_value)` where meter_value > 0
- Conversion for fader positions: existing `_to_db()` calibrated formula
- Target ranges are well-known (e.g., kick at -8 to -6 dB, master peak at -1 to 0 dB)
- No library needed -- all math is `math.log10()` and the existing calibrated formula

**What to add:**
- `_from_db(db_value) -> float` -- inverse of `_to_db()` for setting volume from dB targets
- `_meter_to_db(meter_value) -> float` -- convert 0.0-1.0 meter reading to dBFS
- New Remote Script command: `get_track_meters` -- reads output_meter_level/left/right for one or all tracks

### 5. Role x Genre Mix Recipe Data Format

**Confidence: HIGH** (based on proven genre blueprint pattern)

The existing genre blueprint pattern (Python dicts, TypedDict schema, auto-discovery catalog) is the correct format. The current `MixingSection` in `schema.py` has prose-only fields:

```python
class MixingSection(TypedDict):
    frequency_focus: str        # "sub-bass 40-80Hz, kick presence 100-200Hz"
    stereo_field: str           # "mono bass and kick, wide pads"
    common_effects: List[str]   # ["sidechain compression", "reverb"]
    compression_style: str      # "heavy sidechain on bass and pads"
```

These are human-readable guidelines, not machine-actionable recipes. v1.4 adds a parallel structure with exact parameter values. The existing MixingSection stays (it serves Claude's reasoning). New data lives alongside it.

**Recommended schema for mix recipes:**

```python
class DeviceRecipe(TypedDict):
    device_name: str                  # "EQ Eight", "Compressor", etc.
    parameters: Dict[str, float]      # {"1 Frequency A": 80.0, "1 Gain A": -3.0}

class RoleMixRecipe(TypedDict):
    devices: List[DeviceRecipe]       # Ordered device chain
    volume_db: float                  # Target fader position in dB
    pan: float                        # -1.0 to 1.0

class GenreMixRecipes(TypedDict):
    roles: Dict[str, RoleMixRecipe]   # "kick" -> recipe, "bass" -> recipe
    master: RoleMixRecipe             # Master bus recipe
```

**Why dicts over a database:** Same reasons as genre blueprints -- pure Python, no external dependency, version-controlled, auto-discoverable, TypedDict-validated at import time.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Device catalog format | Python dicts | SQLite database | Overkill for ~20 device definitions; dicts are version-controlled and match existing patterns |
| Device catalog format | Python dicts | JSON files | Python dicts allow TypedDict validation at import time; JSON requires separate loader/validator |
| Gain staging | Extend mixer_helpers.py | pyloudnorm | pyloudnorm needs raw audio (NumPy arrays); we only have meter readings |
| Batch params | New RS handler | Multiple set_device_parameter calls | 10x more round-trips; recipe application becomes prohibitively slow |
| Recipe storage | Parallel to genre blueprints | Extend existing MixingSection | Existing MixingSection is prose for Claude reasoning; recipes need exact values; keep both |

## Installation

```bash
# No new dependencies. Existing install command unchanged:
pip install -e ".[dev]"
```

## Key Architecture Decisions for v1.4

| Decision | Rationale |
|----------|-----------|
| Zero new pip dependencies | All new functionality is pure Python data + existing LOM access |
| Device catalog as Python dicts | Same proven pattern as genre blueprints; discoverable, validated, version-controlled |
| Batch parameter setter | Single biggest ROI addition; reduces round-trips from N to 1 per device |
| Output meter reading via LOM | `track.output_meter_level/left/right` provides gain staging feedback without new deps |
| Drop Spectrum frequency reading | LOM does not expose frequency bin data; visual-only device |
| Drop LUFS measurement | Architecturally impossible -- no audio buffer access from Remote Script or MCP Server |
| Extend _to_db with _from_db | Enables target-based gain staging ("set kick to -8 dB") |

## Sources

- [Cycling 74 LOM Documentation](https://docs.cycling74.com/legacy/max8/vignettes/live_object_model) -- Track metering properties, Device parameter access (HIGH confidence)
- [Ableton Reference Manual v12 -- Audio Effect Reference](https://www.ableton.com/en/manual/live-audio-effect-reference/) -- Device parameters and behaviors (HIGH confidence)
- [pyloudnorm on PyPI](https://pypi.org/project/pyloudnorm/) -- Confirmed requires NumPy audio arrays; not applicable (HIGH confidence)
- [pylive on GitHub](https://github.com/ideoforms/pylive) -- Alternative control approach; not needed (HIGH confidence)
- [PyAbleton on GitHub](https://github.com/hamiltonkibbe/PyAbleton) -- Preset file manipulation; not applicable (HIGH confidence)
- Source code analysis: `AbletonMCP_Remote_Script/handlers/devices.py`, `mixer_helpers.py`, `MCP_Server/genres/schema.py` (HIGH confidence)
