---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: — Theory Engine
status: Ready to execute
stopped_at: Completed 18-01-PLAN.md
last_updated: "2026-03-25T13:14:37.889Z"
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 10
  completed_plans: 9
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-23)

**Core value:** Claude composes with harmonic intelligence — chords, progressions, and voice leading flow from music theory knowledge, not brute-force pitch guessing.
**Current focus:** Phase 18 — harmonic-analysis

## Current Position

Phase: 18 (harmonic-analysis) — EXECUTING
Plan: 2 of 2

## Performance Metrics

**Velocity:**

- Total plans completed: 2
- Average duration: ~3.6min/plan
- Total execution time: 435s

**v1.0 Reference:** 33 plans in ~1.4 hours (avg ~3min/plan)

## Accumulated Context

### Decisions

- [Milestone]: music21 as theory engine — deep, battle-tested music theory library
- [Milestone]: Theory logic server-side only — no Remote Script changes needed
- [Milestone]: Granular tools (15-25) — individual MCP tools, not composite mega-tools
- [Milestone]: Both analysis + generation — read existing clips AND generate new theory-informed content
- [Phase 14]: Force sharps via accidental polarity check instead of simplifyEnharmonic (music21 prefers Eb/Bb)
- [Phase 14]: Parenthesized negative octave format C(-1) to avoid music21 parsing ambiguity
- [Phase 14]: Key-aware spelling via scale pitch lookup (simplifyEnharmonic keyContext not in music21 9.x)
- [Phase 14]: MIDI range validation at tool layer (0-127) returning format_error, not at library layer
- [Phase 15]: Root-based octave transposition: octave param places chord root at that scientific pitch octave
- [Phase 15]: Aliased imports (_build_chord) to avoid name collision between tool function and library function
- [Phase 16]: Interval-based construction for all 38 scales (no music21 class dependency)
- [Phase 16]: Pitch class set comparison for scale detection and validation
- [Phase 16]: Mode rotation from major intervals for related scale computation
- [Phase 16]: Task 1 already committed from prior session - verified tools registered and functional before testing
- [Phase 17]: Permutation-based voice leading for chords up to 5 notes (O(n!) but n<=5)
- [Phase 17]: Chord name normalization "Bb" -> "B-" for music21 ChordSymbol compatibility
- [Phase 17]: Modal progression resolution via parent major key rotation
- [Phase 17]: All 4 tools follow aliased-import + json.dumps + format_error + MIDI boundary validation pattern
- [Phase 17]: Empty input validation at tool boundary before library calls
- [Phase 18]: Use chord root name for analyze_progression input (not full chord name like 'C-major triad')
- [Phase 18]: Melodic patterns with tonic emphasis needed for unambiguous Krumhansl-Schmuckler key detection results

### Roadmap Evolution

- Phases 14-19 defined for v1.1 Theory Engine milestone
- Continues numbering from v1.0 Phase 13

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-25T13:14:37.886Z
Stopped at: Completed 18-01-PLAN.md
Resume file: None
