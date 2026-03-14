"""Unit tests for CommandRegistry @command decorator."""

import sys


def _stub_framework():
    """Stub Ableton _Framework module for import outside Ableton runtime."""
    if "_Framework" not in sys.modules:
        sys.modules["_Framework"] = type(sys)("_Framework")
        sys.modules["_Framework.ControlSurface"] = type(sys)("_Framework.ControlSurface")
        sys.modules["_Framework.ControlSurface"].ControlSurface = type("ControlSurface", (), {})


class TestCommandDecorator:
    """Test the @command decorator in isolation."""

    def test_command_decorator_registers_entry(self):
        """Decorating a function with @command adds it to _entries."""
        _stub_framework()
        from AbletonMCP_Remote_Script.registry import CommandRegistry

        original = CommandRegistry._entries[:]
        try:
            CommandRegistry._entries = []

            @CommandRegistry.command("test_cmd")
            def _test_cmd(self, params=None):
                pass

            assert len(CommandRegistry._entries) == 1
            entry = CommandRegistry._entries[0]
            assert entry[0] == "test_cmd"
            assert entry[1] == "_test_cmd"
            assert entry[2] is False  # not write
            assert entry[3] is False  # not self_scheduling
        finally:
            CommandRegistry._entries = original

    def test_build_tables_separates_read_write(self):
        """build_tables separates read and write commands correctly."""
        _stub_framework()
        from AbletonMCP_Remote_Script.registry import CommandRegistry

        original = CommandRegistry._entries[:]
        try:
            CommandRegistry._entries = [
                ("read_cmd", "method_r", False, False),
                ("write_cmd", "method_w", True, False),
            ]

            class FakeInstance:
                def method_r(self):
                    pass

                def method_w(self):
                    pass

            read_cmds, write_cmds, self_sched = CommandRegistry.build_tables(FakeInstance())
            assert "read_cmd" in read_cmds
            assert "read_cmd" not in write_cmds
            assert "write_cmd" in write_cmds
            assert "write_cmd" not in read_cmds
        finally:
            CommandRegistry._entries = original

    def test_self_scheduling_flag(self):
        """Commands registered with self_scheduling=True appear in self_scheduling set."""
        _stub_framework()
        from AbletonMCP_Remote_Script.registry import CommandRegistry

        original = CommandRegistry._entries[:]
        try:
            CommandRegistry._entries = [
                ("sched_cmd", "method_s", True, True),
                ("normal_cmd", "method_n", True, False),
            ]

            class FakeInstance:
                def method_s(self):
                    pass

                def method_n(self):
                    pass

            _, _, self_sched = CommandRegistry.build_tables(FakeInstance())
            assert "sched_cmd" in self_sched
            assert "normal_cmd" not in self_sched
        finally:
            CommandRegistry._entries = original


class TestFullRegistry:
    """Test the populated registry after all handler imports."""

    def test_all_commands_registered(self):
        """All 29 command type strings are registered in CommandRegistry."""
        _stub_framework()
        import AbletonMCP_Remote_Script.handlers  # noqa: F401
        from AbletonMCP_Remote_Script.registry import CommandRegistry

        registered = {e[0] for e in CommandRegistry._entries}
        assert len(registered) == 40, f"Expected 40 commands, got {len(registered)}: {registered}"

        expected = {
            "get_session_info",
            "get_track_info",
            "get_all_tracks",
            "create_midi_track",
            "create_audio_track",
            "create_return_track",
            "create_group_track",
            "set_track_name",
            "delete_track",
            "duplicate_track",
            "set_track_color",
            "set_group_fold",
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
            # Phase 4: Mixing Controls
            "set_track_volume",
            "set_track_pan",
            "set_track_mute",
            "set_track_solo",
            "set_track_arm",
            "set_send_level",
            # Phase 5: Clip Management
            "delete_clip",
            "duplicate_clip",
            "get_clip_info",
            "set_clip_color",
            "set_clip_loop",
        }
        missing = expected - registered
        assert not missing, f"Commands not registered: {missing}"
