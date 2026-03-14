"""Tests verifying command dispatch via CommandRegistry in the Remote Script.

These tests verify:
- CommandRegistry builds read_commands and write_commands dispatch dicts
- No elif command dispatch chain remains in _process_command
- Unknown commands produce an error naming the command
- All existing command type strings are registered via @command decorators
- Self-scheduling commands are correctly flagged
"""

import re
import sys


def _stub_framework():
    """Stub Ableton _Framework module for import outside Ableton runtime."""
    if '_Framework' not in sys.modules:
        sys.modules['_Framework'] = type(sys)('_Framework')
        sys.modules['_Framework.ControlSurface'] = type(sys)('_Framework.ControlSurface')
        sys.modules['_Framework.ControlSurface'].ControlSurface = type('ControlSurface', (), {})


class TestRegistryDispatchExists:
    """Verify dispatch dicts are built by CommandRegistry."""

    def test_read_commands_built_by_registry(self, remote_script_source):
        """_read_commands is assigned from CommandRegistry.build_tables."""
        assert "CommandRegistry.build_tables" in remote_script_source, (
            "CommandRegistry.build_tables not found in Remote Script -- "
            "dispatch tables must be built from the registry"
        )
        assert "_read_commands" in remote_script_source, (
            "_read_commands attribute not found in Remote Script"
        )

    def test_write_commands_built_by_registry(self, remote_script_source):
        """_write_commands is assigned from CommandRegistry.build_tables."""
        assert "_write_commands" in remote_script_source, (
            "_write_commands attribute not found in Remote Script"
        )

    def test_registry_returns_three_values(self):
        """CommandRegistry.build_tables returns (read, write, self_scheduling)."""
        _stub_framework()
        from AbletonMCP_Remote_Script.registry import CommandRegistry
        # Reset entries for isolated test
        original = CommandRegistry._entries[:]
        try:
            CommandRegistry._entries = [
                ("test_read", "method_r", False, False),
                ("test_write", "method_w", True, False),
                ("test_sched", "method_s", True, True),
            ]

            class FakeInstance:
                def method_r(self): pass
                def method_w(self): pass
                def method_s(self): pass

            read_cmds, write_cmds, self_sched = CommandRegistry.build_tables(FakeInstance())
            assert "test_read" in read_cmds
            assert "test_write" in write_cmds
            assert "test_sched" in write_cmds
            assert "test_sched" in self_sched
            assert "test_read" not in write_cmds
        finally:
            CommandRegistry._entries = original


class TestNoElifChain:
    """Verify the if/elif command dispatch chain is eliminated."""

    def test_no_elif_chain_in_process_command(self, remote_script_source):
        """_process_command does not contain 'elif command_type ==' pattern."""
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


class TestPingRegistered:
    """Verify ping is registered via @command decorator."""

    def test_ping_in_registry(self):
        """'ping' is registered in CommandRegistry._entries."""
        _stub_framework()
        from AbletonMCP_Remote_Script.registry import CommandRegistry
        import AbletonMCP_Remote_Script.handlers  # noqa: F401 -- triggers registration
        names = [e[0] for e in CommandRegistry._entries]
        assert "ping" in names, (
            "'ping' not registered via @command decorator"
        )

    def test_ping_is_read_command(self):
        """'ping' is registered as a read command (write=False)."""
        _stub_framework()
        from AbletonMCP_Remote_Script.registry import CommandRegistry
        import AbletonMCP_Remote_Script.handlers  # noqa: F401
        ping_entries = [e for e in CommandRegistry._entries if e[0] == "ping"]
        assert len(ping_entries) == 1, f"Expected 1 ping entry, got {len(ping_entries)}"
        assert ping_entries[0][2] is False, "ping should be a read command (write=False)"


class TestAllExistingCommandsRegistered:
    """Verify every known command type string is registered via @command."""

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
        "set_device_parameter",
        "load_instrument_or_effect",
    ]

    def test_all_existing_commands_registered(self):
        """All 21 command type strings are registered in CommandRegistry."""
        _stub_framework()
        from AbletonMCP_Remote_Script.registry import CommandRegistry
        import AbletonMCP_Remote_Script.handlers  # noqa: F401
        registered = {e[0] for e in CommandRegistry._entries}
        missing = [cmd for cmd in self.EXPECTED_COMMANDS if cmd not in registered]
        assert not missing, f"Commands not registered: {missing}"
        assert len(registered) == 21, f"Expected 21 commands, got {len(registered)}"

    def test_self_scheduling_commands_flagged(self):
        """load_browser_item and load_instrument_or_effect are self-scheduling."""
        _stub_framework()
        from AbletonMCP_Remote_Script.registry import CommandRegistry
        import AbletonMCP_Remote_Script.handlers  # noqa: F401
        self_sched = {e[0] for e in CommandRegistry._entries if e[3]}
        assert self_sched == {"load_browser_item", "load_instrument_or_effect"}, (
            f"Self-scheduling commands wrong: {self_sched}"
        )
