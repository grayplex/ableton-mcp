"""Note handlers: add MIDI notes to clips."""

from AbletonMCP_Remote_Script.registry import command


class NoteHandlers:
    """Mixin class for note command handlers."""

    @command("add_notes_to_clip", write=True)
    def _add_notes_to_clip(self, params):
        """Add MIDI notes to a clip."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        notes = params.get("notes", [])
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

            # Convert note data to Live's format
            live_notes = []
            for note in notes:
                pitch = note.get("pitch", 60)
                start_time = note.get("start_time", 0.0)
                duration = note.get("duration", 0.25)
                velocity = note.get("velocity", 100)
                mute = note.get("mute", False)

                live_notes.append((pitch, start_time, duration, velocity, mute))

            clip.set_notes(tuple(live_notes))

            return {"note_count": len(notes)}
        except Exception as e:
            self.log_message(f"Error adding notes to clip: {e}")
            raise
