# Requirements — v1.3 Arrangement Intelligence

**Milestone:** v1.3 Arrangement Intelligence
**Status:** Active
**Last updated:** 2026-03-27

## Milestone v1.3 Requirements

### Blueprint Arrangement Data

- [ ] **ARNG-01**: User can retrieve per-section energy level (int 1–10) from genre blueprints — quantifying the energy curve across all 12 genres and their subgenres
- [ ] **ARNG-02**: User can retrieve per-section instrument roles list from genre blueprints — defining which elements are active per section (e.g. [kick, bass, lead, riser])
- [ ] **ARNG-03**: User can retrieve per-section transition descriptor from genre blueprints — describing how to enter each section (e.g. "filter sweep + riser", "impact hit", "gradual strip-back")

### Production Planning

- [ ] **PLAN-01**: User can generate a full production plan from genre + key + BPM + vibe — returns all sections with calculated beat positions and per-section checklists in under 400 tokens
- [ ] **PLAN-02**: User can generate a targeted plan for a single section without planning the full track
- [ ] **PLAN-03**: User can customize a plan with overrides — shorter/longer sections, add/remove bridge, change section bar counts

### Session Scaffolding

- [ ] **SCAF-01**: User can scaffold a full arrangement into Ableton — creates all named locators and named tracks in Arrangement view from a production plan in one atomic operation
- [ ] **SCAF-02**: User can retrieve an arrangement overview from the active Ableton session — returns locators (with positions), track names, and session length for mid-session re-orientation

### Section Execution

- [ ] **EXEC-01**: User can get a per-section execution checklist — returns pending instrument roles for a given section so Claude can execute methodically
- [ ] **EXEC-02**: User can check arrangement progress — flags scaffolded MIDI tracks that have no instrument loaded, preventing silent empty tracks

## Future Requirements

- Arrangement analysis of existing tracks — stem separation/structural segmentation (different domain, v1.4+)
- Default instrument loading on scaffold tracks — auto-load instruments per role (better UX, v1.3.1 candidate)
- Section reordering — delete-and-rebuild locator workflow, document as known limitation for v1.3
- Vibe-to-energy preset library — Claude interprets vibes contextually, formal preset system deferred
- Empty arrangement clip pre-creation — locators provide sufficient visual guidance for v1.3

## Out of Scope

- **Arrangement analysis of existing tracks** — Different problem domain (audio analysis, stem separation). v1.3 is about planning and building, not analyzing.
- **Non-4/4 time signatures in scaffolding** — Beat position arithmetic uses `beats_per_bar = numerator * (4.0 / denominator)` from the session, but UI for non-standard signatures is out of scope.
- **Arrangement view audio clip automation** — v1.3 scaffolding creates MIDI tracks + locators only; audio clips and automation lanes are out of scope.
- **Server-side plan persistence** — MCP is stateless; Claude holds the plan in context. No server-side plan storage.

## Traceability

*To be filled by roadmapper*

| REQ-ID | Phase | Notes |
|--------|-------|-------|
| ARNG-01 | — | — |
| ARNG-02 | — | — |
| ARNG-03 | — | — |
| PLAN-01 | — | — |
| PLAN-02 | — | — |
| PLAN-03 | — | — |
| SCAF-01 | — | — |
| SCAF-02 | — | — |
| EXEC-01 | — | — |
| EXEC-02 | — | — |
