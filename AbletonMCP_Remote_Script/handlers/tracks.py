"""Track handlers: create, rename, query tracks."""

from AbletonMCP_Remote_Script.registry import command


class TrackHandlers:
    """Mixin class for track command handlers."""

    @command("create_midi_track", write=True)
    def _create_midi_track(self, params):
        """Create a new MIDI track at the specified index."""
        index = params.get("index", -1)
        try:
            self._song.create_midi_track(index)

            new_track_index = len(self._song.tracks) - 1 if index == -1 else index
            new_track = self._song.tracks[new_track_index]

            return {
                "index": new_track_index,
                "name": new_track.name,
            }
        except Exception as e:
            self.log_message(f"Error creating MIDI track: {e}")
            raise

    @command("set_track_name", write=True)
    def _set_track_name(self, params):
        """Set the name of a track."""
        track_index = params.get("track_index", 0)
        name = params.get("name", "")
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]
            track.name = name

            return {"name": track.name}
        except Exception as e:
            self.log_message(f"Error setting track name: {e}")
            raise

    @command("get_track_info")
    def _get_track_info(self, params):
        """Get information about a track."""
        track_index = params.get("track_index", 0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            # Get clip slots
            clip_slots = []
            for slot_index, slot in enumerate(track.clip_slots):
                clip_info = None
                if slot.has_clip:
                    clip = slot.clip
                    clip_info = {
                        "name": clip.name,
                        "length": clip.length,
                        "is_playing": clip.is_playing,
                        "is_recording": clip.is_recording,
                    }

                clip_slots.append(
                    {
                        "index": slot_index,
                        "has_clip": slot.has_clip,
                        "clip": clip_info,
                    }
                )

            # Get devices
            devices = []
            for device_index, device in enumerate(track.devices):
                devices.append(
                    {
                        "index": device_index,
                        "name": device.name,
                        "class_name": device.class_name,
                        "type": self._get_device_type(device),
                    }
                )

            result = {
                "index": track_index,
                "name": track.name,
                "is_audio_track": track.has_audio_input,
                "is_midi_track": track.has_midi_input,
                "mute": track.mute,
                "solo": track.solo,
                "arm": track.arm,
                "volume": track.mixer_device.volume.value,
                "panning": track.mixer_device.panning.value,
                "clip_slots": clip_slots,
                "devices": devices,
            }
            return result
        except Exception as e:
            self.log_message(f"Error getting track info: {e}")
            raise
