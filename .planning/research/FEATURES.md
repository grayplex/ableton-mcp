# Feature Landscape: v1.2 Genre/Style Blueprints

**Domain:** Genre blueprint reference system for AI-assisted music production
**Researched:** 2026-03-25
**Confidence:** HIGH

## Table Stakes

Features that define the minimum viable blueprint system. Without these, blueprints add no value.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Genre blueprint retrieval by name | Core value proposition -- Claude must access genre knowledge | Low | `get_genre_blueprint(genre="house")` |
| Genre listing/discovery | Claude needs to know what genres exist | Low | `list_genre_blueprints()` |
| Instrumentation section | Users expect genre-appropriate track/instrument guidance | Med | What instruments to load, role of each |
| Harmony section | Users expect genre-appropriate chords/scales/progressions | Med | Chord types, scales, progressions by name |
| Rhythm section | Users expect genre-appropriate groove guidance | Med | Feel, grid, swing, syncopation |
| Arrangement section | Users expect genre-appropriate song structure | Med | Section order, lengths, techniques |
| Mixing section | Users expect genre-appropriate mixing guidance | Med | Frequency balance, stereo image, effects |
| Minimum 8 genres | Enough to cover major electronic music territory | High (content) | House, techno, DnB, dubstep, trance, ambient, hip-hop/trap, synthwave |
| Subgenre support | Electronic genres have important subgenre distinctions | Med | deep_house vs tech_house are very different |
| Section filtering | Full blueprints are 2000+ tokens; Claude should request only what it needs | Low | `sections=["harmony", "rhythm"]` parameter |

## Differentiators

Features that elevate blueprints beyond a static reference. Not required for MVP but add significant value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Genre palette tool | Bridges blueprints to theory engine -- returns key-resolved chords, scales, progressions | Med | `get_genre_palette(genre="neo_soul", key="Eb")` |
| Ableton-specific tips | Maps genre conventions to actual Ableton instruments/effects | Low | "Use Operator for bass, Wavetable for pads" |
| Cross-genre references | "If you like X, also consider Y" | Low | Metadata linking related genres |
| BPM range per genre | Immediate actionable parameter | Low | `bpm_range: [118, 130]` |
| Subgenre merge with parent | Request deep_house, get house base + deep_house overrides | Med | Shallow merge strategy |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Auto-genre detection from existing project | Requires analyzing Ableton session state (tempo, instruments, patterns); fragile and error-prone | Let Claude infer from conversation context or ask the user |
| Blueprint editing/creation tools | Blueprints are curated reference data, not user-editable | Ship quality content; accept PRs for new genres |
| Real-time blueprint updates from web | Introduces network dependency, staleness issues, trust problems | Static curated data is more reliable and predictable |
| Genre-specific MCP tools (e.g., `create_house_track`) | Combinatorial explosion: 12 genres x N operations = hundreds of tools | Generic tools + blueprint context is the right abstraction |
| MIDI pattern generation from blueprints | Blueprint scope is reference/guidance, not generative | Blueprints describe conventions; theory engine + Claude generate actual MIDI |
| Audio analysis for genre classification | Out of scope (MCP is control, not audio pipeline) | Blueprint data is prescriptive, not analytical |

## Feature Dependencies

```
list_genre_blueprints ─── (no deps, standalone)

get_genre_blueprint ────> Blueprint schema (must be defined first)
                    ────> At least 1 genre data file
                    ────> catalog.py (registry + lookup)

get_genre_palette ──────> get_genre_blueprint (reads blueprint data)
                  ──────> theory.build_chord (resolves chord types)
                  ──────> theory.get_scale_pitches (resolves scales)
                  ──────> theory.generate_progression (resolves progressions)

Section filtering ──────> get_genre_blueprint (adds parameter)

Subgenre merging ───────> Blueprint schema (subgenres key in data)
                 ───────> catalog.py (merge logic)
```

## MVP Recommendation

### Build first (Phase 1-2):
1. Blueprint schema + catalog infrastructure
2. `list_genre_blueprints` and `get_genre_blueprint` tools with section filtering
3. 4 core genres: house, techno, hip-hop/trap, ambient (covers maximum stylistic range)
4. Subgenre support with merge logic

### Build second (Phase 3-4):
5. Remaining 8 genres
6. `get_genre_palette` bridge tool
7. Ableton-specific tips section

### Defer:
- Auto-genre detection (complex, fragile, low value vs. "just ask the user")
- Blueprint editing tools (out of scope)

## Genre Coverage Plan

| Genre | Priority | Subgenres | Rationale |
|-------|----------|-----------|-----------|
| House | P0 | deep, tech, progressive, acid | Most popular electronic genre globally |
| Techno | P0 | minimal, industrial, melodic, Detroit | Second most popular; very distinct from house |
| Hip-hop/Trap | P0 | boom bap, trap, lo-fi | Dominant in mainstream; different production paradigm |
| Ambient | P0 | dark ambient, drone, cinematic | Covers the "non-beat" territory |
| Drum & Bass | P1 | liquid, neurofunk, jungle | Major genre with unique rhythm (breakbeats) |
| Dubstep | P1 | brostep, riddim, melodic | Distinct sound design focus |
| Trance | P1 | progressive, uplifting, psytrance | Large global following |
| Neo-soul/R&B | P1 | neo-soul, contemporary R&B | Leverages existing theory engine jazz/R&B progressions |
| Synthwave | P2 | retrowave, darksynth, outrun | Growing niche; distinct aesthetic |
| Lo-fi | P2 | lo-fi hip-hop, chillhop | Very popular for casual production |
| Future Bass | P2 | future bass, kawaii future | Bridges EDM and pop |
| Disco/Funk | P2 | nu-disco, funk, boogie | Classic foundation genre |

## Sources

- Existing codebase: `PROGRESSION_CATALOG` genre coverage (pop, rock, jazz, blues, rnb, classical, edm)
- Existing codebase: `RHYTHM_CATALOG` style coverage (basic, jazz, pop)
- Electronic music production domain knowledge

---
*Feature research for: v1.2 Genre/Style Blueprints*
*Researched: 2026-03-25*
