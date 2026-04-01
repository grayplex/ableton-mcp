# Testing Patterns

**Analysis Date:** 2026-04-01

## Test Framework

**Runner:**
- pytest 8.3+
- Config: `pyproject.toml` `[tool.pytest.ini_options]`

**Key pytest settings:**
```toml
asyncio_mode = "auto"   # all async tests run automatically without @pytest.mark.asyncio
testpaths = ["tests"]
timeout = 10            # 10-second per-test timeout via pytest-timeout
```

**Plugins required:**
- `pytest-asyncio >= 0.25` — for `asyncio_mode = "auto"`
- `pytest-timeout >= 2.0` — for per-test timeout

**Run Commands:**
```bash
pytest                          # Run all tests
pytest tests/test_theory.py     # Run single file
pytest -k "test_checkpoint"     # Run matching tests by name
pytest -x                       # Stop on first failure
pytest --tb=short               # Shorter tracebacks
```

No coverage tooling is configured (no `pytest-cov` in dev dependencies).

## Test File Organization

**Location:** All tests in `tests/` flat directory — no subdirectories.

**Naming:** `test_<domain>.py` matching the module under test:
- `tests/test_theory.py` → `MCP_Server/tools/theory.py` + `MCP_Server/theory/`
- `tests/test_checkpoint.py` → `MCP_Server/orchestration/checkpoint.py`
- `tests/test_genres.py` → `MCP_Server/genres/`
- `tests/test_tracks.py` → `MCP_Server/tools/tracks.py`

**Special files:**
- `tests/conftest.py` — shared fixtures (`mock_connection`, `mcp_server`, `root_dir`)
- `tests/live_uat_07.py` — live integration UAT (not prefixed `test_`, not collected by pytest)

## Test Categories

### 1. Pure-Computation Tests (no mocking, no fixtures)

Test library functions directly. No MCP, no connection, no `conftest.py` fixtures needed.
These tests import from sub-packages, not from `MCP_Server/tools/`.

**Files:**
- `tests/test_production_agenda.py` — tests `MCP_Server/orchestration/agenda.py`
- `tests/test_phase_execution.py` — tests `MCP_Server/orchestration/execution.py`
- `tests/test_theory.py` — tests `MCP_Server/theory/` functions
- `tests/test_genres.py` — tests `MCP_Server/genres/` catalog and schema
- `tests/test_protocol.py` — tests socket framing protocol
- `tests/test_convert.py`, `tests/test_sounds.py`, `tests/test_mixing.py` — library unit tests

**Pattern:**
```python
class TestProductionAgendaCatalog:
    def test_techno_phase_order(self):
        result = get_agenda("techno")
        assert "error" not in result
        phase_ids = [p["phase_id"] for p in result["phases"]]
        assert phase_ids[0] == "setup"
        assert phase_ids[1] == "drums"
```

### 2. Connection-Mocking Tests (patch `get_ableton_connection`)

Test orchestration functions that call Ableton. Use `_make_conn` helper and `patch`.
These tests import directly from the orchestration or library layer, not from `MCP_Server/tools/`.

**Files:**
- `tests/test_checkpoint.py` — tests `MCP_Server/orchestration/checkpoint.py`
- `tests/test_next_actions.py` — tests `MCP_Server/orchestration/next_actions.py`

**Pattern:**
```python
with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
           return_value=_make_conn(arr, mix, clips)):
    result = get_checkpoint("house")
assert result["completed_phases"] == []
```

### 3. MCP Integration Tests (use `mcp_server` + `mock_connection` fixtures)

Test the full tool-dispatch path via `mcp_server.call_tool(...)`. These tests call through
`MCP_Server/tools/` → `get_ableton_connection()` → `send_command()`. The `mock_connection`
fixture patches all `_GAC_PATCH_TARGETS` at once.

**Files:**
- `tests/test_tracks.py`, `tests/test_session.py`, `tests/test_clips.py`
- `tests/test_transport.py`, `tests/test_mixer.py`, `tests/test_notes.py`
- `tests/test_devices.py`, `tests/test_browser.py`, `tests/test_routing.py`
- `tests/test_arrangement.py`, `tests/test_automation.py`, `tests/test_scenes.py`
- `tests/test_grooves.py`, `tests/test_scaffold.py`, `tests/test_execution.py`

**Pattern:**
```python
async def test_create_midi_track_calls_send_command(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {"name": "MIDI Track", "index": 0}
    result = await mcp_server.call_tool("create_midi_track", {"index": -1})
    text = result[0][0].text
    data = json.loads(text)
    assert data["name"] == "MIDI Track"
    mock_connection.send_command.assert_called_once_with(
        "create_midi_track", {"index": -1}
    )
```

Response extraction: `result[0][0].text` — the FastMCP call_tool response is a nested
list of content objects; `.text` gives the JSON string.

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

Patches `get_ableton_connection` in every tool module that imports it.
Returns a `MagicMock` with `send_command.return_value = {}` by default.

```python
@pytest.fixture
def mock_connection():
    mock = MagicMock()
    mock.send_command.return_value = {}
    patches = [patch(target, return_value=mock) for target in _GAC_PATCH_TARGETS]
    for p in patches: p.start()
    try:
        yield mock
    finally:
        for p in patches: p.stop()
```

`_GAC_PATCH_TARGETS` is the authoritative list of 19 patch paths (e.g.,
`"MCP_Server.tools.tracks.get_ableton_connection"`). Add new tool modules here
when they import `get_ableton_connection`.

### `root_dir`

Returns the project root path string. Used in tests that read catalog JSON files.

## Mock Patterns

### `_make_conn` helper (orchestration tests)

`test_checkpoint.py` and `test_next_actions.py` define a local `_make_conn` factory that
builds a mock connection with `send_command.side_effect` dispatching to fixture data:

```python
def _make_conn(arrangement_state, mix_state, clips_by_track=None):
    """Build a mock connection that returns fixture data."""
    clips_by_track = clips_by_track or {}
    mock_conn = MagicMock()

    def send_command(cmd, params=None):
        if cmd == "get_arrangement_state":
            return arrangement_state
        elif cmd == "get_mix_state":
            return mix_state
        elif cmd == "get_arrangement_clips":
            track_idx = (params or {}).get("track_index", 0)
            track_name = next(
                (t["name"] for t in arrangement_state["tracks"] if t.get("index") == track_idx),
                ""
            )
            return {"clips": clips_by_track.get(track_name, [])}
        return {}

    mock_conn.send_command.side_effect = send_command
    return mock_conn
```

`_make_track` helper builds track fixture dicts:
```python
def _make_track(name, has_devices=True, index=0, devices=None):
    return {"name": name, "has_devices": has_devices, "index": index,
            "devices": devices or []}
```

Fixture constants for empty state:
```python
EMPTY_ARRANGEMENT = {"tracks": [], "cue_points": [], "song_length": 0}
EMPTY_MIX = {"tracks": [], "return_tracks": [], "master_track": {"devices": []}}
```

### `send_command.side_effect` (MCP integration tests)

For multi-command sequences, use `side_effect` with a list:
```python
mock_connection.send_command.side_effect = [
    {"ableton_version": "12.1"},  # first call: ping
    {"tempo": 120.0, "track_count": 4},  # second call: session info
]
```

For dispatch-style mocking (multiple command types in one test), use a function:
```python
def side_effect(cmd, params=None):
    if cmd == "get_arrangement_state":
        return {...}
    return {}
mock_connection.send_command.side_effect = side_effect
```

### `_GAC_PATCH_TARGETS` (conftest mock_connection)

Single-call patch of all 19 `get_ableton_connection` import sites. The mock is
the return value of each patched function — i.e., `get_ableton_connection()` returns
the mock directly (not a function returning the mock):

```python
patches = [patch(target, return_value=mock) for target in _GAC_PATCH_TARGETS]
```

## mcp Module Stub (pure-computation orchestration tests)

Tests for `MCP_Server/orchestration/` modules that indirectly import from `MCP_Server/tools/`
(which import `from MCP_Server.server import mcp`) must stub out the `mcp` package hierarchy
at module load time. This boilerplate appears at the top of `test_production_agenda.py`,
`test_phase_execution.py`, `test_checkpoint.py`, and `test_next_actions.py`:

```python
import sys, types
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
    _mcp_instance.tool.return_value = lambda fn: fn
    _mock_app_server.mcp = _mcp_instance
    sys.modules["MCP_Server.server"] = _mock_app_server
```

The `setdefault` guard prevents double-registration when tests are run together.
The `_mcp_instance.tool.return_value = lambda fn: fn` makes `@mcp.tool()` a no-op decorator.

`import pytest` and the subject module imports follow after this block with `# noqa: E402`
comments.

## Test Structure Pattern

**Class-based grouping:** Tests are grouped into `class Test<Subject>` with plain method names.
No `self` usage beyond method signature — test classes are namespaces, not stateful objects.

```python
class TestCheckpoint:
    def test_empty_session(self):
        ...
    def test_setup_complete_drums_active(self):
        ...
```

**Standalone async functions:** MCP integration tests (using `mcp_server`/`mock_connection`
fixtures) are written as module-level `async def test_...` functions, not classes:

```python
async def test_create_midi_track_calls_send_command(mcp_server, mock_connection):
    ...
```

**No `@pytest.mark.asyncio`:** `asyncio_mode = "auto"` in `pyproject.toml` handles this globally.

## What Is Tested

| Domain | Test File | Test Type | Notes |
|---|---|---|---|
| Theory library | `test_theory.py` | Pure unit | 2278 lines, most comprehensive |
| Orchestration agenda | `test_production_agenda.py` | Pure unit | 8 tests, all 12 genres |
| Orchestration execution | `test_phase_execution.py` | Pure unit | 8 tests, 9 phase types |
| Orchestration checkpoint | `test_checkpoint.py` | Connection mock | 7 tests, _make_conn pattern |
| Next actions | `test_next_actions.py` | Mixed (pure + conn mock) | Two classes: TestGetNextActions, TestGetTransitionGuidance |
| Genre blueprints | `test_genres.py` | Pure unit | Schema, catalog, alias |
| Track tools | `test_tracks.py` | MCP integration | mcp_server + mock_connection |
| Session tools | `test_session.py` | MCP integration | mcp_server + mock_connection |
| Clip tools | `test_clips.py` | MCP integration | — |
| Transport tools | `test_transport.py` | MCP integration | — |
| Mixer tools | `test_mixer.py` | MCP integration | — |
| Device tools | `test_devices.py` | MCP integration | 785 lines |
| Protocol | `test_protocol.py` | Pure unit | Socket framing roundtrips |
| Evaluation schema | `test_evaluation_schema.py` | Pure unit | TypedDict + grading |
| Scaffold | `test_scaffold.py` | MCP integration | — |
| Execution tools | `test_execution.py` | MCP integration | section_checklist, arrangement_progress |
| Sounds | `test_sounds.py` | Pure unit | Instrument preset catalogs |
| Mixing recipes | `test_mixing.py` | Pure unit | 546 lines |
| Prompt tools | `test_prompt_tools.py` | MCP integration | — |
| Prompt deriver | `test_prompt_deriver.py` | Pure unit | — |
| Refinement | `test_refinement_application.py`, `test_refinement_language.py` | Pure unit | — |
| Intelligence | `test_intelligence.py` | MCP integration | — |

## Known Coverage Gaps

**No tests for:**
- `MCP_Server/tools/plans.py` — plan tool wrappers
- `MCP_Server/tools/audio_clips.py` — audio clip manipulation
- `MCP_Server/tools/automation.py` — covered partially in `test_automation.py`
- `MCP_Server/tools/catalog.py` — device catalog tools
- Individual `MCP_Server/genres/*.py` beyond house and techno (catalog-level tests exist; per-genre shape checked only for house/techno/hip_hop_trap)
- `MCP_Server/orchestration/next_actions.py` `get_transition_guidance` coverage for `mix` and `master` phases

**`live_uat_07.py`:** Manual UAT script (requires live Ableton). Not collected by pytest.
File name is intentionally not prefixed with `test_` to exclude it from automated runs.

---

*Testing analysis: 2026-04-01*
