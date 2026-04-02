# Architecture

**Analysis Date:** 2026-04-02

## Pattern Overview

**Overall:** Two-process bridge architecture — a Python MCP server exposes production tools to AI clients; an Ableton Live Remote Script (Python) owns the song object and executes commands inside Live's runtime.

**Key Characteristics:**
- Hard process boundary: MCP server and Ableton run in separate Python interpreters, connected by a TCP socket on `localhost:9877`
- All Ableton Live Object Model (LOM) access is gated through the Remote Script — the MCP server never touches Live APIs directly
- Tool layer and intelligence layer are fully decoupled: MCP tools delegate immediately to either the socket connection (Live commands) or in-process domain modules (theory, genres, orchestration)
- Length-prefix framing (4-byte big-endian uint32 header) provides reliable message boundaries over raw TCP; no HTTP or RPC framework
- Read commands run synchronously on the socket thread; write commands are marshalled onto Ableton's main thread via `schedule_message`

## Layers

**MCP Tool Layer (`MCP_Server/tools/`):**
- Purpose: Thin wrappers that expose named MCP tools to AI clients via `@mcp.tool()` decorators
- Location: `MCP_Server/tools/` — 26 modules
- Contains: One file per domain (tracks, clips, notes, mixer, devices, etc.). Each function calls `get_ableton_connection().send_command(...)` for Live commands, or calls an in-process domain module for pure logic
- Depends on: `MCP_Server/connection.py`, `MCP_Server/server.py` (for `mcp` singleton), domain modules
- Used by: AI client via MCP protocol (FastMCP)

**Connection Layer (`MCP_Server/connection.py`, `MCP_Server/protocol.py`):**
- Purpose: Manages a persistent, singleton TCP connection to the Ableton Remote Script
- Location: `MCP_Server/connection.py` (socket lifecycle, timeout routing), `MCP_Server/protocol.py` (framing)
- Contains: `AbletonConnection` dataclass (line 213), `get_ableton_connection()` factory (line 319), `_timeout_for()` routing (line 202), `format_error()` helper (line 192)
- Key details:
  - Global `_ableton_connection` protected by `threading.Lock` (`_connection_lock`, line 307)
  - `send_command()` acquires `_send_lock` per call — prevents interleaved requests
  - Three timeout tiers: `TIMEOUT_PING=5s`, `TIMEOUT_READ=10s`, `TIMEOUT_WRITE=15s`, `TIMEOUT_BROWSER=30s`
  - Liveness check on reconnect: sends real `ping`, then validates with `get_session_info`
  - Reconnect on any socket error; up to 3 attempts with 1-second delays

**Remote Script Orchestrator (`AbletonMCP_Remote_Script/__init__.py`):**
- Purpose: Ableton Control Surface that runs inside Live's process. Starts a TCP server, accepts clients, dispatches commands
- Location: `AbletonMCP_Remote_Script/__init__.py`
- Contains: `AbletonMCP` class (line 81, inherits `ControlSurface` + all handler mixins), `start_server()` (line 159), `_server_thread()` (line 177), `_handle_client()` (line 210), `_process_command()` (line 245), `_dispatch_write_command()` (line 268)
- Key threading model:
  - `_server_thread`: daemon thread, blocks on `accept()` with 1-second timeout
  - `_handle_client`: one daemon thread per client; loops on `recv_message` → `_process_command` → `send_message`
  - Read commands run inline on the client thread (safe: read-only LOM access)
  - Write commands post a closure to Ableton's main thread via `self.schedule_message(0, task)` and block on `queue.Queue` with 10-second timeout (30 seconds for `self_scheduling` commands)

**Remote Script Handler Layer (`AbletonMCP_Remote_Script/handlers/`):**
- Purpose: Domain-specific command handler mixins composed into `AbletonMCP`
- Location: `AbletonMCP_Remote_Script/handlers/` — 15 domain files + `mixer_helpers.py`
- Files: `arrangement.py`, `audio_clips.py`, `automation.py`, `base.py`, `browser.py`, `clips.py`, `devices.py`, `grooves.py`, `mixer.py`, `notes.py`, `routing.py`, `scaffold.py`, `scenes.py`, `tracks.py`, `transport.py`
- Contains: Methods decorated with `@command(name)` (read) or `@command(name, write=True)` (main-thread)
- Depends on: `AbletonMCP_Remote_Script/registry.py`, Ableton `_Framework` APIs, `self._song`

**Command Registry (`AbletonMCP_Remote_Script/registry.py`):**
- Purpose: Decorator-based handler registration, decoupled from `AbletonMCP` instantiation
- Location: `AbletonMCP_Remote_Script/registry.py`
- Pattern: `@command("cmd_name")` appends `(name, method_name, is_write, is_self_sched)` to `CommandRegistry._entries` at import time. `build_tables(instance)` at `__init__` (line 49) binds methods and returns `(read_commands, write_commands, self_scheduling)` dicts.
- Three command categories: read (socket thread), write (main thread via queue), self_scheduling (handler manages its own `schedule_message` calls)

**Orchestration Layer (`MCP_Server/orchestration/`):**
- Purpose: Pure-Python production workflow engine — no Ableton socket calls except in checkpoint/next_actions
- Location: `MCP_Server/orchestration/` — 6 modules
- Files: `agenda.py` (genre phase ordering + `refine_agenda`), `execution.py` (phase step catalogs with MIDI seed patterns), `checkpoint.py` (live session state inference, 30-second TTL cache), `next_actions.py` (step filter + transition gate), `phase_detection.py` (shared heuristic constants), `schema.py` (TypedDicts)
- Key schemas in `schema.py`: `ProductionAgenda`, `ProductionPhase`, `ExecutionStep`, `PhaseChecklist`, `ProductionCheckpoint`, `SessionStats`

**Domain Intelligence Modules:**
- `MCP_Server/genres/` — 12 genre blueprint modules auto-discovered via `pkgutil.iter_modules`. `catalog.py` provides `get_blueprint()`, `resolve_alias()`, `list_genres()`
- `MCP_Server/theory/` — Music theory primitives: `scales.py`, `chords.py`, `progressions.py`, `voicing.py`, `rhythm.py`, `pitch.py`, `analysis.py`
- `MCP_Server/mixing/` — Mix recipes per role × genre: `catalog.py` provides `get_recipe()`, `get_master_recipe()`, `list_recipes()`
- `MCP_Server/evaluation/` — Four evaluators: `mix_balance.py`, `arrangement.py`, `harmonic.py`, `sounds_coverage.py` + `schema.py`
- `MCP_Server/sounds/` — Instrument profiles: `analog.py`, `wavetable.py`, `operator.py`, `drum_rack.py`, `simpler.py`, `drift.py`
- `MCP_Server/devices/` — Device parameter catalog: `catalog.py` (generated by `scripts/bootstrap_catalog.py`), `convert.py` (natural↔normalized value conversion), `gain_targets.py`
- `MCP_Server/prompt/` — NL prompt parsing: `parser.py` (genre classification), `deriver.py` (`derive()` → `ProductionBrief`), `lexicon.py`, `schema.py`
- `MCP_Server/refinement/` — Section refinement: `interpreter.py`, `parser.py`, `lexicon.py`, `schema.py`

## Data Flow

**AI Tool Call → Ableton Live (write command):**

1. AI client calls an MCP tool (e.g., `create_midi_track(index=-1)`)
2. `@mcp.tool()` function in `MCP_Server/tools/tracks.py` (line 34) calls `get_ableton_connection()` → returns or creates `AbletonConnection` singleton
3. `AbletonConnection.send_command("create_midi_track", {"index": -1})` acquires `_send_lock`, serializes to JSON with 4-byte length header via `protocol.send_message()`
4. Remote Script's `_handle_client` thread receives via `recv_message()`, calls `_process_command()`
5. Command found in `_write_commands` → `_dispatch_write_command()` posts closure to Ableton main thread via `schedule_message(0, task)`, blocks on `queue.Queue.get(timeout=10.0)`
6. Main thread executes handler, puts `{"status": "success", "result": {...}}` on queue
7. Client thread reads queue result, sends back via `send_message()` with length-prefix framing
8. MCP server reads response, returns `result` dict to tool function
9. Tool function serializes to JSON string, returns to AI client

**AI Tool Call → Pure Logic (no socket):**

1. AI calls `get_production_agenda(genre="house")`
2. `MCP_Server/tools/orchestration.py` (line 13) calls `orchestration/agenda.get_agenda("house", None)`
3. `get_agenda` looks up `AGENDA_CATALOG["house"]`, fetches blueprint from `genres.catalog.get_blueprint()`, builds `ProductionAgenda` TypedDict
4. Returns JSON string — no socket involved

**Checkpoint / Next Actions (hybrid flow):**

1. `get_production_checkpoint(genre="house")` calls `orchestration/checkpoint.get_checkpoint("house")`
2. Checks 30-second TTL cache (`_checkpoint_cache` dict, keyed by genre)
3. On cache miss: two socket round-trips — `conn.send_command("get_arrangement_state")` and `conn.send_command("get_mix_state")`
4. `_infer_completed_phases()` walks `AGENDA_CATALOG` phase order, checking track name heuristics (`_DRUM_NAMES`, `_BASS_NAMES`, etc. from `phase_detection.py`) and device class names (`Compressor2`, `GlueCompressor`, `Limiter2`)
5. Returns `ProductionCheckpoint` TypedDict, cached for 30 seconds per genre key

**Prompt → Production Plan:**

1. `interpret_prompt_to_plan(text)` calls `prompt/deriver.derive(text)`
2. `derive()` calls `prompt/parser.classify_prompt()` for genre detection, then runs five DERV-* derivation steps (tempo, key, groove, instruments, velocity) against genre blueprint
3. Returns `ProductionBrief` dict; tool then calls `_build_plan_sections()` to expand blueprint arrangement sections
4. Combined result (brief + plan) returned as JSON — no socket calls

**Mix Recipe Application:**

1. `apply_mix_recipe(track_index, role, genre)` looks up recipe via `mixing/catalog.get_recipe(role, genre)`
2. Converts natural-unit values to normalized via `devices/convert.convert_recipe_to_payload(recipe)`
3. Sends single `apply_recipe` command to Remote Script with full device payload (load + set params atomically)
4. Timeout scales with device count: `max(30.0, len(devices) * 15.0)` seconds

## Key Abstractions

**`AbletonConnection` (dataclass, `MCP_Server/connection.py` line 213):**
- Singleton TCP connection with per-call timeout routing and thread-safe `_send_lock`
- `get_ableton_connection()` factory function with global `_connection_lock`; liveness-tested (ping + session_info) on each access

**`@mcp.tool()` (FastMCP decorator, `MCP_Server/server.py` line 40):**
- Registers Python functions as named MCP tools exposed to AI clients
- Import side-effect: all tools registered when `import MCP_Server.tools` executes at server startup (line 43)

**`@command(name, write=False, self_scheduling=False)` (decorator, `registry.py` line 33):**
- Registers Remote Script handler methods at class import time
- Class-level list `CommandRegistry._entries` populated by decorators; bound to instance in `AbletonMCP.__init__` via `build_tables(self)` (line 119)

**`ProductionAgenda` / `PhaseChecklist` / `ProductionCheckpoint` (TypedDicts, `orchestration/schema.py`):**
- Typed JSON-serializable structures flowing between orchestration tools and AI clients
- TypedDicts throughout — no `.asdict()` calls needed; direct `json.dumps()`

**Genre Blueprints (`MCP_Server/genres/*.py`):**
- Each module defines a `GENRE = {...}` dict with `id`, `name`, `bpm_range`, `instrumentation`, `harmony`, `rhythm`, `arrangement`, `mixing`, `production_tips`
- Auto-discovered at first catalog access via `pkgutil.iter_modules`; validated by `genres/schema.py:validate_blueprint()`; alias resolution normalizes spaces/hyphens/case

**`ExecutionStep` (TypedDict, `orchestration/schema.py` line 36):**
- `tool_name`: exact registered MCP tool name; `suggested_args`: dict with sentinel strings (e.g., `"<track_index>"`) for session-state values resolved at runtime

## Entry Points

**MCP Server:**
- Location: `MCP_Server/server.py` line 46 (`main()`)
- Triggers: `mcp.run()` — starts FastMCP server (stdio or SSE transport)
- Responsibilities: Creates `FastMCP("AbletonMCP")` singleton, attaches lifespan (connect/disconnect), imports `MCP_Server.tools` to trigger all `@mcp.tool()` registrations

**Remote Script:**
- Location: `AbletonMCP_Remote_Script/__init__.py` line 76 (`create_instance(c_instance)`)
- Triggers: Called by Ableton Live when loading the Control Surface from Preferences → Link/Tempo/MIDI
- Responsibilities: Instantiates `AbletonMCP`, builds dispatch tables from registry, starts TCP socket server on port 9877

## Error Handling

**Strategy:** Errors surface to AI clients as formatted strings via `format_error(message, detail, suggestion)` from `MCP_Server/connection.py` line 192 — not as exceptions.

**Patterns:**
- All MCP tool functions wrap logic in `try/except Exception`, return `format_error(...)` on failure
- Socket errors (timeout, broken pipe, JSON decode) reset `self.sock = None` in `AbletonConnection.send_command()` — forces reconnect on next call
- Remote Script handler exceptions caught in `_process_command()` and returned as `{"status": "error", "message": str(e)}` — socket loop never crashes
- `evaluate_session` evaluators individually wrapped by `_run_evaluator()` — one failed evaluator returns score 0.0 but does not abort the composite result
- Genre blueprint import errors logged and skipped; bad modules do not crash server startup

## Cross-Cutting Concerns

**Logging:**
- MCP server: `logging.getLogger("AbletonMCPServer")` throughout `MCP_Server/`
- Remote Script: `self.log_message()` (Ableton ControlSurface API) → Ableton log file

**Thread Safety:**
- MCP side: `_connection_lock` guards global connection singleton; `_send_lock` inside `AbletonConnection` serializes socket writes
- Remote Script side: read commands safe on socket thread; write commands cross to main thread via `schedule_message` + `queue.Queue`

**Validation:**
- Genre blueprints validated at discovery time; malformed modules logged and skipped
- Tool parameters validated inline; no shared validation middleware

**Caching:**
- Checkpoint cache: `_checkpoint_cache` in `orchestration/checkpoint.py`, 30-second TTL per genre key; invalidated by `invalidate_checkpoint_cache()`
- Browser path cache: `_browser_path_cache` on `AbletonMCP` instance, cleared on disconnect

---

*Architecture analysis: 2026-04-02*
