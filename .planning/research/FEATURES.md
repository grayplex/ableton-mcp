# Feature Landscape: v1.3 Arrangement Intelligence

**Domain:** AI-assisted arrangement planning and session scaffolding for Ableton Live MCP server
**Researched:** 2026-03-27
**Confidence:** HIGH (existing codebase well understood, Ableton API verified, domain patterns established)

## Table Stakes

Features users expect when they hear "arrangement intelligence." Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Per-section element lists in arrangement templates | Users need to know WHAT goes in each section, not just the name/length | Medium | Extend existing `arrangement.sections` dicts with `roles` list per section |
| Energy level per section | Energy curve is the fundamental concept of arrangement -- determines intensity, mixing, and listener journey | Low | Integer 1-10 per section dict |
| Automation cues per section | Filter sweeps, risers, and impacts are what differentiate sections sonically | Medium | Descriptive `transition_in` string per section |
| Production plan from genre + vibe | "Give me a plan for a dark techno track" is the entry-point use case | Medium | Combines genre blueprint arrangement data with user intent |
| Locator scaffolding in Ableton | Arrangement plan must be represented in the DAW to be useful | Medium | Create named cue points at section boundaries |
| Named track creation from plan | DAW should be pre-configured with the right tracks for the genre | Low | Orchestration of existing `create_midi_track`/`create_audio_track` + `rename_track` |
| Section execution checklist | "What do I still need to do in this section?" prevents Claude from dropping elements under context pressure | Medium | Per-section element list derived from `roles` |
| Single-section mode | Users often want to work on just one section, not plan a whole track | Low | Plan builder returns one section's data on demand |

## Differentiators

Features that set this apart from static arrangement guides. Not expected, but high-value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Transition descriptors between sections | Tells Claude HOW to connect sections (e.g., "riser into drop," "filter sweep out of breakdown") | Medium | `transition_in` field on each section dict |
| Per-section harmony guidance | Links arrangement to existing harmony engine -- "breakdown uses iv chord, chorus modulates up" | Medium | Plan builder maps `harmony.common_progressions` to sections at generation time |
| Subgenre arrangement overrides | Deep house has longer intros than tech house; progressive house has 32-bar breakdowns | Low | Already partially implemented -- some subgenres override `arrangement.sections` |
| Context-aware plan modification | "Make the breakdown shorter" or "add a bridge" adjusts the plan dynamically | Medium | Plan builder accepts override parameters |
| Atomic named-locator creation | Single Remote Script command to create a locator at a specific position with a name -- avoids multi-step workflow | Medium | New command, not just orchestration of existing tools |

## Anti-Features

Features to explicitly NOT build. Tempting but wrong for this milestone.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Auto-composition of all sections | This is a planning/scaffolding milestone, not a composition engine. Claude composes using existing MIDI/theory tools. | Provide checklists and templates that GUIDE Claude through composition |
| Arrangement analysis of existing tracks | Requires stem separation, beat detection, structural segmentation -- different domain entirely | Defer to future milestone. v1.3 creates arrangements, does not analyze them |
| Per-bar automation curves baked into templates | Existing `write_automation_envelope` tool handles automation. Pre-baking curves is over-specification that breaks when users have different plugins. | Keep automation cues as descriptive strings ("filter sweep 0-100% over 8 bars") that Claude interprets |
| Visual arrangement diagrams / ASCII art | Token-expensive, fragile, not actionable in MCP context | Use structured data (dict/JSON) that tools consume directly |
| Arrangement region moving in Ableton | Ableton LOM has no API for moving arrangement regions -- clips must be individually repositioned | Build scaffolding at plan time; rearranging means re-scaffolding |
| Vibe preset library | Mapping "dark and brooding" to energy curves is nice but Claude can interpret natural language vibes without a lookup table | Let Claude use the energy levels as guidance, interpret vibe descriptions contextually |
| Genre-specific arrangement tools | `create_house_arrangement()`, `create_techno_arrangement()` -- combinatorial explosion | One generic `scaffold_arrangement(plan)` tool works for all genres |

## Arrangement Template Data Schema

### Current State (v1.2)

Each genre blueprint's `arrangement.sections` is a list of dicts with two fields:

```python
{"name": "intro", "bars": 16}
```

The schema validator (`schema.py` line 190-197) requires `name` (str) and `bars` (int), but silently accepts additional keys. This means the extension is **backward-compatible** -- no existing data breaks.

### Proposed Extension (v1.3)

Add three new optional fields per section dict:

```python
{
    "name": "buildup",
    "bars": 8,
    "energy": 7,                    # 1-10, energy level at this section
    "roles": ["kick", "hi-hats", "bass", "riser", "fx"],
    "transition_in": "riser + filter sweep from breakdown"
}
```

### Field Rationale

| Field | Type | Required | Why |
|-------|------|----------|-----|
| `name` | `str` | Yes (existing) | Section identifier, used as locator name in Ableton |
| `bars` | `int` | Yes (existing) | Duration, used to calculate beat positions for locators |
| `energy` | `int` (1-10) | Yes (new) | Quantified energy enables curve reasoning and mixing decisions. Integer is unambiguous and sortable. |
| `roles` | `list[str]` | Yes (new) | References `instrumentation.roles`. This IS the checklist -- tells Claude exactly which elements belong in this section. |
| `transition_in` | `str` | No (new) | Descriptive string for section entry approach. Claude interprets this using existing automation tools. First section typically has no transition. |

### Why NOT More Fields

- **`chords`/`progression`**: Arrangement templates should reference the genre's harmony section, not duplicate it. Plan builder maps progressions to sections at generation time.
- **`automation_values`**: Too specific. "Filter sweep 0-100%" is better than `{"param": "Auto Filter Frequency", "start": 20, "end": 20000}` because the latter breaks with different filter plugins.
- **`bars_alt`**: Variable bar counts per vibe belong in plan builder logic, not hardcoded in every blueprint.

## Production Plan Schema

The plan builder generates a concrete plan from a genre template + user parameters. This is a runtime output, not stored in blueprints.

```python
{
    "genre": "house",
    "subgenre": "deep_house",
    "key": "Dm",
    "bpm": 122,
    "vibe": "warm late-night",
    "total_bars": 128,
    "sections": [
        {
            "name": "intro",
            "start_bar": 1,
            "bars": 16,
            "start_beat": 0.0,       # beat position for Ableton API (0-indexed, in beats)
            "energy": 3,
            "roles": ["kick", "hi-hats", "pad"],
            "transition_in": "fade in from silence",
            "checklist": [
                {"element": "kick", "status": "pending"},
                {"element": "hi-hats", "status": "pending"},
                {"element": "pad", "status": "pending"},
            ]
        },
        # ... more sections
    ],
    "tracks": [
        {"name": "Kick", "type": "midi", "role": "kick"},
        {"name": "Bass", "type": "midi", "role": "bass"},
        {"name": "Hi-Hats", "type": "midi", "role": "hi-hats"},
        {"name": "Pad", "type": "midi", "role": "pad"},
        {"name": "FX", "type": "audio", "role": "fx"},
    ]
}
```

### Beat Position Calculation

`start_beat = sum(previous_sections_bars) * beats_per_bar`

For 4/4 time: `beats_per_bar = 4`, so a section starting at bar 17 has `start_beat = 16 * 4 = 64.0`.

## Session Scaffolding (Ableton Representation)

The plan becomes real in Ableton through two mechanisms:

### 1. Locators (Cue Points)

One locator per section boundary, named with the section name (e.g., "intro", "buildup", "drop").

**API constraint (CRITICAL, verified):** `CuePoint.name` is writable but `CuePoint.time` is READ-ONLY. `Song.set_or_delete_cue()` creates a cue at the CURRENT playback position (`Song.current_song_time`). To create locators at specific positions:

1. Set `Song.current_song_time` to the target beat position
2. Call `Song.set_or_delete_cue()` to create the locator
3. Set the `name` property on the new cue point

**Implication:** Need a new Remote Script command `create_named_locator(time, name)` that performs steps 1-3 atomically. This avoids race conditions and reduces MCP round-trips from 3+ to 1.

### 2. Named Tracks

One track per unique instrument role across all sections. Existing tools cover this:
- `create_midi_track(index)` or `create_audio_track(index)`
- `rename_track(track_index, name)`

### 3. Empty Arrangement Clips (deferred)

Pre-creating empty MIDI clips at each section position on each track would give visual guidance. However, this adds complexity for marginal benefit since locators already mark sections visually. Defer to post-v1.3 or make optional.

## Typical Genre Arrangement Patterns

Research confirms these cross-genre patterns for populating the 12 existing blueprints:

### Drop-based genres (House, Techno, DnB, Dubstep, Future Bass, Trance)

| Section | Typical Bars | Energy | Active Elements | Typical Transition |
|---------|-------------|--------|----------------|-------------------|
| Intro | 8-32 | 2-4 | Stripped drums, atmosphere, maybe bass | Fade in or DJ-mixable beat |
| Buildup | 8-16 | 5-8 | Riser, snare roll, filter sweep opening | Increasing density + pitch |
| Drop | 16-32 | 9-10 | Full drums, bass, lead/hook, all elements | Impact hit, brief silence |
| Breakdown | 8-32 | 3-5 | Drums stripped, pads, atmosphere, melody | Gradual element removal |
| Buildup 2 | 8-16 | 6-9 | Same as buildup, often more intense | More layers than first |
| Drop 2 | 16-32 | 9-10 | Full elements + variation from drop 1 | Second impact |
| Outro | 8-32 | 2-3 | Stripped drums, elements removed | Mirror of intro for DJ mixing |

### Song-form genres (Hip-Hop, Neo-Soul, Synthwave, Disco/Funk)

| Section | Typical Bars | Energy | Active Elements | Typical Transition |
|---------|-------------|--------|----------------|-------------------|
| Intro | 4-8 | 2-3 | Melodic hook preview or drum intro | Sets tone |
| Verse | 16 | 5-6 | Drums, bass, chords, space for vocals | Develops from intro |
| Pre-chorus | 8 | 6-7 | Rising energy, new harmonic movement | Tension before chorus |
| Chorus | 8-16 | 8-9 | Full instrumentation, hook | Release of tension |
| Bridge | 8 | 4-6 | Different harmony, texture change | Contrast |
| Outro | 4-8 | 2-3 | Fading elements or hard stop | Resolution |

### Non-standard form genres (Ambient, Lo-fi)

| Section | Typical Bars | Energy | Active Elements | Typical Transition |
|---------|-------------|--------|----------------|-------------------|
| Intro | 4-16 | 1-2 | Texture, atmosphere | Gradual emergence |
| Movement/Loop | 16-32 | 3-6 | Core loop with slow evolution | Subtle layering |
| Transition | 8-16 | 2-4 | Textural shift, new element | Crossfade or filter |
| Outro | 4-16 | 1-2 | Dissolving elements | Fade or decay |

## Feature Dependencies

```
Genre Blueprint Extensions (energy, roles, transition_in)
    |
    v
Schema Validation Update (optional fields in schema.py)
    |
    v
Production Plan Builder (genre + vibe -> concrete plan)
    |
    +---> Session Scaffolding Tool
    |         |
    |         +---> Named Locator Command (new Remote Script)
    |         +---> Track Creation (existing tools, orchestration)
    |
    +---> Section Execution Checklist Tool
              |
              +---> Single-Section Mode (subset of plan builder)
```

## MVP Recommendation

### Must ship (table stakes):

1. **Extended arrangement sections in blueprints** -- add `energy`, `roles`, `transition_in` to all 12 genre blueprints + subgenres with arrangement overrides
2. **Schema validation update** -- validate new optional fields in `schema.py`
3. **Production plan builder tool** -- `generate_production_plan(genre, key, bpm, subgenre?, vibe?)` returning full plan dict
4. **Named locator Remote Script command** -- `create_named_locator(time, name)` creating a cue point at a specific position with a name in one atomic operation
5. **Session scaffolding tool** -- `scaffold_arrangement(plan)` creating locators + tracks in Ableton from a plan
6. **Section checklist tool** -- `get_section_checklist(plan, section_name)` returning pending elements for a section

### Defer to post-v1.3:

- **Vibe-to-energy presets**: Claude interprets vibes contextually without a lookup table
- **Per-section harmony mapping**: Plan builder can reference genre harmony without formal chord-to-section mapping
- **Empty arrangement clip pre-creation**: Locators provide sufficient visual guidance
- **Arrangement analysis**: Different domain, different milestone

## Complexity Assessment

| Feature | Complexity | Rationale |
|---------|------------|-----------|
| Blueprint extensions (12 genres + subgenres) | Medium | Data authoring across 12 files. Need to determine `roles` and `energy` for every section in every genre/subgenre. Tedious but straightforward. ~20 arrangement sections to update. |
| Schema validation update | Low | Add optional field checks for `energy` (int, 1-10), `roles` (list[str]), `transition_in` (str) in `schema.py`. |
| Production plan builder | Medium | Pure computation -- combine blueprint data with user params, calculate beat positions, generate checklists. No Ableton API calls. |
| Named locator command (Remote Script) | Medium | New handler in `transport.py`: set `current_song_time`, call `set_or_delete_cue()`, set `name` on new cue. Must handle atomicity. Corresponding MCP tool needed. |
| Session scaffolding tool | Medium | Orchestrates locator creation + track creation. Depends on named locator command. Must handle idempotency (don't duplicate tracks/locators on re-run). |
| Section checklist tool | Low | Pure data transformation from plan dict. No Ableton API calls. |
| Tests | Medium | Blueprint validation tests for new fields, plan builder unit tests, locator integration tests. |

## Sources

- [Cycling '74 LOM CuePoint Reference](https://docs.cycling74.com/apiref/lom/cuepoint/) -- CuePoint.name is writable, CuePoint.time is read-only (HIGH confidence, verified)
- [Cycling '74 LOM Reference](https://docs.cycling74.com/apiref/lom/) -- Song.set_or_delete_cue() toggles at current position (HIGH confidence)
- [EDM Tips - EDM Song Structure](https://edmtips.com/edm-song-structure/) -- Section energy/element patterns (MEDIUM confidence)
- [AudioServices - Arrangements in Electronic Music](https://audioservices.studio/blog/understanding-arrangements-in-electronic-music-production) -- Genre-specific arrangement patterns (MEDIUM confidence)
- [Cymatics - EDM Song Structure](https://cymatics.fm/blogs/production/edm-song-structure) -- Standard section definitions (MEDIUM confidence)
- Existing codebase: 12 genre blueprints in `MCP_Server/genres/` with arrangement sections (HIGH confidence, verified in code)
- Existing codebase: `schema.py` validates only `name`+`bars`, extra keys silently accepted (HIGH confidence, verified at lines 190-197)
- Existing codebase: `set_or_delete_cue` and `get_cue_points` tools exist in `tools/transport.py` (HIGH confidence, verified)
- Existing codebase: `create_arrangement_midi_clip`, `create_arrangement_audio_clip`, `get_arrangement_clips`, `duplicate_clip_to_arrangement` in `tools/arrangement.py` (HIGH confidence, verified)

---
*Feature research for: v1.3 Arrangement Intelligence*
*Researched: 2026-03-27*
