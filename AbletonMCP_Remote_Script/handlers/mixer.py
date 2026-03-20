"""Mixer handlers: volume, pan, mute, solo, arm, sends."""

from AbletonMCP_Remote_Script.registry import command
from AbletonMCP_Remote_Script.handlers.tracks import _resolve_track
from AbletonMCP_Remote_Script.handlers.mixer_helpers import _to_db, _pan_label


class MixerHandlers:
    """Mixin class for mixer command handlers.

    Provides volume, pan, mute, solo, arm, and send level control
    for regular, return, and master tracks.
    """

    @command("set_track_volume", write=True)
    def _set_track_volume(self, params):
        """Set the volume of a track (0.0-1.0 normalized)."""
        track_index = params.get("track_index", 0)
        volume = params.get("volume")
        track_type = params.get("track_type", "track")

        try:
            track = _resolve_track(self._song, track_type, track_index)

            if volume is None:
                raise ValueError("volume parameter is required")

            if not (0.0 <= volume <= 1.0):
                current = track.mixer_device.volume.value
                raise ValueError(
                    f"Volume {volume} out of range (0.0-1.0). "
                    f"Current value: {current} ({_to_db(current)})"
                )

            track.mixer_device.volume.value = volume
            actual = track.mixer_device.volume.value

            result = {
                "volume": actual,
                "volume_db": _to_db(actual),
                "name": track.name,
                "type": track_type,
            }
            if track_type != "master":
                result["index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error setting track volume: {e}")
            raise

    @command("set_track_pan", write=True)
    def _set_track_pan(self, params):
        """Set the panning of a track (-1.0 left to 1.0 right)."""
        track_index = params.get("track_index", 0)
        pan = params.get("pan")
        track_type = params.get("track_type", "track")

        try:
            track = _resolve_track(self._song, track_type, track_index)

            if pan is None:
                raise ValueError("pan parameter is required")

            if not (-1.0 <= pan <= 1.0):
                current = track.mixer_device.panning.value
                raise ValueError(
                    f"Pan {pan} out of range (-1.0 to 1.0). "
                    f"Current value: {current} ({_pan_label(current)})"
                )

            track.mixer_device.panning.value = pan
            actual = track.mixer_device.panning.value

            result = {
                "pan": actual,
                "pan_label": _pan_label(actual),
                "name": track.name,
                "type": track_type,
            }
            if track_type != "master":
                result["index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error setting track pan: {e}")
            raise

    @command("set_track_mute", write=True)
    def _set_track_mute(self, params):
        """Set the mute state of a track (explicit boolean, no toggle)."""
        track_index = params.get("track_index", 0)
        mute = params.get("mute")
        track_type = params.get("track_type", "track")

        try:
            if track_type == "master":
                raise ValueError("Master track cannot be muted")

            track = _resolve_track(self._song, track_type, track_index)
            track.mute = mute

            result = {
                "mute": track.mute,
                "name": track.name,
                "type": track_type,
            }
            if track_type != "master":
                result["index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error setting track mute: {e}")
            raise

    @command("set_track_solo", write=True)
    def _set_track_solo(self, params):
        """Set the solo state of a track, with optional exclusive mode."""
        track_index = params.get("track_index", 0)
        solo = params.get("solo")
        track_type = params.get("track_type", "track")
        exclusive = params.get("exclusive", False)

        try:
            if track_type == "master":
                raise ValueError("Master track cannot be soloed")

            track = _resolve_track(self._song, track_type, track_index)

            if exclusive and solo:
                for t in self._song.tracks:
                    if t.solo:
                        t.solo = False
                for t in self._song.return_tracks:
                    if t.solo:
                        t.solo = False

            track.solo = solo

            result = {
                "solo": track.solo,
                "name": track.name,
                "type": track_type,
            }
            if track_type != "master":
                result["index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error setting track solo: {e}")
            raise

    @command("set_track_arm", write=True)
    def _set_track_arm(self, params):
        """Set the arm (record-enable) state of a track."""
        track_index = params.get("track_index", 0)
        arm = params.get("arm")
        track_type = params.get("track_type", "track")

        try:
            track = _resolve_track(self._song, track_type, track_index)

            if not (hasattr(track, "can_be_armed") and track.can_be_armed):
                raise ValueError(
                    f"Track '{track.name}' ({track_type}) cannot be armed. "
                    f"Only MIDI and audio tracks support arming."
                )

            track.arm = arm

            result = {
                "arm": track.arm,
                "name": track.name,
                "type": track_type,
            }
            if track_type != "master":
                result["index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error setting track arm: {e}")
            raise

    @command("set_send_level", write=True)
    def _set_send_level(self, params):
        """Set a send level for a track to a return track."""
        track_index = params.get("track_index", 0)
        track_type = params.get("track_type", "track")
        return_index = params.get("return_index")
        level = params.get("level")

        try:
            if track_type == "master":
                raise ValueError(
                    "Master track does not have sends -- "
                    "it receives the mix bus output directly"
                )

            track = _resolve_track(self._song, track_type, track_index)
            sends = track.mixer_device.sends

            if return_index is None:
                raise ValueError("return_index parameter is required")

            if not (0 <= return_index < len(sends)):
                raise IndexError(
                    f"Return index {return_index} out of range. "
                    f"This session has {len(self._song.return_tracks)} "
                    f"return track(s) (indices 0-{len(self._song.return_tracks) - 1})"
                )

            if level is None:
                raise ValueError("level parameter is required")

            if not (0.0 <= level <= 1.0):
                current = sends[return_index].value
                raise ValueError(
                    f"Send level {level} out of range (0.0-1.0). "
                    f"Current value: {current} ({_to_db(current)})"
                )

            sends[return_index].value = level
            actual = sends[return_index].value
            return_name = self._song.return_tracks[return_index].name

            result = {
                "send_level": actual,
                "send_db": _to_db(actual),
                "return_index": return_index,
                "return_name": return_name,
                "name": track.name,
                "type": track_type,
            }
            if track_type != "master":
                result["index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error setting send level: {e}")
            raise

    @command("set_crossfader", write=True)
    def _set_crossfader(self, params):
        """Set the crossfader position on the master track mixer."""
        value = params.get("value")
        try:
            crossfader = self._song.master_track.mixer_device.crossfader
            crossfader.value = value
            return {
                "crossfader": crossfader.value,
                "min": crossfader.min,
                "max": crossfader.max,
            }
        except Exception as e:
            self.log_message(f"Error setting crossfader: {e}")
            raise

    @command("set_crossfade_assign", write=True)
    def _set_crossfade_assign(self, params):
        """Set the crossfade assignment for a track (0=A, 1=none, 2=B)."""
        track_index = params.get("track_index", 0)
        track_type = params.get("track_type", "track")
        assign = params.get("assign")
        try:
            if track_type == "master":
                raise ValueError(
                    "Master track does not have crossfade assignment"
                )
            if assign not in (0, 1, 2):
                raise ValueError(
                    f"assign must be 0 (A), 1 (none), or 2 (B). "
                    f"Got: {assign}"
                )
            track = _resolve_track(self._song, track_type, track_index)
            track.mixer_device.crossfade_assign = assign
            label = {0: "A", 1: "none", 2: "B"}[assign]
            return {
                "crossfade_assign": track.mixer_device.crossfade_assign,
                "assign_label": label,
                "name": track.name,
                "type": track_type,
                "index": track_index,
            }
        except Exception as e:
            self.log_message(f"Error setting crossfade assignment: {e}")
            raise

    @command("get_panning_mode")
    def _get_panning_mode(self, params):
        """Get the panning mode of a track (Stereo or Split Stereo)."""
        track_index = params.get("track_index", 0)
        track_type = params.get("track_type", "track")
        try:
            track = _resolve_track(self._song, track_type, track_index)
            mode = track.mixer_device.panning_mode
            label = {0: "Stereo", 1: "Split Stereo"}.get(
                mode, f"unknown_{mode}"
            )
            result = {
                "panning_mode": mode,
                "mode_label": label,
                "name": track.name,
                "type": track_type,
            }
            if track_type != "master":
                result["index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error getting panning mode: {e}")
            raise
