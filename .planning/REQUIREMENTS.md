# Requirements: AbletonMCP v1.6 Self-evaluation

**Defined:** 2026-03-31
**Core Value:** An AI assistant can produce actual music in Ableton — and know when it's done well.

## v1.6 Requirements

### Evaluation Framework

- [x] **EVAL-01**: Claude has access to a structured evaluation issue schema — each issue captures dimension (mix/arrangement/harmony/sounds), severity (critical/warning/info), a plain-language message, and a fix_hint naming the specific MCP tool or action to resolve it
- [x] **EVAL-02**: Claude has access to a score model — DimensionScore (dimension name, score 0–10, letter grade A–F, issues list) and SessionScore (composite 0–10, letter grade, per-dimension DimensionScore breakdown)

### Mix Balance Evaluator

- [x] **MIX-01**: Claude can trigger the mix balance evaluator, which compares current device parameters against role×genre recipe targets for every track; tracks where more than a threshold percentage of parameters deviate significantly are flagged as issues with severity proportional to deviation magnitude (builds on check_gain_staging + suggest_mix_adjustments logic)
- [x] **MIX-02**: Mix balance produces a DimensionScore 0–10 derived from the percentage of parameters within target range across all tracks; gain staging deviations (dBFS vs. role targets) are included as additional issues

### Arrangement Completeness Evaluator

- [ ] **ARNG-01**: Claude can trigger the arrangement completeness evaluator, which reads the scaffold structure and checks that every scaffolded track has (a) an instrument loaded and (b) at least one clip placed; tracks missing an instrument are flagged as critical; tracks with an instrument but no clips are flagged as warnings

### Sound Selection Coverage Evaluator

- [ ] **SND-01**: Claude can trigger the sound selection coverage evaluator, which maps each instrument-loaded track's role tag to the expected descriptor profile in the sounds/ package and flags tracks whose loaded instrument does not match the role's top descriptor affinity as a warning

### Harmonic Coherence Evaluator

- [ ] **HARM-01**: Claude can trigger the harmonic coherence evaluator, which reads MIDI clip notes from the session and compares each note against the detected session key and scale; notes outside the scale are flagged as issues carrying clip name, bar position, and MIDI note number

### Composite Evaluation

- [ ] **SESS-01**: Claude can call `evaluate_session()` — a single MCP tool that runs all four evaluators in sequence and returns a SessionScore with composite score (0–10), composite letter grade, per-dimension DimensionScore breakdown, and all issues from all dimensions ranked by severity (critical first)
- [ ] **SESS-02**: `evaluate_session()` response includes a `top_fixes` list — up to 3 highest-severity unfixed issues, each annotated with the specific MCP tool call (tool name + suggested arguments) that directly resolves it; this is the "offer fixes" output Claude uses to propose next actions

## Future Requirements

### Auto-apply Fixes

- **SESS-03**: Claude can call `apply_top_fix(issue_id)` to apply a single top_fix automatically — deferred until SESS-01/SESS-02 are validated in real sessions

### Genre-aware Scoring

- **MIX-03**: Mix balance scoring weighted by genre context (e.g., heavy sidechain compression expected in techno, not ambient) — deferred; genre context dependency adds complexity; validate flat scoring first

### Expanded Harmonic Analysis

- **HARM-02**: Harmonic coherence includes inter-clip key consistency check (flags clips that seem to be in a different key than the session key) — deferred to post-v1.6

## Out of Scope

| Feature | Reason |
|---------|--------|
| Audio clip harmonic analysis | Requires audio streaming not supported by MCP protocol |
| Automated issue resolution without user confirmation | Removes user agency; SESS-02 offers fixes, Claude proposes, user confirms |
| Real-time / live scoring during playback | MCP is request/response; not a streaming protocol |
| External reference track comparison | No audio ingestion capability |
| Per-preset sonic matching in SND-01 | Too many presets; fragile across Live versions; category-level is sufficient |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| EVAL-01 | Phase 39 | Complete |
| EVAL-02 | Phase 39 | Complete |
| MIX-01 | Phase 39 | Complete |
| MIX-02 | Phase 39 | Complete |
| ARNG-01 | Phase 40 | Pending |
| SND-01 | Phase 40 | Pending |
| HARM-01 | Phase 40 | Pending |
| SESS-01 | Phase 41 | Pending |
| SESS-02 | Phase 41 | Pending |

**Coverage:**
- v1.6 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 after roadmap creation*
