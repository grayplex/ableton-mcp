"""Note handlers: MIDI note editing with Live 11+ APIs."""

from AbletonMCP_Remote_Script.handlers.clips import _resolve_clip_slot
from AbletonMCP_Remote_Script.registry import command


class NoteHandlers:
    """Mixin class for note command handlers."""

    @command("add_notes_to_clip", write=True)
    def _add_notes_to_clip(self, params):
        """Add MIDI notes to a clip using Live 11+ append-mode API."""
        import Live.Clip

        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        notes = params.get("notes", [])
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            # Validate and build MidiNoteSpecification objects
            note_specs = []
            for note in notes:
                pitch = note.get("pitch", 60)
                start_time = note.get("start_time", 0.0)
                duration = note.get("duration", 0.25)
                velocity = note.get("velocity", 100)
                mute = note.get("mute", False)

                if pitch < 0 or pitch > 127:
                    raise ValueError(
                        f"Pitch {pitch} out of range (0-127)"
                    )
                if velocity < 1 or velocity > 127:
                    raise ValueError(
                        f"Velocity {velocity} out of range (1-127)"
                    )
                if duration <= 0:
                    raise ValueError(
                        f"Duration {duration} must be greater than 0"
                    )

                # Build spec with optional expression fields
                spec_kwargs = {
                    "pitch": pitch,
                    "start_time": start_time,
                    "duration": duration,
                    "velocity": velocity,
                    "mute": mute,
                }
                # Live 11+ note expression fields (optional)
                probability = note.get("probability")
                if probability is not None:
                    if probability < 0.0 or probability > 1.0:
                        raise ValueError(
                            f"Probability {probability} out of range (0.0-1.0)"
                        )
                    spec_kwargs["probability"] = probability
                velocity_deviation = note.get("velocity_deviation")
                if velocity_deviation is not None:
                    if velocity_deviation < -127.0 or velocity_deviation > 127.0:
                        raise ValueError(
                            f"Velocity deviation {velocity_deviation} out of range (-127.0-127.0)"
                        )
                    spec_kwargs["velocity_deviation"] = velocity_deviation
                release_velocity = note.get("release_velocity")
                if release_velocity is not None:
                    if release_velocity < 0.0 or release_velocity > 127.0:
                        raise ValueError(
                            f"Release velocity {release_velocity} out of range (0.0-127.0)"
                        )
                    spec_kwargs["release_velocity"] = release_velocity

                note_specs.append(
                    Live.Clip.MidiNoteSpecification(**spec_kwargs)
                )

            clip.add_new_notes(tuple(note_specs))

            return {"note_count": len(notes), "clip_name": clip.name}
        except Exception as e:
            self.log_message(f"Error adding notes to clip: {e}")
            raise

    @command("get_notes")
    def _get_notes(self, params):
        """Get all MIDI notes from a clip."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            raw_notes = clip.get_notes_extended(
                0, 128, 0.0, clip.length
            )

            notes = []
            for note in raw_notes:
                note_dict = {
                    "pitch": note.pitch,
                    "start_time": note.start_time,
                    "duration": note.duration,
                    "velocity": note.velocity,
                    "mute": bool(note.mute),
                }
                # Live 11+ expression fields
                if hasattr(note, "note_id"):
                    note_dict["note_id"] = note.note_id
                if hasattr(note, "probability"):
                    note_dict["probability"] = note.probability
                if hasattr(note, "velocity_deviation"):
                    note_dict["velocity_deviation"] = note.velocity_deviation
                if hasattr(note, "release_velocity"):
                    note_dict["release_velocity"] = note.release_velocity
                notes.append(note_dict)

            # Sort by start_time ascending, ties broken by pitch ascending
            notes.sort(key=lambda n: (n["start_time"], n["pitch"]))

            return {"note_count": len(notes), "notes": notes}
        except Exception as e:
            self.log_message(f"Error getting notes: {e}")
            raise

    @command("remove_notes", write=True)
    def _remove_notes(self, params):
        """Remove MIDI notes within a pitch/time range."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            pitch_min = params.get("pitch_min", 0)
            pitch_max = params.get("pitch_max", 127)
            start_time_min = params.get("start_time_min", 0.0)
            start_time_max = params.get("start_time_max", clip.length)

            # Convert min/max to from/span format
            from_pitch = pitch_min
            pitch_span = pitch_max - pitch_min + 1
            from_time = start_time_min
            time_span = start_time_max - start_time_min

            # Count notes before removal
            existing = clip.get_notes_extended(
                from_pitch, pitch_span, from_time, time_span
            )
            count = len(existing)

            clip.remove_notes_extended(
                from_pitch, pitch_span, from_time, time_span
            )

            return {"removed_count": count}
        except Exception as e:
            self.log_message(f"Error removing notes: {e}")
            raise

    @command("quantize_notes", write=True)
    def _quantize_clip_notes(self, params):
        """Quantize note start times to a grid with configurable strength."""
        import Live.Clip

        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        grid_size = params.get("grid_size", 0.25)
        strength = params.get("strength", 1.0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            raw_notes = clip.get_notes_extended(
                0, 128, 0.0, clip.length
            )

            if not raw_notes:
                return {"quantized_count": 0}

            # Extract note data
            note_data = [
                {
                    "pitch": note.pitch,
                    "start_time": note.start_time,
                    "duration": note.duration,
                    "velocity": note.velocity,
                    "mute": bool(note.mute),
                }
                for note in raw_notes
            ]

            # Quantize each note's start_time
            for nd in note_data:
                original = nd["start_time"]
                nearest_grid = round(original / grid_size) * grid_size
                nd["start_time"] = original + (nearest_grid - original) * strength

            # Remove all notes and re-add with quantized positions
            clip.remove_notes_extended(0, 128, 0.0, clip.length)

            specs = tuple(
                Live.Clip.MidiNoteSpecification(
                    pitch=nd["pitch"],
                    start_time=nd["start_time"],
                    duration=nd["duration"],
                    velocity=nd["velocity"],
                    mute=nd["mute"],
                )
                for nd in note_data
            )
            clip.add_new_notes(specs)

            return {"quantized_count": len(note_data)}
        except Exception as e:
            self.log_message(f"Error quantizing notes: {e}")
            raise

    @command("transpose_notes", write=True)
    def _transpose_clip_notes(self, params):
        """Transpose all notes in a clip by semitones with pre-validation."""
        import Live.Clip

        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        semitones = params.get("semitones", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            raw_notes = clip.get_notes_extended(
                0, 128, 0.0, clip.length
            )

            if not raw_notes:
                return {"transposed_count": 0}

            # FIRST PASS: validate ALL notes before modifying any
            for note in raw_notes:
                new_pitch = note.pitch + semitones
                if new_pitch < 0 or new_pitch > 127:
                    raise ValueError(
                        f"Transposing pitch {note.pitch} by {semitones} "
                        f"semitones results in {new_pitch}, "
                        f"which is outside MIDI range (0-127)"
                    )

            # SECOND PASS: build transposed note data
            note_data = [
                {
                    "pitch": note.pitch + semitones,
                    "start_time": note.start_time,
                    "duration": note.duration,
                    "velocity": note.velocity,
                    "mute": bool(note.mute),
                }
                for note in raw_notes
            ]

            # Remove all notes and re-add with transposed pitches
            clip.remove_notes_extended(0, 128, 0.0, clip.length)

            specs = tuple(
                Live.Clip.MidiNoteSpecification(
                    pitch=nd["pitch"],
                    start_time=nd["start_time"],
                    duration=nd["duration"],
                    velocity=nd["velocity"],
                    mute=nd["mute"],
                )
                for nd in note_data
            )
            clip.add_new_notes(specs)

            return {"transposed_count": len(note_data)}
        except Exception as e:
            self.log_message(f"Error transposing notes: {e}")
            raise
