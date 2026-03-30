# Phase 22: Core Genre Library - Research

**Researched:** 2026-03-26
**Phase:** 22-core-genre-library
**Goal:** The 8 most-used electronic genres are available as complete blueprints (P0 + P1 tiers)

## 1. Template Analysis (house.py)

house.py is 187 lines: GENRE dict (71 lines) + SUBGENRES dict (115 lines, 4 subgenres).

### GENRE dict structure:
- `name`, `id`, `bpm_range`, `aliases` (metadata)
- `instrumentation.roles` (list of strings)
- `harmony.scales`, `harmony.chord_types`, `harmony.common_progressions`
- `rhythm.time_signature`, `rhythm.bpm_range`, `rhythm.swing`, `rhythm.note_values`, `rhythm.drum_pattern`
- `arrangement.sections` (list of {name, bars} dicts)
- `mixing.frequency_focus`, `mixing.stereo_field`, `mixing.common_effects`, `mixing.compression_style`
- `production_tips.techniques`, `production_tips.pitfalls`

### SUBGENRES dict structure:
Each subgenre overrides only dimensions that differ from base. Commonly overridden:
- `bpm_range`, `aliases`, `name` (always)
- `harmony` (often — different chord preferences)
- `rhythm` (sometimes — different BPM, swing, pattern)
- `mixing` (sometimes — different frequency focus)
- `instrumentation` (rarely — only if role set differs significantly)
- `arrangement` (rarely — only if structure differs significantly)
- `production_tips` (rarely — only for very distinct techniques)

## 2. Genre Content Research

### Techno (GENR-02) — 5 subgenres
- **File:** `techno.py`
- **BPM:** 125-150
- **Scales:** natural_minor, dorian, phrygian, locrian
- **Chord types:** min7, min, dim, sus4, dom7
- **Key traits:** repetitive, hypnotic, four-on-the-floor, minimal harmony, percussive
- **Subgenres:** minimal (128-135), industrial (135-150), melodic (125-135), Detroit (128-135), peaktime/driving (135-145)

### Hip-hop/Trap (GENR-03) — 3 subgenres
- **File:** `hip_hop_trap.py`
- **BPM:** 70-160 (wide range: boom bap ~85-95, trap ~130-160)
- **Scales:** natural_minor, minor_pentatonic, blues, dorian, mixolydian
- **Chord types:** min7, maj7, dom7, min9, dim7, add9
- **Key traits:** syncopated drums, 808 bass, sample-based, half-time feel
- **Subgenres:** boom_bap (85-95), trap (130-160), lo_fi_hip_hop (70-90)

### Ambient (GENR-04) — 3 subgenres
- **File:** `ambient.py`
- **BPM:** 60-120 (or no BPM — ambient can be atemporal)
- **Scales:** major, lydian, mixolydian, dorian, natural_minor, major_pentatonic
- **Chord types:** maj7, min7, add9, sus4, sus2, maj9
- **Key traits:** textural, atmospheric, pad-heavy, minimal rhythm, spacious
- **Subgenres:** dark_ambient (60-80), drone (0-60), cinematic (80-120)

### Drum & Bass (GENR-05) — 4 subgenres
- **File:** `drum_and_bass.py`
- **BPM:** 160-180
- **Scales:** natural_minor, dorian, minor_pentatonic, harmonic_minor
- **Chord types:** min7, min, dom7, min9, dim
- **Key traits:** fast breakbeats, heavy sub-bass, syncopated drums, reese bass
- **Subgenres:** liquid (170-176), neurofunk (172-178), jungle (160-175), neuro (170-180)

### Dubstep (GENR-06) — 4 subgenres
- **File:** `dubstep.py`
- **BPM:** 138-142 (half-time feel)
- **Scales:** natural_minor, phrygian, minor_pentatonic, harmonic_minor
- **Chord types:** min, min7, dim, sus4, dom7
- **Key traits:** half-time drums, heavy wobble bass, sub-bass focus, build-drop structure
- **Subgenres:** brostep (140-150), riddim (140-150), melodic (138-145), deep_dubstep (138-142)

### Trance (GENR-07) — 3 subgenres
- **File:** `trance.py`
- **BPM:** 128-150
- **Scales:** natural_minor, harmonic_minor, lydian, major, dorian
- **Chord types:** min, maj, min7, sus4, add9, maj7
- **Key traits:** euphoric melodies, long builds, anthem-style, arpeggiated synths, emotional
- **Subgenres:** progressive_trance (128-134), uplifting (136-142), psytrance (140-150)

### Neo-soul/R&B (GENR-08) — 3 subgenres
- **File:** `neo_soul_rnb.py`
- **BPM:** 65-110
- **Scales:** dorian, mixolydian, major, natural_minor, minor_pentatonic, blues
- **Chord types:** min7, maj7, dom7, min9, maj9, add9, 11, 13, dim7
- **Key traits:** jazz-influenced harmony, warm/analog sounds, groovy, soulful vocals
- **Subgenres:** neo_soul (70-95), contemporary_rnb (80-110), alternative_rnb (65-100)

## 3. Valid Theory Engine Names

### Chord types (from _QUALITY_MAP — 26 total):
maj, min, dim, aug, maj7, min7, dom7, 7, dim7, hdim7, min7b5, sus2, sus4, add9, 9, min9, maj9, 11, min11, 13, min13, 7b5, 7#5, 7b9, 7#9, 7#11

### Scale names (from SCALE_CATALOG — 38 total):
major, natural_minor, chromatic, ionian, dorian, phrygian, lydian, mixolydian, aeolian, locrian, harmonic_minor, melodic_minor, major_pentatonic, minor_pentatonic, blues, whole_tone, diminished_hw, diminished_wh, augmented, double_harmonic, hungarian_minor, neapolitan_minor, neapolitan_major, persian, arabic, japanese, hirajoshi, in_sen, iwato, yo, kumoi, pelog, chinese, egyptian, prometheus, tritone, bebop_dominant, bebop_major

ALL genre blueprints must use only names from these sets per D-09/D-10.

## 4. Planning Approach

### Grouping Strategy
7 genres × ~150-200 lines each = ~1000-1400 lines of pure data. Plus tests.

Recommended split into 2 plans:
- **Plan 22-01 (Wave 1):** P0 genres — techno, hip_hop_trap, ambient (3 genres, 3 files + tests)
- **Plan 22-02 (Wave 1, parallel):** P1 genres — drum_and_bass, dubstep, trance, neo_soul_rnb (4 genres, 4 files + tests)

Both waves can be parallel — no dependencies between genres. Each plan creates independent .py files.

### Testing Strategy
Per genre:
1. Schema validation passes (`validate_blueprint(GENRE)` succeeds)
2. All 6 dimensions present with non-empty values
3. All subgenres defined per CONTEXT.md
4. All chord_types in `_QUALITY_MAP`
5. All scale names in `SCALE_CATALOG`
6. Aliases resolve correctly via catalog

## 5. File Naming Conventions
- `techno.py` — straightforward
- `hip_hop_trap.py` — underscores for compound names
- `ambient.py` — straightforward
- `drum_and_bass.py` — full name with underscores
- `dubstep.py` — straightforward
- `trance.py` — straightforward
- `neo_soul_rnb.py` — abbreviate R&B to rnb

## 6. Risk Assessment

### Low Risk
- Pure data authoring — no logic, no external deps
- house.py template proven with 24 tests
- Auto-discovery handles registration

### Only Risk
- Music theory accuracy — wrong chord types or scale names caught by D-09 tests
- Content completeness — each dimension must be musically accurate

## RESEARCH COMPLETE
