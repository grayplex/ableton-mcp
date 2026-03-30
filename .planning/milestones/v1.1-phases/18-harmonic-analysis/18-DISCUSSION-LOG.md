# Phase 18: Harmonic Analysis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 18-harmonic-analysis
**Areas discussed:** Key detection output, Chord segmentation, Harmonic rhythm

---

## Key Detection Output

| Option | Description | Selected |
|--------|-------------|----------|
| Single best with confidence | Returns best match key + confidence score (0-1). Simple, most useful for AI workflows | |
| Top 3 ranked candidates | Returns 3 candidates ranked by confidence. Matches identify_chord pattern from Phase 15 | ✓ |

**User's choice:** Top 3 ranked candidates
**Notes:** Consistent with Phase 15's identify_chord returning ranked candidates for ambiguous input

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — separate candidates | C major and A minor appear as distinct candidates with their own confidence scores | ✓ |
| Grouped — show both together | Each candidate shows the key pair (e.g., "C major / A minor") | |

**User's choice:** Yes — separate candidates (major and minor as distinct entries)
**Notes:** music21's Krumhansl-Schmuckler naturally distinguishes major from minor

---

| Option | Description | Selected |
|--------|-------------|----------|
| Key + confidence + mode only | Clean, minimal: key name, mode, confidence score | ✓ |
| Add scale pitches | Also include scale degrees as MIDI pitches | |
| Add correlation vector | Include pitch-class distribution data | |

**User's choice:** Key + confidence + mode only
**Notes:** Minimal output — user can call get_scale_pitches separately if needed

---

## Chord Segmentation

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed time grid | User specifies beat or bar divisions. Simple, predictable | ✓ (with modification) |
| Onset-based detection | Detect note change boundaries automatically | |
| Configurable grid resolution | Default per-beat with resolution parameter | |

**User's choice:** Fixed time grid, but with concern about strummed chords landing off-beat
**Notes:** User raised the strummed chord concern — resolved by adding a quantization window that captures slightly off-grid notes. User confirmed they don't need odd meter support and want to avoid arpeggio misfires.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Grid + quantization window | Default per-beat grid with resolution param + small quantization tolerance | ✓ |
| Grid + configurable tolerance | Same but user can specify tolerance size | |

**User's choice:** Grid + quantization window (hardcoded tolerance)
**Notes:** Quantization window size left to Claude's discretion

---

| Option | Description | Selected |
|--------|-------------|----------|
| Chord ID + confidence per segment | Time position, chord name, quality, root, MIDI pitches, confidence | ✓ |
| Add raw notes per segment | Same plus raw MIDI notes per segment | |

**User's choice:** Chord ID + confidence per segment (no raw notes)

---

## Harmonic Rhythm

| Option | Description | Selected |
|--------|-------------|----------|
| Beats | Beats as time unit — consistent with beat-based grid | ✓ |
| Bars | Bar-relative positions | |
| Both beats and bars | Report in both units | |

**User's choice:** Beats

---

| Option | Description | Selected |
|--------|-------------|----------|
| Stats + chord timeline | Chord list with durations, avg changes-per-bar, most common duration | ✓ |
| Add repetition/structure detection | Plus pattern detection and section boundaries | |
| Timeline only, no stats | Minimal — just chord timeline | |

**User's choice:** Stats + chord timeline (no structure detection)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Chord timeline with Roman numerals | Each entry includes Roman numeral when key provided | ✓ |
| Timeline without Roman numerals | Skip Roman numerals; use analyze_progression separately | |

**User's choice:** Chord timeline with Roman numerals

---

| Option | Description | Selected |
|--------|-------------|----------|
| Optional key param | Roman numerals included when key given, omitted otherwise | ✓ |
| Required key param | Always require key | |

**User's choice:** Optional key param

---

## Claude's Discretion

- Quantization window size (exact tolerance in beats)
- Choice of music21 key detection algorithm
- Empty segment handling (skip vs report as rest)

## Deferred Ideas

None — discussion stayed within phase scope
