# Phase 15: Chord Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 15-chord-engine
**Areas discussed:** Chord quality vocabulary, Voicing output format, Chord identification depth, Diatonic chord detail

---

## Chord Quality Vocabulary

### Q1: How broad should the chord quality vocabulary be?

| Option | Description | Selected |
|--------|-------------|----------|
| Comprehensive | All standard types: triads, 7ths, extended (9/11/13), sus, add, altered. Covers jazz + pop + classical. music21 supports all natively. | ✓ |
| Essential only | Triads + 7ths + sus only. Extended/altered deferred. | |
| You decide | Claude picks breadth based on music21 support. | |

**User's choice:** Comprehensive
**Notes:** None

### Q2: What format should quality strings use?

| Option | Description | Selected |
|--------|-------------|----------|
| Short symbols | Compact music notation: 'maj7', 'min', 'dim7', 'aug', 'sus4'. Familiar to musicians. | ✓ |
| Full words | 'major-seventh', 'minor', 'diminished-seventh'. More readable but verbose. | |
| Both (aliases) | Accept both formats as input, always output short form. | |

**User's choice:** Short symbols
**Notes:** None

### Q3: Should build_chord take separate params or combined string?

| Option | Description | Selected |
|--------|-------------|----------|
| Separate params | build_chord(root='C', quality='maj7') — clear, unambiguous. | ✓ |
| Combined string | build_chord(chord_name='Cmaj7') — convenient but needs parsing. | |

**User's choice:** Separate params
**Notes:** None

### Q4: Should build_chord have a default octave or require it?

| Option | Description | Selected |
|--------|-------------|----------|
| Default octave 4 | Default to octave 4 (C4 = MIDI 60). User can override. | ✓ |
| Require octave | Octave is required — no default. | |

**User's choice:** Default octave 4
**Notes:** None

---

## Voicing Output Format

### Q1: How should chord/voicing notes be represented?

| Option | Description | Selected |
|--------|-------------|----------|
| Rich note objects | Each note: {"midi": 60, "name": "C4"}. Consistent with Phase 14. | ✓ |
| Flat MIDI arrays | Just MIDI arrays: [60, 64, 67]. Minimal. | |

**User's choice:** Rich note objects
**Notes:** None

### Q2: Should notes carry voice assignment labels?

| Option | Description | Selected |
|--------|-------------|----------|
| No voice labels | Ordered bottom to top. Position implies voice. | ✓ |
| Voice labels | Each note tagged soprano/alto/tenor/bass. | |

**User's choice:** No voice labels
**Notes:** None

### Q3: Should get_chord_inversions return all at once or one at a time?

| Option | Description | Selected |
|--------|-------------|----------|
| All inversions | Return all inversions as a list. One call gets everything. | ✓ |
| Single per call | Return single inversion by parameter. | |

**User's choice:** All inversions
**Notes:** None

### Q4: Should get_chord_voicings return all types at once?

| Option | Description | Selected |
|--------|-------------|----------|
| All voicings at once | Dict with all voicing types. One call, full picture. | ✓ |
| One per call | Specify single voicing type per call. | |

**User's choice:** All voicings at once
**Notes:** None

---

## Chord Identification Depth

### Q1: Best match or multiple candidates?

| Option | Description | Selected |
|--------|-------------|----------|
| Best match only | Single best match with name, quality, root, bass note. | |
| Ranked candidates | Top 3 ranked candidates with confidence. Handles ambiguity. | ✓ |

**User's choice:** Ranked candidates
**Notes:** None

### Q2: How to handle incomplete chords?

| Option | Description | Selected |
|--------|-------------|----------|
| Handle gracefully | Accept dyads, power chords, missing 5ths. Identify as best possible. | ✓ |
| Require minimum notes | Require at least 3 notes. Error for fewer. | |

**User's choice:** Handle gracefully
**Notes:** None

### Q3: Slash chord / inversion detection?

| Option | Description | Selected |
|--------|-------------|----------|
| Report as inversion | "C major, 1st inversion" with bass note indicated. | ✓ |
| Slash notation | Report as "C/E". Lead sheet style. | |
| Both | Inversion label + slash notation. | |

**User's choice:** Report as inversion
**Notes:** None

### Q4: How many ranked candidates?

| Option | Description | Selected |
|--------|-------------|----------|
| Top 3 | Up to 3 ranked candidates. Manageable, covers ambiguous cases. | ✓ |
| Top 5 | More thorough but noisier. Diminishing returns beyond 3. | |

**User's choice:** Top 3
**Notes:** None

---

## Diatonic Chord Detail

### Q1: What metadata per diatonic chord?

| Option | Description | Selected |
|--------|-------------|----------|
| Core info | Roman numeral, quality, root, MIDI pitches, degree number. | ✓ |
| Core + function labels | Add tonic/subdominant/dominant labels and substitutions. | |
| Full theory depth | Core + function + tensions per chord. | |

**User's choice:** Core info
**Notes:** None

### Q2: Triads only or also 7th chords?

| Option | Description | Selected |
|--------|-------------|----------|
| Triads + 7ths | Both as separate arrays in one response. | ✓ |
| Triads + 7ths + extended | Include 9ths/11ths/13ths. Comprehensive but large. | |

**User's choice:** Triads + 7ths
**Notes:** None

### Q3: Which scale types to support?

| Option | Description | Selected |
|--------|-------------|----------|
| Major + natural minor | Clean, covers 90% of use cases. | ✓ |
| All common modes | Major, natural/harmonic/melodic minor. Broader but scope creeps toward Phase 16. | |

**User's choice:** Major + natural minor
**Notes:** Harmonic/melodic minor deferred to Phase 16

---

## Claude's Discretion

- Internal `chords.py` library API design
- music21 chord type mapping internals
- Confidence scoring approach for ranked identification
- Test organization and edge case selection

## Deferred Ideas

- Harmonic/melodic minor diatonic chords — Phase 16
- Function labels (tonic/subdominant/dominant) — future enhancement
- Available tensions per degree — future enhancement
- Slash chord notation output — future enhancement
