# Phase 24: Palette Bridge & Quality Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 24-palette-bridge-quality-gate
**Areas discussed:** Palette tool output, Token budget method, Cross-validation, Palette depth

---

## Palette Tool Output

### What should get_genre_palette return?

| Option | Description | Selected |
|--------|-------------|----------|
| Resolved names only | Chord names (Cmin7), scale names with root (C dorian), progression chord names — no MIDI | :heavy_check_mark: |
| Full MIDI resolution | Actual MIDI note arrays for each chord, scale pitches, full progression with note data | |
| Hybrid — names + optional MIDI | Default to names, add optional include_midi=true parameter | |

**User's choice:** Resolved names only
**Notes:** Claude already has build_chord/get_scale_pitches tools to resolve to MIDI when needed.

### Should get_genre_palette support subgenre and section filtering?

| Option | Description | Selected |
|--------|-------------|----------|
| Genre + key only | Simple interface, subgenre resolves via alias | :heavy_check_mark: |
| Genre + key + subgenre param | Explicit subgenre parameter matching get_genre_blueprint | |
| Genre + key + scale_type | Add optional scale_type override for exploring beyond blueprint defaults | |

**User's choice:** Genre + key only
**Notes:** None

### How should common_progressions be resolved?

| Option | Description | Selected |
|--------|-------------|----------|
| Roman numerals to chord names | Convert 'I-V-vi-IV' to ['Cmaj', 'Gmaj', 'Amin', 'Fmaj'] | :heavy_check_mark: |
| Keep as Roman numerals | Pass through as-is, Claude uses generate_progression separately | |
| Both formats | Return {numerals: ..., chords: ...} giving both representations | |

**User's choice:** Roman numerals to chord names
**Notes:** None

---

## Token Budget Method

### How should the 800-1200 token budget be measured?

| Option | Description | Selected |
|--------|-------------|----------|
| tiktoken cl100k | OpenAI's tiktoken with cl100k_base encoding, Claude-compatible approximation | :heavy_check_mark: |
| Simple word/char heuristic | Approximate: tokens ≈ len(json_str) / 4, no external dependency | |
| Anthropic tokenizer | Official Anthropic tokenizer if available | |

**User's choice:** tiktoken cl100k
**Notes:** Standard for LLM token counting, pip-installable, reproducible.

### What gets measured for QUAL-01?

| Option | Description | Selected |
|--------|-------------|----------|
| json.dumps() of full blueprint | Exactly what Claude sees when requesting a full blueprint | :heavy_check_mark: |
| Just the 6 dimension values | Exclude metadata, tighter measure of actual content | |
| Tool output including metadata | Everything in the tool response | |

**User's choice:** json.dumps() of full blueprint
**Notes:** None

### If a blueprint exceeds 1200 tokens?

| Option | Description | Selected |
|--------|-------------|----------|
| Test fails, must trim | Hard gate — blueprint content must be trimmed to fit | |
| Warning only | Log warning but don't fail | |
| Soft cap with override | Default hard gate at 1200, allow per-genre MAX_TOKENS override | :heavy_check_mark: |

**User's choice:** Soft cap with override
**Notes:** Some genres may genuinely need more space than 1200 tokens.

---

## Cross-Validation

### What additional cross-validation does QUAL-02 need?

| Option | Description | Selected |
|--------|-------------|----------|
| Centralized all-genre test | One test iterating ALL 12 genres + subgenres, single source of truth | :heavy_check_mark: |
| Keep per-genre only | Existing per-genre tests already satisfy QUAL-02 | |
| Both per-genre + centralized | Keep per-genre for fast feedback, add centralized for completeness | |

**User's choice:** Centralized all-genre test
**Notes:** Auto-catches any new genre added later.

### How should palette bridge tests work?

| Option | Description | Selected |
|--------|-------------|----------|
| Mock-free integration | Call get_genre_palette with real genres and keys, verify output end-to-end | :heavy_check_mark: |
| Unit + integration split | Unit tests with mocked catalog, plus some integration tests | |
| Parametrized across genres | Parametrized test across every genre × a few keys | |

**User's choice:** Mock-free integration
**Notes:** Exercises real theory engine + genre catalog end-to-end.

---

## Palette Depth

### How deep should the palette bridge go?

| Option | Description | Selected |
|--------|-------------|----------|
| Name resolution only | Chord names, scale names with root, progression chord names. No MIDI, no voice leading | :heavy_check_mark: |
| Names + diatonic chords | Also include diatonic chords for each scale via get_diatonic_chords | |
| Full theory resolution | Chord names, scale pitches, diatonic chords, voice-led progressions | |

**User's choice:** Name resolution only
**Notes:** Claude calls other tools for deeper resolution.

### What if a blueprint references unsupported theory names?

| Option | Description | Selected |
|--------|-------------|----------|
| Partial results + unresolved list | Return what can be resolved, include 'unresolved' list | :heavy_check_mark: |
| Fail on any unresolved name | Return error, force blueprints to be 100% compatible | |
| Skip silently | Silently skip unresolved names | |

**User's choice:** Partial results + unresolved list
**Notes:** Graceful degradation, not hard failure.

---

## Claude's Discretion

- Tool file placement, bridge function organization, output JSON structure
- Token budget test implementation details
- tiktoken as dev/test dependency only or runtime
- Centralized cross-validation test structure

## Deferred Ideas

None — discussion stayed within phase scope.
