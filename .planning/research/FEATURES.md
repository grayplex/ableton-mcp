# Feature Landscape: Mix/Master Intelligence (v1.4)

**Domain:** AI-assisted mixing and mastering for electronic music production via Ableton Live MCP
**Researched:** 2026-03-28
**Confidence:** MEDIUM-HIGH (domain knowledge well-established; Ableton LOM parameter details need runtime validation)

## Table Stakes

Features that users expect from any AI mixing assistant. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Role x genre mix recipes | Core value prop -- eliminates parameter guessing for AI | High | 12 genres x ~15 roles x ~6 device types = large data surface |
| Apply recipe tool (load + set params) | One-call mixing is the whole point; multi-call load+set is fragile | Medium | Depends on existing `load_instrument_or_effect` + `set_device_parameter` |
| Device state reader (current params) | Cannot suggest adjustments without reading current state | Low | `get_device_parameters` already exists; may need batch/summary wrapper |
| Gain staging check | Every mixing guide starts with gain staging; foundational | Medium | Read all track volumes + output meters, flag outliers |
| Master bus recipes per genre | Mastering is inseparable from mixing in electronic music | Medium | ~12 genre-specific chains, each 4-6 devices |
| Master bus apply tool | Must be able to apply master chain, not just individual devices | Medium | Chain ordering matters: EQ > Comp > Multiband > Limiter |

## Differentiators

Features that set the product apart. Not expected from basic mixing tools, but highly valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Suggest adjustments (diff with reasoning) | AI reads current state, compares to recipe, outputs param diffs with WHY | High | Requires device state reader + recipe lookup + diff logic |
| Frequency conflict detection | Identifies overlapping frequency ranges between roles (e.g., kick vs bass sub) | High | Needs per-track EQ analysis or heuristic from role assignments |
| Sidechain routing setup | Automates sidechain compression routing (kick > bass/pad compressor) | Medium | Uses existing routing tools + compressor sidechain params |
| Section-aware mixing | Different mix settings per arrangement section (breakdown = more reverb, drop = tighter) | High | Builds on v1.3 section/arrangement infrastructure |
| Mix validation checklist | "Is this mix ready?" -- checks gain staging, stereo field, frequency balance | Medium | Aggregates multiple checks into single report |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Real-time audio analysis / metering | LOM does not expose real-time audio buffers; Ableton's meter values are limited | Use heuristic analysis based on device params and role knowledge |
| Full spectrum analyzer | LOM has no FFT / spectrum data access | Provide frequency guidance through recipes and role-based EQ conventions |
| Reference track matching | Requires audio analysis capabilities outside LOM scope | Provide genre-specific target values that encode reference conventions |
| Automatic mix without user confirmation | Users want AI assistance, not black-box automation | Always show what will change + reasoning; apply on confirmation |
| VST/AU plugin parameter control | Parameter names are unpredictable across plugins | Focus exclusively on Ableton built-in devices where params are known |

---

## Detailed Feature Specifications

### F1: Device Parameter Catalog

**What:** Static data mapping of priority Ableton built-in devices to their API parameter names, value ranges, and semantic meaning.

**Priority devices (12):**

| Device | Key Parameters (80/20 rule) | Notes |
|--------|---------------------------|-------|
| **EQ Eight** | Band 1-8 Frequency, Gain, Q, Filter Type, Band On/Off; Adaptive Q; Scale | 8 bands, each with ~5 params; only 3-4 bands typically active per recipe |
| **Compressor** | Threshold, Ratio, Attack, Release, Knee, Makeup, Dry/Wet, Model (Peak/RMS/Expand), Sidechain | Core dynamics control; sidechain is critical for electronic music |
| **Glue Compressor** | Threshold, Ratio, Attack, Release, Makeup, Range, Dry/Wet, Soft Clip | SSL-style bus glue; the "Range" param is unique and important |
| **Drum Buss** | Drive, Crunch, Damp, Transients, Boom, Boom Freq, Decay, Dry/Wet | All-in-one drum processing; Boom is the secret weapon |
| **Multiband Dynamics** | Low/Mid/High Threshold Above/Below, Ratio, Attack, Release; Crossover frequencies; Output Gain | 3-band dynamics; Above = compression, Below = expansion |
| **Reverb** | Decay Time, Size, Pre-Delay, Diffusion, Dry/Wet, Hi/Lo Shelf Freq, Hi/Lo Shelf Gain, Input Filter | Wet/Dry critical; pre-delay separates source from space |
| **Delay** | Delay Time L/R, Feedback, Dry/Wet, Filter Freq, Filter Width | Sync mode vs free time; ping-pong variant |
| **Auto Filter** | Frequency, Resonance, Filter Type, Envelope Amount, LFO Amount, LFO Rate, Drive | Filter sweeps are bread and butter of electronic music |
| **Gate** | Threshold, Return, Attack, Hold, Release, Floor | Noise gate for cleaning up; useful on breaks/samples |
| **Limiter** | Gain, Ceiling, Release | Few params but critical for mastering; ceiling typically -0.3dB |
| **Utility** | Gain, Balance, Width, Mono, Mute, Phase-L, Phase-R | Gain staging workhorse; Width for stereo control |
| **Envelope Follower** | Rise, Fall, Map min/max | Sidechain-style dynamics without compressor; modulation source |

**Complexity:** Medium (data authoring, not code complexity)
**Depends on:** Existing `get_device_parameters` for runtime validation
**Implementation note:** Parameter names must match what `set_device_parameter` accepts. The existing tool uses case-insensitive name matching. Catalog data should be authored, then validated against actual Ableton devices at test time.

---

### F2: Role Categories (Standardized)

**What:** Canonical role taxonomy covering all 12 genres, with role groupings for mix recipe organization.

**Role groups and their members (union across all genre blueprints):**

| Group | Roles | Mix Treatment |
|-------|-------|---------------|
| **Low-end** | kick, bass, sub_bass, 303_bass | Mono below ~120Hz; sidechain relationships; frequency separation |
| **Drums** | snare, clap, hi-hats, percussion, break, amen_break | Transient shaping; stereo placement; bus compression |
| **Melodic** | lead, stab, synth_stab, chords, arp | Mid-range EQ space; stereo width; delay/reverb sends |
| **Harmonic bed** | pad, strings, drone, texture | Wide stereo; high-pass to avoid low-end mud; long reverb |
| **Vocal** | vocal, vocal_chop | De-essing; compression; mid-range presence; reverb/delay |
| **Atmospheric** | fx, noise, field_recording, granular, riser | Variable; often wide stereo; filtered; automated |
| **Tonal color** | bell, piano | Genre-specific; often needs carving EQ space |

**Complexity:** Low (taxonomy design, no new code infrastructure)
**Depends on:** Existing `instrumentation.roles` in genre blueprints

---

### F3: Role x Genre Mix Recipes

**What:** For each (role, genre) pair, a recipe specifying which devices to load and what parameter values to set.

**Recipe structure per role per genre:**

```
recipe = {
    "role": "bass",
    "genre": "house",
    "devices": [
        {
            "device_name": "EQ Eight",       # matches load_instrument_or_effect path
            "params": {
                "1 Filter On A": 1,           # high-pass to separate from kick
                "1 Frequency A": 80.0,        # Hz
                "1 Filter Type A": 1,         # high-pass
                ...
            }
        },
        {
            "device_name": "Compressor",
            "params": {
                "Threshold": -18.0,
                "Ratio": 4.0,
                "Attack": 10.0,
                "Release": 100.0,
                ...
            }
        }
    ]
}
```

**Genre-specific mixing conventions (key differentiators):**

| Genre | Signature Mix Characteristic | Key Devices |
|-------|------------------------------|-------------|
| **House** | Pumping sidechain on bass/pads from kick; warm low-end; offbeat hat brightness | Compressor (sidechain), Glue Compressor, EQ Eight |
| **Techno** | Heavy sidechain; aggressive parallel drum compression; filtered textures | Compressor (sidechain), Drum Buss, Auto Filter |
| **Ambient** | Long reverb tails; minimal compression; wide stereo; very dynamic | Reverb (high wet), Delay, Utility (width), EQ Eight |
| **DnB** | Tight fast compression on breaks; heavy sub-bass; snare crack emphasis | Compressor (fast attack), Drum Buss, EQ Eight |
| **Dubstep** | Aggressive mid-range bass processing; heavy limiting; sidechain on everything | Multiband Dynamics, Compressor, Auto Filter |
| **Trance** | Gated reverb on leads; supersaw layering width; pumping compression | Gate, Reverb, Compressor (sidechain), Utility (width) |
| **Hip-hop/Trap** | 808 sub-bass saturation; crisp hi-hats; vocal presence carving | Drum Buss (boom), EQ Eight, Compressor |
| **Lo-fi** | Warm saturation; rolled-off highs; gentle compression | Auto Filter (low-pass), Compressor, EQ Eight |
| **Synthwave** | Wide synths; gated reverb on snare; chorus-like stereo | Reverb, Utility (width), Compressor |
| **Neo-soul/R&B** | Warm analog compression; smooth EQ; vocal-forward mix | Glue Compressor, EQ Eight, Reverb |
| **Future bass** | Heavy sidechain; bright supersaws; wide stereo image | Compressor (sidechain), Multiband Dynamics, Utility |
| **Disco/Funk** | Natural dynamics; warm compression; live feel preservation | Glue Compressor, EQ Eight, Reverb |

**Complexity:** HIGH (largest data surface in v1.4; ~12 genres x ~10 core roles x 2-4 devices each)
**Depends on:** F1 (device parameter catalog), F2 (role taxonomy)
**Implementation strategy:** Start with 3-4 most-used genres (house, techno, ambient, DnB), expand to remaining 8. Each recipe is a Python dict, same pattern as genre blueprints.

---

### F4: Apply Recipe Tool

**What:** Single MCP tool call that loads all devices in a recipe and sets all their parameters on a target track.

**Interface:**
```
apply_mix_recipe(track_index, role, genre, [subgenre])
  -> loads EQ Eight, Compressor, etc. onto track
  -> sets all params per recipe
  -> returns: devices loaded, params set, any warnings
```

**Complexity:** Medium
**Depends on:** F3 (recipes), existing `load_instrument_or_effect`, existing `set_device_parameter`
**Key constraint:** Device loading order matters. EQ before compressor is standard. Must wait for each device load before setting params (Ableton's async device loading).

---

### F5: Device State Reader (Batch)

**What:** Read all device params across all tracks (or a subset) in one call, returning a structured snapshot of the current mix state.

**Interface:**
```
get_mix_state([track_indices], [track_type])
  -> for each track: device chain with all param names + current values
  -> returns: structured dict, not individual get_device_parameters calls
```

**Complexity:** Low-Medium
**Depends on:** Existing `get_device_parameters` (wraps multiple calls)
**Why needed:** Claude currently must call `get_device_parameters` per device per track. For a 16-track session with 3 devices each, that is 48 tool calls. A batch reader reduces this to 1.

---

### F6: Gain Staging Check

**What:** Reads all track volumes and output levels, compares to target gain staging conventions, flags issues.

**Conventions (genre-independent baseline):**
- Individual tracks: -6 to -12 dB headroom (volume fader ~0.70-0.85)
- Kick: loudest element, typically -6 dB
- Bass: -8 to -10 dB
- Master bus: peaks at -3 to -6 dB before limiting
- No track clipping (output > 0 dB)

**Interface:**
```
check_gain_staging([genre])
  -> reads all track volumes via existing mixer tools
  -> reads master output level
  -> returns: per-track status (ok/too-hot/too-quiet), overall assessment
```

**Complexity:** Medium
**Depends on:** Existing `set_track_volume` / track info tools, F2 (role taxonomy for role-specific targets)
**Limitation:** LOM exposes track.mixer_device.volume (fader position) but NOT real-time peak metering. Gain staging check is based on fader positions and Utility gain values, not actual signal level. This is still highly useful -- the most common gain staging mistake is wrong fader positions.

---

### F7: Suggest Adjustments

**What:** Reads current device state on a track, compares to the recipe for that role/genre, outputs a diff with reasoning for each parameter change.

**Interface:**
```
suggest_mix_adjustments(track_index, role, genre)
  -> reads current device params
  -> looks up recipe
  -> returns: list of {param, current_value, suggested_value, reason}
```

**Example output:**
```json
{
  "suggestions": [
    {
      "device": "EQ Eight",
      "param": "1 Frequency A",
      "current": 50.0,
      "suggested": 80.0,
      "reason": "High-pass at 80Hz for house bass separates from kick sub (40-60Hz)"
    },
    {
      "device": "Compressor",
      "param": "Ratio",
      "current": 2.0,
      "suggested": 4.0,
      "reason": "House bass needs tighter compression to sit under the kick"
    }
  ]
}
```

**Complexity:** High (diff logic + reasoning text generation)
**Depends on:** F5 (device state reader), F3 (recipes)

---

### F8: Master Bus Recipes

**What:** Genre-specific master bus chains with device order and parameter values.

**Standard master bus chain order:**

```
1. EQ Eight (subtractive) -- cut rumble, fix resonances
2. Glue Compressor -- gentle 2-4 dB glue
3. Multiband Dynamics -- balance frequency bands
4. EQ Eight (additive) -- final tonal shaping (optional)
5. Limiter -- ceiling at -0.3 dB, target 2-4 dB reduction
```

**Genre-specific variations:**

| Genre | Chain Modifications | Key Settings |
|-------|--------------------|-------------|
| **Techno** | More aggressive Glue Comp (4:1 ratio); Multiband with tight low-end control | Ceiling -0.1 dB, 4-6 dB limiting |
| **House** | Moderate Glue Comp (2:1); wider Multiband crossovers | Ceiling -0.3 dB, 2-4 dB limiting |
| **Ambient** | Skip Glue Comp or very gentle; skip Multiband; preserve dynamics | Ceiling -1.0 dB, minimal limiting |
| **DnB** | Fast-attack Compressor instead of Glue; tight Multiband on lows | Ceiling -0.3 dB, 4-6 dB limiting |
| **Dubstep** | Aggressive Multiband; mid-range boost on final EQ | Ceiling -0.1 dB, 6+ dB limiting |
| **Hip-hop/Trap** | Warm Glue Comp; bass-forward EQ; moderate limiting | Ceiling -0.3 dB, 3-5 dB limiting |
| **Trance** | Similar to house but more aggressive limiting for loudness | Ceiling -0.1 dB, 4-6 dB limiting |
| **Lo-fi** | Very gentle; maybe just EQ + Limiter; preserve character | Ceiling -1.0 dB, 1-2 dB limiting |
| **Synthwave** | Warm compression; slight mid-scoop on EQ | Ceiling -0.3 dB, 2-4 dB limiting |
| **Neo-soul** | Gentle Glue Comp; warm EQ; preserve dynamics | Ceiling -0.5 dB, 2-3 dB limiting |
| **Future bass** | Aggressive Multiband; bright top-end EQ | Ceiling -0.1 dB, 4-6 dB limiting |
| **Disco/Funk** | Gentle; preserve transients; light Glue Comp | Ceiling -0.3 dB, 2-3 dB limiting |

**Complexity:** Medium (12 chains, each 4-6 devices with ~5 params each)
**Depends on:** F1 (device parameter catalog)
**Implementation:** Separate from per-track recipes. Applied to master track using `track_type="master"`.

---

### F9: Master Bus Tools

**What:** Apply/read master bus chain.

**Interface:**
```
apply_master_recipe(genre, [subgenre])
  -> loads chain onto master track in correct order
  -> sets all params

get_master_state()
  -> reads all devices on master track with params
```

**Complexity:** Low-Medium (thin wrapper over F4 logic targeting master track)
**Depends on:** F8 (master bus recipes), F4 (apply recipe tool)

---

## Feature Dependencies

```
F1 (Device Parameter Catalog)
  |
  +---> F3 (Role x Genre Mix Recipes) ---> F4 (Apply Recipe Tool)
  |         |                                    |
  |         v                                    v
  |     F7 (Suggest Adjustments) <--------- F5 (Device State Reader)
  |
  +---> F8 (Master Bus Recipes) ----------> F9 (Master Bus Tools)

F2 (Role Taxonomy)
  |
  +---> F3 (Role x Genre Mix Recipes)
  +---> F6 (Gain Staging Check)

Existing infrastructure:
  - load_instrument_or_effect  --> F4, F9
  - set_device_parameter       --> F4, F9
  - get_device_parameters      --> F5
  - set_track_volume/pan       --> F6
  - get_track_info             --> F5, F6
  - genre blueprints           --> F2, F3
```

## MVP Recommendation

**Phase 1 (foundation):** Build in this order:
1. **F1: Device Parameter Catalog** -- everything depends on knowing param names/ranges
2. **F2: Role Taxonomy** -- lightweight; categorize existing genre roles
3. **F3: Role x Genre Mix Recipes** (top 4 genres: house, techno, ambient, DnB) -- core data
4. **F4: Apply Recipe Tool** -- the headline feature

**Phase 2 (feedback loop):**
5. **F5: Device State Reader** (batch) -- enables suggest adjustments
6. **F6: Gain Staging Check** -- quick win, high user value
7. **F8: Master Bus Recipes** -- complete the mastering story
8. **F9: Master Bus Tools** -- apply master chains

**Phase 3 (intelligence):**
9. **F7: Suggest Adjustments** -- the "AI mixing engineer" differentiator
10. **F3 expansion** -- remaining 8 genres

**Defer:**
- Section-aware mixing: Requires automation infrastructure; better as v1.5
- Frequency conflict detection: Needs audio analysis or sophisticated heuristics; v1.5+
- Sidechain routing setup: Complex routing automation; include basic sidechain params in recipes but defer full routing automation

## Data Scale Estimate

| Data Item | Count | Authoring Effort |
|-----------|-------|-----------------|
| Device parameter entries | ~120 params across 12 devices | 1 phase |
| Role taxonomy entries | ~25 distinct roles, 7 groups | 0.5 phase |
| Mix recipes (4 core genres) | ~40 recipes (10 roles x 4 genres) | 1-2 phases |
| Mix recipes (remaining 8 genres) | ~80 recipes | 2 phases |
| Master bus recipes | 12 chains (one per genre) | 0.5 phase |
| Total data dicts | ~250 recipe dicts | Major authoring effort |

## Sources

- [Ableton Live 12 Audio Effect Reference](https://www.ableton.com/en/manual/live-audio-effect-reference/) -- HIGH confidence, official
- [Remotify Device Parameters](https://remotify.io/device-parameters/device_params_live11.html) -- MEDIUM confidence, community reference
- [iZotope Mixing Tips for EDM](https://www.izotope.com/en/learn/12-tips-for-mixing-and-producing-edm) -- MEDIUM confidence
- [iZotope Ideal Mastering Signal Chain](https://www.izotope.com/en/learn/what-is-an-ideal-mastering-signal-chain.html) -- HIGH confidence
- [Toolroom Academy Mastering Chains](https://toolroomacademy.com/features/ableton-mastering-chains-an-in-depth-guide/) -- MEDIUM confidence
- [Audeobox How to Master in Ableton](https://www.audeobox.com/learn/ableton/how-to-master-in-ableton/) -- MEDIUM confidence
- [EDM Tips 30 Mixdown Techniques](https://edmtips.com/30-mix-techniques/) -- MEDIUM confidence
- [Loopmasters Mixing Electronic Music Guidelines](https://www.loopmasters.com/articles/2718-Mixing-Electronic-Music-A-Few-Quick-And-Easy-Guidelines) -- MEDIUM confidence
- Existing codebase: genre blueprints, device tools, mixer tools -- HIGH confidence (runtime-validated)

### Confidence Notes

- **Device parameter names:** MEDIUM -- parameter names listed here are based on Ableton documentation and community references. Exact API names as returned by `get_device_parameters` MUST be validated at runtime during implementation. The existing tool uses case-insensitive matching which provides some tolerance.
- **Genre mixing conventions:** HIGH -- well-established domain knowledge corroborated across multiple production education sources.
- **Master bus chain order:** HIGH -- near-universal consensus: subtractive EQ > compression > multiband (if needed) > additive EQ > limiter.
- **Recipe parameter values:** LOW -- specific numeric values (e.g., "threshold at -18 dB") are starting points that need ear-testing. The system should make these easily adjustable.
