# Milestones

## v1.3 Arrangement Intelligence (Shipped: 2026-03-28)

**Phases completed:** 4 phases (25-28), 8 plans
**Requirements:** 10/10 complete
**Git range:** feat(25-01) → feat(28-01), 20+ commits
**Timeline:** 1 day (2026-03-28)

**Delivered:** Systematic production workflow for Ableton — plan sections from genre conventions, encode the plan as locators and tracks, execute section-by-section with checklist guidance.

**Key accomplishments:**

- ArrangementEntry schema extended with optional energy (1-10), roles, and transition_in fields — backward-compatible across all 12 genres and 148 tests
- `generate_production_plan` and `generate_section_plan` MCP tools transforming genre blueprints into token-efficient flat JSON plans with bar positions and override support
- `scaffold_arrangement` MCP tool writing production plans into Ableton as named locators and MIDI tracks in one atomic operation
- `get_arrangement_overview` MCP tool reading back locators, tracks, and session length for mid-session re-orientation
- `get_section_checklist` and `get_arrangement_progress` tools enabling methodical per-section execution — nothing skipped under context pressure

---

## v1.2 Genre/Style Blueprints (Shipped: 2026-03-27)

**Phases completed:** 5 phases (20-24), 9 plans
**Requirements:** 23/23 complete
**Git range:** feat(20-01) → feat(24-02), 40+ commits
**Timeline:** 2 days (2026-03-26 → 2026-03-27)

**Delivered:** Curated genre reference system giving Claude consistent knowledge of 12 electronic music genres — instrumentation, harmony, rhythm, arrangement, and mixing — delivered via MCP with theory engine integration.

**Key accomplishments:**

- Blueprint schema (TypedDict) and auto-discovery catalog (pkgutil) with alias resolution, shallow subgenre merge, and import-time validation
- Two MCP tools: `list_genre_blueprints` + `get_genre_blueprint` with section filtering, subgenre support, and alias resolution
- Full 12-genre catalog: P0 (house, techno, hip-hop/trap, ambient), P1 (DnB, dubstep, trance, neo-soul/R&B), P2 (synthwave, lo-fi, future bass, disco/funk) — 35+ subgenres total
- `get_genre_palette` MCP tool bridging blueprint harmony data to theory engine with key-resolved chord names, scales, and progressions
- Centralized quality gate: all 12 genres validated against token budget (537-670 tokens, under 1200 limit) and theory engine name registry

---

## v1.1 Theory Engine (Shipped: 2026-03-26)

**Phases completed:** 6 phases (14-19), 12 plans, 224 tests
**Lines of code:** 5,704 Python (theory library + tools + tests)
**Git range:** feat(14-01) → feat(19-02), 15 feature commits
**Timeline:** 2 days (2026-03-24 → 2026-03-25)

**Delivered:** Comprehensive music theory intelligence layer powered by music21, giving Claude harmonic awareness for composing, analyzing, and arranging in Ableton Live.

**Key accomplishments:**

- Music theory foundation with music21 integration and bidirectional MIDI-to-note mapping across 128 pitches
- Chord engine supporting 26 qualities with build/identify/invert/voice operations
- 38-scale catalog with pitch generation, note validation, scale detection, and modal relationships
- Progression engine with 25-genre catalog, Roman numeral analysis, voice-led generation, and next-chord suggestions
- Harmonic analysis: Krumhansl-Schmuckler key detection, time-grid chord segmentation, harmonic rhythm analysis
- Voice leading with parallel-5ths/octaves avoidance + 18 rhythm patterns producing add_notes_to_clip-ready MIDI

---
