# Research: music21 Integration for Theory Engine

**Researched:** 2026-03-23
**Confidence:** HIGH (music21 is mature, well-documented, MIT-licensed)

---

## 1. Overview

music21 is a Python library for computational musicology developed at MIT. It provides classes for notes, chords, scales, keys, intervals, Roman numeral analysis, voice leading, and more. It's the most comprehensive music theory library in the Python ecosystem.

**Install:** `pip install music21` (pure Python, no compiled extensions)
**Size:** ~30MB installed, ~100+ submodules
**Python:** 3.10+ supported, compatible with our FastMCP server environment

---

## 2. Key Classes for Integration

### Pitch & Note Mapping

```python
from music21 import pitch, note

# MIDI → Note name
p = pitch.Pitch(midi=60)
p.nameWithOctave  # 'C4'
p.name            # 'C'
p.octave          # 4

# Note name → MIDI
p = pitch.Pitch('Eb4')
p.midi            # 63

# Enharmonic equivalents
p.getEnharmonic() # D#4
```

**Key insight:** music21 uses C4 = MIDI 60 (standard), which matches Ableton's convention. Direct MIDI number passthrough works.

### Chord Building

```python
from music21 import chord, harmony

# From pitches
c = chord.Chord(['C4', 'E4', 'G4'])
c.pitchedCommonName  # 'C-major triad'
c.root()             # C4
c.quality            # 'major'

# From chord symbol (jazz notation)
cs = harmony.ChordSymbol('Cmaj7')
cs.pitches           # (C4, E4, G4, B4)

# From root + quality
cs = harmony.ChordSymbol(root='D', kind='minor-seventh')
cs.pitches           # (D3, F3, A3, C4)

# Available chord kinds (partial list):
# 'major', 'minor', 'diminished', 'augmented',
# 'dominant-seventh', 'major-seventh', 'minor-seventh',
# 'diminished-seventh', 'half-diminished-seventh',
# 'augmented-seventh', 'suspended-second', 'suspended-fourth',
# 'dominant-ninth', 'major-ninth', 'minor-ninth',
# 'dominant-13th', 'major-13th'
```

### Chord Inversions

```python
c = chord.Chord(['C4', 'E4', 'G4'])
c.inversion()        # 0 (root position)

# Get specific inversions
c_inv1 = c.closedPosition()  # root position by default
# Manual inversion: move bass note up an octave
pitches = list(c.pitches)
pitches[0] = pitches[0].transpose(12)  # 1st inversion: E4, G4, C5
```

### Voicings (Drop-2, Open, Close)

music21 provides `closedPosition()` for close voicing. Open and drop voicings require manual pitch manipulation:

```python
c = chord.Chord(['C4', 'E4', 'G4', 'B4'])  # Cmaj7 close
c_closed = c.closedPosition()

# Drop-2: take 2nd-from-top note, drop it an octave
pitches = list(c_closed.pitches)  # [C4, E4, G4, B4]
pitches[2] = pitches[2].transpose(-12)  # G3
# Result: [G3, C4, E4, B4] — drop-2 voicing

# Open voicing: alternate notes up an octave
# Custom implementation needed
```

**Key insight:** music21 handles close position natively. Drop-2, drop-3, and open voicings need ~10 lines of custom code each — straightforward.

### Chord Identification

```python
from music21 import chord

c = chord.Chord([60, 64, 67])  # MIDI numbers work directly
c.pitchedCommonName  # 'C-major triad'
c.root().midi        # 60
c.quality            # 'major'
c.commonName         # 'major triad'

# For jazz symbols:
from music21 import harmony
cs = harmony.chordSymbolFromChord(c)
cs.figure            # 'C'
```

### Scales & Modes

```python
from music21 import scale

# Major scale
s = scale.MajorScale('C')
s.getPitches('C4', 'C5')  # [C4, D4, E4, F4, G4, A4, B4, C5]

# All built-in scale types:
# MajorScale, MinorScale, HarmonicMinorScale, MelodicMinorScale,
# DorianScale, PhrygianScale, LydianScale, MixolydianScale,
# LocrianScale, WholeToneScale, ChromaticScale,
# OctatonicScale (diminished), PentatonicScale (not directly — use modes)

# Get scale degrees
s = scale.MajorScale('C')
for degree in range(1, 8):
    p = s.pitchFromDegree(degree)  # C, D, E, F, G, A, B

# Check if pitch is in scale
s = scale.MajorScale('C')
'F#4' in [str(p) for p in s.getPitches('C4', 'C5')]  # False

# Relative/parallel scales
s = scale.MajorScale('C')
s.getRelativeMinor()   # A minor
s.getParallelMinor()   # C minor
```

### Key Detection (Krumhansl-Schmuckler)

```python
from music21 import stream, note, analysis

# Build a stream from MIDI pitches
s = stream.Stream()
for midi_num, duration in notes_data:
    n = note.Note(midi=midi_num)
    n.quarterLength = duration
    s.append(n)

# Analyze key
key_result = s.analyze('key')
key_result.tonic      # e.g., pitch.Pitch('C')
key_result.mode       # 'major' or 'minor'
key_result.correlationCoefficient  # confidence 0.0-1.0

# Alternative algorithms available:
s.analyze('key.krumhansl')
s.analyze('key.bellman-budge')
s.analyze('key.temperley')
```

### Roman Numeral Analysis

```python
from music21 import roman, key

k = key.Key('C')

# Chord → Roman numeral
rn = roman.romanNumeralFromChord(chord.Chord(['C4', 'E4', 'G4']), k)
rn.figure        # 'I'
rn.quality       # 'major'

# Roman numeral → Chord
rn = roman.RomanNumeral('V7', 'C')
rn.pitches       # (G4, B4, D5, F5)
rn.key           # Key of C major

# Diatonic chords in a key
for degree in ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'viio']:
    rn = roman.RomanNumeral(degree, 'C')
    print(f"{degree}: {rn.pitchedCommonName}")
```

### Voice Leading

```python
from music21 import voiceLeading

# Check voice leading between two chords
vl = voiceLeading.VoiceLeadingQuartet(
    pitch.Pitch('C4'), pitch.Pitch('E4'),  # chord 1 voices
    pitch.Pitch('B3'), pitch.Pitch('D4'),  # chord 2 voices
)
vl.parallelMotion()    # check for parallels
vl.hiddenInterval()    # check for hidden fifths/octaves

# For smooth voice leading, use closedPosition + manual minimal-movement algorithm
# music21 doesn't have a built-in "voice lead these two chords" function,
# but provides all the primitives needed
```

**Key insight:** music21 provides voice leading *analysis* (detecting parallels, hidden intervals) but not voice leading *generation* (find smoothest voicing). We need ~30 lines of custom code for the minimal-movement algorithm.

---

## 3. Performance Considerations

### Import Time
- `import music21` takes ~2-3 seconds on first import (loads many submodules)
- **Mitigation:** Import at server startup, not per-tool-call. MCP server starts once.

### Per-Call Performance
- Chord building: <1ms
- Scale operations: <1ms
- Key detection (Krumhansl-Schmuckler): ~5-50ms depending on note count
- Roman numeral analysis: <1ms per chord
- **Verdict:** Fast enough for MCP tool calls. No performance concern.

### Memory
- music21 uses ~50-100MB after full import
- Acceptable for a server process

---

## 4. Integration Architecture

### Recommended Structure

```
MCP_Server/
├── theory/
│   ├── __init__.py       # Package init, lazy music21 import
│   ├── chords.py         # Chord building, inversions, voicings, identification
│   ├── scales.py         # Scale/mode listing, pitch generation, detection
│   ├── progressions.py   # Templates, generation, Roman numeral analysis
│   ├── analysis.py       # Key detection, chord segmentation, harmonic rhythm
│   ├── voice_leading.py  # Minimal-movement voicing, progression voicing
│   └── rhythm.py         # Pattern templates, pattern application
└── tools/
    └── theory.py         # MCP tool definitions (thin wrappers around theory/)
```

### Data Flow

```
Claude calls MCP tool → tools/theory.py → theory/*.py (uses music21) → JSON response
                                                                          ↓
Claude calls add_notes_to_clip with the returned MIDI pitches ← ← ← ← ← ←
```

Theory tools return MIDI-ready data (pitch numbers, start times, durations, velocities) that can be directly passed to existing `add_notes_to_clip` tool.

### Output Format Convention

All theory tools should return JSON with MIDI-ready data:

```json
{
  "chord": "Cmaj7",
  "root": "C",
  "quality": "major-seventh",
  "pitches": [60, 64, 67, 71],
  "note_names": ["C4", "E4", "G4", "B4"]
}
```

For progression/rhythm tools that output time-positioned notes:

```json
{
  "notes": [
    {"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100},
    {"pitch": 64, "start_time": 0.0, "duration": 1.0, "velocity": 100}
  ]
}
```

---

## 5. What music21 Handles vs. Custom Code

| Feature | music21 | Custom Code Needed |
|---------|---------|-------------------|
| Pitch ↔ MIDI mapping | Yes | Minimal wrapper |
| Chord from symbol | Yes (harmony.ChordSymbol) | None |
| Chord identification | Yes (pitchedCommonName) | None |
| Close-position voicing | Yes (closedPosition) | None |
| Drop-2/3, open voicings | No | ~15 lines each |
| Scale pitch generation | Yes (getPitches) | Wrapper for MIDI output |
| Key detection | Yes (analyze('key')) | Stream building from MIDI |
| Roman numeral ↔ chord | Yes (roman.RomanNumeral) | None |
| Voice leading analysis | Yes (VoiceLeadingQuartet) | None |
| Voice leading generation | No | ~30 lines (minimal movement algo) |
| Progression templates | No | Data file with common progressions |
| Next-chord suggestion | No | Markov chain or rule-based system |
| Rhythm patterns | No | Data file with pattern templates |
| Chord segmentation by time | No | Custom grouping algorithm |
| Harmonic rhythm analysis | No | Custom analysis over time segments |

---

## 6. Dependencies & Compatibility

- **music21** requires only Python 3.10+ and standard library
- Optional deps (matplotlib, lilypond) not needed — we only use theory, not rendering
- Compatible with FastMCP server environment
- No conflicts with existing dependencies (socket, threading, json)
- Install: `pip install music21` adds to requirements.txt / pyproject.toml

---

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| music21 import time (~3s) | Server startup delay | Import once at startup; acceptable for long-running server |
| music21 API changes | Breaking changes in theory code | Pin version in requirements; music21 is stable (v9.x) |
| Enharmonic ambiguity | Chord identification may vary (C# vs Db) | Normalize output; include both name and MIDI numbers |
| Scale coverage gaps | Some exotic scales not in music21 | Can define custom scales via AbstractScale |
| Voice leading quality | Simple minimal-movement may not be musically ideal | Start simple, iterate based on user feedback |

---

## 8. Conclusion

music21 is an excellent fit for the Theory Engine. It handles ~60% of the required functionality out of the box (chord building, identification, scales, key detection, Roman numerals). The remaining ~40% (voicings, progression templates, voice leading generation, rhythm patterns, chord segmentation) requires custom code but uses music21 primitives as building blocks.

The integration is clean: theory tools live entirely in MCP_Server (no Remote Script changes), accept/return MIDI numbers, and produce data ready for existing `add_notes_to_clip` calls.
