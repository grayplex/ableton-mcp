"""Transport handlers: playback control, tempo, time signature, loop, undo/redo."""

from AbletonMCP_Remote_Script.registry import command


class TransportHandlers:
    """Mixin class for transport command handlers."""

    @command("start_playback", write=True)
    def _start_playback(self, params=None):
        """Start playing the session."""
        try:
            self._song.start_playing()
            return {"playing": self._song.is_playing}
        except Exception as e:
            self.log_message(f"Error starting playback: {e}")
            raise

    @command("stop_playback", write=True)
    def _stop_playback(self, params=None):
        """Stop playing the session."""
        try:
            self._song.stop_playing()
            return {"playing": self._song.is_playing}
        except Exception as e:
            self.log_message(f"Error stopping playback: {e}")
            raise

    @command("set_tempo", write=True)
    def _set_tempo(self, params):
        """Set the tempo of the session (20-999 BPM)."""
        tempo = params.get("tempo", 120.0)
        try:
            if not (20.0 <= tempo <= 999.0):
                current = self._song.tempo
                raise ValueError(
                    f"Tempo {tempo} out of range (20-999 BPM). "
                    f"Current value: {current}"
                )

            self._song.tempo = tempo
            return {"tempo": self._song.tempo}
        except Exception as e:
            self.log_message(f"Error setting tempo: {e}")
            raise

    @command("continue_playback", write=True)
    def _continue_playback(self, params=None):
        """Resume playback from current position (not from start marker)."""
        try:
            self._song.continue_playing()
            return {"playing": self._song.is_playing}
        except Exception as e:
            self.log_message(f"Error continuing playback: {e}")
            raise

    @command("stop_all_clips", write=True)
    def _stop_all_clips(self, params=None):
        """Stop all playing clips (transport continues playing)."""
        try:
            self._song.stop_all_clips()
            return {"stopped": True, "transport_playing": self._song.is_playing}
        except Exception as e:
            self.log_message(f"Error stopping all clips: {e}")
            raise

    @command("set_time_signature", write=True)
    def _set_time_signature(self, params):
        """Set the time signature of the session."""
        numerator = params.get("numerator")
        denominator = params.get("denominator")
        try:
            if numerator is None:
                raise ValueError("numerator parameter is required")
            if denominator is None:
                raise ValueError("denominator parameter is required")

            if not (1 <= numerator <= 32):
                current = self._song.signature_numerator
                raise ValueError(
                    f"Numerator {numerator} out of range (1-32). "
                    f"Current value: {current}"
                )

            valid_denominators = {1, 2, 4, 8, 16}
            if denominator not in valid_denominators:
                current = self._song.signature_denominator
                raise ValueError(
                    f"Denominator {denominator} is not valid. "
                    f"Must be one of {sorted(valid_denominators)}. "
                    f"Current value: {current}"
                )

            self._song.signature_numerator = numerator
            self._song.signature_denominator = denominator

            return {
                "numerator": self._song.signature_numerator,
                "denominator": self._song.signature_denominator,
            }
        except Exception as e:
            self.log_message(f"Error setting time signature: {e}")
            raise

    @command("set_loop_region", write=True)
    def _set_loop_region(self, params):
        """Set loop region properties (enabled, start, length).

        All params are optional -- only provided values are applied.
        """
        try:
            if "enabled" in params:
                self._song.loop = params["enabled"]
            if "start" in params:
                self._song.loop_start = params["start"]
            if "length" in params:
                self._song.loop_length = params["length"]

            return {
                "loop_enabled": self._song.loop,
                "loop_start": self._song.loop_start,
                "loop_length": self._song.loop_length,
            }
        except Exception as e:
            self.log_message(f"Error setting loop region: {e}")
            raise

    @command("get_playback_position")
    def _get_playback_position(self, params=None):
        """Get current playback position in beats (lightweight check)."""
        try:
            return {"position": self._song.current_song_time}
        except Exception as e:
            self.log_message(f"Error getting playback position: {e}")
            raise

    @command("get_transport_state")
    def _get_transport_state(self, params=None):
        """Get full composite transport state."""
        try:
            return {
                "is_playing": self._song.is_playing,
                "tempo": self._song.tempo,
                "time_signature": {
                    "numerator": self._song.signature_numerator,
                    "denominator": self._song.signature_denominator,
                },
                "position": self._song.current_song_time,
                "loop_enabled": self._song.loop,
                "loop_start": self._song.loop_start,
                "loop_length": self._song.loop_length,
            }
        except Exception as e:
            self.log_message(f"Error getting transport state: {e}")
            raise

    @command("undo", write=True)
    def _undo(self, params=None):
        """Undo the last action (checks can_undo first)."""
        try:
            if not self._song.can_undo:
                return {"undone": False, "message": "Nothing to undo"}
            self._song.undo()
            return {"undone": True}
        except Exception as e:
            self.log_message(f"Error performing undo: {e}")
            raise

    @command("redo", write=True)
    def _redo(self, params=None):
        """Redo the last undone action (checks can_redo first)."""
        try:
            if not self._song.can_redo:
                return {"undone": False, "message": "Nothing to redo"}
            self._song.redo()
            return {"undone": True}
        except Exception as e:
            self.log_message(f"Error performing redo: {e}")
            raise
