"""Arrangement handlers: arrangement clip CRUD and session-to-arrangement bridge."""

from AbletonMCP_Remote_Script.handlers.clips import _clip_info_dict, _resolve_clip_slot
from AbletonMCP_Remote_Script.handlers.tracks import _resolve_track, COLOR_INDEX_TO_NAME
from AbletonMCP_Remote_Script.registry import command


class ArrangementHandlers:
    """Mixin class for arrangement clip command handlers."""

    @command("create_arrangement_midi_clip", write=True)
    def _create_arrangement_midi_clip(self, params):
        """Create a MIDI clip in the arrangement view at the specified position.

        Params:
            track_index: Index of the track.
            start_time: Start position in beats.
            length: Clip length in beats.
            track_type: "track", "return", or "master" (default "track").

        Returns:
            created, track_name, start_time, length.
        """
        track_index = params.get("track_index", 0)
        start_time = params.get("start_time", 0.0)
        length = params.get("length", 4.0)
        track_type = params.get("track_type", "track")

        try:
            track = _resolve_track(self._song, track_type, track_index)
            track.create_midi_clip(start_time, length)

            return {
                "created": True,
                "track_name": track.name,
                "start_time": start_time,
                "length": length,
            }
        except Exception as e:
            self.log_message(f"Error creating arrangement MIDI clip: {e}")
            raise

    @command("create_arrangement_audio_clip", write=True)
    def _create_arrangement_audio_clip(self, params):
        """Create an audio clip in the arrangement view from a file.

        Params:
            track_index: Index of the track.
            file_path: Path to the audio file.
            position: Position in beats.
            track_type: "track", "return", or "master" (default "track").

        Returns:
            created, track_name, file_path, position.
        """
        track_index = params.get("track_index", 0)
        file_path = params.get("file_path")
        position = params.get("position", 0.0)
        track_type = params.get("track_type", "track")

        try:
            if file_path is None:
                raise ValueError("file_path parameter is required")

            track = _resolve_track(self._song, track_type, track_index)
            track.create_audio_clip(file_path, position)

            return {
                "created": True,
                "track_name": track.name,
                "file_path": file_path,
                "position": position,
            }
        except Exception as e:
            self.log_message(f"Error creating arrangement audio clip: {e}")
            raise

    @command("get_arrangement_clips")
    def _get_arrangement_clips(self, params):
        """Get all arrangement clips on a track.

        Params:
            track_index: Index of the track.
            track_type: "track", "return", or "master" (default "track").

        Returns:
            track_name, clips list with name, start_time, end_time, length,
            is_audio_clip, color.
        """
        track_index = params.get("track_index", 0)
        track_type = params.get("track_type", "track")

        try:
            track = _resolve_track(self._song, track_type, track_index)
            clips = []
            for clip in track.arrangement_clips:
                clips.append({
                    "name": clip.name,
                    "start_time": clip.start_time,
                    "end_time": clip.end_time,
                    "length": clip.length,
                    "is_audio_clip": clip.is_audio_clip,
                    "color": COLOR_INDEX_TO_NAME.get(
                        clip.color_index, f"unknown_{clip.color_index}"
                    ),
                })

            return {
                "track_name": track.name,
                "clips": clips,
            }
        except Exception as e:
            self.log_message(f"Error getting arrangement clips: {e}")
            raise

    @command("duplicate_clip_to_arrangement", write=True)
    def _duplicate_clip_to_arrangement(self, params):
        """Copy a session clip to the arrangement at the specified time.

        Params:
            track_index: Index of the track.
            clip_index: Index of the clip slot in session view.
            arrangement_time: Target position in beats on the arrangement timeline.

        Returns:
            duplicated, clip_name, arrangement_time.
        """
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        arrangement_time = params.get("arrangement_time", 0.0)

        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise ValueError(
                    f"No clip in slot {clip_index} on track '{track.name}' "
                    f"(track {track_index})"
                )

            clip = clip_slot.clip
            track.duplicate_clip_to_arrangement(clip, arrangement_time)

            return {
                "duplicated": True,
                "clip_name": clip.name,
                "arrangement_time": arrangement_time,
            }
        except Exception as e:
            self.log_message(f"Error duplicating clip to arrangement: {e}")
            raise
