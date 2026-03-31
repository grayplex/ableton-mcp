# Requirements: AbletonMCP v1.5 Sound Selection Intelligence

**Defined:** 2026-03-30
**Core Value:** An AI assistant can produce actual music in Ableton — with sound selection intelligence that eliminates instrument fumbling.

## v1.5 Requirements

### Instrument Profiles

- [ ] **INST-01**: Claude can retrieve the Wavetable instrument profile — sonic character, strengths/weaknesses, descriptor affinities, and browser category paths validated against live Ableton
- [ ] **INST-02**: Claude can retrieve the Analog instrument profile — sonic character, strengths/weaknesses, descriptor affinities, and browser category paths validated against live Ableton
- [ ] **INST-03**: Claude can retrieve the Operator instrument profile — sonic character, strengths/weaknesses, descriptor affinities, and browser category paths validated against live Ableton
- [ ] **INST-04**: Claude can retrieve the Drift instrument profile — sonic character, strengths/weaknesses, descriptor affinities, and browser category paths validated against live Ableton
- [ ] **INST-05**: Claude can retrieve the Simpler instrument profile — sonic character, strengths/weaknesses, descriptor affinities, and browser category paths validated against live Ableton
- [ ] **INST-06**: Claude can retrieve the Drum Rack instrument profile — sonic character, strengths/weaknesses, descriptor affinities, and browser category paths validated against live Ableton

### Sound Recommendation Tools

- [ ] **SREC-01**: Claude can call `get_sound_recommendation(descriptor)` with a natural-language tag like "warm pad" or "punchy kick" and receive: instrument name, browser category path, and one-line reasoning
- [ ] **SREC-02**: Claude can call `list_sound_descriptors()` and receive all supported role tags (bass, lead, pad, kick...) and character tags (warm, bright, dark, evolving...)
- [ ] **SREC-03**: Claude can call `get_instrument_profile(instrument)` and receive the full instrument character doc including strengths, weaknesses, and best-for roles

### Infrastructure

- [ ] **PKG-01**: `sounds/` peer package with pkgutil auto-discovery catalog (mirrors `genres/` and `mixing/` structure) — zero-registration, one file per instrument
- [ ] **PKG-02**: Weighted sum scoring engine in `catalog.py` — descriptors parsed into individual tags, affinity weights summed per instrument, top match returned with browser path and reasoning

## Future Requirements

### Genre-Aware Recommendations

- **SREC-04**: Claude can call `get_sound_recommendation(descriptor, genre='techno')` and receive genre-informed recommendations — deferred to post-v1.5 when demand is proven

### Expanded Coverage

- **INST-07**: Claude can retrieve profiles for third-party instruments (Serum, Omnisphere, etc.) — deferred; depends on user's installed plugins
- **INST-08**: Claude can retrieve preset-level descriptions within instrument categories — deferred; too many presets, fragile to maintain across Live versions

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full preset path recommendations (specific preset name) | Preset names change across Live versions/editions; fragile. Category-level depth is sufficient. |
| Audio-analysis-based matching | Requires audio streaming not supported by MCP protocol. Fundamentally different architecture. |
| Automatic preset loading without confirmation | Removes user agency; taste is subjective. Recommendation narrows the search space, Claude/user browses from there. |
| Per-preset sonic descriptions | Hundreds of presets per instrument; descriptions become stale across Live versions. |
| Genre coupling in recommendation call | Separation of concerns. Claude can combine genre blueprint knowledge with sound recommendations separately. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INST-01 | TBD | Pending |
| INST-02 | TBD | Pending |
| INST-03 | TBD | Pending |
| INST-04 | TBD | Pending |
| INST-05 | TBD | Pending |
| INST-06 | TBD | Pending |
| SREC-01 | TBD | Pending |
| SREC-02 | TBD | Pending |
| SREC-03 | TBD | Pending |
| PKG-01 | TBD | Pending |
| PKG-02 | TBD | Pending |

**Coverage:**
- v1.5 requirements: 11 total
- Mapped to phases: 0 (roadmap not yet created)
- Unmapped: 11 ⚠️

---
*Requirements defined: 2026-03-30*
*Last updated: 2026-03-30 after initial definition*
