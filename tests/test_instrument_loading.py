"""Grep-based tests verifying instrument loading correctness and health-check version.

These tests inspect the actual source files to confirm:
- Instrument loading uses same-callback pattern (selected_track + load_item in one tick)
- Verification with retry mechanism exists (_verify_load with retries_remaining)
- Load success reports device chain (device names list)
- _ping returns ableton_version via get_major_version
- get_connection_status health-check tool surfaces ableton_version
"""

import re

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def remote_script_source():
    """Read all Remote Script source (init + registry + handler modules)."""
    base = ROOT / "AbletonMCP_Remote_Script"
    sources = [(base / "__init__.py").read_text()]
    reg = base / "registry.py"
    if reg.exists():
        sources.append(reg.read_text())
    handlers = base / "handlers"
    if handlers.is_dir():
        for f in sorted(handlers.iterdir()):
            if f.suffix == ".py":
                sources.append(f.read_text())
    return "\n".join(sources)


@pytest.fixture
def server_source():
    return (ROOT / "MCP_Server" / "server.py").read_text()


@pytest.fixture
def session_tools_source():
    return (ROOT / "MCP_Server" / "tools" / "session.py").read_text()


class TestSameCallbackPattern:
    """Verify instrument loading uses same-callback pattern."""

    def test_load_browser_item_same_callback(self, remote_script_source):
        """selected_track assignment AND load_item call appear in the same function body.

        The same-callback pattern prevents the race condition where instruments
        load on the wrong track by ensuring track selection and item loading
        happen in a single schedule_message tick.
        """
        # Find the do_load function body -- it should contain BOTH patterns
        # Look for a function body that contains both selected_track and load_item
        # The do_load inner function is inside _load_browser_item
        lines = remote_script_source.splitlines()

        # Extract the _load_browser_item method body
        in_method = False
        method_body_lines = []
        indent_level = None

        for line in lines:
            if "def _load_browser_item" in line:
                in_method = True
                indent_level = len(line) - len(line.lstrip())
                method_body_lines.append(line)
                continue
            if in_method:
                stripped = line.lstrip()
                # Stop at next method at same or lesser indent
                if stripped.startswith("def ") and (len(line) - len(stripped)) <= indent_level:
                    break
                method_body_lines.append(line)

        method_body = "\n".join(method_body_lines)

        # Find do_load function within the method
        assert "def do_load" in method_body, (
            "do_load inner function not found in _load_browser_item"
        )

        # Extract do_load body
        do_load_lines = []
        in_do_load = False
        do_load_indent = None

        for line in method_body_lines:
            if "def do_load" in line:
                in_do_load = True
                do_load_indent = len(line) - len(line.lstrip())
                do_load_lines.append(line)
                continue
            if in_do_load:
                stripped = line.lstrip()
                current_indent = len(line) - len(stripped) if stripped else do_load_indent + 1
                # Stop at next function at same or lesser indent
                if stripped.startswith("def ") and current_indent <= do_load_indent:
                    break
                do_load_lines.append(line)

        do_load_body = "\n".join(do_load_lines)

        assert "selected_track" in do_load_body, (
            "'selected_track' not found in do_load -- "
            "track selection must happen in the same callback as load_item"
        )
        assert "load_item" in do_load_body, (
            "'load_item' not found in do_load -- "
            "browser load must happen in the same callback as track selection"
        )


class TestVerifyLoadRetry:
    """Verify load verification with retry mechanism."""

    def test_verify_load_has_retry(self, remote_script_source):
        """_verify_load function exists and accepts retries_remaining parameter."""
        # Check the function definition exists
        assert re.search(r"def _verify_load", remote_script_source), (
            "_verify_load function not found in Remote Script -- "
            "load verification with retry is required"
        )

        # Check the function has retries_remaining parameter
        verify_match = re.search(
            r"def _verify_load\([^)]*retries_remaining[^)]*\)",
            remote_script_source,
        )
        assert verify_match, (
            "_verify_load does not have retries_remaining parameter -- "
            "one automatic retry on load failure is required"
        )


class TestDeviceChainReporting:
    """Verify load success reports device chain."""

    def test_load_success_reports_device_chain(self, remote_script_source):
        """_verify_load reports device names in success response."""
        # Extract _verify_load body
        lines = remote_script_source.splitlines()
        in_method = False
        method_body_lines = []
        indent_level = None

        for line in lines:
            if "def _verify_load" in line:
                in_method = True
                indent_level = len(line) - len(line.lstrip())
                method_body_lines.append(line)
                continue
            if in_method:
                stripped = line.lstrip()
                if stripped.startswith("def ") and (len(line) - len(stripped)) <= indent_level:
                    break
                method_body_lines.append(line)

        method_body = "\n".join(method_body_lines)

        # Check for device name list comprehension pattern
        assert re.search(r"d\.name\s+for\s+d\s+in", method_body), (
            "Device name list comprehension not found in _verify_load -- "
            "load success must report device chain (e.g., [d.name for d in track.devices])"
        )

        # Check for 'devices' key in response
        assert '"devices"' in method_body or "'devices'" in method_body, (
            "'devices' key not found in _verify_load response -- "
            "success response must include device chain under 'devices' key"
        )


class TestPingAbletonVersion:
    """Verify _ping returns Ableton version."""

    def test_ping_returns_ableton_version(self, remote_script_source):
        """_ping method contains ableton_version key and get_major_version call."""
        # Extract _ping method body
        lines = remote_script_source.splitlines()
        in_method = False
        method_body_lines = []
        indent_level = None

        for line in lines:
            if "def _ping" in line:
                in_method = True
                indent_level = len(line) - len(line.lstrip())
                method_body_lines.append(line)
                continue
            if in_method:
                stripped = line.lstrip()
                if stripped.startswith("def ") and (len(line) - len(stripped)) <= indent_level:
                    break
                method_body_lines.append(line)

        method_body = "\n".join(method_body_lines)

        assert "ableton_version" in method_body, (
            "'ableton_version' not found in _ping method -- "
            "ping must return Ableton version information"
        )
        assert "get_major_version" in method_body, (
            "'get_major_version' not found in _ping method -- "
            "ping must read real Ableton version via application().get_major_version()"
        )


class TestHealthCheckVersion:
    """Verify get_connection_status includes Ableton version."""

    def test_get_connection_status_includes_ableton_version(self, session_tools_source):
        """get_connection_status function body contains ableton_version."""
        # Extract get_connection_status function body
        lines = session_tools_source.splitlines()
        in_func = False
        func_body_lines = []
        indent_level = None

        for line in lines:
            if "def get_connection_status" in line:
                in_func = True
                indent_level = len(line) - len(line.lstrip())
                func_body_lines.append(line)
                continue
            if in_func:
                stripped = line.lstrip()
                if stripped.startswith("def ") and (len(line) - len(stripped)) <= indent_level:
                    break
                if stripped.startswith("@") and (len(line) - len(stripped)) <= indent_level:
                    break
                func_body_lines.append(line)

        func_body = "\n".join(func_body_lines)

        assert "ableton_version" in func_body, (
            "'ableton_version' not found in get_connection_status -- "
            "health-check tool must surface Ableton version from ping result"
        )
