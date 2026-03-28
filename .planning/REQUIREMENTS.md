# Requirements — v1.4 Mix/Master Intelligence

**Milestone:** v1.4 Mix/Master Intelligence
**Status:** Active
**Last updated:** 2026-03-28

## Milestone v1.4 Requirements

### Foundation

- [ ] **CATL-01**: User can look up exact Ableton API parameter names, value ranges, and normalized-to-natural-unit conversion formulas for EQ Eight, Compressor, Glue Compressor, Drum Buss, Multiband Dynamics, Reverb, Delay, Auto Filter, Gate, Limiter, Envelope Follower, and Utility — catalog bootstrapped from live Ableton queries, not documentation
- [ ] **ROLE-01**: User can retrieve the canonical mixing role taxonomy — the role identifiers (kick, bass, lead, pad, chords, vocal, atmospheric, return, master) used as keys for recipe lookup across all genres
- [ ] **BATCH-01**: User can set multiple device parameters in a single socket call via a Remote Script batch handler — reducing recipe application from N sequential round-trips to one

### Mix Recipes

- [ ] **RECIP-01**: User can retrieve a role×genre mix recipe for any of the 4 core genres (house, techno, ambient, DnB) — returns EQ, compression, reverb/delay, panning, and dynamics parameter values for the specified role
- [ ] **RECIP-02**: User can retrieve a role×genre mix recipe for all 12 genres — extends RECIP-01 to synthwave, hip-hop/trap, dubstep, trance, lo-fi, future bass, disco/funk, and neo-soul/R&B
- [ ] **MSTR-01**: User can retrieve a master bus recipe for any of the 12 genres — returns parameter settings for a Glue Compressor + Multiband Dynamics + Limiter chain appropriate to that genre's loudness and tonal conventions

### Apply Tools

- [ ] **APPLY-01**: User can apply a role×genre mix recipe to an Ableton track in one MCP tool call — loads the required devices and sets all parameters without requiring multiple sequential tool calls from Claude
- [ ] **APPLY-02**: User can apply a genre master bus recipe to the Ableton master track in one MCP tool call
- [ ] **APPLY-03**: Recipe application is atomic with respect to device loading — parameters are set only after the device is confirmed as instantiated in the Ableton session (no race condition on async device load)

### State Analysis

- [ ] **STATE-01**: User can retrieve current device parameters for every device on every track in a single MCP tool call — returns a complete snapshot of the session's mix state without N sequential reads
- [ ] **GAIN-01**: User can run a gain staging check — returns per-track dBFS estimates from track meter levels, compares to role-based targets, and flags tracks significantly above or below target
- [ ] **GAIN-02**: Gain staging check excludes MIDI tracks with no instrument loaded from analysis — no false-positive flags on empty scaffold tracks

### Mix Intelligence

- [ ] **INTEL-01**: User can request mix adjustment suggestions for a track — returns a list of parameter diffs (current value → suggested value) with a one-sentence reason per change, based on comparing current device state against the role×genre recipe

### Sidechain Routing

- [ ] **SIDE-01**: User can set a compressor's sidechain input source by track name — resolves the source track to the correct index at apply time rather than requiring hardcoded track indices

## Future Requirements

- Section-aware mixing — apply different mix settings per arrangement section (e.g. louder drop vs. breakdown); requires automation infrastructure (v1.5+)
- Frequency conflict detection — detect masking between competing tracks; requires audio analysis beyond LOM meter access (v1.5+)
- Full sidechain chain automation — auto-wire all genre-conventional sidechain connections (e.g. bass → kick, lead → kick) in one call (v1.5+)
- Per-instrument default device loading on scaffold tracks — auto-load instruments when scaffolding (v1.4.1 candidate)

## Out of Scope

- **Spectrum frequency analysis** — Ableton's Spectrum device exposes no frequency bin data via the LOM; visualization-only device. Dropped from v1.4.
- **LUFS metering** — Requires raw audio sample arrays (NumPy); MCP Server and Remote Script have no audio buffer access. Use output_meter_level as gain staging proxy instead.
- **Automated mixing without human confirmation** — suggest_mix_adjustments always returns diffs for user review before apply; no unsupervised bulk rewrite.
- **Non-Ableton device support** — Recipes cover Ableton built-in devices only; third-party VST/AU parameter naming is outside catalog scope.

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| CATL-01 | Phase 29 | Pending |
| ROLE-01 | Phase 29 | Pending |
| RECIP-01 | Phase 30 | Pending |
| BATCH-01 | Phase 31 | Pending |
| APPLY-01 | Phase 31 | Pending |
| APPLY-02 | Phase 31 | Pending |
| APPLY-03 | Phase 31 | Pending |
| SIDE-01 | Phase 31 | Pending |
| STATE-01 | Phase 32 | Pending |
| GAIN-01 | Phase 32 | Pending |
| GAIN-02 | Phase 32 | Pending |
| INTEL-01 | Phase 33 | Pending |
| RECIP-02 | Phase 34 | Pending |
| MSTR-01 | Phase 34 | Pending |
