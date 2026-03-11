# Project Research Summary

**Project:** Ableton Live 12 MCP Server (ableton-mcp)
**Domain:** DAW control API — AI assistant bridge to Ableton Live via Remote Scripts
**Researched:** 2026-03-10
**Confidence:** HIGH

## Executive Summary

This project is a brownfield extension of an existing MCP server that bridges Claude AI to Ableton Live 12 via a two-layer architecture: a FastMCP server (Python) receiving tool calls from Claude, and an Ableton Remote Script (Python 3.11, embedded in Live) exposing the Live Object Model over a TCP socket. The existing codebase has ~15 working tools covering a narrow slice of what is needed, plus instrument loading which is silently broken. Research across four domains confirms that the architectural approach is sound and well-precedented (AbletonOSC and Ziforge's liveapi-tools demonstrate the same pattern at production scale), but the codebase has accumulated enough structural technical debt that new features cannot be added safely without first establishing proper foundations.

The recommended approach is to address the project in three clear phases: (1) fix foundational correctness issues — the broken instrument loading, Python 2 dead code, thread safety gaps, and error-swallowing bare excepts — before any feature expansion; (2) expand the Live API coverage to match production-level expectations, covering all track types, clip editing, mixing, scenes, and device parameters; (3) implement advanced capabilities (automation envelopes, rack navigation, arrangement view) that differentiate from competing implementations. The most important single decision is to refactor the Remote Script from a monolithic `__init__.py` with a growing `if/elif` dispatch chain to a `handlers/` package with a dict-based router before adding commands, as the current structure will not scale beyond its current 15 commands without becoming unmaintainable.

The primary risks are well-understood and have documented solutions. Instrument loading is broken due to a known race condition between `selected_track` assignment and `browser.load_item()` on the main thread. The `if/elif` dispatch chain will become unmanageable at 50+ tools. The global connection singleton has a race condition under concurrent Claude tool calls. All six critical pitfalls identified have clear, specific fixes that should be implemented in Phase 1 before any new functionality is added. Research confidence is HIGH across all four areas — the Live Object Model is well-documented by community sources, and the architectural patterns are validated by production implementations.

## Key Findings

### Recommended Stack

The stack is fundamentally correct and does not need to change. The MCP server uses `mcp[cli]` 1.26.0 (official Anthropic SDK, FastMCP included) over stdio transport, managed by `uv`. The Remote Script runs inside Ableton's embedded Python 3.11 interpreter using only stdlib (`socket`, `threading`, `queue`, `json`) — no third-party packages are permitted. The primary stack fix needed is stripping Python 2 compatibility code (`from __future__`, `try: import Queue`, `except AttributeError` on `decode()`) which is dead code in Live 12 and masks real bugs. Testing infrastructure (`pytest`, `pytest-asyncio`, `ruff`) should be established immediately — zero test coverage is the root cause of multiple silent regressions.

**Core technologies:**
- `mcp[cli]` 1.26.0: MCP SDK with FastMCP — provides tool decorators, lifespan manager, stdio transport
- Python 3.11 (Remote Script): Ableton Live 12's embedded interpreter — stdlib only, no pip installs
- `socket` + `threading` + `queue` (stdlib): TCP server inside Ableton — must never use asyncio
- `uv`: Package management for the MCP server side — already adopted
- `pytest` + `pytest-asyncio` + `ruff`: Test and lint infrastructure — must be added; zero tests currently exist
- Length-prefix framing (`struct.pack(">I", len(payload))`): Protocol upgrade replacing O(n²) chunk re-parsing

**Critical stack constraint:** The Remote Script must use blocking sockets in daemon threads, with all Live API mutations dispatched via `schedule_message()`. Asyncio is not compatible with Ableton's event model.

### Expected Features

The existing 15 tools cover basic MIDI track/clip creation and playback, but the gap to a production-level server is substantial. Instrument loading — the one feature that makes MIDI clips produce sound — is silently broken and must be fixed first. Competitor analysis shows that Ziforge's liveapi-tools (the most comprehensive implementation, 220 tools) sets the production bar. The recommended v1 expands to approximately 35 tools covering all P1 features, with v1.x adding P2 tools and v2+ tackling the high-complexity items.

**Must have (table stakes for v1):**
- Fix instrument loading — critical path blocker; everything else depends on MIDI producing audio
- Create audio track, return track, group track — complete track type coverage
- Delete track, duplicate track — AI will create wrong tracks
- Track volume / pan / mute / solo / arm — core mixing controls (currently read-only)
- Send levels — route tracks to reverb/delay on returns
- Get clip notes, remove notes from clip — MIDI editing loop requires both read and write
- Clip loop settings (looping, loop_start, loop_end) — all clips loop
- Scene create / name / fire / delete — Session View is primary workflow
- Get device parameters / set device parameter — adjust synth and effect parameters
- Undo / redo — safety net for AI mistakes (non-negotiable)
- Stop all clips, continue playback — session control

**Should have (v1.x differentiators):**
- Bulk session state query — reduces round-trips from ~20 commands to 1; AI context efficiency
- Quantize clip notes, MIDI note transpose — timing and harmonic corrections
- Clip pitch / gain / warp — audio clip control
- Cue point management — arrangement navigation
- Track routing control — advanced signal flow
- Scene color / tempo, track color — organization features

**Defer to v2+:**
- Clip automation envelopes — high value but requires careful API design
- Device chain / rack navigation — Drum Rack, Instrument Rack traversal is complex
- Arrangement clip creation — may be impossible via standard API paths; needs research
- Clip follow actions — generative music use case; complex parameter surface

**Explicit anti-features (do not implement):**
- Audio export / render — not in Live Python API; OS automation is brittle
- Real-time audio input processing — MCP latency makes this impractical
- Parameter listeners / pub-sub push — requires architectural overhaul; polling is sufficient
- Multi-session management — one Live instance per server by design

### Architecture Approach

The system is a two-layer bridge with a strict threading contract: the MCP server (Claude-facing) communicates over JSON-over-TCP with the Remote Script (Ableton-facing), which runs Live API calls exclusively on Ableton's main thread via `schedule_message()`. The current monolithic structure (`__init__.py` containing all handlers, `server.py` containing all tools) must be refactored into domain-separated modules before feature expansion. AbletonOSC (the production reference implementation) uses exactly this structure — `handlers/` package with one file per LOM object type. The critical architectural insight is that the dict-based command router and the `@main_thread` decorator should be the first things built; all subsequent feature work then follows a simple, mechanical pattern.

**Major components:**
1. `MCP_Server/server.py` + `tools/*.py` — FastMCP instance, lifespan, AbletonConnection singleton, domain tool modules
2. `AbletonMCP_Remote_Script/__init__.py` + `server.py` — ControlSurface entry, socket server on daemon thread, dict-based command dispatcher
3. `AbletonMCP_Remote_Script/handlers/*.py` — Domain handlers (tracks, clips, notes, devices, mixer, scenes, browser, arrangement, automation), all extending `BaseHandler`
4. `AbletonConnection` (module-level singleton) — TCP socket lifecycle, length-prefix framing, reconnect logic, `threading.Lock` protection

**Key patterns to follow:**
- Dict-based command router (replaces `if/elif` chain) — O(1) dispatch, one-line registration per command
- `@main_thread` decorator (centralizes `schedule_message` + `queue.Queue` boilerplate) — all mutating handlers get this
- Length-prefix framing (4-byte big-endian length header) — replaces O(n²) JSON re-parsing
- Read/write classification by command name prefix — eliminates manual `is_modifying_command` list

### Critical Pitfalls

1. **`browser.load_item` targets selected UI track, not the track parameter** — Perform `selected_track` assignment and `load_item` in the same synchronous callback, then verify `len(track.devices)` increased before returning success. This is the root cause of instrument loading being broken.

2. **`schedule_message` + `queue.get` deadlock when Ableton is backgrounded or main thread is busy** — Use a 30-second timeout for browser/instrument operations (not 10s), detect main-thread context before scheduling, and after a timeout issue `get_track_info` to check actual state rather than assuming failure.

3. **Recursive browser tree traversal blocks Ableton main thread** — Cache URI-to-item mappings after first lookup; scope search by URI category prefix; never traverse more than 2 levels without a filter. Full library traversal takes several seconds and freezes Ableton's UI.

4. **Bare `except: pass` swallows all errors including crashes** — Replace with `except Exception as e: self.log_message(f"[UNEXPECTED] {e}\n{traceback.format_exc()}")`. This is the primary reason silent failures appear as false successes. Six locations in the codebase require fixing.

5. **Global `_ableton_connection` is not thread-safe under concurrent Claude tool calls** — Wrap all reads/writes with `threading.Lock()`. Replace the empty-send liveness test with a real ping command (`get_session_info`).

6. **`'nstruments'` typo silently breaks browser path navigation** — Replace string comparison with a dictionary dispatch: `{"instruments": browser.instruments, "sounds": browser.sounds, ...}`. No test catches this because there are zero tests.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation Repair
**Rationale:** Every critical pitfall identified applies to the current codebase. Silent error swallowing means failures are invisible. The thread safety bug means parallel Claude tool calls can crash the session. The instrument loading bug means MIDI clips produce no sound. None of this can be deferred — adding new features on top of a broken foundation makes debugging impossible and erodes user trust immediately.
**Delivers:** A server where failures are visible, instrument loading works reliably, and concurrent tool calls do not crash.
**Addresses:** Fix instrument loading (P1), undo/redo (low-hanging fruit to add while in the code)
**Avoids all six critical pitfalls:** browser.load_item race, schedule_message deadlock, browser traversal freeze, bare except swallowing, connection race condition, instruments typo

**Concrete tasks:**
- Strip all Python 2 compat code (`__future__`, `Queue as queue`, `decode()` try/except)
- Replace all bare `except: pass` with exception logging
- Fix `_get_browser_item` instruments typo with dict dispatch
- Fix instrument loading: same-callback `selected_track` + `load_item`, deferred device verification
- Add `threading.Lock` to `AbletonConnection` global
- Upgrade socket framing to length-prefix (4-byte header)
- Add `pytest` + `pytest-asyncio` + `ruff` to dev dependencies
- Write smoke tests for instrument loading and browser navigation

### Phase 2: Infrastructure Refactor
**Rationale:** The `if/elif` dispatch chain at 15 commands is already 60+ lines. Adding 20+ new commands in Phase 3 without refactoring first would produce a 300-line dispatch function that is not maintainable. This phase builds the scaffolding — one architectural investment that makes all subsequent phases mechanical.
**Delivers:** `handlers/` package structure, dict-based router, `@main_thread` decorator, `tools/` module split — ready to accept 50+ commands without structural debt.
**Uses:** Dict command router pattern, `@main_thread` decorator, FastMCP direct-import tool composition
**Implements:** Full domain separation mirroring AbletonOSC's handler structure

**Concrete tasks:**
- Extract `handlers/` package: `base.py`, `transport.py`, `tracks.py`, `clips.py`, `notes.py`, `devices.py`, `mixer.py`, `scenes.py`, `browser.py`
- Implement `BaseHandler` with `@main_thread` decorator and index validation helpers
- Replace `if/elif` chain with `CommandDispatcher` dict-based router
- Split `MCP_Server/server.py` into `tools/` domain modules
- Add command name prefix classification (`READ_PREFIXES`, `WRITE_PREFIXES`)

### Phase 3: Core Feature Expansion (v1)
**Rationale:** With a clean, testable foundation and extensible architecture, P1 features can be added rapidly — each feature is a handler method + dict entry + tool function. This phase targets "production floor" — a server that can create a fully playable, multi-instrument session with basic mixing.
**Delivers:** ~35 tools covering all track types, full clip editing, mixing, scenes, device parameters, and undo. Matches or exceeds uisato/ableton-mcp-extended.
**Features:** All P1 items from FEATURES.md — audio/return/group tracks, delete track, track volume/pan/mute/solo/arm, send levels, get/remove clip notes, clip loop settings, scene management, device parameters, undo/redo, stop all clips, continue playback

**Concrete tasks (grouped by handler):**
- TrackHandler: `create_audio_track`, `create_return_track`, `create_group_track`, `delete_track`, `duplicate_track`
- MixerHandler: `set_track_volume`, `set_track_pan`, `set_send_level`, write mute/solo/arm
- ClipHandler: `delete_clip`, `get_clip_notes`, `remove_clip_notes`, clip loop settings
- SceneHandler: `create_scene`, `delete_scene`, `fire_scene`, `set_scene_name`
- DeviceHandler: `get_device_parameters`, `set_device_parameter` (fix load_browser_item)
- TransportHandler: `undo`, `redo`, `continue_playing`, `stop_all_clips`

### Phase 4: Production Quality (v1.x)
**Rationale:** After validating Phase 3 with real use, add the P2 features that distinguish a capable tool from a toy. Bulk state query is the highest leverage — it dramatically reduces the number of tool calls needed for Claude to understand a session.
**Delivers:** Bulk session state dump, MIDI editing utilities, audio clip controls, organization features (colors, cue points), tap tempo.
**Features:** All P2 items — bulk state query, quantize/transpose, clip pitch/gain/warp, track and scene colors, cue points, track routing, tap tempo/metronome

### Phase 5: Advanced Capabilities (v2+)
**Rationale:** High-complexity, high-value features that require their own research phase. Arrangement clip creation may require investigation into Live API limitations. Rack navigation requires recursive traversal with proper error handling. Clip automation envelopes require careful API design to be usable by an AI.
**Delivers:** Features that no other MCP implementation provides reliably — clip automation, full rack traversal, arrangement view editing.
**Features:** Clip automation envelopes, device chain/rack navigation (Drum Rack, Instrument Rack), track freeze/unfreeze, clip follow actions, arrangement clip creation (subject to API feasibility)

### Phase Ordering Rationale

- **Phase 1 before all others:** Six critical pitfalls are active in the current codebase. Instrument loading is the only path to MIDI producing audio. Foundation must be correct before features are added, or every new feature inherits the bugs.
- **Phase 2 before Phase 3:** Attempting to add 20+ commands to the current monolithic `__init__.py` with a growing `if/elif` chain produces a 1000+ line file that cannot be maintained. The refactor costs ~1 phase but pays back across every subsequent phase.
- **Phase 3 before Phase 4:** P1 features must be validated in real sessions before P2 features are added. User feedback on the core loop (create track → load instrument → add notes → mix) will surface requirements that weren't anticipated.
- **Phase 5 as a separate undertaking:** Arrangement clip creation needs a research spike before implementation — the Live API may not support it cleanly. Rack navigation requires distinct error handling design. These should be planned separately from the feature expansion phases.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (Advanced Capabilities):** Arrangement clip creation is documented as potentially impossible via standard Remote Script API — needs a verification spike before committing to a phase. Clip automation envelopes require understanding the distinction between Session and Arrangement envelopes.
- **Phase 4 (Track routing):** Input/output routing APIs vary by track type and depend on Ableton's audio driver configuration — needs testing against actual hardware before implementation.

Phases with standard, well-documented patterns (skip research-phase):
- **Phase 1:** All bugs are known, all fixes are documented. Pure execution.
- **Phase 2:** Dict router + decorator + module split are standard patterns with examples in AbletonOSC and Ziforge. No unknown territory.
- **Phase 3:** Every P1 feature maps directly to documented Live API methods. No ambiguity.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core stack verified via official PyPI and GitHub releases. Python 3.11 constraint confirmed by community sources consistent with codebase `.cpython-311.pyc` evidence. |
| Features | HIGH | Live Object Model is well-documented via AbletonOSC reference, Cycling74 docs, and Structure Void XML. Competitor feature analysis grounded in actual codebases (Ziforge 220 tools, uisato-extended). |
| Architecture | HIGH | Patterns validated by AbletonOSC (production reference) and Ziforge (220 tools, same threading model). FastMCP composition approach verified against official docs. |
| Pitfalls | HIGH | Six critical pitfalls derived from direct codebase analysis + GitHub Issues on the source repo (#74, #47, #37, #27) + community forum threads. Not theoretical — all confirmed in the existing code. |

**Overall confidence:** HIGH

### Gaps to Address

- **Arrangement clip creation feasibility:** The Live Python API may not support creating arrangement clips directly (track.arrangement_clips is read-only). This needs a verification spike in Phase 5 planning — do not commit to this feature without a proof-of-concept first.
- **Ableton 12.x compatibility for browser API:** Ableton has signaled interest in moving away from Python Remote Scripts (Push 3 uses a different model). The browser API has not changed between Live 11 and Live 12, but future Live versions may deprecate parts of the Remote Script interface. Low risk for a 12-month horizon; worth monitoring.
- **FastMCP concurrency model:** FastMCP runs tool handlers in an async context. The current synchronous socket calls inside async tools may have subtle event loop interactions under high concurrency. The connection lock addresses the worst case, but the interaction should be tested with parallel Claude tool invocations before shipping.
- **Test infrastructure for Remote Script:** The Remote Script runs inside Ableton — it cannot be unit tested in isolation without Ableton running. Integration testing requires either a running Live instance or a mock of the Live API. This gap should be addressed with an integration test harness before Phase 3.

## Sources

### Primary (HIGH confidence)
- PyPI: `mcp` 1.26.0 — official Anthropic MCP SDK, FastMCP included
- PyPI: `fastmcp` 3.1.0 — standalone PrefectHQ package (confirmed diverged from official SDK)
- MCP Python SDK releases (github.com/modelcontextprotocol/python-sdk) — v1.26.0 latest 1.x
- FastMCP SDK issue #1068 — Anthropic engineer confirmed "sufficiently diverged" packages
- AbletonOSC (github.com/ideoforms/AbletonOSC) — production reference for LOM coverage and handler architecture
- Ziforge/ableton-liveapi-tools — 220-tool production implementation, same threading model
- Ableton Live 12 MIDI Remote Scripts source (github.com/gluon/AbletonLive12_MIDIRemoteScripts)
- Live Object Model Reference (docs.cycling74.com/legacy/max5/refpages/m4l-ref/m4l_live_object_model.html)
- Structure Void — Live 10.0.1 Python API XML (structure-void.com/PythonLiveAPI_documentation)
- Existing codebase analysis: `.planning/codebase/STACK.md`, `ARCHITECTURE.md`, `CONCERNS.md`, `CONVENTIONS.md`
- Direct source analysis: `AbletonMCP_Remote_Script/__init__.py`, `MCP_Server/server.py`

### Secondary (MEDIUM confidence)
- Ableton Forum thread on Python 3.11 in Live 12 — confirmed via `.cpython-311.pyc` bytecache
- Ableton Forum thread 174043 — threading constraints in Remote Scripts
- GitHub Issues: ahujasid/ableton-mcp #74 (instruments typo), #47 (load_browser_item bug), #37 (instruments not found), #27 (beat creation failures)
- FastMCP server composition docs (gofastmcp.com/servers/composition) — mount vs. direct import patterns

### Tertiary (LOW confidence)
- Ableton export API docs — confirmed export NOT exposed in Remote Script Python API
- Ableton Forum on Live 12 browser API — no changes from Live 11; Push moving away from Python Remote Scripts (future risk, not current)
- AbletonOSC NIME 2023 paper — high-level overview of LOM scope

---
*Research completed: 2026-03-10*
*Ready for roadmap: yes*
