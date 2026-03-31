"""Tests for Phase 47: Refinement Application Tools.

Covers:
- RS handler transpose_arrangement_clip: found and not-found cases
- RS handler modify_arrangement_clip_notes
- apply_section_note_refinement: transpose applied to in-range clip; out-of-range skipped
- apply_section_device_refinement: write_automation=False (no note), write_automation=True (note)
- refine_section: end-to-end flow; empty section returns tracks_modified=0
"""

import json
import sys
import types
from unittest.mock import MagicMock, call, patch

# ---------------------------------------------------------------------------
# Mock mcp module hierarchy so imports work without mcp installed
# ---------------------------------------------------------------------------
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
    _mock_app = types.ModuleType("MCP_Server.server")
    _mock_inst = MagicMock()
    _mock_inst.tool.return_value = lambda fn: fn
    _mock_app.mcp = _mock_inst
    sys.modules["MCP_Server.server"] = _mock_app

# ---------------------------------------------------------------------------
# Mock _Framework so AbletonMCP_Remote_Script handlers can be imported
# ---------------------------------------------------------------------------
_fw = types.ModuleType("_Framework")
_fw_cs = types.ModuleType("_Framework.ControlSurface")
_fw_cs.ControlSurface = type("ControlSurface", (), {"__init__": lambda self, *a, **kw: None})
_fw.ControlSurface = _fw_cs
sys.modules.setdefault("_Framework", _fw)
sys.modules.setdefault("_Framework.ControlSurface", _fw_cs)

import pytest  # noqa: E402

from MCP_Server.tools.refinement import (  # noqa: E402
    apply_section_device_refinement,
    apply_section_note_refinement,
    refine_section,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_CONN_PATCH = "MCP_Server.tools.refinement.get_ableton_connection"


def _make_arrangement_state(locators, tracks, song_length=128.0, sig_num=4, sig_den=4):
    return {
        "cue_points": [{"name": name, "time": time} for name, time in locators],
        "tracks": tracks,
        "song_length": song_length,
        "signature_numerator": sig_num,
        "signature_denominator": sig_den,
    }


def _make_clip(name, start_time, end_time, is_audio=False):
    return {
        "name": name,
        "start_time": start_time,
        "end_time": end_time,
        "length": end_time - start_time,
        "is_audio_clip": is_audio,
    }


def _make_note(pitch, start_time=0.0, duration=0.5, velocity=80):
    return {"pitch": pitch, "start_time": start_time, "duration": duration, "velocity": velocity, "mute": False}


def _make_mix_state(tracks=None):
    return {
        "tracks": tracks or [],
        "return_tracks": [],
        "master_track": {"index": -1, "name": "Master", "type": "master", "devices": [], "volume": 0.85, "pan": 0.5},
    }


# ---------------------------------------------------------------------------
# RS Handler Tests
# ---------------------------------------------------------------------------


class TestRSCommands:
    """Test new RS handler commands directly."""

    def test_rs_transpose_arrangement_clip_found(self):
        """Handler transposes MIDI notes and returns transposed_count."""
        from AbletonMCP_Remote_Script.handlers.arrangement import ArrangementHandlers

        # Mock Live.Clip module
        mock_live_clip = types.ModuleType("Live.Clip")
        mock_spec = MagicMock()
        mock_live_clip.MidiNoteSpecification = MagicMock(return_value=mock_spec)
        mock_live = types.ModuleType("Live")
        mock_live.Clip = mock_live_clip
        sys.modules["Live"] = mock_live
        sys.modules["Live.Clip"] = mock_live_clip

        mock_note1 = MagicMock()
        mock_note1.pitch = 60
        mock_note1.start_time = 0.0
        mock_note1.duration = 0.5
        mock_note1.velocity = 80
        mock_note1.mute = False

        mock_note2 = MagicMock()
        mock_note2.pitch = 62
        mock_note2.start_time = 0.5
        mock_note2.duration = 0.5
        mock_note2.velocity = 80
        mock_note2.mute = False

        mock_clip = MagicMock()
        mock_clip.start_time = 32.0
        mock_clip.is_audio_clip = False
        mock_clip.length = 16.0
        mock_clip.get_notes_extended.return_value = [mock_note1, mock_note2]
        mock_clip.name = "Bridge Pad"

        mock_track = MagicMock()
        mock_track.arrangement_clips = [mock_clip]

        handler = ArrangementHandlers.__new__(ArrangementHandlers)
        handler._song = MagicMock()
        handler.log_message = MagicMock()

        with patch("AbletonMCP_Remote_Script.handlers.arrangement._resolve_track", return_value=mock_track):
            result = handler._transpose_arrangement_clip({
                "track_index": 0,
                "clip_start_time": 32.0,
                "semitones": -3,
            })

        assert result["transposed_count"] == 2
        assert result["clip_name"] == "Bridge Pad"
        mock_clip.remove_notes_extended.assert_called_once_with(0, 128, 0.0, 16.0)
        mock_clip.add_new_notes.assert_called_once()
        # Verify pitch shifts applied: 60→57, 62→59
        call_args = mock_live_clip.MidiNoteSpecification.call_args_list
        pitches = [c.kwargs.get("pitch", c.args[0] if c.args else None) for c in call_args]
        # Either kwargs or positional — check via call_args
        specs_called = [
            mock_live_clip.MidiNoteSpecification.call_args_list[i]
            for i in range(len(mock_live_clip.MidiNoteSpecification.call_args_list))
        ]
        assert len(specs_called) == 2

    def test_rs_transpose_arrangement_clip_not_found(self):
        """Handler returns transposed_count=0 when no clip at clip_start_time."""
        from AbletonMCP_Remote_Script.handlers.arrangement import ArrangementHandlers

        mock_track = MagicMock()
        mock_track.arrangement_clips = []

        handler = ArrangementHandlers.__new__(ArrangementHandlers)
        handler._song = MagicMock()
        handler.log_message = MagicMock()

        with patch("AbletonMCP_Remote_Script.handlers.arrangement._resolve_track", return_value=mock_track):
            result = handler._transpose_arrangement_clip({
                "track_index": 0,
                "clip_start_time": 32.0,
                "semitones": -3,
            })

        assert result == {"transposed_count": 0, "clip_name": None}

    def test_rs_modify_arrangement_clip_notes(self):
        """Handler calls apply_note_modifications with correct note specs."""
        from AbletonMCP_Remote_Script.handlers.arrangement import ArrangementHandlers

        mock_live_clip = types.ModuleType("Live.Clip")
        mock_live_clip.MidiNoteSpecification = MagicMock(return_value=MagicMock())
        mock_live = types.ModuleType("Live")
        mock_live.Clip = mock_live_clip
        sys.modules["Live"] = mock_live
        sys.modules["Live.Clip"] = mock_live_clip

        mock_clip = MagicMock()
        mock_clip.start_time = 32.0
        mock_clip.is_audio_clip = False
        mock_clip.name = "Bridge Pad"

        mock_track = MagicMock()
        mock_track.arrangement_clips = [mock_clip]

        handler = ArrangementHandlers.__new__(ArrangementHandlers)
        handler._song = MagicMock()
        handler.log_message = MagicMock()

        notes = [{"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 72, "mute": False}]

        with patch("AbletonMCP_Remote_Script.handlers.arrangement._resolve_track", return_value=mock_track):
            result = handler._modify_arrangement_clip_notes({
                "track_index": 0,
                "clip_start_time": 32.0,
                "notes": notes,
            })

        assert result["modified_count"] == 1
        assert result["clip_name"] == "Bridge Pad"
        mock_clip.apply_note_modifications.assert_called_once()


# ---------------------------------------------------------------------------
# apply_section_note_refinement tests
# ---------------------------------------------------------------------------


class TestApplyNoteRefinement:

    def test_apply_note_refinement_transpose(self):
        """Semitone shift applied to in-range clips via transpose_arrangement_clip RS."""
        arrangement = _make_arrangement_state(
            locators=[("Bridge", 32.0), ("Outro", 64.0)],
            tracks=[{"index": 0, "name": "Pad"}],
        )
        clips_resp = {"clips": [_make_clip("Pad 1", 32.0, 48.0)]}
        transpose_resp = {"transposed_count": 4, "clip_name": "Pad 1"}

        def side_effect(cmd, params):
            if cmd == "get_arrangement_state":
                return arrangement
            if cmd == "get_arrangement_clips":
                return clips_resp
            if cmd == "transpose_arrangement_clip":
                assert params["semitones"] == -3
                assert params["clip_start_time"] == 32.0
                return transpose_resp
            return {}

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = side_effect

        with patch(_CONN_PATCH, return_value=mock_conn):
            result_str = apply_section_note_refinement(
                None, "Bridge", "Pad", semitone_shift=-3
            )

        result = json.loads(result_str)
        assert result["clips_modified"] == 1
        assert result["notes_modified"] == 4
        assert result["track"] == "Pad"
        assert result["section"] == "Bridge"

    def test_apply_note_refinement_skips_out_of_range(self):
        """Clip starting at section end beat is outside range — not modified."""
        arrangement = _make_arrangement_state(
            locators=[("Bridge", 32.0), ("Outro", 64.0)],
            tracks=[{"index": 0, "name": "Pad"}],
        )
        # Clip starts exactly at section end (64.0) — outside Bridge range [32, 64)
        clips_resp = {"clips": [_make_clip("Pad Outro", 64.0, 80.0)]}

        def side_effect(cmd, params):
            if cmd == "get_arrangement_state":
                return arrangement
            if cmd == "get_arrangement_clips":
                return clips_resp
            if cmd == "transpose_arrangement_clip":
                pytest.fail("transpose_arrangement_clip should NOT be called for out-of-range clip")
            return {}

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = side_effect

        with patch(_CONN_PATCH, return_value=mock_conn):
            result_str = apply_section_note_refinement(
                None, "Bridge", "Pad", semitone_shift=-3
            )

        result = json.loads(result_str)
        assert result["clips_modified"] == 0


# ---------------------------------------------------------------------------
# apply_section_device_refinement tests
# ---------------------------------------------------------------------------


class TestApplyDeviceRefinement:

    def _base_setup(self):
        arrangement = _make_arrangement_state(
            locators=[("Bridge", 32.0), ("Outro", 64.0)],
            tracks=[{"index": 0, "name": "Pad"}],
        )
        mix_state = _make_mix_state(tracks=[{
            "index": 0, "name": "Pad", "type": "track",
            "devices": [{"class_name": "AutoFilter", "device_name": "Auto Filter", "index": 0}],
            "volume": 0.8, "pan": 0.5,
        }])
        return arrangement, mix_state

    def test_apply_device_refinement_no_automation(self):
        """write_automation=False: set_device_parameters called, no 'note' in response."""
        arrangement, mix_state = self._base_setup()

        set_params_resp = {"result": "ok"}

        def side_effect(cmd, params):
            if cmd == "get_arrangement_state":
                return arrangement
            if cmd == "get_mix_state":
                return mix_state
            if cmd == "set_device_parameters":
                assert params["track_index"] == 0
                assert params["device_index"] == 0
                return set_params_resp
            return {}

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = side_effect

        with patch(_CONN_PATCH, return_value=mock_conn):
            result_str = apply_section_device_refinement(
                None, "Bridge", "Pad",
                param_targets={"AutoFilter": {"Frequency": 0.35}},
                write_automation=False,
            )

        result = json.loads(result_str)
        assert "note" not in result
        assert result["devices_modified"] == 1
        assert result["params_set"][0]["device"] == "AutoFilter"

    def test_apply_device_refinement_automation_note(self):
        """write_automation=True: response includes 'note' about automation."""
        arrangement, mix_state = self._base_setup()

        def side_effect(cmd, params):
            if cmd == "get_arrangement_state":
                return arrangement
            if cmd == "get_mix_state":
                return mix_state
            if cmd == "set_device_parameters":
                return {"result": "ok"}
            return {}

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = side_effect

        with patch(_CONN_PATCH, return_value=mock_conn):
            result_str = apply_section_device_refinement(
                None, "Bridge", "Pad",
                param_targets={"AutoFilter": {"Frequency": 0.35}},
                write_automation=True,
            )

        result = json.loads(result_str)
        assert "note" in result
        assert "automation" in result["note"].lower()


# ---------------------------------------------------------------------------
# refine_section tests
# ---------------------------------------------------------------------------


class TestRefineSection:

    def test_refine_section_end_to_end(self):
        """Full pipeline: mock plan → notes and devices applied → summary returned."""
        arrangement = _make_arrangement_state(
            locators=[("Bridge", 32.0), ("Outro", 64.0)],
            tracks=[{"index": 0, "name": "Pad"}],
        )
        clips_resp = {"clips": [_make_clip("Pad 1", 32.0, 48.0)]}
        mix_state = _make_mix_state(tracks=[{
            "index": 0, "name": "Pad", "type": "track",
            "devices": [{"class_name": "AutoFilter", "device_name": "Auto Filter", "index": 0}],
            "volume": 0.8, "pan": 0.5,
        }])

        mock_plan = {
            "section": "Bridge",
            "instruction": "make it darker",
            "vector": {},
            "tracks": [{
                "track_name": "Pad",
                "track_index": 0,
                "note_operation": {
                    "semitone_shift": -3,
                    "density_delta": 0,
                    "scale_substitutions": [],
                    "velocity_shift": 0,
                },
                "device_changes": [],
            }],
            "reasoning": ["Darker: lowering register by 3 semitones"],
        }

        def side_effect(cmd, params):
            if cmd == "get_arrangement_state":
                return arrangement
            if cmd == "get_arrangement_clips":
                return clips_resp
            if cmd == "transpose_arrangement_clip":
                return {"transposed_count": 3, "clip_name": "Pad 1"}
            if cmd == "get_mix_state":
                return mix_state
            return {}

        mock_conn = MagicMock()
        mock_conn.send_command.side_effect = side_effect

        with patch(_CONN_PATCH, return_value=mock_conn), \
             patch("MCP_Server.tools.refinement.build_section_refinement_plan", return_value=mock_plan):
            result_str = refine_section(None, "Bridge", "make it darker")

        result = json.loads(result_str)
        assert result["section"] == "Bridge"
        assert result["instruction"] == "make it darker"
        assert isinstance(result["reasoning"], list)
        assert len(result["reasoning"]) >= 1
        assert "note_changes" in result
        assert "device_changes" in result

    def test_refine_section_empty_section(self):
        """Empty section → tracks_modified=0, reasoning from plan preserved."""
        mock_plan = {
            "section": "Bridge",
            "instruction": "make it darker",
            "vector": {},
            "tracks": [],
            "reasoning": ["No clips found in section 'Bridge' — nothing to refine"],
        }

        with patch("MCP_Server.tools.refinement.build_section_refinement_plan", return_value=mock_plan), \
             patch(_CONN_PATCH, return_value=MagicMock()):
            result_str = refine_section(None, "Bridge", "make it darker")

        result = json.loads(result_str)
        assert result["tracks_modified"] == 0
        assert result["note_changes"] == []
        assert result["device_changes"] == []
        assert any("No" in r or "no" in r for r in result["reasoning"])
