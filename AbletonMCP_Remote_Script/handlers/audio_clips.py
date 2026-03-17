"""Audio clip handlers: get and set audio-specific clip properties (pitch, gain, warping)."""

from AbletonMCP_Remote_Script.handlers.clips import _resolve_clip_slot
from AbletonMCP_Remote_Script.registry import command


class AudioClipHandlers:
    """Mixin class for audio clip property command handlers.

    Provides pitch, gain, and warping control for audio clips.
    MIDI clips are rejected with a clear error message.
    """

    @command("get_audio_clip_properties")
    def _get_audio_clip_properties(self, params):
        """Get audio-specific properties for a clip (pitch, gain, warping)."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)

        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_audio_clip:
                raise ValueError(
                    f"Clip at track {track_index} slot {clip_index} is a MIDI "
                    f"clip, not audio. Audio clip properties only apply to "
                    f"audio clips."
                )

            result = {
                "track_name": track.name,
                "clip_name": clip.name,
                "pitch_coarse": clip.pitch_coarse,
                "pitch_fine": clip.pitch_fine,
                "gain": clip.gain,
                "gain_display": clip.gain_display_string,
                "warping": clip.warping,
            }

            # Bonus: include warp_mode if available
            try:
                result["warp_mode"] = str(clip.warp_mode)
            except Exception:
                pass

            return result
        except Exception as e:
            self.log_message(f"Error getting audio clip properties: {e}")
            raise

    @command("set_audio_clip_properties", write=True)
    def _set_audio_clip_properties(self, params):
        """Set audio-specific properties on a clip (pitch, gain, warping).

        All property parameters are optional -- set whichever you need.
        Returns before/after for each changed property.
        """
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        pitch_coarse = params.get("pitch_coarse", None)
        pitch_fine = params.get("pitch_fine", None)
        gain = params.get("gain", None)
        warping = params.get("warping", None)

        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if not clip.is_audio_clip:
                raise ValueError(
                    f"Clip at track {track_index} slot {clip_index} is a MIDI "
                    f"clip, not audio. Audio clip properties only apply to "
                    f"audio clips."
                )

            changes = []

            if pitch_coarse is not None:
                if not (-48 <= pitch_coarse <= 48):
                    raise ValueError(
                        f"pitch_coarse {pitch_coarse} out of range "
                        f"(-48 to 48 semitones). "
                        f"Current value: {clip.pitch_coarse}"
                    )
                prev = clip.pitch_coarse
                clip.pitch_coarse = pitch_coarse
                changes.append({
                    "property": "pitch_coarse",
                    "previous": prev,
                    "current": clip.pitch_coarse,
                })

            if pitch_fine is not None:
                if not (-500 <= pitch_fine <= 500):
                    raise ValueError(
                        f"pitch_fine {pitch_fine} out of range "
                        f"(-500 to 500). "
                        f"Current value: {clip.pitch_fine}"
                    )
                prev = clip.pitch_fine
                clip.pitch_fine = pitch_fine
                changes.append({
                    "property": "pitch_fine",
                    "previous": prev,
                    "current": clip.pitch_fine,
                })

            if gain is not None:
                if not (0.0 <= gain <= 1.0):
                    raise ValueError(
                        f"gain {gain} out of range (0.0 to 1.0). "
                        f"Current value: {clip.gain} "
                        f"({clip.gain_display_string})"
                    )
                prev = clip.gain
                prev_display = clip.gain_display_string
                clip.gain = gain
                changes.append({
                    "property": "gain",
                    "previous": prev,
                    "previous_display": prev_display,
                    "current": clip.gain,
                    "current_display": clip.gain_display_string,
                })

            if warping is not None:
                prev = clip.warping
                clip.warping = warping
                changes.append({
                    "property": "warping",
                    "previous": prev,
                    "current": clip.warping,
                })

            return {
                "track_name": track.name,
                "clip_name": clip.name,
                "changes": changes,
            }
        except Exception as e:
            self.log_message(f"Error setting audio clip properties: {e}")
            raise
