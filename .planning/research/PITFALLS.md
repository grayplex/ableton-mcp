# Domain Pitfalls: v1.3 Arrangement Intelligence

**Domain:** Arrangement templates, production plan generation, and session scaffolding for an existing Ableton MCP server
**Researched:** 2026-03-27
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Cue Point Creation Requires Sequential Seek-Then-Toggle

**What goes wrong:**
The Ableton LOM `Song.set_or_delete_cue()` can only create a cue point at the *current playback position* (`Song.current_song_time`). There is no `create_cue_at(time, name)` method. To scaffold an arrangement with 7 locators, the Remote Script must: (1) set `current_song_time` to the target beat, (2) call `set_or_delete_cue()`, (3) set the name on the resulting `CuePoint` object. This sequential three-step process for each locator is fragile -- if any step fails mid-sequence, the session is left in an inconsistent state with some locators placed and others missing.

**Why it happens:**
The LOM API was designed for interactive use (user clicks "Set Cue" while playback is at a position), not for batch programmatic creation. Developers assume a simple `create_cue(time, name)` API exists and discover the constraint late.

**How to avoid:**
Build a dedicated `scaffold_arrangement` Remote Script command that atomically creates all locators in a single handler call. Inside the handler, iterate through section positions, seeking and toggling for each. If any step fails, clean up previously created cue points. Return the full list of created locators so the MCP tool can verify completeness. Do NOT expose the seek-toggle-name as three separate MCP tool calls that Claude must chain -- that wastes tool calls and risks partial failures.

**Warning signs:**
- MCP tool design that requires Claude to call `set_playback_position` + `set_or_delete_cue` + "rename cue" in sequence per locator
- Any scaffolding workflow requiring more than 2-3 tool calls total
- Tests that pass individually but fail when run in sequence (position state leaking)

**Phase to address:**
Session scaffolding phase (locator creation). Must be a single atomic Remote Script command.

---

### Pitfall 2: CuePoint.name Writability Assumptions

**What goes wrong:**
In Ableton Live versions before 12, `CuePoint.name` was read-only via the LOM. Live 12 made it writable. Developers either (a) assume it is writable without checking their target version, leading to silent failures on older installs, or (b) assume it is read-only based on old documentation and skip naming entirely, making locators useless as plan markers.

**Why it happens:**
The Cycling '74 LOM documentation was historically incomplete about `CuePoint` properties. The change in Live 12 was not prominently announced. Forum threads from 2022 say "read-only" while 2025 threads confirm "writable in Live 12."

**How to avoid:**
This project targets Ableton Live 12 exclusively (Python 3.11 constraint confirms this). Treat `CuePoint.name` as writable. Add a defensive check in the Remote Script: after setting the name, read it back and verify. If the name did not stick, log a warning and return a degraded result rather than crashing. Include the Live version constraint in the project documentation.

**Warning signs:**
- Locators appear in Ableton but all have default names like "1", "2", "3" instead of "Intro", "Drop", etc.
- Tests cannot verify locator names because the test mock does not simulate the writable property

**Phase to address:**
Session scaffolding phase. Verify name writability in the first integration test against a live Ableton instance.

---

### Pitfall 3: Context Collapse at Tool Call 40+

**What goes wrong:**
Claude loses track of the production plan during long workflows. By tool call 30-40, it forgets which sections have been completed, which tracks have which instruments, and what the harmonic plan was. It starts duplicating work, skipping sections, or making inconsistent harmonic choices.

**Why it happens:**
The MCP protocol is stateless per tool call. Claude's context window fills with 40+ tool call results (track listings, clip data, device parameters). The production plan -- if it was only in the initial conversation -- gets pushed out of the effective attention window. No external persistence mechanism reminds Claude of progress.

**How to avoid:**
The core insight of v1.3 is correct: **the session IS the plan.** Locators with section names and tracks with role-based names serve as persistent external memory readable via existing tools (`get_cue_points`, `get_all_tracks`, `get_arrangement_clips`). But the implementation must ensure:

1. **Section checklists** are embedded in a readable format (not just locator names, but a tool that returns "Section X: kick done, bass pending, pad pending").
2. **A progress-check tool** that Claude can call to re-orient: scans locators, checks which sections have clips, returns a status summary. This is cheap (one tool call) vs. Claude trying to reconstruct state from raw clip listings.
3. **Do NOT rely on Claude remembering** the plan from earlier conversation. Every execution step should start with "read the plan from the session."

**Warning signs:**
- Claude asks "what section are we working on?" mid-workflow
- Duplicate clips appearing in the same section
- Claude re-creates tracks that already exist
- The production plan is only stored as a Python dict in tool output, never written to the Ableton session

**Phase to address:**
Must be addressed in architecture design (first phase). The progress-check tool should ship alongside scaffolding, not as a later addition.

---

### Pitfall 4: Blueprint Schema Changes Breaking Existing Tools and Tests

**What goes wrong:**
v1.3 needs richer arrangement data in blueprints (energy curves, per-section instrument elements, automation cues). Adding new required fields to `ArrangementEntry` in `schema.py` breaks all 12 existing genre files and their 148 passing tests simultaneously. The "extend schema" change cascades into a multi-file refactor.

**Why it happens:**
The v1.2 `ArrangementEntry` TypedDict has only `name: str` and `bars: int`. Adding `energy`, `elements`, or `automation_cues` as required fields forces every genre file to be updated atomically -- and every test that validates blueprints.

**How to avoid:**
Make ALL new arrangement fields **optional** in the schema. Use `typing.NotRequired` (Python 3.11 supports it) or validate them only when present. The existing `{"name": "intro", "bars": 16}` entries remain valid. New extended entries like `{"name": "intro", "bars": 16, "energy": "low", "elements": ["pad", "hi-hats"]}` are validated when present but not required.

Concretely:
- Add a new `ExtendedArrangementEntry` TypedDict that extends `ArrangementEntry` with optional fields
- Update `validate_blueprint()` to validate new fields only when present
- Migrate genres incrementally (house first as the reference, then others in a batch)
- Keep existing tests passing throughout

**Warning signs:**
- PR that touches all 12 genre files plus schema.py plus catalog.py in a single commit
- Test suite goes from 148 passing to 148 failing during development
- Schema validation errors on `import` because a genre file lacks the new fields

**Phase to address:**
Schema extension must be the FIRST phase. Get the schema right before writing any arrangement template logic. Test that all existing genres still pass validation before adding new fields.

---

### Pitfall 5: Over-Engineering the Plan Representation

**What goes wrong:**
The production plan becomes a complex nested data structure (sections with sub-sections, dependency graphs, state machines for execution tracking, energy curves as polynomial functions). The plan builder tool returns 2000+ tokens. Claude spends its context budget parsing the plan rather than producing music.

**Why it happens:**
Arrangement intelligence is intellectually interesting. It is tempting to model every aspect: energy curves, transition types, instrument layering rules, dynamic arrangement decisions. The developer builds a production planning framework rather than a production tool.

**How to avoid:**
The plan is a **flat list of sections** with per-section data. Nothing more.

```python
# GOOD: Flat, terse, one tool call to read
{"sections": [
    {"name": "intro", "start_beat": 0, "bars": 16, "energy": "low",
     "elements": ["pad", "hi-hats"]},
    {"name": "drop", "start_beat": 64, "bars": 32, "energy": "high",
     "elements": ["kick", "bass", "lead", "hi-hats", "clap"]},
]}

# BAD: Nested, verbose, requires parsing
{"arrangement": {
    "phases": [
        {"phase": "exposition", "sections": [
            {"name": "intro", "start": {"bar": 1, "beat": 1},
             "end": {"bar": 16, "beat": 4},
             "energy_curve": {"type": "linear", "start": 0.1, "end": 0.3},
             "transitions": {"in": "fade", "out": "filter_sweep"},
             "element_timeline": [
                 {"bar": 1, "add": ["pad"]},
                 {"bar": 5, "add": ["hi-hats"]},
             ]}
        ]}
    ]
}}
```

The plan builder should output something Claude can glance at and immediately know: where it is, what to put there, and what energy level to target. If the plan takes more than 400 tokens, it is too complex.

**Warning signs:**
- Plan builder returns more than 500 tokens for a standard 7-section arrangement
- TypedDicts nested more than 2 levels deep
- Claude needs a "parse the plan" step before it can start working
- Energy curves require mathematical computation

**Phase to address:**
Plan builder phase. Define the output format BEFORE writing any code. Test it by feeding the output to Claude in a dry run conversation and verifying Claude can use it without confusion.

---

### Pitfall 6: Beat Position Arithmetic with Non-4/4 Time Signatures

**What goes wrong:**
The scaffold tool calculates section start positions as `beat = sum(prior_bars) * 4` (4 beats per bar). This is correct for 4/4 but wrong for 3/4, 6/8, 5/4, or 7/8 time signatures. Sections overlap or have gaps. Clips are placed at wrong positions.

**Why it happens:**
Electronic music is overwhelmingly 4/4, so the developer hardcodes `beats_per_bar = 4`. The blueprint schema stores `time_signature: "4/4"` as a string, but the bar-to-beat calculation ignores it. When a user tries ambient (sometimes 3/4) or experimental genres, everything breaks silently.

**How to avoid:**
Parse `time_signature` from the blueprint or the Ableton session (`Song.signature_numerator`, `Song.signature_denominator`). Calculate `beats_per_bar = numerator * (4 / denominator)`. Use this in ALL beat position arithmetic. The existing Remote Script already reads time signature (see `transport.py` lines 79-99), so the data is available.

Important edge cases:
- `6/8` = 6 eighth-notes per bar = 3 quarter-note beats per bar (NOT 6)
- `3/4` = 3 beats per bar
- `5/4` = 5 beats per bar
- Clips in Ableton use quarter-note beats as the unit regardless of time signature
- Ableton's `Song.signature_numerator` / `Song.signature_denominator` are the TIME SIGNATURE values, not beats-per-bar directly

The safest formula: `beats_per_bar = numerator * (4.0 / denominator)`, which gives: 4/4=4, 3/4=3, 6/8=3, 7/8=3.5, 5/4=5.

**Warning signs:**
- Any literal `* 4` or `* 4.0` in beat position calculations
- Tests only use 4/4 time signature
- Locators not aligning with bar lines in Ableton's arrangement view

**Phase to address:**
Session scaffolding phase. Time signature handling must be in the beat calculation from day one, not retrofitted.

---

## Moderate Pitfalls

### Pitfall 7: Scaffold Creates Tracks But Forgets to Load Instruments

**What goes wrong:**
The scaffolding tool creates named MIDI tracks ("Kick", "Bass", "Lead") but does not load instruments onto them. As documented in project memory: "MIDI tracks without an instrument/device have NO volume fader." The user sees tracks with no volume control, no sound output, and must manually load instruments. The scaffolding feels incomplete and broken.

**Why it happens:**
Track creation and instrument loading are separate LOM operations. The developer scaffolds the track structure and considers it "done," deferring instrument loading to the execution phase. But the execution phase is 20+ tool calls away, and by then Claude may have lost track of which tracks need instruments.

**How to avoid:**
Two valid approaches:
1. **Scaffold tracks only, but document clearly** that these are placeholder tracks. The progress-check tool should flag "Track X: no instrument loaded" so Claude knows to load one before writing MIDI.
2. **Load default instruments during scaffolding** using the genre blueprint's instrumentation roles. Map roles to default Ableton instruments (e.g., "kick" -> Drum Rack, "bass" -> Analog, "pad" -> Wavetable). This is more complex but gives a better starting point.

Approach 1 is recommended for v1.3 MVP. Approach 2 is a differentiator for a later milestone.

**Warning signs:**
- User reports "no sound" from scaffolded tracks
- Volume automation fails because there is no volume parameter on instrumentless MIDI tracks

**Phase to address:**
Session scaffolding phase. At minimum, the progress-check tool must flag instrumentless tracks.

---

### Pitfall 8: Locator Position Drift When Sections Are Reordered

**What goes wrong:**
User asks Claude to "move the breakdown before the second drop." Claude recalculates beat positions and moves clips, but the locators (cue points) still point to the old positions. The session plan no longer matches the actual arrangement. The progress-check tool reports incorrect status.

**Why it happens:**
Locators in Ableton are fixed beat positions, not markers that "follow" sections. Moving clips does not move locators. The LOM provides no "move cue point" API -- you must delete and recreate.

**How to avoid:**
Build a `reshuffle_arrangement` or `rebuild_locators` command that can delete all existing locators and recreate them from a revised section plan. Accept that section reordering is a "destructive rebuild" of the locator scaffold, not an incremental edit. Make this a single atomic Remote Script command.

Alternatively, for v1.3 MVP: document that section reordering requires re-scaffolding and is a known limitation. Prevent scope creep.

**Warning signs:**
- Locator names no longer match the sections at those beat positions
- Progress-check tool reports wrong completion status after manual edits

**Phase to address:**
This is a v1.3+ concern. For v1.3 MVP, document the limitation. If reordering support is needed, it should be a separate phase with its own planning.

---

### Pitfall 9: Plan Builder Returns Genre Template Verbatim Without Customization

**What goes wrong:**
The plan builder tool takes a genre and returns the blueprint's arrangement sections unchanged. "Build me a house track" returns the exact same 7 sections every time. There is no customization based on user vibe, track length, or creative intent. The tool adds no value over `get_genre_blueprint(genre, sections=["arrangement"])`.

**Why it happens:**
The developer implements the plan builder as a thin wrapper around the existing blueprint arrangement data, planning to add customization "later." But without customization, the tool is redundant and Claude will not use it (or will use the existing blueprint tool instead).

**How to avoid:**
The plan builder must add value beyond raw blueprint data. Minimum viable customization:
1. **Vibe parameter** that adjusts section count and bar lengths (e.g., "chill" = longer intros/breakdowns, "banger" = shorter intro, longer drops)
2. **Duration target** that scales bar counts proportionally to hit a target track length
3. **Per-section element list** derived from genre instrumentation roles (which elements play in which sections) -- this is data the raw blueprint does NOT have

If none of these are feasible in v1.3, reconsider whether a separate plan builder tool is needed at all. Claude can read the blueprint and customize it in-conversation.

**Warning signs:**
- Plan builder output is identical to `blueprint["arrangement"]["sections"]`
- No parameters beyond `genre` and `key`
- Claude stops using the plan builder and calls `get_genre_blueprint` instead

**Phase to address:**
Plan builder phase. Define the value-add BEFORE implementation. If the only value is "writes locators to Ableton," merge plan building into the scaffold tool.

---

### Pitfall 10: Scaffold Tool Creates Clips That Conflict with Existing Session Content

**What goes wrong:**
User has existing tracks and clips in their Ableton session. They ask Claude to scaffold an arrangement. The scaffold tool creates new tracks that duplicate existing ones (two "Kick" tracks) or creates arrangement clips that overlap with existing clips. The session becomes a mess.

**Why it happens:**
The scaffold tool assumes a blank session. It does not check for existing tracks or clips before creating new ones.

**How to avoid:**
Before scaffolding, query existing session state:
1. Check existing track names -- if "Kick" exists, reuse it instead of creating a duplicate
2. Check existing arrangement clips on target tracks -- warn if the scaffold would overlap
3. Offer two modes: "scaffold from scratch" (blank session assumed) and "scaffold around existing" (respects existing content)

For v1.3 MVP, "scaffold from scratch" is acceptable with a clear warning that existing content may be affected. The tool should at minimum report what it created vs. what already existed.

**Warning signs:**
- Duplicate track names in the session after scaffolding
- Overlapping clips in arrangement view
- User reports "it messed up my existing work"

**Phase to address:**
Session scaffolding phase. At minimum, return a warning when existing content is detected.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode 4/4 time signature in beat math | Simpler arithmetic, covers 95% of use | Breaks for any non-4/4 genre | Never -- the fix is one line of math |
| Store plan only in tool output, not in session | No new Remote Script commands needed | Claude loses the plan at tool call 30+ | Never -- defeats the core v1.3 purpose |
| Skip progress-check tool, rely on Claude's memory | One fewer tool to build | Context collapse on long productions | Never -- this is the key differentiator |
| Make all new schema fields required | Simpler validation | Breaks all 12 genre files simultaneously | Never -- use optional fields |
| Copy-paste scaffold logic into each MCP tool | Quick per-tool implementation | Duplicate beat-math bugs, inconsistent behavior | Never -- extract to shared utility |
| Skip instrument presence check in progress tool | Simpler progress logic | "Complete" sections with no sound | MVP only -- add instrument check in v1.3.1 |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Plan builder + genre blueprints | Plan builder re-fetches and re-parses blueprint data instead of using the catalog API | Import `get_blueprint()` from `MCP_Server.genres.catalog` directly. Do not duplicate alias resolution. |
| Scaffold tool + existing arrangement tools | Scaffold creates clips using raw `create_arrangement_midi_clip` but does not name them, making progress tracking impossible | Use `create_arrangement_midi_clip` then immediately `set_clip_name` (or create a combined command). Clip names must match section names for progress tracking. |
| Progress-check + cue points | Progress tool counts clips between cue points by iterating ALL clips on ALL tracks per section. With 8 tracks x 7 sections = 56 clip slot checks per call. | Query `get_arrangement_clips` per track and bin clips by beat position ranges derived from cue points. Cache the cue point positions, do not re-query per track. |
| New arrangement schema + existing `get_genre_blueprint` tool | New optional fields appear in blueprint output, inflating token count for users who do not need arrangement details | The existing `sections=["arrangement"]` filter already works. Ensure new arrangement sub-fields are included only when the arrangement section is requested, not in every response. |
| Theory engine + plan builder | Plan builder calls `generate_progression()` to pre-resolve harmony for each section. This adds latency and unnecessary data to the plan. | The plan builder should reference scale/key names, not resolved MIDI. Claude resolves harmony per-section using existing theory tools when it actually writes MIDI. Separation of concerns. |
| Scaffold tool + track creation | Scaffold calls `create_midi_track` in a loop, but track indices shift after each creation (track at index 5 becomes index 6 after a new track is inserted at index 0) | Create tracks in reverse order (last track first), or create all tracks and then query `get_all_tracks` to get the actual indices before proceeding. Better: create tracks at index `-1` (append to end) to avoid index shifting. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Per-locator tool calls from Claude | 7 sections = 21+ tool calls just for scaffolding (seek + toggle + name x 7) | Single `scaffold_arrangement` command that creates all locators atomically | Immediately -- 21 tool calls is unacceptable for setup |
| Progress-check queries every track | Slow response (2-3 seconds) for sessions with 15+ tracks | Accept track indices as a parameter, or cache track list within the handler | At 15+ tracks, noticeable lag |
| Plan builder resolving all harmony upfront | Plan output bloats to 1000+ tokens with chord voicings for every section | Plan stores key + scale name only. Claude resolves per-section on demand. | At 7+ sections with 4+ chords each |
| Scaffold creating clips for every section on every track | 7 sections x 8 tracks = 56 `create_midi_clip` calls | Scaffold creates locators and tracks only. Clips are created per-section during execution. | Immediately -- 56 operations is too slow |

## "Looks Done But Isn't" Checklist

- [ ] **Scaffold tool:** Often missing locator NAME assignment -- locators exist but are all unnamed. Verify each cue point has a name matching its section.
- [ ] **Scaffold tool:** Often missing time signature awareness -- verify beat positions are correct for non-4/4 signatures by testing with 3/4.
- [ ] **Progress-check tool:** Often missing instrument presence check -- verify it flags MIDI tracks without instruments as "not ready."
- [ ] **Plan builder:** Often missing vibe/duration customization -- verify output varies with different parameters, not just genre.
- [ ] **Schema extension:** Often missing backward compatibility test -- verify all 12 existing genres still pass validation WITHOUT any changes to their files.
- [ ] **Blueprint arrangement data:** Often missing per-section element lists -- verify each section specifies which instruments play (this is the key new data v1.3 needs).
- [ ] **Atomic scaffold command:** Often missing rollback on partial failure -- verify that if locator 4 of 7 fails, the first 3 are cleaned up.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Schema change breaks all genres | MEDIUM | Revert schema.py, make fields optional, re-run tests |
| Locators created without names | LOW | Delete all cue points, re-scaffold. Single command if atomic scaffold exists. |
| Context collapse mid-production | LOW | Call progress-check tool to re-orient. This is recovery-by-design. |
| Wrong beat positions (time sig bug) | HIGH | Must delete clips and locators, fix arithmetic, re-scaffold, re-create all clips. No shortcut. |
| Overlapping clips from blind scaffold | MEDIUM | Undo (Ctrl+Z) if caught immediately. Otherwise, manually delete duplicates. |
| Plan builder too verbose | LOW | Simplify the output format. No session state to clean up. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Cue point seek-toggle fragility | Session scaffolding | Integration test: create 7 locators, verify all named and positioned correctly |
| CuePoint.name writability | Session scaffolding | Test against live Ableton: set name, read back, assert match |
| Context collapse | Architecture design (first phase) | Dry-run: 40+ tool call conversation produces a complete track without Claude losing the plan |
| Schema breaking existing genres | Schema extension (first phase) | All 148 existing genre tests pass with zero genre file changes |
| Over-engineered plan | Plan builder design | Plan output under 400 tokens for a 7-section house track |
| Time signature arithmetic | Session scaffolding | Test with 3/4 and 6/8 time signatures, verify beat positions |
| Missing instruments on scaffolded tracks | Session scaffolding / progress tool | Progress-check flags instrumentless tracks |
| Locator position drift | Document as limitation in v1.3 | N/A for MVP |
| Redundant plan builder | Plan builder design | Plan output differs from raw blueprint arrangement data |
| Scaffold conflicts with existing content | Session scaffolding | Test scaffold on non-empty session, verify no duplicates |

## Sources

- [Cycling '74 LOM Documentation](https://docs.cycling74.com/max8/vignettes/live_object_model) -- CuePoint properties, Song.set_or_delete_cue behavior
- [Cycling '74 Forum: Setting Locator Names](https://cycling74.com/forums/setting-locator-names) -- CuePoint.name read-only in pre-Live 12, writable in Live 12
- Existing codebase: `AbletonMCP_Remote_Script/handlers/transport.py` -- current cue point implementation (toggle at current position only)
- Existing codebase: `MCP_Server/genres/schema.py` -- current ArrangementEntry schema (name + bars only)
- Existing codebase: `MCP_Server/genres/house.py` -- current blueprint arrangement data structure
- Project memory: MIDI tracks without instruments have no volume fader
- Existing codebase: `AbletonMCP_Remote_Script/handlers/arrangement.py` -- current arrangement clip CRUD (4 commands)

---
*Pitfalls research for: v1.3 Arrangement Intelligence*
*Researched: 2026-03-27*
