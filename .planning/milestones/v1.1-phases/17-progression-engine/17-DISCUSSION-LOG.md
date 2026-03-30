# Phase 17: Progression Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 17-progression-engine
**Areas discussed:** Progression catalog, Voice leading in generate_progression, Next-chord suggestion, Roman numeral analysis, Progression length limits, Output consistency

---

## Progression Catalog

### Template Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Roman numerals only | Store as Roman numeral sequences, resolve to MIDI at call time. Key-agnostic | ✓ |
| Roman numerals + voicing hints | Store numerals plus optional voicing metadata per chord | |
| Pre-computed MIDI in C | Store as MIDI pitches in C, transpose at call time | |

**User's choice:** Roman numerals only
**Notes:** Keeps catalog clean and key-agnostic. Resolution happens at call time using existing build_chord/diatonic_chords.

### Genre Coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Core genres (~20-30) | Pop, rock, jazz, blues, R&B/soul, classical, EDM — 3-5 per genre | ✓ |
| Broad genres (~40-60) | Core plus funk, gospel, Latin, country, metal, lo-fi/ambient | |
| Minimal (~10-15) | Universal essentials only | |

**User's choice:** Core genres (~20-30 progressions)

### Metadata

| Option | Description | Selected |
|--------|-------------|----------|
| Name + genre + numerals | Simple, sufficient for retrieval and generation | ✓ |
| Add mood/energy tags | Include mood-based filtering tags | |
| Add tempo/feel hints | Include tempo range and feel suggestions | |

**User's choice:** Name + genre + numerals

### Output Format

| Option | Description | Selected |
|--------|-------------|----------|
| Both: numerals + MIDI | Return Roman numerals AND resolved MIDI pitches using key param | ✓ |
| MIDI pitches only | Resolve to MIDI, lose abstract view | |
| Roman numerals only | Return just the template | |

**User's choice:** Both: numerals + MIDI

---

## Voice Leading in generate_progression

### Sophistication Level

| Option | Description | Selected |
|--------|-------------|----------|
| Basic nearest-voice | Minimize total pitch movement. No parallel checking. Phase 19 adds sophistication | ✓ |
| Root position only | No voice leading, every chord in root position | |
| Full voice leading rules | music21's full rules. Overlaps Phase 19 scope | |

**User's choice:** Basic nearest-voice

### Key Input

| Option | Description | Selected |
|--------|-------------|----------|
| Key + optional scale | Default major/minor, allow modal (dorian, mixolydian, etc.) | ✓ |
| Major/minor key only | Simpler but no modal support | |

**User's choice:** Key + optional scale

---

## Next-Chord Suggestion

### Algorithm

| Option | Description | Selected |
|--------|-------------|----------|
| Rule-based from theory | Music theory rules: dominant→tonic, predominant→dominant, substitutions | |
| Pattern-matching from catalog | Match against catalog progressions, suggest continuations | |
| Hybrid: rules + catalog | Theory rules weighted by catalog frequency | ✓ |

**User's choice:** Hybrid: rules + catalog
**Notes:** More nuanced than either approach alone.

### Context Input

| Option | Description | Selected |
|--------|-------------|----------|
| Key + preceding chords | Key and 1-4 preceding chords. Style/genre optional | ✓ |
| Key + preceding + style required | All three required | |
| Just preceding chords | Infer key from context | |

**User's choice:** Key + preceding chords

### Suggestion Count

| Option | Description | Selected |
|--------|-------------|----------|
| Top 3-5 ranked | Ranked by likelihood/fit, each with brief reason | ✓ |
| All valid options | Every theoretically valid chord, grouped by function | |

**User's choice:** Top 3-5 ranked

### Explanation

| Option | Description | Selected |
|--------|-------------|----------|
| Brief reason per suggestion | e.g., "dominant resolution", "common pop pattern" | ✓ |
| No explanation | Just ranked chords with scores | |
| Detailed analysis | Full harmonic function + theory rule + catalog match info | |

**User's choice:** Brief reason per suggestion

---

## Roman Numeral Analysis

### Non-Diatonic Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Detect and label them | Secondary dominants, borrowed chords, Neapolitan | ✓ |
| Diatonic only | Flag non-diatonic as "outside key" | |
| Full chromatic analysis | Modulations, pivot chords, augmented 6ths | |

**User's choice:** Detect and label them

### Input Format

| Option | Description | Selected |
|--------|-------------|----------|
| Chord names + key | Accept chord names ("Cmaj7", "Dm", "G7") + key | ✓ |
| MIDI pitch sets + key | Arrays of MIDI pitches per chord | |
| Both formats | Accept either format | |

**User's choice:** Chord names + key

### Output Detail

| Option | Description | Selected |
|--------|-------------|----------|
| Rich output | Roman numeral + quality + root + MIDI pitches per chord | ✓ |
| Roman numerals only | Just the numeral sequence | |

**User's choice:** Rich output

---

## Progression Length Limits

### Max Length

| Option | Description | Selected |
|--------|-------------|----------|
| No hard limit | Accept any sequence length | ✓ |
| Cap at 16 chords | Reject > 16 | |
| Soft limit with warning | Accept any but warn above 16 | |

**User's choice:** No hard limit

### History Window

| Option | Description | Selected |
|--------|-------------|----------|
| Up to 4, use what's given | Accept 1-4 preceding chords, use all provided | ✓ |
| Always use last 2 only | Fixed 2-chord window | |
| Variable window up to 8 | Longer pattern detection | |

**User's choice:** Up to 4, use what's given

---

## Output Consistency

### Chord Object Format

| Option | Description | Selected |
|--------|-------------|----------|
| Unified chord object | Same shape across all 4 tools with optional fields | ✓ |
| Tool-specific formats | Each tool returns what makes sense for it | |
| Minimal + expandable | Base object with optional fields per tool | |

**User's choice:** Unified chord object

### Grouping

| Option | Description | Selected |
|--------|-------------|----------|
| Flat list with genre field | Each progression has genre field. Consistent with list_scales | ✓ |
| Grouped by genre | Output grouped as dict by genre | |

**User's choice:** Flat list with genre field

---

## Claude's Discretion

- Internal progressions.py library API design
- Progression catalog exact contents (specific progressions per genre)
- Theory rule weights vs. catalog frequency in hybrid suggestion algorithm
- Chord name parsing implementation for analyze_progression
- music21 roman numeral module usage patterns
- Reuse strategy for existing chords.py/scales.py functions
- Test organization and edge case selection
- Error handling for invalid input

## Deferred Ideas

- Full voice leading rules — Phase 19 scope
- Modulation detection — Phase 18 scope
- Mood/energy tags on templates — future enhancement
- Tempo/feel hints on templates — future enhancement
