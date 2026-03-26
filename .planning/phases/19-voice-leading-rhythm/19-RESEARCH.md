# Phase 19: Voice Leading & Rhythm - Research

**Researched:** 2026-03-25
**Domain:** Voice leading algorithms, parallel motion detection, rhythm pattern MIDI generation
**Confidence:** HIGH

## Summary

Phase 19 delivers the final 4 MCP tools in the Theory Engine milestone, bridging abstract music theory (chords, progressions) to playable MIDI note sequences. The voice leading component upgrades Phase 17's basic `_voice_lead_pair()` with parallel 5ths/octaves detection, while the rhythm component introduces a new pattern catalog and applicator. Both domains are well-understood algorithmically and the existing codebase provides clear implementation patterns from 5 prior theory phases.

The voice leading algorithm requires pairwise interval checking between consecutive chords across all voice pairs. The rhythm pattern system is a straightforward data catalog (similar to `PROGRESSION_CATALOG`) plus a mapping function that converts chord-tone references to absolute MIDI pitches at specific beat positions. The output format for `apply_rhythm_pattern` must match `add_notes_to_clip` exactly: `{"pitch": int, "start_time": float, "duration": float, "velocity": int}`.

**Primary recommendation:** Implement voice leading in `voicing.py` using the existing permutation-based approach enhanced with an interval-pair filter, and rhythm patterns in `rhythm.py` as a flat catalog with a mapping function. Both follow the established Phase 14-18 patterns exactly.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Nearest-voice algorithm (minimize total pitch movement) PLUS parallel 5ths and octaves avoidance. Upgrades Phase 17's basic `_voice_lead_pair()` which has no parallel motion checking
- **D-02:** Input format: MIDI pitch arrays (e.g., `[60, 64, 67]`), not chord name strings. Matches how Claude already works with `build_chord` output
- **D-03:** `voice_lead_chords` returns the re-voiced target chord as rich note objects only -- no voice motion details or labels
- **D-04:** `voice_lead_progression` accepts key + Roman numeral sequence (like Phase 17's `generate_progression`) but uses the upgraded voice leading algorithm with parallel avoidance
- **D-05:** Core 4 categories: arpeggios (up, down, alternating), bass lines (root-5th, walking), comping (block, syncopated), strumming (down, up-down). ~15-20 patterns total
- **D-06:** Each pattern step: chord tone reference (root, 3rd, 5th, 7th, octave), beat position (in beats), duration (in beats), velocity (0-127)
- **D-07:** Flat list output with category field per pattern. Optional category and style filter parameters (consistent with scales and progressions catalogs)
- **D-08:** Output format matches `add_notes_to_clip` exactly: `{"pitch": int, "start_time": float, "duration": float, "velocity": int}` per note. Zero transformation needed to write to clip
- **D-09:** Accepts single chord (MIDI pitches) + pattern name per call. Claude calls it per chord in a loop for full progressions -- simple, composable
- **D-10:** `start_beat` offset parameter positions notes in the clip timeline (e.g., chord at bar 3 = start_beat 8 in 4/4)
- **D-11:** `duration` parameter in beats controls pattern length. Pattern plays once within that duration. Claude controls repetition by calling multiple times with different start_beat offsets
- **D-12:** Library code split by domain: `MCP_Server/theory/voicing.py` (voice leading) and `MCP_Server/theory/rhythm.py` (rhythm patterns). Tools in `MCP_Server/tools/theory.py`
- **D-13:** Barrel exports from `MCP_Server/theory/__init__.py`
- **D-14:** No prefix on tool names -- `voice_lead_chords`, not `theory_voice_lead_chords`
- **D-15:** MIDI validation (0-127) at tool boundary layer, not in library functions
- **D-16:** Rich note objects `{"midi": int, "name": str}` for voice leading output
- **D-17:** `json.dumps()` string returns; errors use `format_error()`
- **D-18:** Standalone tests -- no `mock_connection` needed
- **D-19:** Lazy music21 imports inside functions

### Claude's Discretion
- Exact parallel 5ths/octaves detection algorithm implementation
- How `voice_lead_progression` internally reuses `voice_lead_chords` or shares logic
- Specific rhythm pattern step definitions (exact beat positions, velocities per pattern)
- How chord tone references map to actual MIDI pitches for extended chords (9ths, 11ths)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| VOIC-01 | User can get voice-led connection between two chords (minimal movement voicing) | Nearest-voice permutation algorithm from Phase 17 `_voice_lead_pair()` enhanced with parallel 5ths/octaves filter. Input: two MIDI pitch arrays. Output: re-voiced target as rich note objects. |
| VOIC-02 | User can generate a full voice-led chord progression from a Roman numeral sequence | Reuses `_resolve_numeral_to_chord()` from progressions.py + upgraded voice leading. Pattern mirrors `generate_progression()` but routes through the new parallel-safe algorithm. |
| RHYM-01 | User can retrieve rhythm pattern templates (arpeggios, bass lines, comping patterns, strumming) by style | Flat catalog of ~15-20 patterns with category/style fields. Each step uses chord tone references (root, 3rd, 5th, 7th, octave) + beat position + duration + velocity. |
| RHYM-02 | User can apply a rhythm pattern to a chord or progression to get time-positioned MIDI notes ready for `add_notes_to_clip` | Maps chord tone references to MIDI pitches from input chord, applies start_beat offset and duration scaling. Output: `[{"pitch": int, "start_time": float, "duration": float, "velocity": int}]` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| music21 | 9.x (already installed) | Pitch/interval computation, Roman numeral resolution | Already the theory engine foundation (Phase 14) |
| Python itertools | stdlib | permutations for voice leading optimization | Already used in existing `_voice_lead_pair()` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| MCP_Server.theory.chords | existing | `_make_note_obj()`, `_midi_to_pitch()`, `build_chord()` | Voice leading note object construction |
| MCP_Server.theory.progressions | existing | `_resolve_numeral_to_chord()`, `_voice_lead_pair()` | Reference/reuse for progression resolution |
| MCP_Server.theory.pitch | existing | `_force_sharp()`, `_format_note_name()` | Consistent note naming |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom permutation voice leading | music21's voiceLeading module | music21's module is complex, underdocumented; custom is simpler and already proven in Phase 17 |
| Manual parallel detection | music21's checker functions | Custom is transparent and only needs interval comparison; music21's API adds unnecessary complexity |

**Installation:**
No new dependencies needed. All libraries already installed from Phase 14.

## Architecture Patterns

### Recommended Project Structure
```
MCP_Server/theory/
    voicing.py          # NEW: voice_lead_chords(), voice_lead_progression(), _has_parallel_motion()
    rhythm.py           # NEW: RHYTHM_CATALOG, get_rhythm_patterns(), apply_rhythm_pattern()
    __init__.py         # ADD: 4 new exports
    chords.py           # EXISTING: _make_note_obj, _midi_to_pitch, build_chord (imported by voicing.py)
    progressions.py     # EXISTING: _resolve_numeral_to_chord, _voice_lead_pair (referenced by voicing.py)

MCP_Server/tools/
    theory.py           # ADD: 4 new @mcp.tool() functions

tests/
    test_theory.py      # ADD: TestVoiceLeadingLibrary, TestRhythmLibrary, TestVoiceLeadingTools, TestRhythmTools
```

### Pattern 1: Parallel 5ths/Octaves Detection
**What:** Check whether two consecutive chord voicings contain parallel perfect 5ths (7 semitones) or octaves (0/12 semitones) between any voice pair.
**When to use:** After computing a candidate voice leading, before accepting it.
**Algorithm:**
```python
def _has_parallel_motion(prev_midis, next_midis):
    """Check for parallel perfect 5ths or octaves between voice pairs.

    For each pair of voices (i, j), compute the interval (mod 12) in both
    the previous and next chord. If both are 7 (P5) or 0 (P8/unison),
    AND the voices moved in the same direction (not contrary/oblique),
    that's a parallel motion violation.

    Args:
        prev_midis: sorted MIDI pitches of previous chord
        next_midis: sorted MIDI pitches of next chord (same length)

    Returns:
        bool: True if parallel 5ths or octaves detected
    """
    n = len(prev_midis)
    for i in range(n):
        for j in range(i + 1, n):
            prev_interval = (prev_midis[j] - prev_midis[i]) % 12
            next_interval = (next_midis[j] - next_midis[i]) % 12

            # Both intervals are perfect 5ths or both are unisons/octaves
            if prev_interval == next_interval and prev_interval in (0, 7):
                # Check that both voices moved (not oblique motion)
                motion_i = next_midis[i] - prev_midis[i]
                motion_j = next_midis[j] - prev_midis[j]
                # Parallel = same direction, both moved
                if motion_i != 0 and motion_j != 0 and (motion_i > 0) == (motion_j > 0):
                    return True
    return False
```

### Pattern 2: Voice Leading with Parallel Avoidance
**What:** Try all permutations (n<=5), filter out those with parallel motion, pick minimum total movement from remaining.
**When to use:** In `voice_lead_chords()` and `voice_lead_progression()`.
**Algorithm:**
```python
def voice_lead_chords(source_midis, target_midis):
    """Voice-lead target chord to minimize movement, avoiding parallel 5ths/octaves.

    1. Generate candidate placements for each target pitch class near source center
    2. Try all permutations (chords <= 5 notes)
    3. Filter out permutations that create parallel 5ths/octaves with source
    4. Pick the permutation with minimum total movement
    5. If ALL permutations have parallels, fall back to minimum movement (best effort)
    """
    # ... candidate generation (reuse from _voice_lead_pair logic) ...
    # ... permutation search with parallel filter ...
```

### Pattern 3: Rhythm Pattern Catalog Structure
**What:** Flat list of pattern dicts with chord tone references, matching the `PROGRESSION_CATALOG` and `SCALE_CATALOG` patterns.
**When to use:** For `get_rhythm_patterns()` and `apply_rhythm_pattern()`.
**Data Structure:**
```python
RHYTHM_CATALOG = [
    {
        "name": "arpeggio_up",
        "category": "arpeggio",
        "style": "basic",
        "description": "Ascending arpeggio through chord tones",
        "time_signature": "4/4",
        "steps": [
            {"tone": "root",  "beat": 0.0, "duration": 0.25, "velocity": 100},
            {"tone": "3rd",   "beat": 0.25, "duration": 0.25, "velocity": 90},
            {"tone": "5th",   "beat": 0.5, "duration": 0.25, "velocity": 85},
            {"tone": "octave","beat": 0.75, "duration": 0.25, "velocity": 80},
            # ... repeats for remaining beats
        ],
    },
    # ... ~15-20 patterns total
]
```

### Pattern 4: Chord Tone Resolution
**What:** Map abstract tone references ("root", "3rd", "5th", "7th", "octave") to actual MIDI pitches from an input chord.
**When to use:** In `apply_rhythm_pattern()`.
**Algorithm:**
```python
def _resolve_chord_tone(tone_ref, chord_midis):
    """Map a chord tone reference to an actual MIDI pitch.

    chord_midis is sorted ascending. Mapping:
    - "root"   -> chord_midis[0]
    - "3rd"    -> chord_midis[1] (if exists, else root)
    - "5th"    -> chord_midis[2] (if exists, else last available)
    - "7th"    -> chord_midis[3] (if exists, else 5th or last)
    - "octave" -> chord_midis[0] + 12
    """
```

### Anti-Patterns to Avoid
- **Hand-rolling interval theory from scratch:** Use `% 12` arithmetic for pitch class intervals. Do NOT use music21's interval module for this -- it's overkill for simple semitone comparison
- **Modifying `progressions.py` directly:** The existing `_voice_lead_pair()` must remain untouched for backward compatibility. Create upgraded version in `voicing.py` that imports and extends
- **Absolute pitch patterns:** Rhythm patterns must use chord tone references ("root", "3rd"), not absolute MIDI pitches. Patterns must be reusable across any chord
- **Over-engineering the parallel detector:** Only check perfect 5ths (7 semitones) and octaves/unisons (0 semitones mod 12). Do NOT check for hidden/direct 5ths or other advanced voice leading rules

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MIDI-to-note conversion | Custom pitch math | `_make_note_obj(_midi_to_pitch(m))` from chords.py | Already handles sharp preference, octave format |
| Roman numeral resolution | Custom scale degree math | `_resolve_numeral_to_chord()` from progressions.py | Handles modal scales, borrowed chords, quality suffixes |
| Chord construction | Manual pitch stacking | `build_chord()` from chords.py | Handles 21+ quality types, proper voicing |
| Permutation optimization | Custom search | `itertools.permutations` | Standard library, already proven in Phase 17 |

**Key insight:** Most of the hard music theory problems were solved in Phases 14-17. Phase 19 composes existing solutions with two new algorithms (parallel detection + rhythm mapping).

## Common Pitfalls

### Pitfall 1: Parallel Detection with Unequal Chord Sizes
**What goes wrong:** `voice_lead_chords` receives chords of different sizes (e.g., triad -> 7th chord). Voice pair tracking becomes ambiguous.
**Why it happens:** Different chord qualities have different note counts.
**How to avoid:** When chord sizes differ, parallel detection operates on the minimum of the two sizes. Extra voices in the larger chord have no "partner" and cannot create parallels.
**Warning signs:** IndexError on voice pair comparison, or false positives from misaligned voices.

### Pitfall 2: All Permutations Have Parallels
**What goes wrong:** For some chord transitions (e.g., I -> V in root position triads), every permutation may contain parallel 5ths.
**Why it happens:** Certain harmonic progressions inherently have parallel perfect intervals when both chords share the same structure.
**How to avoid:** Fall back to minimum-movement permutation when all candidates have parallels. The parallel filter is a preference, not a hard constraint. Log or flag that best-effort was used.
**Warning signs:** Empty candidate list after filtering.

### Pitfall 3: Rhythm Pattern Duration Exceeds Chord Duration
**What goes wrong:** A pattern designed for 4 beats gets applied to a 2-beat chord, causing notes to extend beyond the intended range.
**Why it happens:** Pattern step beat positions exceed the `duration` parameter.
**How to avoid:** Clip pattern steps to the specified duration. Skip steps that would start at or after `start_beat + duration`. Do not attempt to compress/scale the pattern.
**Warning signs:** Notes overlapping with the next chord's time region.

### Pitfall 4: Chord Tone Reference for Missing Chord Notes
**What goes wrong:** Pattern references "7th" but chord is a triad (only 3 notes).
**Why it happens:** Not all chords have the same number of notes.
**How to avoid:** Graceful fallback: if index exceeds chord size, wrap to the highest available tone, or use the root an octave up. Document the fallback strategy.
**Warning signs:** IndexError when resolving chord tones.

### Pitfall 5: Import Cycle Between voicing.py and progressions.py
**What goes wrong:** `voicing.py` imports from `progressions.py` for `_resolve_numeral_to_chord`, and if progressions.py ever imports from voicing.py, circular import occurs.
**Why it happens:** Shared utility functions across theory modules.
**How to avoid:** Voicing imports from progressions (one-way dependency). Progressions never imports from voicing. If shared utilities are needed, extract to a common module or import at function level.
**Warning signs:** ImportError at module load time.

### Pitfall 6: Output Format Mismatch for apply_rhythm_pattern
**What goes wrong:** Output includes extra fields (like `"name"`) or uses wrong types (float velocity instead of int), causing `add_notes_to_clip` to fail.
**Why it happens:** Mixing the theory engine's rich note format with Ableton's note format.
**How to avoid:** The `apply_rhythm_pattern` output format is `{"pitch": int, "start_time": float, "duration": float, "velocity": int}` -- matching `add_notes_to_clip` exactly. This is deliberately different from the rich note objects used elsewhere in the theory engine.
**Warning signs:** Type errors when passing output to `add_notes_to_clip`.

## Code Examples

### Voice Lead Two Chords (Library Function)
```python
# Source: Derived from existing _voice_lead_pair() in progressions.py
from itertools import permutations
from MCP_Server.theory.chords import _make_note_obj, _midi_to_pitch

def voice_lead_chords(source_midis, target_midis):
    """Voice-lead target chord to minimize movement from source, avoiding parallels.

    Args:
        source_midis: List of MIDI pitches for the source/previous chord
        target_midis: List of MIDI pitches for the target/next chord

    Returns:
        list[dict]: Re-voiced target chord as rich note objects [{"midi": int, "name": str}, ...]
    """
    source_sorted = sorted(source_midis)
    center = sum(source_sorted) / len(source_sorted)

    # Generate candidates: place each target pitch class near source center
    target_pcs = [m % 12 for m in target_midis]
    candidates = []
    for pc in target_pcs:
        base = int(center) - (int(center) % 12) + pc
        options = [base - 12, base, base + 12]
        best = min(options, key=lambda x: abs(x - center))
        candidates.append(best)

    # Try all permutations for small chords
    n_source = len(source_sorted)
    n_target = len(candidates)

    if n_target <= 5:
        best_perm = None
        best_cost = float("inf")

        for perm in permutations(candidates):
            sorted_perm = sorted(perm)
            cost = sum(abs(s - t) for s, t in zip(source_sorted[:n_target], sorted_perm[:n_source]))

            # Check for parallel 5ths/octaves
            if n_source == n_target and not _has_parallel_motion(source_sorted, sorted_perm):
                if cost < best_cost:
                    best_cost = cost
                    best_perm = sorted_perm

        # Fallback: if all have parallels, use minimum movement
        if best_perm is None:
            best_cost = float("inf")
            for perm in permutations(candidates):
                sorted_perm = sorted(perm)
                cost = sum(abs(s - t) for s, t in zip(source_sorted[:n_target], sorted_perm[:n_source]))
                if cost < best_cost:
                    best_cost = cost
                    best_perm = sorted_perm
    else:
        best_perm = sorted(candidates)

    return [_make_note_obj(_midi_to_pitch(m)) for m in best_perm]
```

### Apply Rhythm Pattern (Library Function)
```python
# Source: Designed per D-08, D-09, D-10, D-11
def apply_rhythm_pattern(chord_midis, pattern_name, start_beat=0.0, duration=4.0):
    """Apply a rhythm pattern to a chord, producing time-positioned MIDI notes.

    Args:
        chord_midis: List of MIDI pitches (sorted ascending) for the chord
        pattern_name: Name of pattern from RHYTHM_CATALOG
        start_beat: Starting beat position in clip timeline
        duration: Duration in beats (pattern plays once within this)

    Returns:
        list[dict]: Notes in add_notes_to_clip format:
                    [{"pitch": int, "start_time": float, "duration": float, "velocity": int}]
    """
    pattern = _get_pattern(pattern_name)  # lookup from catalog
    sorted_midis = sorted(chord_midis)

    notes = []
    for step in pattern["steps"]:
        # Skip steps beyond duration
        if step["beat"] >= duration:
            continue

        pitch = _resolve_chord_tone(step["tone"], sorted_midis)
        note_dur = min(step["duration"], duration - step["beat"])

        notes.append({
            "pitch": pitch,
            "start_time": start_beat + step["beat"],
            "duration": note_dur,
            "velocity": step["velocity"],
        })

    return notes
```

### Tool Registration Pattern (from existing codebase)
```python
# Source: MCP_Server/tools/theory.py existing pattern
from MCP_Server.theory import voice_lead_chords as _voice_lead_chords

@mcp.tool()
def voice_lead_chords(ctx: Context, source_midis: list[int], target_midis: list[int]) -> str:
    """Connect two chords with smooth voice leading, minimizing pitch movement
    and avoiding parallel 5ths/octaves.

    Parameters:
    - source_midis: MIDI pitches of the source/current chord (e.g., [60, 64, 67])
    - target_midis: MIDI pitches of the target/next chord (e.g., [65, 69, 72])
    """
    try:
        if not source_midis or not target_midis:
            return format_error(
                "Empty chord input",
                detail="Both source_midis and target_midis must be non-empty lists",
                suggestion="Provide MIDI pitches from build_chord output",
            )
        for midis, label in [(source_midis, "source"), (target_midis, "target")]:
            for m in midis:
                if not (0 <= m <= 127):
                    return format_error(
                        f"MIDI pitch out of range in {label}",
                        detail=f"Got {m}, must be 0-127",
                        suggestion="All MIDI pitches must be between 0 and 127",
                    )
        result = _voice_lead_chords(source_midis, target_midis)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to voice lead chords",
            detail=str(e),
            suggestion="Provide two lists of MIDI pitches (e.g., from build_chord)",
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Basic nearest-voice (Phase 17) | Nearest-voice + parallel filter | Phase 19 | More musically correct voice leading |
| No rhythm output | Pattern-based MIDI generation | Phase 19 | Theory engine connects to actual clip writing |
| Manual note placement by Claude | `apply_rhythm_pattern` automation | Phase 19 | Claude composes by combining theory tools |

**Deprecated/outdated:**
- Phase 17's `_voice_lead_pair()` remains for backward compatibility but is superseded by Phase 19's `voice_lead_chords()` for new code

## Open Questions

1. **Extended chord tone mapping for 9ths, 11ths, 13ths**
   - What we know: Standard chords have root/3rd/5th/7th. Extended chords add 9th, 11th, 13th.
   - What's unclear: Should rhythm patterns reference "9th" directly, or just use the chord's pitch array index?
   - Recommendation: Use index-based fallback. Map "root"->0, "3rd"->1, "5th"->2, "7th"->3, "octave"->chord[0]+12. If index exceeds chord size, wrap to last available. This handles any chord size gracefully. This is explicitly in Claude's discretion per CONTEXT.md.

2. **Pattern normalization: 4/4 assumption**
   - What we know: All patterns assume 4/4 time with beat positions in beats.
   - What's unclear: Should patterns support other time signatures?
   - Recommendation: All patterns assume 4/4 for now. The `duration` parameter naturally handles any bar length (3 beats for 3/4, etc.). Future enhancement if needed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured in pyproject.toml) |
| Config file | `pyproject.toml` |
| Quick run command | `python -m pytest tests/test_theory.py -x --tb=short -q` |
| Full suite command | `python -m pytest tests/test_theory.py --tb=short -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VOIC-01 | Voice-led connection between two chords | unit | `python -m pytest tests/test_theory.py -k "TestVoiceLeadingLibrary" -x` | No - Wave 0 |
| VOIC-01 | voice_lead_chords MCP tool | integration | `python -m pytest tests/test_theory.py -k "TestVoiceLeadingTools and voice_lead_chords" -x` | No - Wave 0 |
| VOIC-02 | Full voice-led progression from Roman numerals | unit | `python -m pytest tests/test_theory.py -k "TestVoiceLeadingLibrary and progression" -x` | No - Wave 0 |
| VOIC-02 | voice_lead_progression MCP tool | integration | `python -m pytest tests/test_theory.py -k "TestVoiceLeadingTools and progression" -x` | No - Wave 0 |
| RHYM-01 | Retrieve rhythm pattern templates | unit | `python -m pytest tests/test_theory.py -k "TestRhythmLibrary and get_rhythm" -x` | No - Wave 0 |
| RHYM-01 | get_rhythm_patterns MCP tool | integration | `python -m pytest tests/test_theory.py -k "TestRhythmTools and get_rhythm" -x` | No - Wave 0 |
| RHYM-02 | Apply rhythm pattern to chord | unit | `python -m pytest tests/test_theory.py -k "TestRhythmLibrary and apply_rhythm" -x` | No - Wave 0 |
| RHYM-02 | apply_rhythm_pattern MCP tool | integration | `python -m pytest tests/test_theory.py -k "TestRhythmTools and apply_rhythm" -x` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_theory.py -x --tb=short -q`
- **Per wave merge:** `python -m pytest tests/test_theory.py --tb=short -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
None -- existing test infrastructure (`tests/conftest.py`, `mcp_server` fixture, pytest config) covers all needs. Tests will be added in-plan alongside implementation (matching Phase 14-18 pattern where tests are part of the implementation tasks).

## Sources

### Primary (HIGH confidence)
- `MCP_Server/theory/progressions.py` lines 250-294 -- Existing `_voice_lead_pair()` implementation (permutation-based, center-placement)
- `MCP_Server/theory/chords.py` -- `_make_note_obj()`, `_midi_to_pitch()`, `build_chord()` API signatures
- `MCP_Server/tools/theory.py` -- 19 existing tools following the aliased-import + json.dumps + format_error + MIDI validation pattern
- `MCP_Server/tools/clips.py` lines 35-57 -- `add_notes_to_clip` target format: `{"pitch": int, "start_time": float, "duration": float, "velocity": int}`
- `MCP_Server/theory/__init__.py` -- Barrel export pattern
- `tests/test_theory.py` -- 181 existing tests across 10 test classes; established unit (direct function call) and integration (mcp_server fixture) patterns
- `.planning/phases/19-voice-leading-rhythm/19-CONTEXT.md` -- All locked decisions D-01 through D-19
- `.planning/phases/14-theory-foundation/14-CONTEXT.md` -- Foundation patterns (lazy imports, output format, naming)
- `.planning/phases/17-progression-engine/17-CONTEXT.md` -- Voice leading origin, unified chord format

### Secondary (MEDIUM confidence)
- [Voice leading parallel fifths/octaves theory](https://en.wikipedia.org/wiki/Voice_leading) -- Definition of parallel motion rules
- [Chorale guide parallels](http://www.choraleguide.com/vl-parallels.php) -- Practical parallel 5ths/octaves detection methodology
- [Music theory parallel avoidance](https://musictheory.pugetsound.edu/mt21c/AvoidingObjectionableParallels.html) -- Rules for what constitutes parallel motion (same direction, both voices move)

### Tertiary (LOW confidence)
None -- all findings verified against codebase and music theory fundamentals.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies; all libraries already in use since Phase 14
- Architecture: HIGH - Direct extension of 5 prior phases with identical patterns
- Pitfalls: HIGH - Derived from code analysis of existing implementations and music theory fundamentals
- Voice leading algorithm: HIGH - Based on existing `_voice_lead_pair()` plus well-understood interval theory
- Rhythm patterns: HIGH - Straightforward catalog + mapping pattern, no external dependencies

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain, no external dependency changes expected)
