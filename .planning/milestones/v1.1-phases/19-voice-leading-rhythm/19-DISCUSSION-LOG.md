# Phase 19: Voice Leading & Rhythm - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 19-voice-leading-rhythm
**Areas discussed:** Voice leading rules, Rhythm catalog, MIDI output

---

## Voice Leading Rules

| Option | Description | Selected |
|--------|-------------|----------|
| Nearest-voice + parallel avoidance | Minimize pitch movement PLUS avoid parallel 5ths/octaves | ✓ |
| Full classical rules | Add contrary motion, SATB ranges, tendency tone resolution | |
| Keep it simple — nearest-voice only | Same as Phase 17, just exposed as standalone tools | |

**User's choice:** Nearest-voice + parallel avoidance
**Notes:** Catches the most common voice leading errors without over-engineering

---

| Option | Description | Selected |
|--------|-------------|----------|
| MIDI pitch arrays | Input: two arrays of MIDI pitches. Matches build_chord output | ✓ |
| Chord names | Input: chord name strings | |
| Both formats | Accept either MIDI arrays or chord names | |

**User's choice:** MIDI pitch arrays

---

| Option | Description | Selected |
|--------|-------------|----------|
| Re-voiced chord only | Returns re-voiced target chord as rich note objects | ✓ |
| Add voice motion details | Also include per-voice motion description | |

**User's choice:** Re-voiced chord only

---

## Rhythm Pattern Catalog

| Option | Description | Selected |
|--------|-------------|----------|
| Core 4 categories | Arpeggios, bass lines, comping, strumming. ~15-20 patterns | ✓ |
| Extended 6+ categories | Also add fingerpicking, ostinato, broken chord | |
| Minimal — 2 categories | Just arpeggios and bass lines | |

**User's choice:** Core 4 categories

---

| Option | Description | Selected |
|--------|-------------|----------|
| Chord tone + beat + duration + velocity | Full step data for generating MIDI notes | ✓ |
| No velocity — uniform dynamics | Omit velocity, use default | |
| Add articulation | Add staccato/legato/accent hints | |

**User's choice:** Chord tone + beat + duration + velocity

---

| Option | Description | Selected |
|--------|-------------|----------|
| Flat list + category filter | Consistent with scales and progressions catalogs | ✓ |
| Grouped by category | Nested dict by category | |

**User's choice:** Flat list + category filter

---

## MIDI Output

| Option | Description | Selected |
|--------|-------------|----------|
| Match add_notes_to_clip format | {pitch, start_time, duration, velocity} — zero transformation | ✓ |
| Rich note objects + timing | {midi, name} for pitch plus timing — needs conversion | |

**User's choice:** Match add_notes_to_clip format

---

| Option | Description | Selected |
|--------|-------------|----------|
| Single chord at a time | Input: single chord + pattern name. Claude loops for progressions | ✓ |
| Full progression at once | Input: full progression + pattern + durations | |

**User's choice:** Single chord at a time

---

| Option | Description | Selected |
|--------|-------------|----------|
| start_beat offset param | User provides offset for clip positioning | ✓ |
| Always start at beat 0 | Claude calculates offsets manually | |

**User's choice:** start_beat offset param

---

| Option | Description | Selected |
|--------|-------------|----------|
| Duration param, single iteration | Pattern plays once within duration. Claude controls repetition | ✓ |
| Repeat count param | Pattern repeats N times automatically | |

**User's choice:** Duration param, single iteration

---

## Claude's Discretion

- Parallel 5ths/octaves detection algorithm
- How voice_lead_progression reuses voice_lead_chords
- Specific rhythm pattern step definitions
- Chord tone reference mapping for extended chords

## Deferred Ideas

None — discussion stayed within phase scope
