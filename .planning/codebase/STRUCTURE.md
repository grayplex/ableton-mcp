# Codebase Structure

**Analysis Date:** 2026-04-02

## Directory Layout

```
ableton-mcp/
├── MCP_Server/                  # Python MCP server (runs in AI client process)
│   ├── server.py                # FastMCP server entry point + lifespan
│   ├── connection.py            # AbletonConnection, get_ableton_connection(), timeout routing
│   ├── protocol.py              # Length-prefix framing (send_message / recv_message)
│   ├── tools/                   # MCP tool registration — one module per domain
│   │   ├── __init__.py          # Imports all tool modules to trigger @mcp.tool() registration
│   │   ├── session.py           # get_connection_status, get_session_info, get_session_state
│   │   ├── tracks.py            # get_track_info, create_midi_track, create_audio_track, etc.
│   │   ├── clips.py             # create_clip, fire_clip, stop_clip, set_clip_*, etc.
│   │   ├── notes.py             # add_notes_to_clip, remove_notes, quantize_notes, etc.
│   │   ├── mixer.py             # get_volume, set_track_volume, set_track_pan, etc.
│   │   ├── devices.py           # get_device_parameters, set_device_parameter, load_instrument_or_effect, etc.
│   │   ├── transport.py         # set_tempo, start_playback, stop_playback, set_time_signature, etc.
│   │   ├── scenes.py            # create_scene, fire_scene, set_scene_name, etc.
│   │   ├── browser.py           # get_browser_tree, get_browser_items_at_path, load_browser_item
│   │   ├── arrangement.py       # get_arrangement_state, create_arrangement_midi_clip
│   │   ├── audio_clips.py       # set_audio_clip_properties, create_session_audio_clip
│   │   ├── automation.py        # insert_envelope_breakpoints, clear_clip_envelopes
│   │   ├── routing.py           # set_input_routing, set_output_routing
│   │   ├── grooves.py           # set_groove_amount, set_swing_amount, set_clip_groove
│   │   ├── scaffold.py          # scaffold_arrangement, get_arrangement_overview
│   │   ├── genres.py            # list_genre_blueprints, get_genre_blueprint
│   │   ├── theory.py            # get_scale, generate_chord, generate_progression, etc.
│   │   ├── plans.py             # generate_production_plan
│   │   ├── prompt.py            # interpret_prompt, interpret_prompt_to_plan
│   │   ├── orchestration.py     # get_production_agenda, get_phase_execution_plan, get_production_checkpoint, get_next_actions, refine_agenda, get_phase_transition_guidance
│   │   ├── mixing.py            # get_mix_recipe, apply_mix_recipe, apply_master_recipe, set_sidechain_source
│   │   ├── analysis.py          # get_mix_state, check_gain_staging
│   │   ├── intelligence.py      # suggest_mix_adjustments
│   │   ├── evaluation.py        # evaluate_session
│   │   ├── execution.py         # get_all_tracks (runtime sentinel resolver)
│   │   ├── sounds.py            # get_instrument_profile, list_instrument_profiles
│   │   ├── catalog.py           # list_recipes
│   │   └── refinement.py        # get_section_state, apply_section_refinement, interpret_refinement
│   ├── orchestration/           # Production workflow engine (pure Python)
│   │   ├── schema.py            # TypedDicts: ProductionAgenda, ProductionPhase, ExecutionStep, PhaseChecklist, ProductionCheckpoint, SessionStats
│   │   ├── agenda.py            # AGENDA_CATALOG, get_agenda(), refine_agenda()
│   │   ├── execution.py         # _DRUM_PATTERNS, _GENRE_PARAMS, get_execution_plan()
│   │   ├── checkpoint.py        # get_checkpoint(), _infer_completed_phases(), 30s TTL cache
│   │   ├── next_actions.py      # get_next_actions_result(), get_transition_guidance()
│   │   └── phase_detection.py   # _DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES, _COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER
│   ├── genres/                  # Genre blueprint modules (auto-discovered)
│   │   ├── schema.py            # Blueprint schema + validate_blueprint()
│   │   ├── catalog.py           # get_blueprint(), resolve_alias(), list_genres()
│   │   ├── house.py             # GENRE = {...}
│   │   ├── techno.py            # GENRE = {...}
│   │   ├── ambient.py           # GENRE = {...}
│   │   ├── hip_hop_trap.py      # GENRE = {...}
│   │   ├── drum_and_bass.py     # GENRE = {...}
│   │   ├── dubstep.py           # GENRE = {...}
│   │   ├── trance.py            # GENRE = {...}
│   │   ├── synthwave.py         # GENRE = {...}
│   │   ├── future_bass.py       # GENRE = {...}
│   │   ├── lo_fi.py             # GENRE = {...}
│   │   ├── neo_soul_rnb.py      # GENRE = {...}
│   │   └── disco_funk.py        # GENRE = {...}
│   ├── theory/                  # Music theory primitives
│   │   ├── scales.py            # SCALE_CATALOG, get_scale_notes()
│   │   ├── chords.py            # _QUALITY_MAP, build_chord()
│   │   ├── progressions.py      # generate_progression()
│   │   ├── voicing.py           # voice_chord(), spread_voicing()
│   │   ├── rhythm.py            # rhythm helpers
│   │   ├── pitch.py             # pitch/MIDI number utilities
│   │   └── analysis.py          # harmonic analysis helpers
│   ├── mixing/                  # Mix recipes (role × genre)
│   │   ├── catalog.py           # get_recipe(), get_master_recipe(), list_recipes()
│   │   ├── house.py             # Mix recipes for house genre
│   │   ├── techno.py            # ... (one file per genre)
│   │   └── [10 other genre files]
│   ├── evaluation/              # Session quality evaluators
│   │   ├── schema.py            # EvaluationIssue, DimensionScore, SessionScore, grade_from_score()
│   │   ├── mix_balance.py       # evaluate_mix_balance(genre, conn)
│   │   ├── arrangement.py       # evaluate_arrangement(conn)
│   │   ├── harmonic.py          # evaluate_harmonic(conn)
│   │   └── sounds_coverage.py   # evaluate_sounds_coverage(conn)
│   ├── devices/                 # Device parameter catalog and conversion
│   │   ├── catalog.py           # CATALOG dict (generated), ROLES list
│   │   ├── convert.py           # natural_to_normalized(), normalized_to_natural(), convert_recipe_to_payload()
│   │   └── gain_targets.py      # GAIN_TARGETS per role
│   ├── sounds/                  # Instrument profiles
│   │   ├── catalog.py           # get_instrument_profile(), list_instrument_profiles()
│   │   ├── analog.py            # Analog synth profile
│   │   ├── wavetable.py         # Wavetable synth profile
│   │   ├── operator.py          # Operator FM synth profile
│   │   ├── drum_rack.py         # Drum Rack profile
│   │   ├── simpler.py           # Simpler profile
│   │   └── drift.py             # Drift synth profile
│   ├── prompt/                  # Natural-language prompt interpretation
│   │   ├── schema.py            # ProductionBrief TypedDict
│   │   ├── parser.py            # classify_prompt() — genre detection from text
│   │   ├── deriver.py           # derive() — five DERV-* derivation steps → ProductionBrief
│   │   └── lexicon.py           # GROOVE_HINTS and other signal word tables
│   └── refinement/              # Section refinement engine
│       ├── schema.py            # ClipSummary, SectionState, TrackStateEntry TypedDicts
│       ├── interpreter.py       # build_section_refinement_plan()
│       ├── parser.py            # refinement instruction parsing
│       └── lexicon.py           # refinement signal words
├── AbletonMCP_Remote_Script/    # Ableton Control Surface (runs inside Live)
│   ├── __init__.py              # AbletonMCP class, create_instance(), socket server, command dispatch
│   ├── registry.py              # CommandRegistry, @command decorator, build_tables()
│   └── handlers/                # Command handler mixins (one per domain)
│       ├── __init__.py          # Imports all handler modules to trigger @command registration
│       ├── base.py              # ping, get_session_info
│       ├── tracks.py            # track CRUD, COLOR_NAMES palette (70 colors)
│       ├── clips.py             # session clip CRUD, clip properties
│       ├── notes.py             # MIDI note CRUD on clips
│       ├── mixer.py             # volume, pan, mute, solo, arm, sends, gain staging
│       ├── mixer_helpers.py     # _to_db(), _pan_label() — shared utilities (no @command)
│       ├── devices.py           # device CRUD, parameter get/set, apply_recipe, complex device ops
│       ├── transport.py         # tempo, playback, time signature, loop, undo/redo, cue points
│       ├── scenes.py            # scene CRUD, fire_scene
│       ├── browser.py           # browser tree navigation, load_browser_item
│       ├── arrangement.py       # arrangement clip CRUD, get_arrangement_state
│       ├── audio_clips.py       # audio clip properties, warp markers
│       ├── automation.py        # envelope breakpoints
│       ├── routing.py           # input/output routing
│       ├── scaffold.py          # scaffold_tracks, create_locator_at
│       └── grooves.py           # groove amount, swing, clip groove assignment
├── tests/                       # Test suite (pytest)
│   ├── conftest.py              # Shared fixtures (mock Ableton connection)
│   └── test_*.py                # ~50 test files, one per module
├── scripts/                     # Maintenance scripts
│   └── bootstrap_catalog.py    # Generates MCP_Server/devices/catalog.py from live Ableton session
└── .planning/                   # GSD planning artifacts (not production code)
    ├── codebase/                # Architecture docs (this file)
    └── milestones/              # Phase plans and summaries by milestone version
```

## Key File Locations

**Entry Points:**
- `MCP_Server/server.py` line 46: `main()` — starts the MCP server (`mcp.run()`)
- `AbletonMCP_Remote_Script/__init__.py` line 76: `create_instance(c_instance)` — Ableton loads this on startup

**Configuration:**
- `AbletonMCP_Remote_Script/__init__.py` line 72: `DEFAULT_PORT = 9877` — socket port constant
- `MCP_Server/connection.py` lines 16–19: timeout constants (`TIMEOUT_READ`, `TIMEOUT_WRITE`, `TIMEOUT_BROWSER`, `TIMEOUT_PING`)

**Core Communication:**
- `MCP_Server/protocol.py`: `send_message()`, `recv_message()` — length-prefix framing (identical implementations on both sides)
- `MCP_Server/connection.py` line 247: `AbletonConnection.send_command()` — the single MCP-side socket call

**Tool Registration:**
- `MCP_Server/tools/__init__.py` line 3: single import line that triggers all `@mcp.tool()` decorators
- `AbletonMCP_Remote_Script/handlers/__init__.py`: single import line that triggers all `@command()` decorators

**Orchestration:**
- `MCP_Server/orchestration/agenda.py` line 110: `AGENDA_CATALOG` — 12-genre phase ordering dict
- `MCP_Server/orchestration/agenda.py` line 141: `get_agenda()` — primary agenda factory
- `MCP_Server/orchestration/execution.py` line 29: `_DRUM_PATTERNS` — MIDI seed patterns per genre group
- `MCP_Server/orchestration/checkpoint.py` line 134: `get_checkpoint()` — live session state inference
- `MCP_Server/orchestration/phase_detection.py`: all shared phase-detection constants

**Domain Catalogs:**
- `MCP_Server/genres/catalog.py` line 141: `get_agenda()` entry; `resolve_alias()` normalizes input
- `MCP_Server/devices/catalog.py`: `CATALOG` dict — generated, maps device class → parameter specs
- `MCP_Server/mixing/catalog.py`: `get_recipe(role, genre)` — mix recipe lookup
- `MCP_Server/evaluation/schema.py` line 43: `grade_from_score()` — A/B/C/D/F thresholds

## Naming Conventions

**Files:**
- `MCP_Server/tools/`: snake_case matching domain noun (e.g., `tracks.py`, `mixer.py`)
- `AbletonMCP_Remote_Script/handlers/`: snake_case matching domain noun (mirrors tools/)
- Test files: `test_{module_name}.py` in `tests/`

**Functions:**
- MCP tools: lowercase verbs matching the `@mcp.tool()` registered name (e.g., `get_track_info`, `create_midi_track`)
- Remote Script handlers: underscore-prefixed to signal non-public (e.g., `_get_track_info`, `_create_midi_track`)
- Domain module entry points: verbs without prefix (e.g., `get_agenda()`, `get_checkpoint()`, `derive()`)

**Classes:**
- `AbletonConnection` (dataclass) — MCP-side socket client
- `AbletonMCP` (ControlSurface subclass) — Remote Script main class
- `CommandRegistry` — registry singleton; handler classes are all named `*Handlers`

**TypedDicts:**
- PascalCase matching the concept: `ProductionAgenda`, `ProductionPhase`, `ExecutionStep`, `PhaseChecklist`, `ProductionCheckpoint`, `SessionStats`, `EvaluationIssue`, `DimensionScore`, `SessionScore`, `ProductionBrief`

**Constants:**
- `UPPERCASE_SNAKE` for module-level catalogs and sets: `AGENDA_CATALOG`, `SCALE_CATALOG`, `CATALOG`, `_DRUM_NAMES`, `_WRITE_COMMANDS`, `_BROWSER_COMMANDS`

## Where to Add New Code

**New MCP Tool (live Ableton command):**
- Add handler method to appropriate `AbletonMCP_Remote_Script/handlers/*.py` with `@command("cmd_name", write=True)` or `@command("cmd_name")`
- Add the command name to `_WRITE_COMMANDS` or `_BROWSER_COMMANDS` set in `MCP_Server/connection.py` if it needs a non-default timeout
- Add `@mcp.tool()` function in the matching `MCP_Server/tools/*.py` file calling `get_ableton_connection().send_command("cmd_name", params)`
- Add test in `tests/test_{domain}.py`

**New MCP Tool (pure Python, no socket):**
- Add `@mcp.tool()` function in the appropriate `MCP_Server/tools/*.py`
- Implement logic in the matching domain module under `MCP_Server/{domain}/`
- No changes needed to Remote Script or connection layer

**New Genre Blueprint:**
- Add `MCP_Server/genres/{genre_id}.py` with `GENRE = {...}` following the structure in `genres/schema.py`
- Add the genre id to `MCP_Server/orchestration/agenda.py:AGENDA_CATALOG`
- Add mix recipes in `MCP_Server/mixing/{genre_id}.py` following existing pattern
- Auto-discovered at runtime — no imports to update

**New Orchestration Phase Type:**
- Add the phase type to `_ESTIMATED_STEPS`, `_PHASE_GOALS`, `_PHASE_NAMES` in `orchestration/agenda.py`
- Add phase-completion heuristics in `orchestration/checkpoint.py:_infer_completed_phases()`
- Add transition gate logic in `orchestration/next_actions.py:_phase_complete()`
- Update phase order in all relevant entries in `AGENDA_CATALOG`

**New Evaluation Dimension:**
- Add evaluator module in `MCP_Server/evaluation/{dimension}.py` returning `DimensionScore`
- Import and call in `MCP_Server/tools/evaluation.py:evaluate_session()` via `_run_evaluator()`

## Special Directories

**`MCP_Server/devices/`:**
- `catalog.py` is **generated** — run `scripts/bootstrap_catalog.py` against a live Ableton session to regenerate after Ableton version upgrade
- Do not edit `catalog.py` manually

**`tests/`:**
- All tests use `pytest`; mock Ableton connection via `conftest.py` fixtures
- `live_uat_07.py` is a manual UAT script (not run in CI), requires live Ableton

**`.planning/`:**
- Not production code — GSD planning artifacts only
- `milestones/` contains phase plans (`*-PLAN.md`) and summaries (`*-SUMMARY.md`) organized by version milestone

---

*Structure analysis: 2026-04-02*
