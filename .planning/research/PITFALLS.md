# Pitfalls Research

**Domain:** Sound selection/recommendation layer for Ableton MCP (v1.5)
**Researched:** 2026-03-30
**Confidence:** HIGH (based on deep analysis of existing codebase, browser integration, and established patterns)

## Critical Pitfalls

### Pitfall 1: Browser Path Mismatch Between Authored Profiles and Live Browser

**What goes wrong:**
Instrument profiles author category paths like `instruments/Wavetable/Pads/Warm Pad` but the actual Ableton browser tree uses different folder names, nesting, or casing. The `_resolve_browser_path` method does case-insensitive matching on child names, but if a folder literally does not exist at that path level, the load silently returns `None` and the recommendation fails. Ableton Live 12 updates can rename or restructure browser folders between versions without warning.

**Why it happens:**
The author writes category paths from memory or from one Ableton installation. Ableton's browser tree varies by: (a) Live version/update, (b) installed Packs (Core Library vs Suite), (c) "sounds" vs "instruments" category -- these are two DIFFERENT browser roots. `instruments/Wavetable` lists the raw instrument, while `sounds/` organizes by *sonic category* (Pads, Bass, Keys, etc.) with presets from multiple instruments mixed together. Confusing these two hierarchies is easy.

**How to avoid:**
1. Clearly distinguish between "instrument path" (loads the bare instrument) and "preset category path" (loads a specific preset from sounds/ or from the instrument's own preset subfolder).
2. For v1.5's scope (descriptor -> instrument + category), use `instruments/{InstrumentName}` as the load path (loads default preset) since that is stable. Store the *preset category hint* separately as a human-readable suggestion for Claude, not as a loadable browser path.
3. Validate all authored paths against a live Ableton session during development using `get_browser_items_at_path`.
4. Document which paths are "load paths" (used with `load_instrument_or_effect`) vs "browsing hints" (used to guide Claude's manual browsing).

**Warning signs:**
- `_resolve_browser_path` returning `None` for paths that "should work"
- Tests passing with mocked browser but failing in live UAT
- Paths that work in Suite but not Standard (missing Packs)

**Phase to address:**
Phase 1 (Instrument Profile Data) -- establish the path schema and validate against live browser before authoring all 6 profiles.

---

### Pitfall 2: Descriptor Tag Taxonomy That Is Either Too Broad or Too Overlapping

**What goes wrong:**
Descriptors like "warm" match too many instruments (Wavetable pads, Analog pads, Drift everything). Descriptors like "FM metallic bell" match exactly one instrument but are too specific for users to discover. Overlapping descriptors ("lush pad" vs "warm pad" vs "thick pad") create inconsistent recommendations where the same intent returns different instruments depending on exact wording.

**Why it happens:**
Sound descriptors are inherently subjective and overlapping in music production. There is no standard taxonomy. Authors tend to either: (a) go broad ("pad", "bass", "lead") which gives zero differentiating signal between instruments, or (b) go granular with synthesis-specific terms ("wavetable morphing pad", "subtractive analog sweep") which only experts know to ask for.

**How to avoid:**
1. Use a two-level descriptor system: **role** (what it does: pad, bass, lead, pluck, kick, etc.) + **character** (how it sounds: warm, bright, aggressive, etc.). The combination is what drives instrument selection.
2. Each descriptor tag should resolve to a PRIMARY instrument recommendation (the best match) -- not a ranked list. If "warm pad" maps to both Analog and Drift, pick one and commit. The reasoning string explains why.
3. Keep the total descriptor vocabulary small (30-50 tags). Users can always combine role + character. Avoid synonyms -- if "thick" and "fat" mean the same thing, pick one.
4. Test the taxonomy by running every descriptor and checking that: (a) no two descriptors return identical results unless intentional, (b) every instrument appears as primary for at least 3 descriptors, (c) Drum Rack is only recommended for percussive descriptors.

**Warning signs:**
- Multiple descriptors returning identical instrument+category combinations
- One instrument dominating recommendations (e.g., Wavetable for everything)
- Drum Rack appearing for melodic descriptors
- Descriptors that Claude would never naturally use in conversation

**Phase to address:**
Phase 1 (Instrument Profile Data) -- the descriptor-to-instrument mapping is authored data, so taxonomy design must be right before profiles are written. Phase 2 (get_sound_recommendation tool) should include a test that exercises every descriptor.

---

### Pitfall 3: "sounds" vs "instruments" Browser Category Confusion

**What goes wrong:**
Ableton's browser has both `instruments` (raw instruments by device name) and `sounds` (presets organized by sonic category like Bass, Keys, Pad, Lead). The existing `_CATEGORY_MAP` and `_resolve_browser_path` treat these as separate root categories. If instrument profiles point to `sounds/Bass/Analog` expecting to find Analog bass presets, but the actual path is `sounds/Bass/` containing presets from ALL instruments mixed together (not subfoldered by instrument), the path resolution fails.

**Why it happens:**
The `sounds` category in Ableton's browser organizes by *what it sounds like* (Bass, Keys, Pad), not by *which instrument made it*. Presets within `sounds/Bass/` come from Wavetable, Analog, Operator, etc. all mixed together. This is the opposite of what an "instrument profile" would naturally want to express. The `instruments/Analog/` hierarchy, by contrast, has all Analog presets organized by the instrument's own preset categories.

**How to avoid:**
1. For instrument profiles, use the `instruments/{InstrumentName}` browser root exclusively. This gives instrument-specific preset subcategories.
2. The `sounds/` category is useful for *discovering what exists* but not for *loading by instrument*. Do not reference it in instrument profiles.
3. If a recommendation wants to suggest "browse bass presets for Analog," the authored path should be `instruments/Analog/Bass` (the instrument's own subfolder), NOT `sounds/Bass/`.
4. For Drum Rack, the relevant browser root is `drums/` not `instruments/` or `sounds/`.

**Warning signs:**
- Profile paths starting with `sounds/` instead of `instruments/`
- Drum Rack paths using `instruments/` instead of `drums/`
- Preset counts that don't match expectations (too many = wrong category, too few = wrong subfolder name)

**Phase to address:**
Phase 1 (Instrument Profile Data) -- path schema decision must happen before any profile is authored.

---

### Pitfall 4: Instrument Profile Data Coupled to Genre System

**What goes wrong:**
The profile data embeds genre-specific recommendations ("use Wavetable for house pads") which creates a coupling between the instrument knowledge layer and the genre blueprint layer. When a new genre is added, all instrument profiles need updating. When Claude asks for "a warm pad" with no genre context, the recommendation becomes ambiguous or defaults to one genre's preference.

**Why it happens:**
It is tempting to make instrument recommendations genre-aware because "the right instrument for a bass" genuinely differs between house (Analog sub) and dubstep (Operator growl). But the PROJECT.md explicitly states "descriptor-only, no genre dependency" for v1.5. Creeping genre coupling happens when authors add "best for: house, techno" fields to profiles.

**How to avoid:**
1. Instrument profiles describe the instrument's inherent sonic character, NOT its genre associations. "Analog excels at warm, resonant sounds with analog-modeled filter character" -- not "Analog is best for house."
2. Genre-to-instrument mapping is a FUTURE milestone concern (v1.6+). Keep it out of v1.5 entirely.
3. If a descriptor like "acid bass" inherently implies a genre context, that is fine -- the descriptor tag itself carries that context. The profile maps "acid bass" -> Operator (because 303-style acid = FM/PM synthesis). The reasoning says "Operator's feedback FM recreates acid-style resonance" not "because acid house uses Operator."
4. Do not add genre fields to the instrument profile schema.

**Warning signs:**
- Profile dicts containing "genres" or "best_for_genres" keys
- Recommendation logic importing from `MCP_Server.genres`
- Test cases that pass genre as a parameter to `get_sound_recommendation`

**Phase to address:**
Phase 1 (Instrument Profile Data) -- schema design. If the schema has no genre field, genre coupling cannot creep in.

---

### Pitfall 5: Returning Browser Paths That Require Additional Navigation Steps

**What goes wrong:**
`get_sound_recommendation` returns a category path like `instruments/Wavetable/Pads` but the user (Claude) needs to then call `get_browser_items_at_path` to see specific presets, pick one, and then call `load_instrument_or_effect` with the exact preset path. This multi-step workflow means the recommendation alone does not result in a loaded instrument -- it requires 2-3 more tool calls. Under context pressure (tool call #40+), Claude may skip these steps or pick randomly.

**Why it happens:**
The recommendation tool tries to be helpful by suggesting a specific preset category, but loading a specific preset requires knowing the exact preset name (which varies by Ableton installation and installed Packs). The tool cannot predict which presets exist on the user's system.

**How to avoid:**
1. `get_sound_recommendation` should return TWO things: (a) a **load path** that can be passed directly to `load_instrument_or_effect` to load the bare instrument (e.g., `instruments/Analog`), and (b) a **category hint** (e.g., "browse Pads subfolder for warm presets") as advisory text. This way Claude can always load *something* in one tool call and optionally browse for a better preset.
2. The load path should be validated to work with `load_instrument_or_effect(path=...)` -- meaning it loads the instrument's default preset.
3. Test the full round-trip: `get_sound_recommendation("warm pad")` -> extract load path -> `load_instrument_or_effect(track_index=0, path=load_path)` -> verify instrument loaded.

**Warning signs:**
- Recommendation output that cannot be used directly with any existing tool
- Claude needing 3+ tool calls to go from recommendation to loaded instrument
- Recommendation returning preset-specific paths that may not exist on all installations

**Phase to address:**
Phase 2 (get_sound_recommendation tool) -- the tool's output schema must include a directly-loadable path.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoding preset subfolder names | Fast to author | Breaks when Ableton updates folder names; differs between Suite/Standard | Never -- use instrument root paths for loading, subfolder names only as advisory hints |
| One flat list of descriptor tags | Simple lookup | No way to combine role+character; taxonomy explodes as new descriptors are added | Only in MVP if the total count stays under 50 |
| Putting all 6 profiles in one file | Quick to write | Hard to maintain; no auto-discovery pattern; merge conflicts | Never -- follow the established one-file-per-entity pattern (genres, mix recipes) |
| Skipping live UAT for browser paths | Saves manual testing time | Authored paths may be wrong; only discovered when user hits the bug | Never -- browser path validation is the single highest-risk area |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `load_instrument_or_effect` path param | Using `sounds/` root for instrument loading | Use `instruments/{Name}` for instruments, `drums/` for Drum Rack |
| `_resolve_browser_path` | Assuming exact path strings will work across Ableton versions | Validate paths against live browser during development; document which Ableton version was tested |
| `DEVICE_PATHS` dict in Remote Script | Adding instrument paths to `DEVICE_PATHS` (which is for audio_effects used by apply_recipe) | Instrument profiles live in MCP_Server, not Remote Script. Only add to `DEVICE_PATHS` if a Remote Script command needs them. |
| `get_browser_items_at_path` | Returning raw browser tree data as recommendation output | Return curated, human-readable recommendation text + one loadable path string |
| Existing genre blueprint `instrumentation.roles` | Trying to link instrument profiles to genre roles at this milestone | Roles describe *what* (kick, bass, pad); instrument profiles describe *how* (which device). The mapping is a future milestone concern. |
| pkgutil auto-discovery pattern | Not adding `__init__.py` to the new instruments package | Every discoverable package needs `__init__.py` with the package path for pkgutil |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading full browser tree to validate paths | Tool response takes 5-10 seconds; timeout on slow machines | Only validate paths during development/testing, not at runtime. Profile data is static. | Always -- browser tree traversal is expensive |
| Large instrument profile dicts | Token budget bloat when Claude reads all profiles | Keep profiles concise. Use the same token-budget discipline as genre blueprints (target under 700 tokens per profile). | When Claude's context window fills up after reading multiple profiles |
| Iterating all descriptors for fuzzy matching | Linear scan is fine for 50 tags; slow for 500 | Use exact dict lookup, not fuzzy search. Normalize input (lowercase, strip whitespace) and match against canonical tags. | At 200+ descriptors (unlikely for v1.5) |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Recommendation returns synthesis jargon ("use wavetable morphing with FM modulation") | Claude cannot translate this into actionable Ableton steps | Return plain descriptor reasoning: "Wavetable for warm pads because its filter and modulation create evolving textures" |
| Returning multiple equally-ranked options | Claude paralyzed by choice, picks randomly or asks user to decide | Return ONE primary recommendation with ONE reasoning sentence. If a second option is notably different, include it as an alternative. |
| Descriptor list too long for Claude to usefully browse | Claude guesses descriptors instead of consulting list_sound_descriptors | Group descriptors by role (bass descriptors, pad descriptors, lead descriptors, etc.) in list_sound_descriptors output |
| No fallback when descriptor does not match | Claude gets empty result, falls back to random instrument selection | Always return a recommendation. If no exact match, fall back to the closest role match with a note that it is approximate. |

## "Looks Done But Isn't" Checklist

- [ ] **Instrument profiles authored:** Often missing Drum Rack (it is a container, not a synth, and its browser path is `drums/` not `instruments/`) -- verify Drum Rack has its own profile with correct browser root
- [ ] **Browser paths validated:** Often tested with `get_browser_tree` (which shows folder structure) but never actually loaded via `load_instrument_or_effect(path=...)` -- verify round-trip loading for every instrument's load path
- [ ] **Descriptor coverage:** Often missing percussive descriptors (kick, snare, hi-hat) that should map to Drum Rack -- verify Drum Rack has descriptor coverage
- [ ] **Simpler profile:** Often treated as a sampler-only tool, but Simpler in Ableton has Classic/One-Shot/Slice modes and loads from `instruments/Simpler` -- verify the profile covers all three modes
- [ ] **list_sound_descriptors output:** Often returns a flat unstructured list -- verify it is grouped by role for readability
- [ ] **get_instrument_profile output:** Often missing the load path field -- verify the output includes a field Claude can pass directly to `load_instrument_or_effect`
- [ ] **Auto-discovery registration:** New instruments package has `__init__.py` and catalog follows pkgutil pattern -- verify `list_sound_descriptors` discovers all profiles without explicit registration

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Browser path mismatch | LOW | Fix the authored path string in the profile dict. No schema change needed. Run live UAT to find correct path. |
| Descriptor taxonomy too broad | MEDIUM | Redesign the two-level (role + character) taxonomy. Requires rewriting all descriptor mappings but no tool API changes. |
| sounds/ vs instruments/ confusion | LOW | Find-and-replace path roots in profile dicts. The `_resolve_browser_path` logic does not need changes. |
| Genre coupling crept in | MEDIUM | Remove genre fields from profile schema, strip genre logic from recommendation tool. May require rethinking some descriptors that were implicitly genre-dependent. |
| Recommendation not directly loadable | LOW | Add a `load_path` field to recommendation output. The path is just `instruments/{Name}` or `drums/Drum Rack`. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Browser path mismatch | Phase 1 (Instrument Profiles) | Live UAT: `load_instrument_or_effect(path=profile.load_path)` succeeds for all 6 instruments |
| Descriptor taxonomy overlap | Phase 1 (Instrument Profiles) | Automated test: every descriptor returns a unique instrument+category combo OR intentional duplicates are documented |
| sounds/ vs instruments/ confusion | Phase 1 (Instrument Profiles) | Code review: no profile path starts with `sounds/`; Drum Rack path starts with `drums/` |
| Genre coupling | Phase 1 (Instrument Profiles) | Code review: no import from `MCP_Server.genres` in instruments package; no "genre" key in profile schema |
| Recommendation not loadable | Phase 2 (Recommendation Tool) | Integration test: recommendation output `load_path` field passes to `load_instrument_or_effect` without modification |
| Descriptor not found / no fallback | Phase 2 (Recommendation Tool) | Test: calling `get_sound_recommendation("xyzzy_nonexistent")` returns a fallback recommendation, not an error |
| Auto-discovery failure | Phase 1 (Instrument Profiles) | Test: `catalog.list_instruments()` returns all 6 instruments without explicit registration |

## Sources

- Codebase analysis: `AbletonMCP_Remote_Script/handlers/browser.py` -- `_resolve_browser_path` implementation (case-insensitive child matching, `_CATEGORY_MAP`)
- Codebase analysis: `AbletonMCP_Remote_Script/handlers/devices.py` -- `DEVICE_PATHS` pattern (audio_effects only, used by apply_recipe)
- Codebase analysis: `MCP_Server/tools/browser.py` -- `get_browser_tree` and `get_browser_items_at_path` tool interfaces
- Codebase analysis: `MCP_Server/tools/devices.py` -- `load_instrument_or_effect` accepts `path` param
- Codebase analysis: `MCP_Server/mixing/catalog.py` and `MCP_Server/genres/catalog.py` -- pkgutil auto-discovery pattern
- Codebase analysis: `MCP_Server/genres/house.py` -- genre blueprint structure (instrumentation.roles)
- Project context: `.planning/PROJECT.md` -- "descriptor-only, no genre dependency" requirement for v1.5
- Project memory: MIDI tracks without instruments have no volume fader (relevant to load-path correctness)

---
*Pitfalls research for: Sound Selection Intelligence (v1.5)*
*Researched: 2026-03-30*
