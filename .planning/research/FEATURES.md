# Feature Research: Sound Selection Intelligence (v1.5)

**Domain:** AI-driven instrument/preset recommendation for electronic music production via Ableton Live MCP
**Researched:** 2026-03-30
**Confidence:** MEDIUM-HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features that make the sound recommendation system minimally useful. Without these, the feature feels broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `get_sound_recommendation(descriptor)` returning instrument + category path | Core promise of the feature; without it, Claude still fumbles randomly through the browser | MEDIUM | Must map descriptor tags to one of 6 native instruments + a browser category path (e.g., `Instruments/Wavetable/Bass`). Dynamic reasoning from instrument profiles, not a static lookup table. |
| `list_sound_descriptors` returning all supported tags | Users (and Claude) need to know what vocabulary is available; without this, descriptor usage is guesswork | LOW | Returns the full set of descriptor tags. Critical for discoverability. |
| `get_instrument_profile` returning full character doc | Producers want to understand *why* an instrument was recommended; profiles serve as the reasoning substrate | LOW | One profile per instrument. Returns sonic character, strengths, weaknesses, and preset category map. |
| Instrument profiles for all 6 native instruments | Incomplete coverage = recommendations that silently fail for whole sound categories | MEDIUM | Wavetable, Analog, Operator, Drift, Simpler, Drum Rack. Each needs: sonic character, strengths/weaknesses, best-for roles, preset category map. |
| Descriptor tags covering all 9 mix roles | Every role in the existing taxonomy (kick, bass, lead, pad, chords, vocal, atmospheric, return, master) must be addressable by at least one descriptor | LOW | If "pad" role exists but no descriptor maps to pad sounds, the system has a blind spot. |
| Browser category paths that actually work | Recommended paths must resolve via existing `get_browser_items_at_path` and `load_instrument_or_effect` tools | LOW | Paths are in the format `instruments/Wavetable/Bass` or `instruments/Drift/Pad`. Must be validated against real Ableton browser structure. |

### Differentiators (Competitive Advantage)

Features that make this system notably better than "just browse manually."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Two-axis descriptor system: role + character | Descriptors combine a role (what the sound does) with a tonal character (how it sounds), e.g., "warm pad" vs "bright pad" vs "dark pad" | MEDIUM | This is the key differentiator. Most preset browsers only categorize by role (Bass, Lead, Pad). Adding tonal character axis ("warm," "dark," "bright," "punchy") gives Claude real taste. |
| Reasoning in recommendations | Each recommendation includes a one-line reasoning explaining *why* this instrument + category, not just *what* | LOW | Already specified in requirements. Makes recommendations transparent and educational. |
| Coverage of tonal descriptors beyond basic role names | Tags like "glitchy," "ethereal," "aggressive," "lo-fi" that describe texture/mood, not just instrument role | LOW | Most DAW browsers don't support mood-based searching. This is where AI-driven selection adds value over manual browsing. |
| Instrument strengths/weaknesses in profiles | Profiles say what each instrument is *bad* at, not just good at -- guides Claude away from poor choices | LOW | E.g., "Drift is poor for metallic/FM textures -- use Operator instead." Negative guidance prevents bad recommendations. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full preset path recommendation (specific preset name) | "Just tell me exactly which preset to load" | Preset names change across Live versions and Packs; preset availability depends on user's Live edition (Intro/Standard/Suite); specific preset taste is subjective | Recommend instrument + category path, then let Claude browse from there using existing browser tools. Depth stops at category, not preset. |
| Genre-aware recommendations (descriptor + genre) | "A warm pad for house is different from ambient" | Adds combinatorial explosion (descriptors x genres = hundreds of mappings); genre context already available in genre blueprints; makes the tool tightly coupled to genre system | Keep `get_sound_recommendation` descriptor-only. Claude can combine genre blueprint knowledge with sound recommendation separately. Separation of concerns. |
| Audio-analysis-based matching (Jamahook-style) | "Analyze this audio and find similar sounds" | Requires audio streaming capability the MCP protocol doesn't support; fundamentally different architecture (signal processing vs. knowledge graph) | Text descriptor approach. Producer describes what they want in words, system maps to instrument + category. |
| Automatic preset loading without confirmation | "Just load the best preset automatically" | Removes user agency; preset selection is subjective; loading the wrong sound wastes more time than browsing | Recommend the path, let Claude (or user) browse and choose. The recommendation narrows the search space from hundreds to a manageable category. |
| Per-preset sonic descriptions | "Describe every factory preset" | Hundreds of presets per instrument; descriptions would be stale if presets change; massive data maintenance burden | Category-level descriptions in instrument profiles are sufficient. Claude can audition presets within the recommended category using existing browser tools. |
| Dynamic instrument profile updates | "Profiles should update when new Packs are installed" | Pack content varies per user; no API to introspect Pack contents programmatically; creates maintenance nightmare | Profiles cover factory instruments only. User library and Pack presets are browsable but not profiled. |

## Descriptor Tag Taxonomy

### Design Principles

Sound descriptors should follow a **role + character** two-axis model:

- **Role axis**: What musical function the sound serves (bass, lead, pad, keys, etc.)
- **Character axis**: How the sound feels tonally (warm, bright, dark, punchy, etc.)

A descriptor is typically `[character] [role]` -- e.g., "warm pad," "punchy kick," "bright pluck." Some descriptors are role-only ("kick," "hi-hat") or character-only ("ethereal," "aggressive") when context makes the other axis obvious.

### Role Tags (aligned with Ableton Live 12 Sounds filter tags)

Ableton Live 12's browser uses these Sound filter categories for instrument presets:

| Role Tag | Ableton Browser Equivalent | Notes |
|----------|---------------------------|-------|
| `bass` | Bass | Sub-bass, synth bass, 808, etc. |
| `lead` | Lead | Monophonic melodic lines |
| `pad` | Pad | Sustained, evolving textures |
| `keys` | Keys | Piano-like, electric piano, Rhodes |
| `pluck` | Plucked | Short-attack melodic sounds |
| `strings` | Strings | Bowed string textures |
| `brass` | Brass & Woodwind | Horn stabs, brass sections |
| `organ` | Organ | Sustained organ tones |
| `arp` | Arp | Arpeggiated sequences |
| `drums` | Drums | Full drum kits, percussion |
| `kick` | (within Drums) | Specific to electronic kick drums |
| `hi-hat` | (within Drums) | Open/closed hi-hats |
| `snare` | (within Drums) | Snare and clap sounds |
| `percussion` | (within Drums) | Non-standard rhythmic hits |
| `fx` | FX | Risers, impacts, sweeps, textures |
| `vocal` | Vocal | Vocal chops, processed voices |

### Character Tags (tonal/textural descriptors)

Derived from standard music production vocabulary and synthesis terminology:

| Character Tag | Meaning | Synthesis Implication |
|---------------|---------|----------------------|
| `warm` | Rich low-mids, gentle harmonics, analog feel | Low-pass filtered, moderate resonance, slight detune |
| `bright` | Emphasized highs, crisp, present | Open filter, sawtooth-heavy, high harmonics |
| `dark` | Rolled-off highs, deep, subdued | Heavy low-pass, sine/triangle basis, low resonance |
| `punchy` | Fast attack, strong transient, compact | Short amp envelope, fast attack/decay, compression |
| `lush` | Wide stereo, detuned, evolving | Unison voices, chorus, slow LFO modulation |
| `gritty` | Distorted, raw, edgy | Drive/saturation, harsh waveforms, bit reduction |
| `clean` | Pure tone, minimal processing | Simple waveform, no distortion, subtle filtering |
| `aggressive` | Hard-hitting, intense, in-your-face | Distortion, fast envelopes, sharp resonance |
| `ethereal` | Spacious, dreamy, atmospheric | Long reverb tail, slow attack, high-register |
| `lo-fi` | Degraded, vintage, imperfect | Bit crush, vinyl noise, reduced bandwidth |
| `glitchy` | Stuttering, digital artifacts, broken | Granular, sample manipulation, rhythmic gating |
| `metallic` | Bell-like, inharmonic, FM-style | FM synthesis, ring modulation, inharmonic ratios |
| `plucky` | Short decay, percussive attack | Fast envelope decay, no sustain |
| `evolving` | Morphing, changing over time | Wavetable scanning, LFO on multiple params |
| `thick` | Dense, full-bodied, heavy | Multiple oscillators, unison, saturation |
| `thin` | Narrow, minimal harmonics | Single oscillator, high-pass, sine-based |

### Compound Descriptors (examples)

These are the natural-language descriptors users will pass to `get_sound_recommendation`:

| Descriptor | Mapped Role | Mapped Character | Recommended Instrument |
|------------|-------------|------------------|----------------------|
| "warm pad" | pad | warm | Analog or Drift |
| "dark bass" | bass | dark | Analog |
| "bright pluck" | pluck | bright | Wavetable |
| "punchy kick" | kick | punchy | Drum Rack |
| "glitchy texture" | fx | glitchy | Simpler (slice mode) or Wavetable |
| "metallic bell" | keys | metallic | Operator |
| "lush strings" | strings | lush | Wavetable |
| "aggressive lead" | lead | aggressive | Wavetable or Operator |
| "ethereal pad" | pad | ethereal | Wavetable or Drift |
| "lo-fi keys" | keys | lo-fi | Drift or Simpler |
| "thick bass" | bass | thick | Analog or Wavetable |
| "clean lead" | lead | clean | Drift |
| "evolving texture" | fx/pad | evolving | Wavetable |
| "gritty bass" | bass | gritty | Operator |

## Instrument Profiles: Sonic Character Summary

### Wavetable
- **Synthesis type**: Wavetable (two oscillators scanning through wavetable banks) + sub oscillator + dual filters + modulation matrix
- **Sonic character**: Versatile, modern, can range from pristine to aggressive. Excels at evolving, complex timbres that subtractive synths cannot achieve.
- **Best for**: Leads, pads, evolving textures, bright plucks, aggressive basses, complex sound design
- **Weaknesses**: Can sound "digital" when unprocessed; not the first choice for classic warm analog sounds
- **Preset categories**: Bass, Keys, Lead, Pad, Strings, Synths, Plucks (MEDIUM confidence -- needs runtime validation)

### Analog
- **Synthesis type**: Virtual analog (modeled analog circuits) with dual oscillators, filters, amplifiers, LFOs
- **Sonic character**: Warm, fat, vintage. Delivers the classic analog synthesizer sound with authentic circuit-modeled warmth.
- **Best for**: Warm basses, warm pads, classic leads, lo-fi textures, vintage-sounding keys
- **Weaknesses**: Less capable of complex evolving textures or metallic/FM sounds; CPU heavier than Drift
- **Preset categories**: Bass, Keys, Lead, Pad, Brass, Strings (MEDIUM confidence)

### Operator
- **Synthesis type**: FM synthesis (four operators) with additive and subtractive modes
- **Sonic character**: Can produce timbres impossible with analog-style synths -- metallic, bell-like, inharmonic. Also capable of clean, precise digital tones.
- **Best for**: Electric pianos, bells, metallic textures, complex bass, FM leads, organ sounds, percussive tones
- **Weaknesses**: Less intuitive for beginners; FM synthesis is harder to predict; not ideal for classic warm/analog sounds
- **Preset categories**: Bass, Keys, Lead, Pad, Organ (MEDIUM confidence)

### Drift
- **Synthesis type**: Subtractive (two oscillators, multi-mode filter, analog character via "drift" parameter)
- **Sonic character**: Warm, organic, musical by default. The drift parameter adds subtle pitch/filter instability mimicking vintage hardware.
- **Best for**: Simple warm basses, organic pads, clean leads, plucks, quick sketching, anything needing analog character with minimal effort
- **Weaknesses**: Less capable of complex sound design; limited modulation compared to Wavetable; no FM or wavetable scanning
- **Preset categories**: Bass, Pad, Strings, Synth Lead (MEDIUM confidence -- confirmed from documentation)

### Simpler
- **Synthesis type**: Sample playback with Classic (one-shot/loop), 1-Shot (trigger), and Slice (auto-segment) modes
- **Sonic character**: Depends entirely on loaded sample. As a sampler, it reproduces real-world timbres or processes them beyond recognition.
- **Best for**: Sample-based sounds, lo-fi textures, vocal chops, sliced loops, one-shots, any sound that starts from a recording
- **Weaknesses**: No synthesis engine -- requires samples; sound quality limited by source material
- **Preset categories**: N/A (Simpler loads samples, not synth presets; category depends on loaded content)

### Drum Rack
- **Synthesis type**: Multi-pad instrument hosting individual samples or instruments per pad (128 pads)
- **Sonic character**: Varies per pad -- each pad is its own instrument chain. The instrument of choice for all drum/percussion sounds.
- **Best for**: Kick drums, snares, hi-hats, percussion, drum kits, layered percussive sounds
- **Weaknesses**: Not a melodic instrument; primarily for drums and one-shots
- **Preset categories**: Kit-Core (electronic kits), Kit-Acoustic (acoustic kits), Kit-Processed (processed/mangled kits), Hit (individual hits) (LOW confidence -- needs runtime validation)

## Ableton Live 12 Browser: Preset Category Paths

The `get_sound_recommendation` tool must return paths that resolve in the Ableton browser via `get_browser_items_at_path`. Based on research, the likely path format is:

```
instruments/{InstrumentName}/{CategoryName}
```

For example:
- `instruments/Wavetable/Bass`
- `instruments/Analog/Pad`
- `instruments/Operator/Keys`
- `instruments/Drift/Bass`

**CRITICAL: These paths need runtime validation.** The exact category folder names within each instrument's browser node must be confirmed by running `get_browser_tree(category_type="instruments", max_depth=3)` in a live Ableton session. The categories listed above are best-effort from documentation and third-party sources but are not confirmed from the Ableton API.

Known Ableton Live 12 Sounds browser filter tags (HIGH confidence -- from official documentation):
- Bass, Lead, Pad, Keys, Strings, Plucked, Brass & Woodwind, Organ, Arp, Drums, FX, Vocal, Piano, Mallet, Synth

These are *tags* in the Live 12 tag system, not necessarily *folder paths* in the browser tree. The instrument-specific preset folders may use slightly different names.

## Feature Dependencies

```
Instrument Profiles (INST-01..06)
    |
    +---> get_instrument_profile (SREC-03) [serves profiles as MCP tool]
    |
    +---> get_sound_recommendation (SREC-01) [reasons over profiles to map descriptors]
    |         |
    |         +---> requires: descriptor tag taxonomy (embedded in code)
    |         +---> requires: browser category paths per instrument (in profiles)
    |         +---> output feeds: load_instrument_or_effect (existing tool)
    |         +---> output feeds: get_browser_items_at_path (existing tool)
    |
    +---> list_sound_descriptors (SREC-02) [returns all valid descriptor tags]

Existing tools (no changes needed):
    get_browser_tree           -- validates category paths exist
    get_browser_items_at_path  -- browses within recommended category
    load_instrument_or_effect  -- loads the recommended instrument
    get_role_taxonomy          -- 9 canonical roles already defined
```

### Dependency Notes

- **Instrument profiles must exist before recommendation tool**: `get_sound_recommendation` reasons over profile data to select instruments. Profiles are the data layer; recommendation is the logic layer.
- **Browser category paths must be validated**: The profiles include preset category maps with browser paths. These must be confirmed against a live Ableton session before the recommendation tool can be trusted.
- **Descriptor taxonomy must align with existing role taxonomy**: The 9 roles in `ROLES` (kick, bass, lead, pad, chords, vocal, atmospheric, return, master) overlap with but don't match 1:1 the Ableton browser Sound tags. The descriptor system bridges both.
- **No Remote Script changes needed**: All new tools are server-side only, operating on static data (instrument profiles) and existing browser tools.

## MVP Definition

### Launch With (Phase 1: Instrument Profiles)

- [x] Instrument profile data for all 6 instruments (INST-01..06)
  - Sonic character, strengths, weaknesses
  - Best-for roles
  - Preset category map with browser paths
  - **Requires runtime browser validation for paths**
- [x] `get_instrument_profile` MCP tool (SREC-03)

### Launch With (Phase 2: Recommendation Engine)

- [x] Descriptor tag taxonomy: ~16 character tags x ~16 role tags
- [x] `get_sound_recommendation(descriptor)` MCP tool (SREC-01)
  - Parses compound descriptor into role + character
  - Selects best instrument from profiles
  - Returns: instrument name, browser category path, one-line reasoning
- [x] `list_sound_descriptors` MCP tool (SREC-02)

### Defer (Future Consideration)

- [ ] Genre-aware recommendations -- wait for user demand; separation of concerns favors descriptor-only for now
- [ ] Third-party plugin profiles -- scope limited to 6 native instruments
- [ ] Preset-level descriptions -- too many presets, too fragile to maintain
- [ ] Audio-based matching -- fundamentally different architecture, not MCP-compatible

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Instrument profiles (6 instruments) | HIGH | MEDIUM | P1 |
| `get_sound_recommendation` | HIGH | MEDIUM | P1 |
| `list_sound_descriptors` | MEDIUM | LOW | P1 |
| `get_instrument_profile` | MEDIUM | LOW | P1 |
| Character descriptor taxonomy | HIGH | LOW | P1 |
| Browser path validation | HIGH | LOW | P1 |
| Genre-aware recommendations | LOW | HIGH | P3 |
| Third-party plugin profiles | LOW | HIGH | P3 |

## Competitor Feature Analysis

| Feature | Jamahook (AI Sound Matching) | FL Studio Gopher/Loop Starter | Our Approach |
|---------|------------------------------|-------------------------------|--------------|
| Sound selection | Audio-analysis matching (psychoacoustic) | Manual loop browsing with genre tags | Text descriptor to instrument + category mapping |
| Input method | Audio signal (plays back, listens, matches) | Genre selection for loop loading | Natural language descriptor string |
| Output | Matched sample/loop from library | Genre-specific loops in session | Instrument name + browser category path + reasoning |
| Scope | Any audio content | Loops only | 6 native Ableton instruments |
| Requires audio streaming | Yes | No | No (text-based, fits MCP protocol) |
| Works offline | No (cloud-based) | Yes | Yes (static data, no network) |
| Transparent reasoning | No (black box algorithm) | No | Yes (one-line reasoning per recommendation) |

Our approach is deliberately narrower (6 instruments, text descriptors, no audio analysis) but fits perfectly within the MCP command/response model and provides transparent, explainable recommendations. The value is in eliminating random preset fumbling, not in replacing the producer's ears.

## Sources

- [Ableton Live 12 Browser and Tags FAQ](https://help.ableton.com/hc/en-us/articles/11425042663708-Browser-and-Tags-in-Live-12-FAQ) -- Sound filter tags
- [Ableton Live 12 Browser documentation](https://help.ableton.com/hc/en-us/articles/12927340213660-The-Live-12-Browser) -- Browser categories
- [Ableton Live Instrument Reference Manual](https://www.ableton.com/en/manual/live-instrument-reference/) -- Instrument architectures
- [Ableton Drift blog post](https://www.ableton.com/en/blog/drift-exploring-the-new-synth-in-live-113/) -- Drift sonic character
- [ADSR Sounds: Drift Presets](https://www.adsrsounds.com/synth/ableton-drift/) -- Drift preset categories
- [Audeobox: Best Free Instruments for Ableton](https://www.audeobox.com/learn/ableton/best-free-instruments-for-ableton/) -- Instrument character comparison
- [BeatShaper: Drift Guide](https://www.beatshaper.ai/blog/ableton-drift) -- Drift sonic character detail
- [VI-Control: Taxonomy of Synth Sounds](https://vi-control.net/community/threads/taxonomy-of-synth-sounds.140158/) -- Descriptor taxonomy discussion
- [Jamahook](https://jamahook.com/) -- AI sound matching competitor
- [Soundfly: Learning to Describe Synth Sounds](https://flypaper.soundfly.com/discover/learning-to-describe-synth-sounds-to-rebuild-patches/) -- Sound descriptor vocabulary

---
*Feature research for: Sound Selection Intelligence (v1.5)*
*Researched: 2026-03-30*
