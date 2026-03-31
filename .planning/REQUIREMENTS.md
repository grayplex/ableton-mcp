# Requirements: AbletonMCP v1.7 Prompt Interpretation

**Defined:** 2026-03-31
**Core Value:** An AI assistant can produce actual music in Ableton — starting from a single natural-language description.

## v1.7 Requirements

### Signal Extraction

- [x] **PARS-01**: The prompt parser tokenizes a free-text music prompt and classifies tokens into five signal types: genre signals (lo-fi, techno, ambient), mood/energy signals (dark, euphoric, chill, dreamy, driving), instrument references (Rhodes, 808, pad, piano), effect references (vinyl crackle, sidechain, reverb, distortion), and structural hints (beat, track, vibe, anthem); unrecognized tokens are passed through as raw descriptors

- [x] **LEX-01**: The signal lexicon covers at minimum: all 12 genres in the blueprint catalog (with their aliases), 25+ mood/energy adjectives mapped to energy levels (1-10) and scale preference biases, 15+ instrument references mapped to role+descriptor pairs, 10+ effect references mapped to effect descriptor strings, and 5+ tempo signals (slow, mid-tempo, driving, fast, frantic) mapped to BPM modifier offsets

### ProductionBrief Schema

- [x] **BRIEF-01**: A `ProductionBrief` TypedDict schema captures all derived parameters in one serializable structure: `primary_genre` (blueprint id), `tempo_range` (min_bpm + max_bpm), `key_feel` (scale name + mode, e.g. `minor_pentatonic` / `minor`), `groove_feel` (pattern_type enum + swing_pct 0-100), `energy_level` (1-10), `instrument_hints` (list of `{role, descriptor}` dicts), `effect_hints` (list of effect descriptor strings), `velocity_style` (enum: `laid_back` / `medium` / `driving`), `raw_prompt` (original text), `confidence` (0.0-1.0), and `reasoning` (list of plain-English derivation notes)

### Parameter Derivation

- [x] **DERV-01**: Tempo range is derived deterministically: if the prompt contains an explicit BPM number, use ±5 BPM as the range; otherwise start from the matched genre blueprint's `bpm_range` and apply an energy modifier (+10% max/min per energy point above 5, -10% per point below 5); result is always clamped to 40-200 BPM

- [x] **DERV-02**: Key feel is derived from genre convention first (e.g. lo-fi → `dorian`/`minor`, house → `minor`/`major`, trance → `minor`), then overridden by mood signal: euphoric/uplifting signals bias toward major modes, dark/melancholic signals bias toward minor/phrygian; result is a single (scale, mode) pair

- [x] **DERV-03**: Groove feel (drum pattern type + swing percentage) is derived from genre: lo-fi/hip-hop → `boom_bap` + 60-70% swing; house/techno → `four_on_floor` + 0-5% swing; DnB/jungle → `breakbeat` + 10-20% swing; trance/synthwave → `straight_16th` + 0% swing; explicit structural hints in the prompt (e.g. "boom-bap", "four-on-the-floor") override the genre default

- [x] **DERV-04**: Instrument hints list is built by merging: (a) explicit instrument references extracted from the prompt (mapped to role+descriptor), (b) the matched genre blueprint's canonical roles with their top sound recommendation descriptors; duplicates merged by role (explicit prompt signal wins)

- [x] **DERV-05**: Velocity style is derived from energy level: energy 1-3 → `laid_back` (low MIDI velocity 40-70), energy 4-6 → `medium` (velocity 65-90), energy 7-10 → `driving` (velocity 80-110); explicit prompt signals ("soft", "gentle", "hard", "aggressive") override the energy derivation

### MCP Tools

- [x] **TOOL-01**: `interpret_prompt(text)` MCP tool accepts a free-text string and returns a complete `ProductionBrief` — including `reasoning`: a list of plain-English notes explaining which signal triggered which parameter (e.g. "lo-fi detected → primary_genre=lo_fi, tempo 60-95 BPM"; "chill detected → energy_level=3, velocity_style=laid_back")

- [x] **TOOL-02**: `interpret_prompt_to_plan(text, bars_per_section?)` MCP tool calls `interpret_prompt` internally, resolves the `ProductionBrief`, then routes directly to `generate_production_plan` with the derived genre + a structured overrides dict built from `tempo_range`, `groove_feel`, and `energy_level`; returns the full production plan alongside the `ProductionBrief` so Claude has both the interpretation and the execution plan in one call

## Future Requirements

### Multi-prompt Refinement

- **PARS-02**: `refine_prompt(brief, refinement_text)` — takes an existing `ProductionBrief` and a follow-up instruction ("make it darker", "add more swing"), re-runs derivation for affected parameters only, and returns an updated brief with a diff showing which parameters changed — deferred until TOOL-01/TOOL-02 are validated

### Conflict Resolution

- **PARS-03**: When contradictory signals are present (e.g. "euphoric dark techno"), a `signal_conflicts` list is included in the `ProductionBrief` naming the conflict and which signal won; confidence drops proportionally — deferred to post-v1.7

### Prompt History

- **SESS-03**: Session-scoped prompt history — `list_production_briefs()` returns all briefs generated in the current session with their source prompts; allows Claude to compare briefs and avoid redundant calls — deferred

## Out of Scope

| Feature | Reason |
|---------|--------|
| Audio sample analysis | No audio ingestion capability in MCP |
| Real-time prompt streaming | MCP is request/response |
| LLM-inside-parser | Parser is deterministic rule-based; Claude provides the NLP layer, not a nested LLM |
| DAW-side prompt parsing | All computation server-side; no Remote Script changes needed |
| Non-English prompts | English signal lexicon only for v1.7 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PARS-01 | Phase 42 | Complete |
| LEX-01 | Phase 42 | Complete |
| BRIEF-01 | Phase 42 | Complete |
| DERV-01 | Phase 43 | Complete |
| DERV-02 | Phase 43 | Complete |
| DERV-03 | Phase 43 | Complete |
| DERV-04 | Phase 43 | Complete |
| DERV-05 | Phase 43 | Complete |
| TOOL-01 | Phase 44 | Complete |
| TOOL-02 | Phase 44 | Complete |

**Coverage:**
- v1.7 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 — v1.7 complete*
