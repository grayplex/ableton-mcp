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

    # --- Scale & Key ---

    @command("get_scale_info")
    def _get_scale_info(self, params=None):
        """Get the current scale/key settings of the song."""
        try:
            return {
                "root_note": self._song.root_note,
                "scale_name": self._song.scale_name,
                "scale_intervals": list(self._song.scale_intervals),
                "scale_mode": self._song.scale_mode,
            }
        except Exception as e:
            self.log_message(f"Error getting scale info: {e}")
            raise

    @command("set_scale", write=True)
    def _set_scale(self, params):
        """Set scale/key properties (root_note, scale_name, scale_mode)."""
        try:
            if "root_note" in params:
                root_note = params["root_note"]
                if not (0 <= root_note <= 11):
                    raise ValueError(
                        f"root_note {root_note} out of range (0-11). "
                        f"Current value: {self._song.root_note}"
                    )
                self._song.root_note = root_note
            if "scale_name" in params:
                self._song.scale_name = params["scale_name"]
            if "scale_mode" in params:
                self._song.scale_mode = params["scale_mode"]
            return {
                "root_note": self._song.root_note,
                "scale_name": self._song.scale_name,
                "scale_intervals": list(self._song.scale_intervals),
                "scale_mode": self._song.scale_mode,
            }
        except Exception as e:
            self.log_message(f"Error setting scale: {e}")
            raise

    # --- Cue Points ---

    @command("get_cue_points")
    def _get_cue_points(self, params=None):
        """Get all cue points in the song."""
        try:
            return {
                "cue_points": [
                    {"name": cp.name, "time": cp.time}
                    for cp in self._song.cue_points
                ]
            }
        except Exception as e:
            self.log_message(f"Error getting cue points: {e}")
            raise

    @command("set_or_delete_cue", write=True)
    def _set_or_delete_cue(self, params=None):
        """Toggle a cue point at the current playback position."""
        try:
            self._song.set_or_delete_cue()
            return {
                "toggled": True,
                "position": self._song.current_song_time,
            }
        except Exception as e:
            self.log_message(f"Error toggling cue point: {e}")
            raise

    @command("jump_to_cue", write=True)
    def _jump_to_cue(self, params):
        """Jump to next/prev cue point, or a specific cue by index."""
        try:
            index = params.get("index")
            direction = params.get("direction", "next")
            if index is not None:
                cue_points = self._song.cue_points
                if index < 0 or index >= len(cue_points):
                    raise IndexError(
                        f"Cue index {index} out of range "
                        f"(0-{len(cue_points) - 1})"
                    )
                cue_points[index].jump()
            elif direction == "next":
                self._song.jump_to_next_cue()
            elif direction == "prev":
                self._song.jump_to_prev_cue()
            else:
                raise ValueError(
                    f"Invalid direction '{direction}'. Use 'next' or 'prev'."
                )
            return {
                "jumped": True,
                "direction": direction,
                "position": self._song.current_song_time,
            }
        except Exception as e:
            self.log_message(f"Error jumping to cue: {e}")
            raise

    # --- Capture ---

    @command("capture_scene", write=True)
    def _capture_scene(self, params=None):
        """Capture currently playing clips as a new scene."""
        try:
            self._song.capture_and_insert_scene()
            return {
                "captured": True,
                "scene_count": len(self._song.scenes),
            }
        except Exception as e:
            self.log_message(f"Error capturing scene: {e}")
            raise

    @command("capture_midi", write=True)
    def _capture_midi(self, params=None):
        """Capture recently played MIDI input."""
        try:
            self._song.capture_midi()
            return {"captured": True}
        except Exception as e:
            self.log_message(f"Error capturing MIDI: {e}")
            raise

    # --- Session Controls ---

    @command("tap_tempo", write=True)
    def _tap_tempo(self, params=None):
        """Tap tempo to set BPM by rhythm."""
        try:
            self._song.tap_tempo()
            return {"tapped": True, "tempo": self._song.tempo}
        except Exception as e:
            self.log_message(f"Error tapping tempo: {e}")
            raise

    @command("set_metronome", write=True)
    def _set_metronome(self, params):
        """Enable or disable the metronome."""
        try:
            enabled = params.get("enabled")
            if enabled is None:
                raise ValueError("enabled parameter is required")
            self._song.metronome = enabled
            return {"metronome": self._song.metronome}
        except Exception as e:
            self.log_message(f"Error setting metronome: {e}")
            raise

    @command("set_groove_amount", write=True)
    def _set_groove_amount(self, params):
        """Set the global groove amount (0.0-1.0)."""
        try:
            amount = params.get("amount")
            if amount is None:
                raise ValueError("amount parameter is required")
            if not (0.0 <= amount <= 1.0):
                raise ValueError(
                    f"Groove amount {amount} out of range (0.0-1.0). "
                    f"Current value: {self._song.groove_amount}"
                )
            self._song.groove_amount = amount
            return {"groove_amount": self._song.groove_amount}
        except Exception as e:
            self.log_message(f"Error setting groove amount: {e}")
            raise

    @command("set_swing_amount", write=True)
    def _set_swing_amount(self, params):
        """Set the global swing amount (0.0-1.0)."""
        try:
            amount = params.get("amount")
            if amount is None:
                raise ValueError("amount parameter is required")
            if not (0.0 <= amount <= 1.0):
                raise ValueError(
                    f"Swing amount {amount} out of range (0.0-1.0). "
                    f"Current value: {self._song.swing_amount}"
                )
            self._song.swing_amount = amount
            return {"swing_amount": self._song.swing_amount}
        except Exception as e:
            self.log_message(f"Error setting swing amount: {e}")
            raise

    @command("set_clip_trigger_quantization", write=True)
    def _set_clip_trigger_quantization(self, params):
        """Set the clip trigger quantization (0-14)."""
        try:
            quantization = params.get("quantization")
            if quantization is None:
                raise ValueError("quantization parameter is required")
            if not (0 <= quantization <= 14):
                raise ValueError(
                    f"Quantization {quantization} out of range (0-14). "
                    f"Current value: {self._song.clip_trigger_quantization}"
                )
            self._song.clip_trigger_quantization = quantization
            return {
                "clip_trigger_quantization": self._song.clip_trigger_quantization
            }
        except Exception as e:
            self.log_message(f"Error setting clip trigger quantization: {e}")
            raise

    @command("set_session_record", write=True)
    def _set_session_record(self, params):
        """Enable/disable session recording and optionally set record mode."""
        try:
            enabled = params.get("enabled")
            if enabled is None:
                raise ValueError("enabled parameter is required")
            self._song.session_record = enabled
            if "record_mode" in params:
                self._song.record_mode = params["record_mode"]
            return {
                "session_record": self._song.session_record,
                "record_mode": self._song.record_mode,
            }
        except Exception as e:
            self.log_message(f"Error setting session record: {e}")
            raise

    # --- Navigation ---

    @command("jump_by", write=True)
    def _jump_by(self, params):
        """Jump forward or backward by a number of beats."""
        try:
            beats = params.get("beats")
            if beats is None:
                raise ValueError("beats parameter is required")
            self._song.jump_by(beats)
            return {
                "jumped": True,
                "beats": beats,
                "position": self._song.current_song_time,
            }
        except Exception as e:
            self.log_message(f"Error jumping by beats: {e}")
            raise

    @command("play_selection", write=True)
    def _play_selection(self, params=None):
        """Play the current arrangement selection."""
        try:
            self._song.play_selection()
            return {"playing_selection": True}
        except Exception as e:
            self.log_message(f"Error playing selection: {e}")
            raise

    @command("get_song_length")
    def _get_song_length(self, params=None):
        """Get the total song length and last event time."""
        try:
            return {
                "song_length": self._song.song_length,
                "last_event_time": self._song.last_event_time,
            }
        except Exception as e:
            self.log_message(f"Error getting song length: {e}")
            raise
