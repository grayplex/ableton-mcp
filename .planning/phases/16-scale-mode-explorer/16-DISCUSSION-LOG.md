# Phase 16: Scale & Mode Explorer - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 16-scale-mode-explorer
**Areas discussed:** Scale catalog scope, Scale detection strategy, Related scale relationships, Harmonic/melodic minor handling

---

## Scale Catalog Scope

### Q1: How broad should the scale catalog be?

| Option | Description | Selected |
|--------|-------------|----------|
| Curated practical set (Recommended) | ~30-50 scales covering 95% of real composition needs | ✓ |
| All music21 scales | Everything music21 supports (hundreds) with category filtering | |
| Tiered with filtering | Curated core set + optional filter param for extended scales | |

**User's choice:** Curated practical set
**Notes:** None

### Q2: How should scale interval patterns be represented?

| Option | Description | Selected |
|--------|-------------|----------|
| Semitone intervals (Recommended) | List of semitone steps, e.g., major = [2, 2, 1, 2, 2, 2, 1] | ✓ |
| Both semitones and names | Semitone list plus "W W H W W W H" formula | |
| Degree-based | Absolute positions relative to chromatic, e.g., [0, 2, 4, 5, 7, 9, 11] | |

**User's choice:** Semitone intervals
**Notes:** None

### Q3: Should list_scales include a category/family per scale?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, include category | Category field for grouping (modal, pentatonic, symmetric) | ✓ |
| No, just name + intervals (Recommended) | Minimal output, name is descriptive enough | |

**User's choice:** Yes, include category
**Notes:** User chose against recommendation — wants category metadata for better organization

---

## Scale Detection Strategy

### Q1: How should detect_scales_from_notes rank matching scales?

| Option | Description | Selected |
|--------|-------------|----------|
| Coverage + simplicity (Recommended) | Coverage %, tiebreak by scale simplicity (major/minor first) | ✓ |
| Coverage only | Pure coverage percentage | |
| Weighted scoring | Multi-factor: coverage + common usage + note count proximity | |

**User's choice:** Coverage + simplicity
**Notes:** None

### Q2: How many scale candidates to return?

| Option | Description | Selected |
|--------|-------------|----------|
| Top 5 candidates (Recommended) | Consistent approach, enough for alternatives | ✓ |
| Top 3 candidates | Tight — just top matches | |
| All above threshold | Variable output size, coverage > 80% | |

**User's choice:** Top 5 candidates
**Notes:** None

### Q3: What detail per candidate?

| Option | Description | Selected |
|--------|-------------|----------|
| Coverage percentage (Recommended) | Report only coverage % | ✓ |
| Coverage + out-of-scale notes | Coverage % plus which notes fall outside | |
| Coverage + characteristic notes | Coverage + mode-defining intervals | |

**User's choice:** Coverage percentage
**Notes:** None

---

## Related Scale Relationships

### Q1: Which relationships to expose? (multi-select)

| Option | Description | Selected |
|--------|-------------|----------|
| Parallel (Recommended) | Same root, different quality | ✓ |
| Relative (Recommended) | Same key signature | ✓ |
| Modes of parent scale (Recommended) | All rotations of a parent scale | ✓ |
| Enharmonic equivalents | Same sound, different name | |

**User's choice:** Parallel, Relative, Modes of parent scale (excluded enharmonic equivalents)
**Notes:** None

### Q2: Output structure?

| Option | Description | Selected |
|--------|-------------|----------|
| Grouped by relationship (Recommended) | Dict: {"parallel": [...], "relative": [...], "modes": [...]} | ✓ |
| Flat list with tags | Flat list, each tagged with relationship type | |

**User's choice:** Grouped by relationship
**Notes:** None

---

## Harmonic/Melodic Minor Handling

### Q1: How should Phase 16 handle harmonic/melodic minor?

| Option | Description | Selected |
|--------|-------------|----------|
| First-class citizens (Recommended) | Fully integrated into all 5 scale tools | ✓ |
| Basic support only | In list_scales and get_scale_pitches only | |
| Defer again | Exclude entirely from Phase 16 | |

**User's choice:** First-class citizens
**Notes:** None

### Q2: Extend get_diatonic_chords for harmonic/melodic minor?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, extend get_diatonic_chords (Recommended) | Add harmonic/melodic minor support to existing tool | ✓ |
| No, keep chords as-is | Phase 16 is scales only, leave chord tool unchanged | |

**User's choice:** Yes, extend get_diatonic_chords
**Notes:** None

---

## Claude's Discretion

- Internal `scales.py` library API design
- Scale name to music21 mapping approach
- Simplicity scoring heuristic for detection ranking
- Curated scale list composition (exact ~30-50 selection)
- Test organization and edge cases
- How to extend `get_diatonic_chords` internally

## Deferred Ideas

- Function labels (tonic/subdominant/dominant) for diatonic chords — carried from Phase 15
- Available tensions per diatonic degree — carried from Phase 15
- Slash chord notation output — carried from Phase 15
- Enharmonic equivalent scale relationships — excluded from get_related_scales
