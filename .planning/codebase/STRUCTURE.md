# Codebase Structure

**Analysis Date:** 2026-04-01

## Directory Layout

```
ableton-mcp/
├── MCP_Server/                   # MCP Server — Python process exposed to AI client
│   ├── __init__.py               # Exposes AbletonConnection, get_ableton_connection
│   ├── server.py                 # FastMCP instance creation + lifespan; entry point
│   ├── connection.py             # Socket lifecycle, get_ableton_connection(), format_error()
│   ├── protocol.py               # Length-prefix framing: send_message / recv_message
│   ├── tools/                    # All @mcp.tool() registrations (28 modules, ~233 tools)
│   │   ├── __init__.py           # Imports all tool modules to trigger registration
│   │   ├── session.py            # Connection health, session info, session state
│   │   ├── tracks.py             # Track CRUD (create, delete, duplicate, rename, color)
│   │   ├── clips.py              # Clip management (create, delete, loop, color)
│   │   ├── notes.py              # MIDI note editing (add, remove, quantize, transpose)
│   │   ├── devices.py            # Device loading, parameter reading/writing (~2365 lines)
│   │   ├── mixer.py              # Volume, pan, mute, solo, arm, send levels
│   │   ├── transport.py          # Tempo, playback, time signature, cue markers
│   │   ├── scenes.py             # Scene create/fire/delete, scene properties
│   │   ├── browser.py            # Browser tree traversal, item loading
│   │   ├── arrangement.py        # Arrangement view, locators, arrangement clips
│   │   ├── audio_clips.py        # Audio clip properties, warp markers
│   │   ├── automation.py         # Envelope breakpoints, automation
│   │   ├── routing.py            # Input/output routing configuration
│   │   ├── grooves.py            # Groove pool management
│   │   ├── scaffold.py           # Arrangement scaffolding, track creation from plan
│   │   ├── plans.py              # Production plan builder (pure computation)
│   │   ├── execution.py          # Section checklist builder, arrangement progress
│   │   ├── theory.py             # Music theory tools wrapping theory/ library
│   │   ├── genres.py             # Genre blueprint discovery and retrieval
│   │   ├── sounds.py             # Instrument profile recommendation tools
│   │   ├── mixing.py             # Mix recipe lookup and application
│   │   ├── catalog.py            # Device catalog and role taxonomy tools
│   │   ├── evaluation.py         # Session quality evaluator (evaluate_session)
│   │   ├── intelligence.py       # Mix adjustment intelligence tools
│   │   ├── analysis.py           # Section state analysis tools
│   │   ├── prompt.py             # Prompt interpretation tools
│   │   ├── refinement.py         # Section state reader, iterative refinement
│   │   └── orchestration.py      # 5 orchestration tools (agenda, plan, checkpoint, etc.)
│   ├── theory/                   # Music theory library (music21-backed)
│   │   ├── pitch.py              # MIDI ↔ note name conversion
│   │   ├── chords.py             # Chord building, identification, voicings
│   │   ├── scales.py             # Scale catalog, pitch sets, detection
│   │   ├── progressions.py       # Progression generation and analysis
│   │   ├── analysis.py           # Key detection, clip chord analysis
│   │   ├── voicing.py            # Voice leading algorithms
│   │   └── rhythm.py             # Rhythm pattern library
│   ├── genres/                   # Genre blueprint library (12 genres)
│   │   ├── schema.py             # GenreBlueprint TypedDict + validate_blueprint
│   │   ├── catalog.py            # get_blueprint(), list_genres(), resolve_alias()
│   │   ├── house.py              # House blueprint
│   │   ├── techno.py             # Techno blueprint
│   │   ├── ambient.py            # Ambient blueprint
│   │   ├── hip_hop_trap.py       # Hip-hop/trap blueprint
│   │   ├── drum_and_bass.py      # Drum and bass blueprint
│   │   ├── dubstep.py            # Dubstep blueprint
│   │   ├── trance.py             # Trance blueprint
│   │   ├── synthwave.py          # Synthwave blueprint
│   │   ├── future_bass.py        # Future bass blueprint
│   │   ├── lo_fi.py              # Lo-fi blueprint
│   │   ├── neo_soul_rnb.py       # Neo-soul/R&B blueprint
│   │   └── disco_funk.py         # Disco/funk blueprint
│   ├── sounds/                   # Instrument profile library
│   │   ├── catalog.py            # get_profile(), list_profiles(), recommend()
│   │   ├── analog.py             # Analog synth profile
│   │   ├── wavetable.py          # Wavetable synth profile
│   │   ├── operator.py           # Operator FM synth profile
│   │   ├── drift.py              # Drift synth profile
│   │   ├── simpler.py            # Simpler sampler profile
│   │   └── drum_rack.py          # Drum Rack profile
│   ├── mixing/                   # Mix recipe library (role x genre)
│   │   ├── catalog.py            # get_recipe(), get_master_recipe(), list_recipes()
│   │   ├── house.py … trance.py  # Per-genre recipe modules
│   │   └── ambient.py … lo_fi.py
│   ├── devices/                  # Device parameter catalog
│   │   ├── catalog.py            # CATALOG dict + ROLES set (bootstrapped from live Ableton)
│   │   ├── convert.py            # natural_to_normalized(), convert_recipe_to_payload()
│   │   └── gain_targets.py       # Gain staging target levels
│   ├── evaluation/               # Session quality evaluators
│   │   ├── schema.py             # SessionScore, DimensionScore, grade_from_score
│   │   ├── arrangement.py        # evaluate_arrangement()
│   │   ├── harmonic.py           # evaluate_harmonic()
│   │   ├── mix_balance.py        # evaluate_mix_balance()
│   │   └── sounds_coverage.py    # evaluate_sounds_coverage()
│   ├── prompt/                   # Prompt interpretation
│   │   ├── schema.py             # ProductionBrief, SignalSet TypedDicts
│   │   ├── parser.py             # classify_prompt()
│   │   ├── deriver.py            # derive() — extracts genre, tempo, energy, etc.
│   │   └── lexicon.py            # GROOVE_HINTS and classification vocabularies
│   ├── refinement/               # Iterative refinement
│   │   ├── schema.py             # SectionState, TrackStateEntry, ClipSummary TypedDicts
│   │   ├── interpreter.py        # build_section_refinement_plan()
│   │   └── lexicon.py            # Refinement vocabulary
│   └── orchestration/            # Production guidance system (v1.9)
│       ├── schema.py             # All TypedDicts: ProductionPhase/Agenda, ExecutionStep,
│       │                         #   PhaseChecklist, ProductionCheckpoint, SessionStats
│       ├── agenda.py             # AGENDA_CATALOG + get_agenda() — pure computation
│       ├── execution.py          # get_execution_plan() — pure computation, genre MIDI patterns
│       ├── checkpoint.py         # get_checkpoint() — reads live Ableton state
│       └── next_actions.py       # get_next_actions_result(), get_transition_guidance()
│                                 #   — reads live state or falls back to pure computation
│
├── AbletonMCP_Remote_Script/     # Ableton Live Remote Script (plugin)
│   ├── __init__.py               # AbletonMCP class, socket server, command dispatch
│   ├── registry.py               # CommandRegistry, @command decorator
│   └── handlers/                 # Domain handler mixin classes (~190 commands total)
│       ├── __init__.py           # Imports all handler modules
│       ├── base.py               # ping, get_session_info
│       ├── tracks.py             # Track CRUD + queries
│       ├── clips.py              # Clip management
│       ├── notes.py              # MIDI note operations
│       ├── devices.py            # Device loading, parameter get/set (~2839 lines)
│       ├── mixer.py              # Volume, pan, mute, solo, send
│       ├── transport.py          # Playback, tempo, time signature
│       ├── scenes.py             # Scene operations
│       ├── browser.py            # Browser tree and item loading
│       ├── arrangement.py        # Arrangement view queries and clip operations
│       ├── audio_clips.py        # Audio clip and warp marker operations
│       ├── automation.py         # Envelope automation
│       ├── routing.py            # Input/output routing
│       ├── grooves.py            # Groove pool operations
│       ├── scaffold.py           # Track scaffolding from production plan
│       └── mixer_helpers.py      # dB conversion, pan label utilities
│
├── tests/                        # Test suite (~50 test files)
│   ├── conftest.py               # mock_connection fixture, mcp_server fixture
│   ├── test_orchestration*.py    # (covered by test_checkpoint.py, test_next_actions.py,
│   │                             #   test_production_agenda.py, test_execution.py)
│   └── test_*.py                 # One file per domain area
│
├── scripts/
│   └── bootstrap_catalog.py      # One-time script: queries live Ableton to generate
│                                  #   MCP_Server/devices/catalog.py parameter data
│
└── .planning/                    # Project planning documents (not deployed)
    ├── codebase/                 # Auto-generated codebase analysis docs
    └── milestones/               # Phase plans and summaries per milestone
```

---

## Directory Purposes

### `MCP_Server/`
The full MCP server implementation. Installed as a Python package. Entry point for `mcp.run()` is `MCP_Server/server.py:main()`.

### `MCP_Server/tools/`
All 28 tool modules. Each module is responsible for one domain. Tools are registered at import time via `@mcp.tool()`. `__init__.py` imports all modules explicitly — adding a new tool module requires adding it to this import list.

Tool modules split into two categories:
- **Live-state tools** (call `get_ableton_connection()`): `session`, `tracks`, `clips`, `notes`, `devices`, `mixer`, `transport`, `scenes`, `browser`, `arrangement`, `audio_clips`, `automation`, `routing`, `grooves`, `scaffold`, `execution`, `mixing`, `analysis`, `refinement`
- **Pure-computation tools** (no socket call): `plans`, `theory`, `genres`, `sounds`, `catalog`, `prompt`, `orchestration` (partially — `get_production_agenda` and `get_phase_execution_plan` are pure; `get_production_checkpoint`, `get_next_actions`, `get_phase_transition_guidance` call RS)

### `MCP_Server/orchestration/`
The v1.9 production guidance package. The key architectural constraint: `schema.py`, `agenda.py`, and `execution.py` are pure computation; `checkpoint.py` and `next_actions.py` call RS via `get_ableton_connection`. This split allows orchestration planning to work without a live Ableton session.

### `MCP_Server/genres/`
Static genre blueprint data. Each genre file exports a single dict conforming to `GenreBlueprint`. `catalog.py` aggregates all genres and provides `resolve_alias()` to normalize genre name variants (e.g., `"lo-fi"` → `"lo_fi"`).

### `MCP_Server/devices/`
The device parameter catalog is generated by `scripts/bootstrap_catalog.py` running against a live Ableton session (constraint CATL-01: must be validated against real Ableton API data). `convert.py` handles bidirectional unit conversion between natural units (dB, Hz, ms) and Ableton's normalized 0.0–1.0 range.

### `AbletonMCP_Remote_Script/`
Installed into Ableton Live as a Remote Script (copy to `~/Music/Ableton/User Library/Remote Scripts/AbletonMCP_Remote_Script/`). Ableton calls `create_instance(c_instance)` on load. All handler domain logic is split into mixin classes under `handlers/` to keep `__init__.py` focused on socket/dispatch mechanics.

### `tests/`
pytest test suite. Tests are not co-located with source — all live in `tests/`. `conftest.py` provides the `mock_connection` fixture (patches `get_ableton_connection` in every tool module) and `mcp_server` fixture (returns the live FastMCP instance for in-process tool invocation).

---

## Key File Locations

**Entry Points:**
- `MCP_Server/server.py` — `main()` function, FastMCP instance (`mcp`)
- `AbletonMCP_Remote_Script/__init__.py` — `create_instance()`, `AbletonMCP` class

**Communication Core:**
- `MCP_Server/connection.py` — `get_ableton_connection()`, `AbletonConnection`, `format_error()`
- `MCP_Server/protocol.py` — `send_message()`, `recv_message()`
- `AbletonMCP_Remote_Script/registry.py` — `CommandRegistry`, `command` decorator

**Tool Registration:**
- `MCP_Server/tools/__init__.py` — master import list for tool modules
- `AbletonMCP_Remote_Script/handlers/__init__.py` — master import list for handler modules

**Orchestration (v1.9):**
- `MCP_Server/orchestration/schema.py` — all orchestration TypedDicts
- `MCP_Server/orchestration/agenda.py` — `AGENDA_CATALOG`, `get_agenda()`
- `MCP_Server/orchestration/execution.py` — `get_execution_plan()`, drum patterns, genre params
- `MCP_Server/orchestration/checkpoint.py` — `get_checkpoint()` (live RS calls)
- `MCP_Server/orchestration/next_actions.py` — `get_next_actions_result()`, `get_transition_guidance()`
- `MCP_Server/tools/orchestration.py` — the 5 `@mcp.tool()` wrappers

**Genre Data:**
- `MCP_Server/genres/catalog.py` — `get_blueprint()`, `resolve_alias()`, `list_genres()`
- `MCP_Server/genres/schema.py` — `GenreBlueprint` TypedDict

**Device Catalog:**
- `MCP_Server/devices/catalog.py` — `CATALOG` dict, `ROLES` set
- `MCP_Server/devices/convert.py` — `natural_to_normalized()`, `convert_recipe_to_payload()`

**Test Infrastructure:**
- `tests/conftest.py` — `mock_connection`, `mcp_server` fixtures

---

## Module Boundaries

**MCP Server tools → domain libraries:**
Tool modules import from domain libraries directly (e.g., `from MCP_Server.theory import build_chord`). Domain libraries never import from `tools/`.

**Orchestration → genres:**
`orchestration/agenda.py` and `orchestration/execution.py` import from `MCP_Server.genres.catalog`. This is the only cross-package dependency within domain libraries.

**Orchestration → checkpoint (internal):**
`next_actions.py` imports private functions from `checkpoint.py` (`_infer_completed_phases`, `_build_session_stats`). This tight coupling is intentional — both modules share phase-completion heuristics.

**tools/refinement.py → multiple packages:**
`refinement.py` is the most cross-cutting tool module — imports from `devices/`, `mixing/`, `prompt/`, `refinement/`, `tools/analysis`, `tools/intelligence`, `tools/scaffold`.

**Remote Script handler isolation:**
RS handlers import only from `AbletonMCP_Remote_Script.registry` and `AbletonMCP_Remote_Script.handlers.mixer_helpers`. They never import from `MCP_Server/`.

---

## Naming Conventions

**Files:**
- Tool modules: `snake_case.py` matching their domain (e.g., `tracks.py`, `orchestration.py`)
- Handler modules: same domain names as their tool counterparts
- Domain library modules: descriptive nouns (`catalog.py`, `schema.py`, `convert.py`)
- Genre blueprint files: `genre_id.py` matching the key in `AGENDA_CATALOG`

**Classes:**
- `AbletonConnection` — the socket connection dataclass
- `AbletonMCP` — the RS control surface class
- `CommandRegistry` — the RS command registry
- TypedDicts: PascalCase noun phrases (`ProductionCheckpoint`, `PhaseChecklist`, `ExecutionStep`)

---

## Where to Add New Code

**New MCP tool:**
1. Add function to appropriate module in `MCP_Server/tools/` with `@mcp.tool()` decorator.
2. If it's a new domain, create a new file and add it to `MCP_Server/tools/__init__.py` imports.

**New RS command:**
1. Add method to appropriate handler class in `AbletonMCP_Remote_Script/handlers/` with `@command(name, write=True/False)`.
2. Add the command name to `_WRITE_COMMANDS` or `_BROWSER_COMMANDS` frozenset in `MCP_Server/connection.py` for correct timeout selection.

**New genre:**
1. Create `MCP_Server/genres/<genre_id>.py` with a `GenreBlueprint` dict.
2. Register it in `MCP_Server/genres/catalog.py`.
3. Add genre to `MCP_Server/orchestration/agenda.py:AGENDA_CATALOG`.
4. Add drum pattern group in `MCP_Server/orchestration/execution.py:_GENRE_DRUM_GROUP`.
5. Add instrument hints in `MCP_Server/orchestration/execution.py:_GENRE_PARAMS`.
6. Add mix recipes in `MCP_Server/mixing/<genre_id>.py` and register in `MCP_Server/mixing/catalog.py`.

**New orchestration phase type:**
1. Add to `_ESTIMATED_STEPS`, `_PHASE_GOALS`, `_PHASE_NAMES` in `MCP_Server/orchestration/agenda.py`.
2. Add step builder function in `MCP_Server/orchestration/execution.py`.
3. Add completion heuristic in `MCP_Server/orchestration/checkpoint.py:_infer_completed_phases`.
4. Add `_phase_complete` case in `MCP_Server/orchestration/next_actions.py`.

**New pure-computation domain library:**
- Create `MCP_Server/<domain>/` package with `__init__.py`, `schema.py`, `catalog.py` pattern.
- Add tool wrappers in a new or existing `MCP_Server/tools/<domain>.py`.
- Register in `MCP_Server/tools/__init__.py`.

**New test:**
- Add `tests/test_<domain>.py`.
- Use `mock_connection` fixture for tools that call RS; test domain libraries directly without fixtures.

---

## Special Directories

**`.planning/`:**
- Purpose: GSD project planning documents, milestone summaries, phase plans
- Generated: No (hand-maintained)
- Committed: Yes
- Not consumed at runtime

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python interpreter)
- Committed: No (in `.gitignore`)

**`scripts/`:**
- Purpose: One-off maintenance scripts (currently only `bootstrap_catalog.py`)
- Not imported by server; run manually against live Ableton

---

*Structure analysis: 2026-04-01*
