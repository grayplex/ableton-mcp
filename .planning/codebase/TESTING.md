# Testing Patterns

**Analysis Date:** 2026-04-02

## Test Framework

**Runner:**
- pytest 8.3+
- Config: `pyproject.toml` `[tool.pytest.ini_options]`

**Key pytest settings:**
```toml
asyncio_mode = "auto"   # all async tests run without @pytest.mark.asyncio
testpaths = ["tests"]
timeout = 10            # 10-second per-test timeout via pytest-timeout
```

**Plugins required:**
- `pytest-asyncio >= 0.25` — `asyncio_mode = "auto"` is set globally
- `pytest-timeout >= 2.0` — per-test timeout enforcement

**Run Commands:**
```bash
pytest                          # Run all tests
pytest tests/test_theory.py     # Run single file
pytest -k "test_checkpoint"     # Run matching tests by name
pytest -x                       # Stop on first failure
pytest --tb=short               # Shorter tracebacks
```

No coverage tooling configured (no `pytest-cov` in dev dependencies). Total: ~1074 test functions
across 46 collected test files (plus `live_uat_07.py` which is excluded from collection).

## Test File Organization

**Location:** All tests in `tests/` flat directory — no subdirectories.

**Naming:** `test_<domain>.py` mirrors the module under test:
- `tests/test_theory.py` → `MCP_Server/tools/theory.py` + `MCP_Server/theory/`
- `tests/test_checkpoint.py` → `MCP_Server/orchestration/checkpoint.py`
- `tests/test_genres.py` → `MCP_Server/genres/`
- `tests/test_tracks.py` → `MCP_Server/tools/tracks.py`

**Special files:**
- `tests/conftest.py` — shared fixtures (`mock_connection`, `mcp_server`, `root_dir`)
- `tests/live_uat_07.py` — live integration UAT (not prefixed `test_`, excluded from pytest collection)
- `tests/__init__.py` — empty, marks `tests/` as a package

## Test Categories

### 1. Pure-Computation Tests (no mocking, no fixtures)

Test library functions directly. No MCP, no socket connection, no `conftest.py` fixtures.
Import from sub-packages, not from `MCP_Server/tools/`.

**Files:**
- `tests/test_theory.py` (2278 lines) — tests `MCP_Server/theory/` functions: pitch, chords, scales, voicing, rhythm
- `tests/test_genres.py` (736 lines) — tests `MCP_Server/genres/` schema, catalog, alias resolution
- `tests/test_mixing.py` (562 lines) — tests `MCP_Server/mixing/` recipes, auto-discovery, validation
- `tests/test_sounds.py` (408 lines) — tests `MCP_Server/sounds/` instrument catalog
- `tests/test_protocol.py` — tests `MCP_Server/protocol.py` socket framing
- `tests/test_convert.py` — tests `MCP_Server/devices/convert.py` parameter normalization
- `tests/test_catalog.py` — tests `MCP_Server/devices/catalog.py` device/role catalog

**Pattern:**
```python
class TestPitchLibrary:
    def test_midi_to_note_middle_c(self):
        result = midi_to_note(60)
        assert result == {"midi": 60, "name": "C4", "octave": 4, "pitch_class": "C"}

    def test_roundtrip_all_128(self):
        for i in range(128):
            note_info = midi_to_note(i)
            back = note_to_midi(note_info["name"])
            assert back["midi"] == i
```

### 2. Connection-Mocking Tests (patch `get_ableton_connection`)

Test orchestration functions that call Ableton. Use local `_make_conn` helper and `patch`.
Import directly from the orchestration or library layer, not from `MCP_Server/tools/`.

**Files:**
- `tests/test_checkpoint.py` — tests `MCP_Server/orchestration/checkpoint.py`
- `tests/test_next_actions.py` — tests `MCP_Server/orchestration/next_actions.py`
- `tests/test_evaluate_session.py` — tests `MCP_Server/tools/evaluation.py`
- `tests/test_intelligence.py` — tests `MCP_Server/tools/intelligence.py`
- `tests/test_analysis.py` — tests `MCP_Server/tools/analysis.py` including private helpers

**Pattern:**
```python
with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
           return_value=_make_conn(arr, mix)):
    result = get_checkpoint("house")
assert result["completed_phases"] == []
assert result["active_phase"] == "setup"
```

### 3. MCP Integration Tests (use `mcp_server` + `mock_connection` fixtures)

Test the full tool-dispatch path via `mcp_server.call_tool(...)`. These call through
`MCP_Server/tools/` → `get_ableton_connection()` → `send_command()`. The `mock_connection`
fixture patches all `_GAC_PATCH_TARGETS` at once.

**Files:**
- `tests/test_tracks.py` (331 lines) — all track CRUD tools
- `tests/test_transport.py` (297 lines) — all transport, scale, cue, capture, session tools
- `tests/test_clips.py` (327 lines) — all clip management tools
- `tests/test_mixer.py` — mixing control tools
- `tests/test_devices.py` (785 lines) — all 34+ device and LOM-gap tools
- `tests/test_session.py`, `tests/test_browser.py`, `tests/test_routing.py`
- `tests/test_arrangement.py`, `tests/test_automation.py`, `tests/test_scenes.py`
- `tests/test_grooves.py`, `tests/test_scaffold.py`, `tests/test_execution.py`
- `tests/test_audio_clips.py`, `tests/test_notes.py`

**Pattern:**
```python
async def test_create_midi_track_calls_send_command(mcp_server, mock_connection):
    """create_midi_track invokes send_command and returns JSON."""
    mock_connection.send_command.return_value = {"name": "MIDI Track", "index": 0, "type": "midi"}
    result = await mcp_server.call_tool("create_midi_track", {"index": -1})
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "MIDI Track"
    mock_connection.send_command.assert_called_once_with(
        "create_midi_track", {"index": -1}
    )
```

Response extraction: `result[0][0].text` — the FastMCP `call_tool` response is a nested list
of content objects; `.text` gives the raw JSON string.

### 4. Thread Safety / Concurrency Tests

Use `unittest.TestCase` classes with `threading` directly. No pytest fixtures required.

**File:** `tests/test_connection_thread_safety.py`

**Pattern:** Two threads attempt `send_command` concurrently; mock `send_message` captures a call
log and a `threading.Event` synchronizes timing. Asserts log is `["send","recv","send","recv"]`
(not `["send","send",...]`), proving `_send_lock` serializes concurrent I/O.

## Shared Fixtures (`tests/conftest.py`)

### `mcp_server`

Returns the live `FastMCP` instance from `MCP_Server.server`:

```python
@pytest.fixture
def mcp_server():
    from MCP_Server.server import mcp
    return mcp
```

### `mock_connection`

Patches `get_ableton_connection` in every tool module and orchestration module that imports it.
Returns a `MagicMock` with `send_command.return_value = {}` by default.

```python
@pytest.fixture
def mock_connection():
    mock = MagicMock()
    mock.send_command.return_value = {}
    patches = [patch(target, return_value=mock) for target in _GAC_PATCH_TARGETS]
    for p in patches:
        p.start()
    try:
        yield mock
    finally:
        for p in patches:
            p.stop()
```

### `root_dir`

Returns the project root path string. Used in tests that read fixture JSON files from disk.

## `_GAC_PATCH_TARGETS` — The Ableton Socket Mock

`_GAC_PATCH_TARGETS` in `tests/conftest.py` (lines 11-36) is the authoritative list of 24
import paths for `get_ableton_connection`. The full list is:

```python
_GAC_PATCH_TARGETS = [
    "MCP_Server.connection.get_ableton_connection",
    "MCP_Server.tools.automation.get_ableton_connection",
    "MCP_Server.tools.audio_clips.get_ableton_connection",
    "MCP_Server.tools.session.get_ableton_connection",
    "MCP_Server.tools.tracks.get_ableton_connection",
    "MCP_Server.tools.clips.get_ableton_connection",
    "MCP_Server.tools.transport.get_ableton_connection",
    "MCP_Server.tools.devices.get_ableton_connection",
    "MCP_Server.tools.browser.get_ableton_connection",
    "MCP_Server.tools.mixer.get_ableton_connection",
    "MCP_Server.tools.notes.get_ableton_connection",
    "MCP_Server.tools.routing.get_ableton_connection",
    "MCP_Server.tools.scenes.get_ableton_connection",
    "MCP_Server.tools.arrangement.get_ableton_connection",
    "MCP_Server.tools.grooves.get_ableton_connection",
    "MCP_Server.tools.scaffold.get_ableton_connection",
    "MCP_Server.tools.execution.get_ableton_connection",
    "MCP_Server.tools.mixing.get_ableton_connection",
    "MCP_Server.tools.analysis.get_ableton_connection",
    "MCP_Server.orchestration.checkpoint.get_ableton_connection",
    "MCP_Server.orchestration.next_actions.get_ableton_connection",
    "MCP_Server.tools.evaluation.get_ableton_connection",
    "MCP_Server.tools.intelligence.get_ableton_connection",
    "MCP_Server.tools.refinement.get_ableton_connection",
]
```

**Why this pattern exists:** Python's `from X import Y` binds `Y` at import time in the
importing module's namespace. Patching `MCP_Server.connection.get_ableton_connection` alone
does not affect tool modules that have already bound their own local reference via
`from MCP_Server.connection import get_ableton_connection`. Each import site must be patched
separately.

**When to update:** Every new tool module that does `from MCP_Server.connection import
get_ableton_connection` must be added to `_GAC_PATCH_TARGETS`. Missing entries cause
integration tests to attempt a real TCP connection on port 9877.

## Mock Patterns

### Simple return value (most MCP integration tests)

```python
mock_connection.send_command.return_value = {"tempo": 140.0}
result = await mcp_server.call_tool("set_tempo", {"tempo": 140.0})
mock_connection.send_command.assert_called_once_with("set_tempo", {"tempo": 140.0})
```

### Sequential return values (`side_effect` list)

For tools that call `send_command` more than once (e.g., `get_connection_status` which
calls `ping` then `get_session_info`):

```python
mock_connection.send_command.side_effect = [
    {"ableton_version": "12.1"},         # first call: ping
    {"tempo": 120.0, "track_count": 4},  # second call: get_session_info
]
```

### Dispatch-style mocking (`side_effect` function)

Used in orchestration tests where different commands must return different data:

```python
def send_command(cmd, params=None):
    if cmd == "get_arrangement_state":
        return arrangement_state
    elif cmd == "get_mix_state":
        return mix_state
    return {}

mock_conn.send_command.side_effect = send_command
```

### `_make_conn` factory helper (orchestration tests)

`tests/test_checkpoint.py` and `tests/test_next_actions.py` define a local `_make_conn`
factory that wraps the dispatch pattern:

```python
def _make_conn(arrangement_state, mix_state, clips_by_track=None):
    """Build a mock connection that returns fixture data."""
    clips_by_track = clips_by_track or {}
    for t in arrangement_state.get("tracks", []):
        if t["name"] in clips_by_track and clips_by_track[t["name"]]:
            t["has_clips"] = True
        elif "has_clips" not in t:
            t["has_clips"] = False
    mock_conn = MagicMock()

    def send_command(cmd, params=None):
        if cmd == "get_arrangement_state":
            return arrangement_state
        elif cmd == "get_mix_state":
            return mix_state
        return {}

    mock_conn.send_command.side_effect = send_command
    return mock_conn
```

Companion `_make_track` helper:
```python
def _make_track(name, has_instrument=True, index=0, devices=None, has_clips=False):
    return {"name": name, "has_instrument": has_instrument, "index": index,
            "devices": devices or [], "has_clips": has_clips}
```

Fixture constants for empty state (used as defaults):
```python
EMPTY_ARRANGEMENT = {"tracks": [], "cue_points": [], "song_length": 0}
EMPTY_MIX = {"tracks": [], "return_tracks": [], "master_track": {"devices": []}}
```

## mcp Module Stub (pure-computation tests importing tools)

Tests for `MCP_Server/orchestration/` or `MCP_Server/tools/` modules that do not use the
`mcp_server` fixture must stub out the `mcp` package hierarchy at module load time. This
prevents `ImportError` when `mcp` is not installed or when side-effects of importing
`MCP_Server.server` (which tries to create a `FastMCP` instance) are undesirable.

This boilerplate appears at the top of 21 test files (`test_checkpoint.py`,
`test_evaluation_schema.py`, `test_mixing.py`, `test_analysis.py`, etc.):

```python
import sys
import types
from unittest.mock import MagicMock

_mock_mcp = types.ModuleType("mcp")
_mock_fastmcp = types.ModuleType("mcp.server.fastmcp")
_mock_server_mod = types.ModuleType("mcp.server")
_mock_fastmcp.Context = type("Context", (), {})
_mock_mcp.server = _mock_server_mod
_mock_server_mod.fastmcp = _mock_fastmcp
sys.modules.setdefault("mcp", _mock_mcp)
sys.modules.setdefault("mcp.server", _mock_server_mod)
sys.modules.setdefault("mcp.server.fastmcp", _mock_fastmcp)

if "MCP_Server.server" not in sys.modules:
    _mock_app_server = types.ModuleType("MCP_Server.server")
    _mcp_instance = MagicMock()
    _mcp_instance.tool.return_value = lambda fn: fn  # makes @mcp.tool() a no-op
    _mock_app_server.mcp = _mcp_instance
    sys.modules["MCP_Server.server"] = _mock_app_server
```

`setdefault` guards prevent double-registration when tests run together. Subject module
imports follow after this block with `# noqa: E402` comments.

## Test Structure

**Class-based grouping:** Related tests grouped into `class Test<Subject>`. No `self` usage
beyond method signature — test classes are namespaces only.

```python
class TestCheckpoint:
    def setup_method(self):
        """Clear checkpoint cache before each test to avoid cross-test leakage."""
        ...

    def test_empty_session(self):
        ...
```

**`setup_method`:** Used (not `setUp`) when test state must be reset between each test in a
class. Present in `test_checkpoint.py` (line 79), `test_next_actions.py`, and
`test_prompt_deriver.py` (line 43).

**`autouse=True` fixtures:** Used in `test_mixing.py` (lines 163, 191, 220, 337) to call
`_ensure_initialized()` before each test in catalog validation classes:

```python
class TestRecipeParameterNames:
    @pytest.fixture(autouse=True)
    def init_registry(self):
        _ensure_initialized()
```

**Standalone async functions:** MCP integration tests using `mcp_server`/`mock_connection`
fixtures are module-level `async def test_...` functions, not classes:

```python
async def test_set_tempo_calls_send_command(mcp_server, mock_connection):
    """set_tempo invokes send_command with correct tempo value."""
```

**No `@pytest.mark.asyncio`:** `asyncio_mode = "auto"` in `pyproject.toml` handles this globally.

## What Is Tested

| Domain | Test File | Type | Lines |
|---|---|---|---|
| Theory library | `test_theory.py` | Pure unit | 2278 |
| Devices / LOM tools | `test_devices.py` | MCP integration | 785 |
| Genre blueprints | `test_genres.py` | Pure unit | 736 |
| Mixing recipes | `test_mixing.py` | Pure unit | 562 |
| Section state / refinement | `test_section_state.py` | Conn mock | 358 |
| Scaffold tools | `test_scaffold.py` | Mixed | 352 |
| Evaluation schema | `test_evaluation_schema.py` | Pure unit | 399 |
| Evaluation phase 40 | `test_evaluation_phase40.py` | Conn mock | 340 |
| Intelligence tools | `test_intelligence.py` | Conn mock | 336 |
| Track tools | `test_tracks.py` | MCP integration | 331 |
| Clip tools | `test_clips.py` | MCP integration | 327 |
| Sounds catalog | `test_sounds.py` | Pure unit | 408 |
| Plan tools | `test_plan_tools.py` | MCP integration | 413 |
| Refinement application | `test_refinement_application.py` | Pure unit | 452 |
| Transport tools | `test_transport.py` | MCP integration | 297 |
| Prompt deriver | `test_prompt_deriver.py` | Pure unit | — |
| Prompt tools | `test_prompt_tools.py` | Conn mock | — |
| Orchestration agenda | `test_production_agenda.py` | Pure unit | — |
| Phase execution | `test_phase_execution.py` | Pure unit | — |
| Checkpoint | `test_checkpoint.py` | Conn mock | — |
| Next actions | `test_next_actions.py` | Conn mock | — |
| Device catalog | `test_catalog.py` | Pure unit | — |
| Param conversion | `test_convert.py` | Pure unit | — |
| Protocol framing | `test_protocol.py` | Pure unit | — |
| Connection thread safety | `test_connection_thread_safety.py` | Threading | — |
| Mixer tools | `test_mixer.py` | MCP integration | — |
| Session tools | `test_session.py` | MCP integration | — |
| Registry | `test_registry.py` | Mixed | — |
| Arrangement tools | `test_arrangement.py` | MCP integration | — |
| Arrangement extension | `test_arrangement_extension.py` | MCP integration | — |

## Known Coverage Gaps

**No tests for:**
- `MCP_Server/tools/plans.py` — plan tool wrappers have no dedicated test file
- `MCP_Server/tools/catalog.py` — device catalog tool wrappers (`get_device_catalog`, `get_role_taxonomy`) have minimal coverage only in `test_catalog.py` lower section (lines 162+)
- Individual `MCP_Server/genres/*.py` beyond house/techno/hip_hop_trap — per-genre shape tested at catalog level only; genre-specific content assertions are sparse
- `MCP_Server/orchestration/next_actions.py` `get_transition_guidance` — only `setup`, `drums`, `bass`, `harmony` phases covered; `mix` and `master` phases untested
- `MCP_Server/tools/refinement.py` — `get_section_state` internal private helper `_note_summary` tested directly in `test_section_state.py` but the MCP tool wrapper itself is not exercised via `mcp_server.call_tool`

**Partial coverage:**
- `tests/test_automation.py` — only 7 tests for automation tools; envelope tools have limited assertion depth
- `tests/test_browser.py` — only 4 tests (tool registration + 1 send_command check)

**`live_uat_07.py`:** Manual UAT script requiring live Ableton connection. Not collected by
pytest (file not prefixed `test_`). Contains 8 async test functions exercising the full
end-to-end stack. Run manually: `python tests/live_uat_07.py`.

---

*Testing analysis: 2026-04-02*
