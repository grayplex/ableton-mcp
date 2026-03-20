"""Clip handlers: create, rename, fire, stop, delete, duplicate, info, color, loop."""

from AbletonMCP_Remote_Script.handlers.tracks import COLOR_NAMES, COLOR_INDEX_TO_NAME
from AbletonMCP_Remote_Script.registry import command


def _resolve_clip_slot(song, track_index, clip_index):
    """Resolve a clip slot from track and clip indices.

    Returns:
        (clip_slot, track) tuple.

    Raises:
        IndexError: If track or clip index out of range.
    """
    if track_index < 0 or track_index >= len(song.tracks):
        raise IndexError(
            f"Track index {track_index} out of range "
            f"(0-{len(song.tracks) - 1})"
        )
    track = song.tracks[track_index]
    if clip_index < 0 or clip_index >= len(track.clip_slots):
        raise IndexError(
            f"Clip index {clip_index} out of range "
            f"(0-{len(track.clip_slots) - 1})"
        )
    return track.clip_slots[clip_index], track


def _clip_info_dict(clip):
    """Build standard clip info dictionary."""
    return {
        "name": clip.name,
        "length": clip.length,
        "color": COLOR_INDEX_TO_NAME.get(clip.color_index, f"unknown_{clip.color_index}"),
        "color_index": clip.color_index,
        "loop_enabled": clip.looping,
        "loop_start": clip.loop_start,
        "loop_end": clip.loop_end,
        "start_marker": clip.start_marker,
        "end_marker": clip.end_marker,
        "is_playing": clip.is_playing,
        "is_triggered": clip.is_triggered,
        "is_audio_clip": clip.is_audio_clip,
        "signature_numerator": clip.signature_numerator,
        "signature_denominator": clip.signature_denominator,
    }


class ClipHandlers:
    """Mixin class for clip command handlers."""

    @command("create_clip", write=True)
    def _create_clip(self, params):
        """Create a new MIDI clip in the specified track and clip slot."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        length = params.get("length", 4.0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

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
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

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
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip_name = clip_slot.clip.name
            clip_slot.fire()

            return {
                "fired": True,
                "is_playing": clip_slot.clip.is_playing,
                "clip_name": clip_name,
            }
        except Exception as e:
            self.log_message(f"Error firing clip: {e}")
            raise

    @command("stop_clip", write=True)
    def _stop_clip(self, params):
        """Stop a clip slot. Works on both occupied and empty slots."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )
            clip_slot.stop()

            if clip_slot.has_clip:
                return {"stopped": True, "clip_name": clip_slot.clip.name}
            return {"stopped": True}
        except Exception as e:
            self.log_message(f"Error stopping clip: {e}")
            raise

    @command("delete_clip", write=True)
    def _delete_clip(self, params):
        """Delete a clip from the specified slot."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception(
                    f"No clip in slot {clip_index} on track '{track.name}' "
                    f"(track {track_index})"
                )

            clip_name = clip_slot.clip.name
            clip_slot.delete_clip()

            return {"deleted": True, "clip_name": clip_name}
        except Exception as e:
            self.log_message(f"Error deleting clip: {e}")
            raise

    @command("duplicate_clip", write=True)
    def _duplicate_clip(self, params):
        """Duplicate a clip to a target slot."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        target_track_index = params.get("target_track_index", 0)
        target_clip_index = params.get("target_clip_index", 0)
        try:
            source_slot, source_track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )
            target_slot, target_track = _resolve_clip_slot(
                self._song, target_track_index, target_clip_index
            )

            if not source_slot.has_clip:
                raise Exception(
                    f"No clip in source slot {clip_index} on track "
                    f"'{source_track.name}' (track {track_index})"
                )

            if target_slot.has_clip:
                raise Exception(
                    f"Target slot {target_clip_index} on track "
                    f"'{target_track.name}' already has a clip "
                    f"('{target_slot.clip.name}'). Delete it first."
                )

            source_slot.duplicate_clip_to(target_slot)

            new_clip = target_slot.clip
            return {
                "name": new_clip.name,
                "length": new_clip.length,
                "target_track_index": target_track_index,
                "target_clip_index": target_clip_index,
            }
        except Exception as e:
            self.log_message(f"Error duplicating clip: {e}")
            raise

    @command("get_clip_info")
    def _get_clip_info(self, params):
        """Get detailed info about a clip, or slot status if empty."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                return {
                    "has_clip": False,
                    "slot_index": clip_index,
                    "track_index": track_index,
                    "track_name": track.name,
                }

            clip = clip_slot.clip
            info = _clip_info_dict(clip)
            info["has_clip"] = True
            return info
        except Exception as e:
            self.log_message(f"Error getting clip info: {e}")
            raise

    @command("set_clip_color", write=True)
    def _set_clip_color(self, params):
        """Set clip color by friendly name."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        color = params.get("color", "")
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception(
                    f"No clip in slot {clip_index} on track '{track.name}' "
                    f"(track {track_index})"
                )

            if color not in COLOR_NAMES:
                valid = ", ".join(sorted(COLOR_NAMES.keys()))
                raise ValueError(
                    f"Unknown color '{color}'. Valid colors: {valid}"
                )

            clip = clip_slot.clip
            clip.color_index = COLOR_NAMES[color]

            return {
                "name": clip.name,
                "color": color,
                "color_index": clip.color_index,
            }
        except Exception as e:
            self.log_message(f"Error setting clip color: {e}")
            raise

    @command("get_clip_launch_settings")
    def _get_clip_launch_settings(self, params):
        """Get clip launch settings (mode, quantization, legato, velocity)."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip
            return {
                "clip_name": clip.name,
                "launch_mode": clip.launch_mode,
                "launch_quantization": clip.launch_quantization,
                "legato": clip.legato,
                "velocity_amount": clip.velocity_amount,
            }
        except Exception as e:
            self.log_message(f"Error getting clip launch settings: {e}")
            raise

    @command("set_clip_launch_settings", write=True)
    def _set_clip_launch_settings(self, params):
        """Set clip launch settings (mode, quantization, legato, velocity).

        launch_mode: 0=Trigger, 1=Gate, 2=Toggle, 3=Repeat
        launch_quantization: 0-14
        legato: bool
        velocity_amount: 0.0-1.0
        """
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            launch_mode = params.get("launch_mode")
            if launch_mode is not None:
                if not (0 <= launch_mode <= 3):
                    raise ValueError(
                        f"launch_mode {launch_mode} out of range (0-3). "
                        f"Current value: {clip.launch_mode}"
                    )
                clip.launch_mode = launch_mode

            launch_quantization = params.get("launch_quantization")
            if launch_quantization is not None:
                if not (0 <= launch_quantization <= 14):
                    raise ValueError(
                        f"launch_quantization {launch_quantization} out of range (0-14). "
                        f"Current value: {clip.launch_quantization}"
                    )
                clip.launch_quantization = launch_quantization

            legato = params.get("legato")
            if legato is not None:
                clip.legato = legato

            velocity_amount = params.get("velocity_amount")
            if velocity_amount is not None:
                if not (0.0 <= velocity_amount <= 1.0):
                    raise ValueError(
                        f"velocity_amount {velocity_amount} out of range (0.0-1.0). "
                        f"Current value: {clip.velocity_amount}"
                    )
                clip.velocity_amount = velocity_amount

            return {
                "clip_name": clip.name,
                "launch_mode": clip.launch_mode,
                "launch_quantization": clip.launch_quantization,
                "legato": clip.legato,
                "velocity_amount": clip.velocity_amount,
            }
        except Exception as e:
            self.log_message(f"Error setting clip launch settings: {e}")
            raise

    @command("set_clip_muted", write=True)
    def _set_clip_muted(self, params):
        """Set clip muted/active state (clip activator)."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        muted = params.get("muted", False)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip
            clip.muted = muted

            return {"clip_name": clip.name, "muted": clip.muted}
        except Exception as e:
            self.log_message(f"Error setting clip muted: {e}")
            raise

    @command("crop_clip", write=True)
    def _crop_clip(self, params):
        """Crop clip to loop/markers."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip
            clip.crop()

            return {
                "cropped": True,
                "clip_name": clip.name,
                "length": clip.length,
            }
        except Exception as e:
            self.log_message(f"Error cropping clip: {e}")
            raise

    @command("duplicate_clip_loop", write=True)
    def _duplicate_clip_loop(self, params):
        """Double the loop length and duplicate the content."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip
            clip.duplicate_loop()

            return {
                "duplicated": True,
                "clip_name": clip.name,
                "length": clip.length,
                "loop_end": clip.loop_end,
            }
        except Exception as e:
            self.log_message(f"Error duplicating clip loop: {e}")
            raise

    @command("duplicate_clip_region", write=True)
    def _duplicate_clip_region(self, params):
        """Duplicate a region within a clip to a destination time."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        region_start = params.get("region_start", 0.0)
        region_end = params.get("region_end", 0.0)
        destination_time = params.get("destination_time", 0.0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip
            clip.duplicate_region(region_start, region_end, destination_time)

            return {
                "duplicated": True,
                "clip_name": clip.name,
                "region_start": region_start,
                "region_end": region_end,
                "destination_time": destination_time,
            }
        except Exception as e:
            self.log_message(f"Error duplicating clip region: {e}")
            raise

    @command("set_clip_groove", write=True)
    def _set_clip_groove(self, params):
        """Assign a groove from the groove pool to a clip, or clear it."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        groove_index = params.get("groove_index")
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if groove_index is None:
                clip.groove = None
                return {
                    "clip_name": clip.name,
                    "has_groove": False,
                    "groove": None,
                }

            grooves = self._song.groove_pool.grooves
            if groove_index < 0 or groove_index >= len(grooves):
                raise IndexError(
                    f"Groove index {groove_index} out of range "
                    f"(0-{len(grooves) - 1})"
                )
            groove = grooves[groove_index]
            clip.groove = groove

            return {
                "clip_name": clip.name,
                "has_groove": clip.has_groove,
                "groove_index": groove_index,
                "groove_name": groove.name,
            }
        except Exception as e:
            self.log_message(f"Error setting clip groove: {e}")
            raise

    @command("create_session_audio_clip", write=True)
    def _create_session_audio_clip(self, params):
        """Create an audio clip in a session view clip slot from a file path."""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        file_path = params.get("file_path")
        try:
            if file_path is None:
                raise ValueError("file_path parameter is required")

            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            clip_slot.create_audio_clip(file_path)

            return {
                "created": True,
                "track_name": track.name,
                "track_index": track_index,
                "clip_index": clip_index,
                "file_path": file_path,
                "clip_name": clip_slot.clip.name if clip_slot.has_clip else None,
            }
        except Exception as e:
            self.log_message(f"Error creating session audio clip: {e}")
            raise

    @command("set_clip_loop", write=True)
    def _set_clip_loop(self, params):
        """Set loop/region properties on a clip.

        Optional params: enabled, loop_start, loop_end, start_marker, end_marker.
        All position values are in beats (float).
        Returns all current loop/marker values regardless of what was changed.
        """
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception(
                    f"No clip in slot {clip_index} on track '{track.name}' "
                    f"(track {track_index})"
                )

            clip = clip_slot.clip

            # Apply enabled first (Pitfall 3: so loop points can diverge
            # from markers)
            if "enabled" in params:
                clip.looping = params["enabled"]

            # Validate and apply loop_start / loop_end with safe ordering
            # (Pitfall 1)
            new_start = params.get("loop_start")
            new_end = params.get("loop_end")

            if new_start is not None and new_end is not None:
                if new_end <= new_start:
                    raise ValueError(
                        f"loop_end ({new_end}) must be greater than "
                        f"loop_start ({new_start}). "
                        f"Current values: loop_start={clip.loop_start}, "
                        f"loop_end={clip.loop_end}"
                    )
                # Safe ordering: widen first, then narrow
                if new_end > clip.loop_end:
                    clip.loop_end = new_end
                    clip.loop_start = new_start
                else:
                    clip.loop_start = new_start
                    clip.loop_end = new_end
            elif new_start is not None:
                if new_start >= clip.loop_end:
                    raise ValueError(
                        f"loop_start ({new_start}) must be less than "
                        f"current loop_end ({clip.loop_end}). "
                        f"Current values: loop_start={clip.loop_start}, "
                        f"loop_end={clip.loop_end}"
                    )
                clip.loop_start = new_start
            elif new_end is not None:
                if new_end <= clip.loop_start:
                    raise ValueError(
                        f"loop_end ({new_end}) must be greater than "
                        f"current loop_start ({clip.loop_start}). "
                        f"Current values: loop_start={clip.loop_start}, "
                        f"loop_end={clip.loop_end}"
                    )
                clip.loop_end = new_end

            # Validate and apply start_marker / end_marker with same safe
            # ordering pattern
            new_sm = params.get("start_marker")
            new_em = params.get("end_marker")

            if new_sm is not None and new_em is not None:
                if new_em <= new_sm:
                    raise ValueError(
                        f"end_marker ({new_em}) must be greater than "
                        f"start_marker ({new_sm}). "
                        f"Current values: start_marker={clip.start_marker}, "
                        f"end_marker={clip.end_marker}"
                    )
                # Safe ordering: widen first, then narrow
                if new_em > clip.end_marker:
                    clip.end_marker = new_em
                    clip.start_marker = new_sm
                else:
                    clip.start_marker = new_sm
                    clip.end_marker = new_em
            elif new_sm is not None:
                if new_sm >= clip.end_marker:
                    raise ValueError(
                        f"start_marker ({new_sm}) must be less than "
                        f"current end_marker ({clip.end_marker}). "
                        f"Current values: start_marker={clip.start_marker}, "
                        f"end_marker={clip.end_marker}"
                    )
                clip.start_marker = new_sm
            elif new_em is not None:
                if new_em <= clip.start_marker:
                    raise ValueError(
                        f"end_marker ({new_em}) must be greater than "
                        f"current start_marker ({clip.start_marker}). "
                        f"Current values: start_marker={clip.start_marker}, "
                        f"end_marker={clip.end_marker}"
                    )
                clip.end_marker = new_em

            # Always echo ALL current values
            return {
                "loop_enabled": clip.looping,
                "loop_start": clip.loop_start,
                "loop_end": clip.loop_end,
                "start_marker": clip.start_marker,
                "end_marker": clip.end_marker,
            }
        except Exception as e:
            self.log_message(f"Error setting clip loop: {e}")
            raise
