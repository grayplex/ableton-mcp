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
        assert len(registered) == 178, f"Expected 178 commands, got {len(registered)}: {registered}"

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
            # Phase 6: MIDI Editing
            "get_notes",
            "remove_notes",
            "quantize_notes",
            "transpose_notes",
            # Phase 7: Device & Browser
            "get_device_parameters",
            "delete_device",
            "get_rack_chains",
            "get_session_state",
            # Phase 8: Scene Management
            "create_scene",
            "set_scene_name",
            "fire_scene",
            "delete_scene",
            # Phase 8: Transport Extensions
            "continue_playback",
            "stop_all_clips",
            "set_time_signature",
            "set_loop_region",
            "get_playback_position",
            "get_transport_state",
            "undo",
            "redo",
            # Phase 9: Automation
            "get_clip_envelope",
            "insert_envelope_breakpoints",
            "clear_clip_envelopes",
            # Phase 10: Routing & Audio Clips
            "get_input_routing_types",
            "set_input_routing",
            "get_output_routing_types",
            "set_output_routing",
            "get_audio_clip_properties",
            "set_audio_clip_properties",
            # Phase 12: Song Gaps
            "get_scale_info",
            "set_scale",
            "get_cue_points",
            "set_or_delete_cue",
            "jump_to_cue",
            "capture_scene",
            "capture_midi",
            "tap_tempo",
            "set_metronome",
            "set_groove_amount",
            "set_swing_amount",
            "set_clip_trigger_quantization",
            "set_session_record",
            "jump_by",
            "play_selection",
            "get_song_length",
            "duplicate_scene",
            # Phase 12: Track + Arrangement Gaps
            "create_arrangement_midi_clip",
            "create_arrangement_audio_clip",
            "get_arrangement_clips",
            "duplicate_clip_to_arrangement",
            "insert_device",
            "move_device",
            "stop_track_clips",
            "get_track_freeze_state",
            "get_input_routing_channels",
            "get_output_routing_channels",
            # Phase 12: Clip + Note Gaps
            "set_clip_launch_settings",
            "get_clip_launch_settings",
            "set_clip_muted",
            "crop_clip",
            "duplicate_clip_loop",
            "duplicate_clip_region",
            "apply_note_modifications",
            "select_all_notes",
            "deselect_all_notes",
            "select_notes_by_id",
            "get_notes_by_id",
            "remove_notes_by_id",
            "duplicate_notes_by_id",
            "get_selected_notes",
            "native_quantize",
            "get_warp_markers",
            "insert_warp_marker",
            "move_warp_marker",
            "remove_warp_marker",
            # Phase 13: Scene + Mixer Extended
            "set_scene_color",
            "get_scene_color",
            "set_scene_tempo",
            "set_scene_time_signature",
            "fire_scene_as_selected",
            "get_scene_is_empty",
            "set_crossfader",
            "set_crossfade_assign",
            "get_panning_mode",
            # Phase 13: Device Extended (Simpler, DrumPad, Plugin, A/B)
            "get_simpler_info",
            "crop_simpler",
            "reverse_simpler",
            "warp_simpler",
            "set_simpler_playback_mode",
            "insert_simpler_slice",
            "move_simpler_slice",
            "remove_simpler_slice",
            "clear_simpler_slices",
            "set_drum_pad_mute",
            "set_drum_pad_solo",
            "delete_drum_pad_chains",
            "set_plugin_preset",
            "list_plugin_presets",
            "compare_ab",
            # Phase 13: Groove + Clip Extended
            "list_grooves",
            "get_groove_params",
            "set_groove_params",
            "set_clip_groove",
            "create_session_audio_clip",
            # Quick Task: LOM gaps (34 new commands)
            "get_wavetable_info",
            "set_wavetable_oscillator",
            "set_wavetable_voice_config",
            "add_wavetable_modulation",
            "set_wavetable_modulation_value",
            "get_wavetable_modulation_value",
            "get_compressor_sidechain",
            "set_compressor_sidechain",
            "get_rack_variations",
            "rack_variation_action",
            "rack_macro_action",
            "insert_rack_chain",
            "copy_drum_pad",
            "get_drum_chain_config",
            "set_drum_chain_config",
            "get_parameter_automation_state",
            "re_enable_parameter_automation",
            "get_drift_mod_matrix",
            "set_drift_mod_matrix",
            "get_looper_info",
            "looper_action",
            "looper_export_to_clip_slot",
            "get_spectral_resonator_info",
            "set_spectral_resonator_config",
            "get_eq8_info",
            "set_eq8_mode",
            "get_take_lanes",
            "get_take_lane_clips",
            "create_take_lane_clip",
            "get_tuning_system",
            "set_tuning_system",
            "set_chain_mute_solo",
            "set_chain_name_color",
            "get_chain_info",
        }
        missing = expected - registered
        assert not missing, f"Commands not registered: {missing}"
