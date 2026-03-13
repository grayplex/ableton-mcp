"""Tests verifying dict-based command dispatch in the Remote Script.

These tests grep the actual source files to confirm:
- _read_commands and _write_commands dicts exist
- No elif command dispatch chain remains in _process_command
- Unknown commands produce an error naming the command
- All existing command type strings are registered as dict keys
"""

import re

import pytest


class TestDictDispatchExists:
    """Verify dispatch dicts are defined as class attributes."""

    def test_read_commands_dict_exists(self, remote_script_source):
        """_read_commands dict is defined as an attribute assignment."""
        assert re.search(r"self\._read_commands\s*[=:]\s*\{", remote_script_source), (
            "_read_commands dict not found in Remote Script -- "
            "expected self._read_commands = { ... } or self._read_commands: dict = { ... }"
        )

    def test_write_commands_dict_exists(self, remote_script_source):
        """_write_commands dict is defined as an attribute assignment."""
        assert re.search(r"self\._write_commands\s*[=:]\s*\{", remote_script_source), (
            "_write_commands dict not found in Remote Script -- "
            "expected self._write_commands = { ... } or self._write_commands: dict = { ... }"
        )


class TestNoElifChain:
    """Verify the if/elif command dispatch chain is eliminated."""

    def test_no_elif_chain_in_process_command(self, remote_script_source):
        """_process_command does not contain 'elif command_type ==' pattern."""
        # Extract _process_command method body
        lines = remote_script_source.splitlines()
        in_method = False
        method_body = []
        indent_level = None

        for line in lines:
            if "def _process_command" in line:
                in_method = True
                indent_level = len(line) - len(line.lstrip())
                method_body.append(line)
                continue
            if in_method:
                stripped = line.lstrip()
                if stripped.startswith("def ") and (len(line) - len(stripped)) <= indent_level:
                    break
                if stripped and not line[0].isspace() and not stripped.startswith("#"):
                    break
                method_body.append(line)

        method_text = "\n".join(method_body)
        assert "elif command_type ==" not in method_text, (
            "Found 'elif command_type ==' in _process_command -- "
            "the if/elif dispatch chain must be replaced with dict lookup"
        )

    def test_no_elif_command_type_in_batch(self, remote_script_source):
        """_process_command does not contain 'elif command_type in' batch check pattern."""
        lines = remote_script_source.splitlines()
        in_method = False
        method_body = []
        indent_level = None

        for line in lines:
            if "def _process_command" in line:
                in_method = True
                indent_level = len(line) - len(line.lstrip())
                method_body.append(line)
                continue
            if in_method:
                stripped = line.lstrip()
                if stripped.startswith("def ") and (len(line) - len(stripped)) <= indent_level:
                    break
                if stripped and not line[0].isspace() and not stripped.startswith("#"):
                    break
                method_body.append(line)

        method_text = "\n".join(method_body)
        assert "elif command_type in" not in method_text, (
            "Found 'elif command_type in' in _process_command -- "
            "the batch command type check must be replaced with dict lookup"
        )


class TestUnknownCommandError:
    """Verify unknown commands produce descriptive error messages."""

    def test_unknown_command_returns_error(self, remote_script_source):
        """_process_command body contains fallback for unknown commands."""
        lines = remote_script_source.splitlines()
        in_method = False
        method_body = []
        indent_level = None

        for line in lines:
            if "def _process_command" in line:
                in_method = True
                indent_level = len(line) - len(line.lstrip())
                method_body.append(line)
                continue
            if in_method:
                stripped = line.lstrip()
                if stripped.startswith("def ") and (len(line) - len(stripped)) <= indent_level:
                    break
                if stripped and not line[0].isspace() and not stripped.startswith("#"):
                    break
                method_body.append(line)

        method_text = "\n".join(method_body)
        assert "Unknown command" in method_text, (
            "'Unknown command' not found in _process_command -- "
            "unknown commands must return an error message naming the command"
        )


class TestPingInReadCommands:
    """Verify ping is registered in the read commands dict."""

    def test_ping_in_read_commands(self, remote_script_source):
        """'ping' appears as a key in the _read_commands dict definition."""
        # Find the _read_commands dict block
        match = re.search(
            r"self\._read_commands\s*(?::\s*dict\[.*?\]\s*)?=\s*\{([^}]+)\}",
            remote_script_source,
            re.DOTALL,
        )
        assert match, "_read_commands dict definition not found"
        dict_body = match.group(1)
        assert '"ping"' in dict_body or "'ping'" in dict_body, (
            "'ping' not found as a key in _read_commands dict"
        )


class TestAllExistingCommandsRegistered:
    """Verify every known command type string appears as a dict key."""

    # All command type strings from the current codebase
    EXPECTED_COMMANDS = [
        "get_session_info",
        "get_track_info",
        "create_midi_track",
        "set_track_name",
        "create_clip",
        "add_notes_to_clip",
        "set_clip_name",
        "set_tempo",
        "fire_clip",
        "stop_clip",
        "start_playback",
        "stop_playback",
        "load_browser_item",
        "get_browser_item",
        "get_browser_categories",
        "get_browser_items",
        "get_browser_tree",
        "get_browser_items_at_path",
        "ping",
    ]

    def test_all_existing_commands_registered(self, remote_script_source):
        """All existing command type strings appear as dict keys in source."""
        missing = []
        for cmd in self.EXPECTED_COMMANDS:
            # Check for the command string as a dict key: "command_name": or 'command_name':
            pattern = rf'["\']{re.escape(cmd)}["\']'
            if not re.search(pattern, remote_script_source):
                missing.append(cmd)

        assert not missing, (
            f"Commands not found as dict keys in source: {missing}"
        )
