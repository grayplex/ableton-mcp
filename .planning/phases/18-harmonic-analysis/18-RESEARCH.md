# Phase 18: Harmonic Analysis - Research

**Researched:** 2026-03-25
**Domain:** Music theory analysis tools (key detection, chord segmentation, harmonic rhythm) using music21
**Confidence:** HIGH

## Summary

Phase 18 adds three pure-computation analysis tools to the existing theory engine: `detect_key`, `analyze_clip_chords`, and `analyze_harmonic_rhythm`. All tools accept note data (the output format of `get_notes`: objects with `pitch`, `start_time`, `duration`, `velocity`) rather than clip references. The implementation builds on the established pattern from Phases 14-17: library code in `MCP_Server/theory/analysis.py`, tool wrappers in `MCP_Server/tools/theory.py`, barrel exports from `MCP_Server/theory/__init__.py`.

music21 9.9.1 (already installed) provides the Krumhansl-Schmuckler key detection algorithm via `stream.analyze('key')`, which returns a Key object with `tonic`, `mode`, `correlationCoefficient`, and `alternateInterpretations`. The existing `identify_chord()` from Phase 15 handles chord identification for each time segment. The existing `analyze_progression()` from Phase 17 provides Roman numeral analysis for harmonic rhythm output.

**Primary recommendation:** Build `analysis.py` with three pure functions that convert note data lists into music21 Streams for key detection, use time-grid binning for chord segmentation (reusing `identify_chord`), and compute harmonic rhythm statistics from chord timeline data.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** detect_key returns top 3 ranked candidates
- **D-02:** Major and minor keys are distinct separate candidates (C major and A minor ranked independently)
- **D-03:** Each candidate: key name, mode (major/minor), confidence score (0-1). No scale pitches or correlation vectors
- **D-04:** Fixed time grid segmentation with configurable resolution: 'beat' (default), 'half_beat', 'bar'. No onset-based detection
- **D-05:** Small quantization window catches off-grid notes. Hardcoded tolerance, not user-configurable
- **D-06:** Each segment: time position (beat), chord name, quality, root, MIDI pitches as rich note objects, confidence. Reuses identify_chord
- **D-07:** No raw MIDI notes per segment in output -- only chord identification result
- **D-08:** Time unit is beats
- **D-09:** Returns stats + chord timeline: chord list with durations, avg changes-per-bar, most common chord duration. No repetition/structure detection
- **D-10:** Chord timeline includes Roman numeral analysis when key is provided
- **D-11:** Key parameter is optional -- when provided, Roman numerals included; when omitted, chord names only
- **D-12:** Library code in `MCP_Server/theory/analysis.py`, tools in `MCP_Server/tools/theory.py`
- **D-13:** Barrel exports from `MCP_Server/theory/__init__.py`
- **D-14:** No prefix on tool names
- **D-15:** MIDI validation (0-127) at tool boundary layer
- **D-16:** Rich note objects `{"midi": int, "name": str}` for pitch output
- **D-17:** `json.dumps()` string returns; errors use `format_error()`
- **D-18:** Standalone tests -- no `mock_connection` needed (pure computation)
- **D-19:** Lazy music21 imports inside functions

### Claude's Discretion
- Quantization window size (exact tolerance in beats for off-grid note capture)
- Internal implementation of Krumhansl-Schmuckler vs other music21 key detection algorithms
- How to handle empty segments (no notes in a time window) -- skip or report as rest

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ANLY-01 | Detect key and scale from MIDI notes using music21's key detection algorithms | music21 `stream.analyze('key')` returns Key with tonic, mode, correlationCoefficient, and alternateInterpretations. Verified working with music21 9.9.1. Top 3 from alternateInterpretations gives ranked candidates. |
| ANLY-02 | Segment clip's notes into chords by time position and identify each chord | Time-grid binning with configurable resolution (beat/half_beat/bar), quantization window for off-grid notes, then `identify_chord()` from chords.py on each segment's collected pitches. |
| ANLY-03 | Analyze harmonic rhythm -- chord change frequency, durations, progression structure | Computed from chord timeline: consecutive same-chord segments merged, durations in beats, average changes-per-bar, most common duration. Optional Roman numeral via `analyze_progression()`. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| music21 | 9.9.1 | Key detection (Krumhansl-Schmuckler), Stream building | Already installed, used by all theory modules |

### Supporting (Existing Project Code)
| Module | Location | Purpose | Reuse Pattern |
|--------|----------|---------|---------------|
| `identify_chord()` | `MCP_Server/theory/chords.py` | Chord identification from MIDI pitches | Called per time segment in analyze_clip_chords |
| `analyze_progression()` | `MCP_Server/theory/progressions.py` | Roman numeral analysis | Called for harmonic rhythm Roman numeral output |
| `_make_note_obj()` | `MCP_Server/theory/chords.py` | Rich note object creation | Pitch output formatting |
| `_midi_to_pitch()` | `MCP_Server/theory/chords.py` | MIDI to music21 Pitch | Helper for note building |
| `format_error()` | `MCP_Server/connection.py` | Error formatting | Tool error returns |

## Architecture Patterns

### Project Structure (Addition Points)
```
MCP_Server/
  theory/
    __init__.py        # ADD: export detect_key, analyze_clip_chords, analyze_harmonic_rhythm
    analysis.py        # NEW: 3 library functions
    chords.py          # EXISTING: identify_chord() reused
    progressions.py    # EXISTING: analyze_progression() reused
  tools/
    theory.py          # ADD: 3 new @mcp.tool() functions
tests/
  test_theory.py       # ADD: new test classes for analysis tools
```

### Pattern 1: Note Data Input Format
**What:** All three tools accept a list of note objects matching `get_notes` output format.
**When to use:** Every function in analysis.py takes `notes` as first parameter.
**Input format:**
```python
# Notes from get_notes output (Ableton clip data)
notes = [
    {"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100},
    {"pitch": 64, "start_time": 0.0, "duration": 1.0, "velocity": 100},
    {"pitch": 67, "start_time": 0.0, "duration": 1.0, "velocity": 100},
    # ...
]
```
**Key fields used:** `pitch` (MIDI number), `start_time` (in beats), `duration` (in beats). `velocity` and other fields ignored by analysis.

### Pattern 2: Lazy Import + Module Caching
**What:** Each music21 submodule cached in module-level global, imported on first use.
**Example (from existing code):**
```python
_stream_module = None

def _get_stream_module():
    global _stream_module
    if _stream_module is None:
        from music21 import stream
        _stream_module = stream
    return _stream_module
```

### Pattern 3: Aliased Imports in Tool Layer
**What:** Library functions imported with underscore prefix to avoid name collision.
**Example (from existing tools/theory.py):**
```python
from MCP_Server.theory import detect_key as _detect_key

@mcp.tool()
def detect_key(ctx: Context, notes: list[dict], ...) -> str:
    # ... validation ...
    result = _detect_key(notes)
    return json.dumps(result, indent=2)
```

### Pattern 4: Tool Boundary Validation
**What:** MIDI range (0-127) and input validation at tool layer, not library layer.
**Example:**
```python
@mcp.tool()
def detect_key(ctx: Context, notes: list[dict]) -> str:
    try:
        if not notes:
            return format_error("No notes provided", ...)
        for n in notes:
            if not (0 <= n.get("pitch", -1) <= 127):
                return format_error("MIDI pitch out of range", ...)
        result = _detect_key(notes)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error("Failed to detect key", detail=str(e), ...)
```

### Anti-Patterns to Avoid
- **Importing music21 at module level:** Violates D-19. Always use lazy import pattern.
- **Validating MIDI range in library functions:** Violates D-15. Only at tool boundary.
- **Building custom key detection:** music21's Krumhansl-Schmuckler is battle-tested and already installed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Key detection algorithm | Custom pitch-class histogram correlation | `music21.stream.Stream.analyze('key')` | Implements Krumhansl-Schmuckler with proper weight profiles, returns alternateInterpretations |
| Chord identification | Custom interval pattern matching | `identify_chord()` from chords.py | Already handles ranked candidates, inversions, enharmonic reinterpretation |
| Roman numeral analysis | Custom degree mapping | `analyze_progression()` from progressions.py | Already handles diatonic, borrowed chords, secondary dominants |
| MIDI-to-note conversion | Custom math | `_make_note_obj()` / `_midi_to_pitch()` from chords.py | Handles sharp-default spelling, octave formatting |

## Common Pitfalls

### Pitfall 1: Empty Stream Key Analysis
**What goes wrong:** music21 raises `DiscreteAnalysisException` when analyzing an empty Stream.
**Why it happens:** No pitch data to correlate against key profiles.
**How to avoid:** Check that `notes` list is non-empty before building Stream. Return an error at the library level for empty input.
**Warning signs:** `DiscreteAnalysisException: failed to get likely keys`
**Verified:** Tested with music21 9.9.1 -- empty stream raises exception.

### Pitfall 2: Correlation Coefficient vs Confidence Score
**What goes wrong:** music21's `correlationCoefficient` ranges from roughly -1 to 1, not 0 to 1 as required by D-03.
**Why it happens:** Krumhansl-Schmuckler uses Pearson correlation; negative values indicate anti-correlation with key profile.
**How to avoid:** Normalize: `confidence = max(0, correlationCoefficient)` or map the range to 0-1. The top candidate typically has r > 0.7 for clear keys, 0.3-0.7 for ambiguous passages.
**Warning signs:** Negative confidence scores in output.

### Pitfall 3: Off-Grid Notes Missed by Segment Boundaries
**What goes wrong:** Notes starting at beat 0.98 belong logically to beat 1 but fall into the beat 0 segment.
**Why it happens:** Strict boundary comparison without quantization tolerance.
**How to avoid:** Use a quantization window (e.g., 0.1 beats) where a note at `start_time` is assigned to the nearest grid point if within tolerance.
**Recommendation for discretion area:** 0.1 beats (approximately a 32nd note at 120bpm) is a good tolerance -- catches strummed chords and slight timing offsets without merging intentionally separate beats.

### Pitfall 4: Single-Note Segments
**What goes wrong:** `identify_chord([60])` returns a result but with `quality: "other"` and unhelpful name.
**Why it happens:** A single pitch is not a chord.
**How to avoid:** Segments with only 1 note should be reported as a single note, not passed to `identify_chord`. Could report as `{"chord": null, "single_note": {"midi": 60, "name": "C4"}}` or skip the segment.

### Pitfall 5: Time Signature Assumption for "bar" Resolution
**What goes wrong:** "bar" resolution assumes 4 beats per bar but the clip might be in 3/4 or 6/8.
**Why it happens:** Note data from `get_notes` has no time signature metadata.
**How to avoid:** Accept an optional `beats_per_bar` parameter (default 4) for bar-level segmentation. Document that this defaults to 4/4.

### Pitfall 6: Duplicate Pitch Classes in Segment
**What goes wrong:** Same note sounding at octave 3 and octave 4 creates duplicate pitch classes for chord identification.
**Why it happens:** Chords often have doubled notes across octaves (e.g., bass note + same note in chord).
**How to avoid:** `identify_chord()` already handles this -- it works on the full MIDI pitch list including octave duplicates. music21's chord identification is pitch-class aware.

## Code Examples

### detect_key Implementation Pattern
```python
# Source: Verified with music21 9.9.1 on this system
def detect_key(notes):
    """Detect key from a list of note dicts [{pitch, start_time, duration, ...}].

    Returns top 3 key candidates with confidence scores.
    """
    stream_mod = _get_stream_module()
    note_mod = _get_note_module()

    if not notes:
        raise ValueError("No notes provided for key detection")

    s = stream_mod.Stream()
    for nd in notes:
        n = note_mod.Note(midi=nd["pitch"])
        n.quarterLength = nd.get("duration", 1.0)
        s.append(n)

    k = s.analyze('key')

    # Build top 3 candidates from primary + alternateInterpretations
    candidates = []
    # Primary result
    candidates.append({
        "key": k.tonic.name,
        "mode": k.mode,
        "confidence": round(max(0, k.correlationCoefficient), 4),
    })
    # Alternate interpretations
    for alt in k.alternateInterpretations:
        if len(candidates) >= 3:
            break
        candidates.append({
            "key": alt.tonic.name,
            "mode": alt.mode,
            "confidence": round(max(0, alt.correlationCoefficient), 4),
        })

    return candidates
```

### Time-Grid Chord Segmentation Pattern
```python
# Source: Custom implementation using existing identify_chord
def analyze_clip_chords(notes, resolution='beat', beats_per_bar=4):
    """Segment notes into time windows and identify chord at each position."""

    QUANTIZE_WINDOW = 0.1  # beats tolerance for off-grid notes

    # Determine grid size in beats
    grid_size = {
        'beat': 1.0,
        'half_beat': 0.5,
        'bar': float(beats_per_bar),
    }[resolution]

    # Find time range
    max_time = max(nd["start_time"] + nd["duration"] for nd in notes)

    segments = []
    t = 0.0
    while t < max_time:
        # Collect notes that fall within this segment (with quantization window)
        segment_pitches = []
        for nd in notes:
            # Note starts within [t - QUANTIZE_WINDOW, t + grid_size + QUANTIZE_WINDOW)
            note_start = nd["start_time"]
            # Snap to nearest grid point
            nearest_grid = round(note_start / grid_size) * grid_size
            if abs(nearest_grid - t) < 0.001:  # belongs to this grid point
                segment_pitches.append(nd["pitch"])
            elif t - QUANTIZE_WINDOW <= note_start < t + grid_size:
                # Note starts within this segment's time window
                segment_pitches.append(nd["pitch"])

        if segment_pitches:
            unique_pitches = sorted(set(segment_pitches))
            if len(unique_pitches) >= 2:
                chord_results = identify_chord(unique_pitches)
                # ... build segment result from chord_results[0]
            else:
                # Single note -- report as single note, not chord
                pass

        t += grid_size

    return segments
```

### Harmonic Rhythm Analysis Pattern
```python
# Source: Custom computation from chord timeline
def analyze_harmonic_rhythm(notes, resolution='beat', beats_per_bar=4, key=None):
    """Analyze harmonic rhythm from note data."""

    # Step 1: Get chord timeline from analyze_clip_chords
    chord_segments = analyze_clip_chords(notes, resolution, beats_per_bar)

    # Step 2: Merge consecutive identical chords into spans
    timeline = []
    for seg in chord_segments:
        if timeline and timeline[-1]["chord"] == seg.get("chord_name"):
            timeline[-1]["duration"] += grid_size  # extend
        else:
            timeline.append({
                "chord": seg.get("chord_name"),
                "start_beat": seg["beat"],
                "duration": grid_size,
            })

    # Step 3: Optional Roman numeral analysis
    if key and timeline:
        chord_names = [t["chord"] for t in timeline if t["chord"]]
        roman_analysis = analyze_progression(chord_names, key)
        # Merge Roman numerals into timeline

    # Step 4: Compute statistics
    total_bars = max_time / beats_per_bar
    changes_per_bar = len(timeline) / total_bars if total_bars > 0 else 0
    durations = [t["duration"] for t in timeline]
    most_common_duration = max(set(durations), key=durations.count)

    return {
        "timeline": timeline,
        "stats": {
            "total_chords": len(timeline),
            "average_changes_per_bar": round(changes_per_bar, 2),
            "most_common_duration": most_common_duration,
        }
    }
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x with pytest-asyncio |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `python -m pytest tests/test_theory.py -x -q --timeout=30` |
| Full suite command | `python -m pytest tests/test_theory.py -q --timeout=60` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ANLY-01 | detect_key returns top 3 candidates with key, mode, confidence | unit | `python -m pytest tests/test_theory.py::TestAnalysisLibrary::test_detect_key_c_major -x` | Wave 0 |
| ANLY-01 | detect_key distinguishes major/minor | unit | `python -m pytest tests/test_theory.py::TestAnalysisLibrary::test_detect_key_minor -x` | Wave 0 |
| ANLY-01 | detect_key tool integration (MCP layer) | integration | `python -m pytest tests/test_theory.py::TestAnalysisTools::test_detect_key_tool -x` | Wave 0 |
| ANLY-02 | analyze_clip_chords segments by beat | unit | `python -m pytest tests/test_theory.py::TestAnalysisLibrary::test_chord_segmentation_beat -x` | Wave 0 |
| ANLY-02 | analyze_clip_chords configurable resolution | unit | `python -m pytest tests/test_theory.py::TestAnalysisLibrary::test_chord_segmentation_resolution -x` | Wave 0 |
| ANLY-02 | analyze_clip_chords quantization window | unit | `python -m pytest tests/test_theory.py::TestAnalysisLibrary::test_quantization_window -x` | Wave 0 |
| ANLY-02 | analyze_clip_chords tool integration | integration | `python -m pytest tests/test_theory.py::TestAnalysisTools::test_analyze_clip_chords_tool -x` | Wave 0 |
| ANLY-03 | analyze_harmonic_rhythm returns timeline + stats | unit | `python -m pytest tests/test_theory.py::TestAnalysisLibrary::test_harmonic_rhythm_stats -x` | Wave 0 |
| ANLY-03 | analyze_harmonic_rhythm with key returns Roman numerals | unit | `python -m pytest tests/test_theory.py::TestAnalysisLibrary::test_harmonic_rhythm_roman -x` | Wave 0 |
| ANLY-03 | analyze_harmonic_rhythm without key omits Roman numerals | unit | `python -m pytest tests/test_theory.py::TestAnalysisLibrary::test_harmonic_rhythm_no_key -x` | Wave 0 |
| ANLY-03 | analyze_harmonic_rhythm tool integration | integration | `python -m pytest tests/test_theory.py::TestAnalysisTools::test_analyze_harmonic_rhythm_tool -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_theory.py -x -q --timeout=30`
- **Per wave merge:** `python -m pytest tests/test_theory.py -q --timeout=60`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_theory.py::TestAnalysisLibrary` -- new class for unit tests of detect_key, analyze_clip_chords, analyze_harmonic_rhythm
- [ ] `tests/test_theory.py::TestAnalysisTools` -- new class for integration tests of 3 MCP tools
- No framework install needed (pytest already configured)
- No new conftest fixtures needed (D-18: standalone tests, no mock_connection)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom pitch histogram | music21 `stream.analyze('key')` | music21 stable since v5+ | Proven KS algorithm with multiple weight profiles |
| Onset-based chord detection | Fixed time-grid segmentation | D-04 decision | Simpler, predictable, configurable granularity |

## Open Questions

1. **Sharp-default spelling in key names**
   - What we know: The project uses `_force_sharp()` everywhere for consistent sharp spelling (C# not Db)
   - What's unclear: music21's key analysis returns Key objects with tonic names that may use flats (e.g., "E-" for Eb)
   - Recommendation: Apply `_force_sharp()` to the tonic Pitch before extracting the name, consistent with all other theory output

2. **Beats per bar for harmonic rhythm**
   - What we know: D-08 says time unit is beats, D-09 says "average changes-per-bar"
   - What's unclear: Whether beats_per_bar should be a parameter or hardcoded to 4
   - Recommendation: Make it a parameter with default 4 (consistent with Ableton's default). Not user-facing in the tool initially -- just a library parameter.

## Sources

### Primary (HIGH confidence)
- music21 9.9.1 installed locally -- tested `stream.analyze('key')`, `correlationCoefficient`, `alternateInterpretations`, empty stream error handling
- Existing codebase: `MCP_Server/theory/chords.py` `identify_chord()`, `MCP_Server/theory/progressions.py` `analyze_progression()`

### Secondary (MEDIUM confidence)
- [music21 key detection docs](https://www.music21.org/music21docs/usersGuide/usersGuide_15_key.html) -- Krumhansl-Schmuckler algorithm options
- [music21 analysis.discrete module](https://www.music21.org/music21docs/moduleReference/moduleAnalysisDiscrete.html) -- weight profile classes

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - music21 9.9.1 verified locally, all APIs tested interactively
- Architecture: HIGH - follows exact patterns from Phases 14-17 with clear CONTEXT.md decisions
- Pitfalls: HIGH - all edge cases verified with actual music21 calls (empty stream, single note, correlation range)

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain, music21 9.x API unlikely to change)
