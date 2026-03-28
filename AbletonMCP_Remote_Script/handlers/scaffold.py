"""Scaffold handlers: create locators and batch-create named tracks."""

from AbletonMCP_Remote_Script.registry import command


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
