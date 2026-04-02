"""Scaffold handlers: create locators and batch-create named tracks."""

from AbletonMCP_Remote_Script.registry import command


def _is_instrument_device(device):
    """Return True if device is an instrument (drum machine, instrument rack, or plugin instrument).

    Excludes audio effect racks, MIDI effect racks, and standalone audio/MIDI effects.
    """
    try:
        if device.can_have_drum_pads:
            return True
        if device.can_have_chains:
            return "instrument" in device.class_display_name.lower()
        # Standalone device: instrument if class_name does not indicate audio or MIDI effect
        cn = device.class_name.lower()
        return "audio_effect" not in cn and "midi_effect" not in cn
    except Exception:
        return False


class ScaffoldHandler:
    """Mixin class for scaffold command handlers."""

    @command("create_locator_at", write=True)
    def _create_locator_at(self, params):
        """Create a named locator (cue point) at a specific beat position.

        If a cue point already exists at the target position, renames it
        instead of toggling it off.

        Params:
            beat_position: Beat position (float) for the locator.
            name: Display name for the locator.

        Returns:
            name, beat_position, existed (bool).
        """
        beat_position = float(params["beat_position"])
        name = str(params["name"])

        try:
            # Check if cue already exists at this position (toggle safety)
            for cp in self._song.cue_points:
                if abs(cp.time - beat_position) < 0.001:
                    # Rename existing cue instead of toggling it off
                    cp.name = name
                    return {"name": name, "beat_position": beat_position, "existed": True}

            # Save playhead, create cue, name it, restore
            original_position = self._song.current_song_time
            self._song.current_song_time = beat_position
            self._song.set_or_delete_cue()

            # Find newly created cue point
            for cp in self._song.cue_points:
                if abs(cp.time - beat_position) < 0.001:
                    cp.name = name
                    break

            self._song.current_song_time = original_position
            return {"name": name, "beat_position": beat_position, "existed": False}
        except Exception as e:
            self.log_message(f"Error creating locator: {e}")
            raise

    @command("get_arrangement_state")
    def _get_arrangement_state(self, params=None):
        """Read arrangement state: cue points, tracks, song length, time sig.

        Returns:
            cue_points: List of {name, time} dicts from song cue points.
            tracks: List of {"index": int, "name": str, "has_instrument": bool, "has_clips": bool} dicts.
            song_length: Total song length in beats.
            signature_numerator: Time signature numerator.
            signature_denominator: Time signature denominator.
        """
        cue_points = []
        for cp in self._song.cue_points:
            cue_points.append({"name": cp.name, "time": cp.time})

        tracks = []
        for i, track in enumerate(self._song.tracks):
            tracks.append({
                "index": i,
                "name": track.name,
                "has_instrument": any(_is_instrument_device(d) for d in track.devices),
                "has_clips": len(track.arrangement_clips) > 0,
            })

        return {
            "cue_points": cue_points,
            "tracks": tracks,
            "song_length": self._song.song_length,
            "signature_numerator": self._song.signature_numerator,
            "signature_denominator": self._song.signature_denominator,
        }

    @command("scaffold_tracks", write=True)
    def _scaffold_tracks(self, params):
        """Create multiple named MIDI tracks in one operation.

        Params:
            track_names: List of track name strings.

        Returns:
            created_tracks (list of {index, name}), count.
        """
        track_names = params["track_names"]

        try:
            created = []
            for name in track_names:
                self._song.create_midi_track(-1)
                new_track = self._song.tracks[len(self._song.tracks) - 1]
                new_track.name = name
                created.append({"index": len(self._song.tracks) - 1, "name": name})
            return {"created_tracks": created, "count": len(created)}
        except Exception as e:
            self.log_message(f"Error scaffolding tracks: {e}")
            raise
