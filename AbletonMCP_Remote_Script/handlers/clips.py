"""Clip handlers: create, rename, fire, stop clips."""

from AbletonMCP_Remote_Script.registry import command


class ClipHandlers:
    """Mixin class for clip command handlers."""

    @command("create_clip", write=True)
    def _create_clip(self, params):
        """Create a new MIDI clip in the specified track and clip slot."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        length = params.get("length", 4.0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if clip_slot.has_clip:
                raise Exception("Clip slot already has a clip")

            clip_slot.create_clip(length)

            return {
                "name": clip_slot.clip.name,
                "length": clip_slot.clip.length,
            }
        except Exception as e:
            self.log_message(f"Error creating clip: {e}")
            raise

    @command("set_clip_name", write=True)
    def _set_clip_name(self, params):
        """Set the name of a clip."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        name = params.get("name", "")
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip
            clip.name = name

            return {"name": clip.name}
        except Exception as e:
            self.log_message(f"Error setting clip name: {e}")
            raise

    @command("fire_clip", write=True)
    def _fire_clip(self, params):
        """Fire a clip."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip_slot.fire()

            return {"fired": True}
        except Exception as e:
            self.log_message(f"Error firing clip: {e}")
            raise

    @command("stop_clip", write=True)
    def _stop_clip(self, params):
        """Stop a clip."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]
            clip_slot.stop()

            return {"stopped": True}
        except Exception as e:
            self.log_message(f"Error stopping clip: {e}")
            raise
