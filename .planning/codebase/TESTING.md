# Testing Patterns

**Analysis Date:** 2026-03-10

## Test Framework

**Status:** No testing framework detected

**Current State:**
- No unit tests, integration tests, or test framework dependencies found
- No `pytest`, `unittest`, `nose2`, or other test runner configurations
- No test files (*.test.py, *.spec.py) in the codebase
- No `pytest.ini`, `tox.ini`, `setup.cfg`, or test configuration files
- Dependencies in `pyproject.toml` contain only: `mcp[cli]>=1.3.0`

**Testing Gap:**
This is a critical concern. The codebase lacks automated testing entirely.

## Manual Testing Approach

**Current Testing Method:**
Based on code analysis, testing appears to be manual:

1. **Socket Communication Testing:**
   - Manual verification of socket connections to Ableton Remote Script
   - Testing JSON message format and response parsing
   - Verification of timeout behavior and error handling

2. **Integration Testing:**
   - Manual testing with Ableton Live running
   - Verification of CLI invocation: `ableton-mcp`
   - Testing through Claude Desktop or Cursor MCP integrations

3. **Command Testing:**
   - Each tool function requires manual invocation through Claude
   - Example: `get_session_info()` requires connecting to Ableton and verifying response format
   - Track creation, clip manipulation require live Ableton session

## Code Coverage

**Coverage Tool:** Not configured

**Coverage Status:**
- No coverage measurement framework detected
- No `.coverage` config or coverage thresholds
- Recommendation: Implement pytest-cov or similar

## Test Structure (Recommended)

**Location:**
- Tests should reside in `tests/` directory at project root (co-located with source)
- Structure: `tests/test_[module_name].py` pattern

**Naming Convention:**
- Test files: `test_server.py`, `test_ableton_connection.py`
- Test functions: `test_send_command_success()`, `test_socket_timeout_retry()`
- Test classes (if used): `TestAbletonConnection`, `TestMCPServer`

**Recommended Directory Structure:**
```
ableton-mcp/
├── tests/
│   ├── __init__.py
│   ├── test_server.py           # MCP server tests
│   ├── test_ableton_connection.py # Socket connection tests
│   ├── test_tools.py            # Tool endpoint tests
│   ├── fixtures/
│   │   ├── __init__.py
│   │   └── mock_responses.py    # Mock Ableton responses
│   └── integration/
│       └── test_e2e.py          # End-to-end tests
├── MCP_Server/
├── AbletonMCP_Remote_Script/
└── pyproject.toml
```

## Recommended Testing Framework

**Recommendation:** pytest

**Setup in pyproject.toml:**
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
]
```

**Run Commands:**
```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=MCP_Server  # Coverage report
pytest -k test_send      # Run specific tests
pytest -x                # Stop on first failure
```

## Test Structure Pattern (Recommended)

**Basic Unit Test Structure:**
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from MCP_Server.server import AbletonConnection, get_ableton_connection


class TestAbletonConnection:
    """Test suite for AbletonConnection class"""

    @pytest.fixture
    def connection(self):
        """Create a test connection instance"""
        return AbletonConnection(host="localhost", port=9877)

    def test_connect_success(self, connection):
        """Test successful socket connection"""
        with patch('socket.socket') as mock_socket:
            connection.sock = mock_socket.return_value
            result = connection.connect()
            assert result is True

    def test_connect_failure(self, connection):
        """Test connection failure handling"""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.connect.side_effect = ConnectionRefusedError()
            result = connection.connect()
            assert result is False
            assert connection.sock is None
```

**Async Test Structure:**
```python
@pytest.mark.asyncio
async def test_server_lifespan():
    """Test server startup and shutdown lifecycle"""
    from MCP_Server.server import server_lifespan, mcp

    async with server_lifespan(mcp) as state:
        # Server is running
        assert state is not None
    # Server has shut down
```

## Mocking

**Framework:** `unittest.mock` (built-in Python)

**What to Mock:**
- Socket operations: `socket.socket`, `socket.recv()`, `socket.sendall()`
- External Ableton connection: Mock `AbletonConnection` entirely for unit tests
- Time-dependent operations: Mock `time.sleep()` to avoid delays in tests
- JSON parsing: Can test with actual JSON for integration tests

**What NOT to Mock:**
- Core business logic (command routing, response formatting)
- Error handling paths (test actual exception behavior)
- State management (test actual state transitions)

**Mocking Pattern Example:**
```python
from unittest.mock import Mock, patch, MagicMock
import json

def test_send_command_success():
    """Test successful command sending"""
    with patch('socket.socket') as mock_socket_class:
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        # Mock the response
        response_data = json.dumps({
            "status": "success",
            "result": {"tempo": 120}
        }).encode('utf-8')

        mock_sock.recv.return_value = response_data

        conn = AbletonConnection("localhost", 9877)
        conn.connect()
        result = conn.send_command("get_session_info")

        assert result.get("tempo") == 120
        mock_sock.sendall.assert_called_once()
```

## Fixtures and Test Data

**Test Data Location:**
- Recommended: `tests/fixtures/mock_responses.py`

**Fixture Pattern (Recommended):**
```python
# tests/fixtures/mock_responses.py

MOCK_SESSION_INFO = {
    "status": "success",
    "result": {
        "tempo": 120.0,
        "signature_numerator": 4,
        "signature_denominator": 4,
        "track_count": 1,
        "return_track_count": 0,
        "master_track": {
            "name": "Master",
            "volume": 0.0,
            "panning": 0.0
        }
    }
}

MOCK_TRACK_INFO = {
    "status": "success",
    "result": {
        "index": 0,
        "name": "Track 1",
        "is_audio_track": False,
        "is_midi_track": True,
        "mute": False,
        "solo": False,
        "arm": False,
        "volume": 0.0,
        "panning": 0.0,
        "clip_slots": [],
        "devices": []
    }
}
```

**pytest Fixture Usage:**
```python
@pytest.fixture
def session_info_response(monkeypatch):
    """Provide mock session info response"""
    return MOCK_SESSION_INFO
```

## Test Types

**Unit Tests (Recommended):**
- Scope: Individual functions and classes in isolation
- Approach: Mock all external dependencies (sockets, Ableton)
- Examples to test:
  - `AbletonConnection.connect()` with socket mocking
  - `AbletonConnection.receive_full_response()` with chunked data
  - `get_ableton_connection()` with connection caching logic
  - Tool functions with mocked connection
  - JSON parsing and response formatting

**Integration Tests (Recommended):**
- Scope: Multiple components working together
- Approach: Mock Ableton socket but test full request/response cycle
- Examples to test:
  - Complete command flow: send_command -> receive_full_response -> parse
  - Connection recovery and retry logic
  - Tool endpoint calling AbletonConnection
  - Response formatting for MCP protocol

**E2E Tests (Recommended for CI/CD):**
- Scope: Full system with real Ableton (if available)
- Approach: Connect to actual Ableton Remote Script socket
- Examples:
  - Actual socket communication test (optional, requires Ableton running)
  - Full CLI invocation through uvx
  - Can be conditional on Ableton availability

## Critical Areas Without Testing

**High Priority (Security/Stability):**
1. **Socket Error Handling:** `receive_full_response()` has complex error logic with timeouts and chunking
2. **Connection Recovery:** `get_ableton_connection()` has retry logic (3 attempts) that needs testing
3. **State Management:** Global `_ableton_connection` lifecycle needs validation
4. **JSON Parsing:** Incomplete JSON handling in buffering logic

**Medium Priority:**
1. **Tool Parameter Validation:** Track/clip indices validation
2. **Browser Tree Traversal:** Recursive tree formatting logic
3. **Encoding/Decoding:** Python 2/3 compatibility handling
4. **Thread Safety:** Client thread handling in remote script

**Low Priority:**
1. **UI Messages:** Ableton UI feedback (log messages, show_message)
2. **Error Message Formatting:** User-facing error strings

## Coverage Goals (Recommended)

**Target Coverage:**
- Line coverage: >= 80%
- Critical paths: 100%
- Exception paths: >= 90%

**Exclude from Coverage:**
- `if __name__ == "__main__"` blocks
- Ableton framework imports (external dependency)

## Run Commands Setup (Recommended)

```bash
# Add to Makefile or tox.ini
test:
    pytest

test-cov:
    pytest --cov=MCP_Server --cov-report=html

test-watch:
    pytest-watch

test-ci:
    pytest --cov=MCP_Server --cov-report=xml
```

---

*Testing analysis: 2026-03-10*
