# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.1 — Theory Engine

**Shipped:** 2026-03-26
**Phases:** 6 | **Plans:** 12 | **Tests:** 224

### What Was Built
- Music theory intelligence layer powered by music21 (23 functions, 23 MCP tools)
- Chord engine: build/identify/invert/voice across 26 chord qualities
- Scale explorer: 38-scale catalog with detection, validation, and modal relationships
- Progression engine: 25-genre catalog with Roman numeral analysis and voice-led generation
- Harmonic analysis: key detection, chord segmentation, harmonic rhythm
- Voice leading + rhythm: smooth connections with parallel-5ths avoidance, 18 pattern templates

### What Worked
- Consistent tool pattern (aliased-import + json.dumps + format_error + MIDI boundary validation) made phases 15-19 fast — pattern established in phase 14, reused verbatim
- Library-then-tools plan structure (XX-01 = library + unit tests, XX-02 = MCP wiring + integration tests) scaled perfectly across all 6 phases
- music21 as backend eliminated need to implement music theory from scratch — Krumhansl-Schmuckler key detection, chord identification, and pitch spelling all delegated
- Server-side only approach meant zero Remote Script changes — no Ableton restart cycles

### What Was Inefficient
- SUMMARY frontmatter `requirements_completed` left empty in phases 14-18 (caught by audit, cosmetic only)
- Nyquist VALIDATION.md files all in draft status — process overhead that didn't add value for a fast-moving milestone
- Phase 17 missing VALIDATION.md entirely — should have been caught during execution

### Patterns Established
- Aliased imports (`_build_chord = build_chord`) to avoid tool/library name collisions
- MIDI range validation at tool boundary, not library layer
- Interval-based scale construction (no music21 scale class dependency)
- Permutation-based voice leading for chords ≤5 notes
- Chord name normalization ("Bb" → "B-") for music21 ChordSymbol compatibility

### Key Lessons
1. When the library/tool split is clean, 2-plan phases execute in ~7 minutes each — keep this structure
2. music21's enharmonic spelling defaults (Eb not D#) require explicit polarity correction for sharp keys — document gotchas early
3. Audit found zero code gaps but 13 metadata items — metadata enforcement should be lighter-touch for fast milestones

### Cost Observations
- Model mix: ~80% opus (execution), ~20% sonnet (planning/research agents)
- Total: 12 plans across ~6 sessions
- Notable: 2-day milestone delivery for 5,704 lines of code — library/tool pattern is highly efficient

---

## Milestone: v1.3 — Arrangement Intelligence

**Shipped:** 2026-03-28
**Phases:** 4 (25-28) | **Plans:** 8 | **Requirements:** 10/10

### What Was Built
- ArrangementEntry schema extended with energy/roles/transition_in — all 12 genres + 4 subgenre overrides authored
- `generate_production_plan` + `generate_section_plan` — blueprint → flat JSON plans with cumulative bar positions and section overrides
- `scaffold_arrangement` — writes production plan into Ableton as locators + MIDI tracks in one atomic call
- `get_arrangement_overview` — reads locators, tracks, session length back from Ableton for re-orientation
- `get_section_checklist` + `get_arrangement_progress` — per-section execution guidance and empty-track detection

### What Worked
- Schema extension was backward-compatible: 148 existing genre tests required zero changes — optional fields with defaults
- Pure-computation plan builder (no Ableton calls) made phases 25-26 fast and fully testable without Ableton running
- Splitting scaffold (write) and overview (read) into separate plans kept scope tight and both plans under 2 hours
- Live Ableton checkpoint in phase 28 caught no regressions — the mock-based unit tests were sufficient

### What Was Inefficient
- Phase 28 plan 02 (live verification checkpoint) was auto-approved without a live Ableton session — VERIFICATION.md left in human_needed state; should close these explicitly or drop as a separate plan type
- Missing SUMMARY.md for 28-02 — absorbed into phase completion notes but not formally recorded
- ARNG-01..03 and PLAN-03 were left unchecked in REQUIREMENTS.md at v1.4 start — requirements should be checked off immediately at plan completion, not caught during retroactive audit

### Patterns Established
- Plan split: pure-computation plans (no Ableton) execute in isolation; Ableton-dependent plans in separate plan
- Deduplicated MIDI track names on scaffold (roles may repeat across sections — only create once)
- Beat position math: bar_count × beats_per_bar for locator positioning, divide by beats_per_bar for display

### Key Lessons
1. Backward-compatible schema extensions are free when fields are optional — add Optional fields, keep defaults, skip migration
2. Pure-computation phases need no live Ableton setup — test them with mock data; reserve live checkpoints for integration phases
3. Mark requirements as complete immediately at plan execution — retroactive audits are slower and more error-prone

### Cost Observations
- Model mix: ~80% opus (execution), ~20% sonnet (planning/research agents)
- Sessions: ~4 sessions in 1 day
- Notable: 4-phase milestone completed in a single day — arrangement data authoring (phase 25) was the bulk; tools phases were fast

---

## Milestone: v1.2 — Genre/Style Blueprints

**Shipped:** 2026-03-27
**Phases:** 5 (20-24) | **Plans:** 9 | **Requirements:** 23/23

### What Was Built
- Blueprint schema (TypedDict) and pkgutil auto-discovery catalog with alias resolution and subgenre merge
- `list_genre_blueprints` + `get_genre_blueprint` MCP tools with section filtering and subgenre support
- Full 12-genre catalog across 3 tiers: P0 house/techno/hip-hop/ambient, P1 DnB/dubstep/trance/neo-soul, P2 synthwave/lo-fi/future bass/disco-funk
- `get_genre_palette` bridging blueprint harmony to theory engine for key-resolved chord/scale/progression output
- Centralized quality gate: token budget + theory name cross-validation across all 12 genres

### What Worked
- Pure data genre files (no imports, no functions) — zero dependency issues, easy to test in isolation
- pkgutil auto-discovery means adding a genre requires zero registration code — dropped straight in
- Building on existing theory engine (v1.1) gave palette bridge for free — `build_chord`, `get_scale_pitches`, `generate_progression` already existed
- Phased genre rollout (P0→P1→P2) kept each plan focused and fast — each plan was 3-5 genre files

### What Was Inefficient
- QUAL-01 token budget lower bound had to be revised from 800 → 400 mid-milestone — should define realistic bounds from a sample blueprint before locking requirements
- Phase 23 plan 02 (future bass + disco/funk) started before plan 01 (synthwave + lo-fi) was complete — small ordering confusion in progress tracking

### Patterns Established
- Pure data genre modules (no code, just a dict) with separate catalog for all logic
- `_QUALITY_MAP` direct lookup for chord type validation (avoids music21 import in genre files)
- Unknown subgenre graceful fallback to base genre (not an error)
- Alias normalization: lowercase + replace spaces/hyphens with underscores before lookup

### Key Lessons
1. Pure data modules + auto-discovery is the right pattern for extensible catalogs — zero boilerplate when adding new genres
2. Define token budgets empirically (measure a real example) before writing requirements — avoid mid-milestone revisions
3. Quality gate with theory engine cross-validation catches naming errors early — worth building upfront for data-heavy phases

### Cost Observations
- Model mix: ~80% opus (execution), ~20% sonnet (planning/research agents)
- Sessions: ~5 sessions across 2 days
- Notable: 9 plans × 5 phases delivered in 2 days — pure data phases are fast; no Remote Script changes needed

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 MVP | 13 | 33 | Established mixin/handler/tool architecture |
| v1.1 Theory Engine | 6 | 12 | Library-then-tools pattern, server-side only |
| v1.2 Genre Blueprints | 5 | 9 | Pure data modules + auto-discovery, quality gate cross-validation |
| v1.3 Arrangement Intelligence | 4 | 8 | Pure-computation + Ableton-write split, backward-compatible schema extension |

### Cumulative Quality

| Milestone | Tests | New Tools | Total Tools |
|-----------|-------|-----------|-------------|
| v1.0 | 204 | 174 | 174 |
| v1.1 | 224 | 23 | 197 |
| v1.2 | 148 genre tests | 3 | 200 |
| v1.3 | ~30 arrangement tests | 6 | 206 |

### Top Lessons (Verified Across Milestones)

1. Consistent patterns accelerate delivery — mixin pattern (v1.0), aliased-import pattern (v1.1), pure data + auto-discovery (v1.2) all proved this
2. Server-side logic that doesn't touch Remote Script ships faster — no Ableton restart overhead
3. Build quality gates into infrastructure phases — token budget + theory name validation (v1.2) caught issues early across all subsequent genre files
4. Split pure-computation and Ableton-write work into separate plans — computation plans are fast, fully testable, and don't need live Ableton
