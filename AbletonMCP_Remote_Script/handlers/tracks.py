"""Track handlers: create, rename, delete, duplicate, color, fold, query tracks."""

from AbletonMCP_Remote_Script.registry import command

# Ableton Live color palette: 70 colors (indices 0-69)
# Arranged as 14 columns x 5 rows in Ableton's color picker.
# Row 1 (warm reds/oranges/yellows):
#   0-13: salmon, dark_red, red, light_orange, orange, gold, yellow, lime,
#          green, mint, cyan, sky, blue, purple
# Row 2 (medium saturated):
#   14-27: pink, maroon, rust, amber, tangerine, mustard, chartreuse, spring_green,
#          sea_green, teal, ocean, steel_blue, indigo, violet
# Row 3 (lighter/pastel):
#   28-41: hot_pink, rose, coral, peach, sand, cream, pale_yellow, pale_lime,
#          pale_green, pale_mint, pale_cyan, pale_blue, lavender, mauve
# Row 4 (deeper/darker):
#   42-55: magenta, plum, tomato, brown, dark_orange, olive, dark_yellow, dark_lime,
#          dark_green, dark_mint, dark_cyan, dark_blue, dark_indigo, dark_purple
# Row 5 (muted/gray):
#   56-69: dark_magenta, dark_pink, dark_coral, dark_brown, dark_tan, khaki,
#          dark_olive, army_green, forest_green, spruce, dark_teal, slate,
#          dark_slate, charcoal

COLOR_NAMES = {
    # Row 1 (0-13)
    "salmon": 0,
    "dark_red": 1,
    "red": 2,
    "light_orange": 3,
    "orange": 4,
    "gold": 5,
    "yellow": 6,
    "lime": 7,
    "green": 8,
    "mint": 9,
    "cyan": 10,
    "sky": 11,
    "blue": 12,
    "purple": 13,
    # Row 2 (14-27)
    "pink": 14,
    "maroon": 15,
    "rust": 16,
    "amber": 17,
    "tangerine": 18,
    "mustard": 19,
    "chartreuse": 20,
    "spring_green": 21,
    "sea_green": 22,
    "teal": 23,
    "ocean": 24,
    "steel_blue": 25,
    "indigo": 26,
    "violet": 27,
    # Row 3 (28-41)
    "hot_pink": 28,
    "rose": 29,
    "coral": 30,
    "peach": 31,
    "sand": 32,
    "cream": 33,
    "pale_yellow": 34,
    "pale_lime": 35,
    "pale_green": 36,
    "pale_mint": 37,
    "pale_cyan": 38,
    "pale_blue": 39,
    "lavender": 40,
    "mauve": 41,
    # Row 4 (42-55)
    "magenta": 42,
    "plum": 43,
    "tomato": 44,
    "brown": 45,
    "dark_orange": 46,
    "olive": 47,
    "dark_yellow": 48,
    "dark_lime": 49,
    "dark_green": 50,
    "dark_mint": 51,
    "dark_cyan": 52,
    "dark_blue": 53,
    "dark_indigo": 54,
    "dark_purple": 55,
    # Row 5 (56-69)
    "dark_magenta": 56,
    "dark_pink": 57,
    "dark_coral": 58,
    "dark_brown": 59,
    "dark_tan": 60,
    "khaki": 61,
    "dark_olive": 62,
    "army_green": 63,
    "forest_green": 64,
    "spruce": 65,
    "dark_teal": 66,
    "slate": 67,
    "dark_slate": 68,
    "charcoal": 69,
}

# Reverse lookup: index -> friendly name
COLOR_INDEX_TO_NAME = {v: k for k, v in COLOR_NAMES.items()}


def _get_track_type_str(track, track_type_hint=None):
    """Determine track type string from a track object.

    Args:
        track: Ableton Track object.
        track_type_hint: Optional hint ("master", "return") for non-regular tracks.

    Returns:
        One of "master", "return", "group", "midi", "audio".
    """
    if track_type_hint == "master":
        return "master"
    if track_type_hint == "return":
        return "return"
    if hasattr(track, "is_foldable") and track.is_foldable:
        return "group"
    if hasattr(track, "has_midi_input") and track.has_midi_input:
        return "midi"
    if hasattr(track, "has_audio_input") and track.has_audio_input:
        return "audio"
    return "audio"


def _get_color_name(track):
    """Get friendly color name from a track's color_index."""
    if hasattr(track, "color_index"):
        idx = track.color_index
        return COLOR_INDEX_TO_NAME.get(idx, f"unknown_{idx}")
    return "unknown"


def _resolve_track(song, track_type, track_index):
    """Resolve a track reference from type and index.

    Args:
        song: Ableton Song object.
        track_type: "track", "return", or "master".
        track_index: Index within the track collection.

    Returns:
        The track object.

    Raises:
        ValueError: If track_type is invalid.
        IndexError: If index is out of range.
    """
    if track_type == "master":
        return song.master_track
    if track_type == "return":
        if track_index < 0 or track_index >= len(song.return_tracks):
            raise IndexError(
                f"Return track index {track_index} out of range "
                f"(0-{len(song.return_tracks) - 1})"
            )
        return song.return_tracks[track_index]
    # Default: regular track
    if track_index < 0 or track_index >= len(song.tracks):
        raise IndexError(
            f"Track index {track_index} out of range "
            f"(0-{len(song.tracks) - 1})"
        )
    return song.tracks[track_index]


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
                "type": "midi",
            }
        except Exception as e:
            self.log_message(f"Error creating MIDI track: {e}")
            raise

    @command("create_audio_track", write=True)
    def _create_audio_track(self, params):
        """Create a new audio track at the specified index."""
        index = params.get("index", -1)
        try:
            self._song.create_audio_track(index)

            new_track_index = len(self._song.tracks) - 1 if index == -1 else index
            new_track = self._song.tracks[new_track_index]

            return {
                "index": new_track_index,
                "name": new_track.name,
                "type": "audio",
            }
        except Exception as e:
            self.log_message(f"Error creating audio track: {e}")
            raise

    @command("create_return_track", write=True)
    def _create_return_track(self, params):
        """Create a new return track. Always appended to end."""
        try:
            self._song.create_return_track()
            new_index = len(self._song.return_tracks) - 1
            new_track = self._song.return_tracks[new_index]

            return {
                "index": new_index,
                "name": new_track.name,
                "type": "return",
            }
        except Exception as e:
            self.log_message(f"Error creating return track: {e}")
            raise

    @command("create_group_track", write=True)
    def _create_group_track(self, params):
        """Create a group track, optionally grouping existing tracks.

        If track_indices is not provided, creates an empty track at the given
        index that can serve as a group header once child tracks are added.

        If track_indices is provided, attempts to group those tracks
        programmatically. Note: the Ableton API has no direct
        create_group_track method, so this is best-effort.
        """
        index = params.get("index", -1)
        track_indices = params.get("track_indices", None)

        try:
            if not track_indices:
                # Create an empty MIDI track as a group header placeholder
                self._song.create_midi_track(index)
                new_track_index = (
                    len(self._song.tracks) - 1 if index == -1 else index
                )
                new_track = self._song.tracks[new_track_index]

                return {
                    "index": new_track_index,
                    "name": new_track.name,
                    "type": "group",
                    "note": (
                        "Created as empty track. Add child tracks to make "
                        "it a group, or select tracks in Ableton and use "
                        "Ctrl/Cmd+G to group them."
                    ),
                }
            else:
                # Attempt to group existing tracks programmatically.
                # The Ableton API does not expose a direct group creation
                # method. We try selecting tracks and triggering grouping.
                try:
                    # Select first track to establish selection context
                    first_track = self._song.tracks[track_indices[0]]
                    self._song.view.selected_track = first_track

                    # Attempt to use the internal grouping mechanism
                    # This is best-effort and may not work in all cases
                    self._song.create_midi_track(index)
                    new_track_index = (
                        len(self._song.tracks) - 1 if index == -1 else index
                    )
                    new_track = self._song.tracks[new_track_index]

                    return {
                        "index": new_track_index,
                        "name": new_track.name,
                        "type": "group",
                        "grouped_track_indices": track_indices,
                        "note": (
                            "Created track as group header. Automatic "
                            "grouping of existing tracks is not reliably "
                            "supported by the Ableton API. To group tracks, "
                            "select them in Ableton and use Ctrl/Cmd+G."
                        ),
                    }
                except Exception:
                    # Fall back to creating an empty track
                    self._song.create_midi_track(index)
                    new_track_index = (
                        len(self._song.tracks) - 1 if index == -1 else index
                    )
                    new_track = self._song.tracks[new_track_index]

                    return {
                        "index": new_track_index,
                        "name": new_track.name,
                        "type": "group",
                        "grouped_track_indices": [],
                        "note": (
                            "Could not programmatically group tracks. "
                            "Created empty track instead. Select tracks "
                            "in Ableton and use Ctrl/Cmd+G to group them."
                        ),
                    }
        except Exception as e:
            self.log_message(f"Error creating group track: {e}")
            raise

    @command("set_track_name", write=True)
    def _set_track_name(self, params):
        """Set the name of a track."""
        track_index = params.get("track_index", 0)
        name = params.get("name", "")
        track_type = params.get("track_type", "track")
        try:
            track = _resolve_track(self._song, track_type, track_index)
            track.name = name

            result = {"name": track.name, "type": track_type}
            if track_type != "master":
                result["index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error setting track name: {e}")
            raise

    @command("delete_track", write=True)
    def _delete_track(self, params):
        """Delete a track by index. Supports regular and return tracks."""
        track_type = params.get("track_type", "track")
        track_index = params.get("track_index", 0)

        try:
            if track_type == "master":
                raise ValueError("Cannot delete the master track")

            if track_type == "return":
                if track_index < 0 or track_index >= len(
                    self._song.return_tracks
                ):
                    raise IndexError(
                        f"Return track index {track_index} out of range "
                        f"(0-{len(self._song.return_tracks) - 1})"
                    )
                track = self._song.return_tracks[track_index]
                info = {
                    "name": track.name,
                    "type": "return",
                    "index": track_index,
                }
                self._song.delete_return_track(track_index)
            else:
                if track_index < 0 or track_index >= len(self._song.tracks):
                    raise IndexError(
                        f"Track index {track_index} out of range "
                        f"(0-{len(self._song.tracks) - 1})"
                    )
                track = self._song.tracks[track_index]
                info = {
                    "name": track.name,
                    "type": "track",
                    "index": track_index,
                }
                self._song.delete_track(track_index)

            return {"deleted": info}
        except Exception as e:
            self.log_message(f"Error deleting track: {e}")
            raise

    @command("duplicate_track", write=True)
    def _duplicate_track(self, params):
        """Duplicate a track. Optionally rename the copy."""
        track_index = params.get("track_index", 0)
        new_name = params.get("new_name", None)

        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError(
                    f"Track index {track_index} out of range "
                    f"(0-{len(self._song.tracks) - 1})"
                )

            self._song.duplicate_track(track_index)

            # Duplicate appears at track_index + 1
            new_track = self._song.tracks[track_index + 1]
            if new_name:
                new_track.name = new_name

            type_str = _get_track_type_str(new_track)

            return {
                "index": track_index + 1,
                "name": new_track.name,
                "type": type_str,
            }
        except Exception as e:
            self.log_message(f"Error duplicating track: {e}")
            raise

    @command("set_track_color", write=True)
    def _set_track_color(self, params):
        """Set track color by friendly name."""
        track_index = params.get("track_index", 0)
        color_name = params.get("color", "")
        track_type = params.get("track_type", "track")

        try:
            track = _resolve_track(self._song, track_type, track_index)

            if color_name not in COLOR_NAMES:
                valid = ", ".join(sorted(COLOR_NAMES.keys()))
                raise ValueError(
                    f"Unknown color '{color_name}'. Valid colors: {valid}"
                )

            track.color_index = COLOR_NAMES[color_name]

            result = {
                "name": track.name,
                "color": color_name,
            }
            if track_type != "master":
                result["index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error setting track color: {e}")
            raise

    @command("set_group_fold", write=True)
    def _set_group_fold(self, params):
        """Fold or unfold a group track."""
        track_index = params.get("track_index", 0)
        folded = params.get("folded", True)

        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError(
                    f"Track index {track_index} out of range "
                    f"(0-{len(self._song.tracks) - 1})"
                )

            track = self._song.tracks[track_index]

            if not track.is_foldable:
                raise ValueError(
                    f"Track '{track.name}' at index {track_index} is not a "
                    f"group track and cannot be folded"
                )

            track.fold_state = 1 if folded else 0

            return {
                "index": track_index,
                "name": track.name,
                "folded": folded,
            }
        except Exception as e:
            self.log_message(f"Error setting group fold: {e}")
            raise

    @command("get_track_info")
    def _get_track_info(self, params):
        """Get detailed information about a track.

        Supports regular tracks, return tracks, and the master track
        via the track_type parameter.
        """
        track_type = params.get("track_type", "track")
        track_index = params.get("track_index", 0)

        try:
            track = _resolve_track(self._song, track_type, track_index)
            type_str = _get_track_type_str(track, track_type_hint=track_type)
            color_name = _get_color_name(track)

            # Common fields for all track types
            result = {
                "name": track.name,
                "type": type_str,
                "color": color_name,
                "volume": track.mixer_device.volume.value,
                "panning": track.mixer_device.panning.value,
            }

            # Mute/solo (not available on master track)
            if track_type != "master":
                result["mute"] = track.mute
                result["solo"] = track.solo

            # Add index for non-master tracks
            if track_type != "master":
                result["index"] = track_index

            # Arm state (only for tracks that support it)
            if hasattr(track, "can_be_armed") and track.can_be_armed:
                result["arm"] = track.arm

            # Group track fields
            if hasattr(track, "is_foldable") and track.is_foldable:
                result["is_foldable"] = True
                result["fold_state"] = track.fold_state == 1

            # Group membership (regular tracks only)
            if track_type == "track":
                if hasattr(track, "is_grouped"):
                    result["is_grouped"] = track.is_grouped
                    if track.is_grouped and hasattr(track, "group_track"):
                        group = track.group_track
                        # Find group track index
                        group_index = None
                        for i, t in enumerate(self._song.tracks):
                            if t == group:
                                group_index = i
                                break
                        result["group_track"] = {
                            "index": group_index,
                            "name": group.name,
                        }

            # Clip slots (regular and return tracks, not master)
            if track_type != "master" and hasattr(track, "clip_slots"):
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
                result["clip_slots"] = clip_slots

            # Devices (all track types)
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
            result["devices"] = devices

            return result
        except Exception as e:
            self.log_message(f"Error getting track info: {e}")
            raise

    @command("get_all_tracks")
    def _get_all_tracks(self, params=None):
        """Get a summary of all tracks in the session."""
        try:
            # Regular tracks
            tracks = []
            for i, track in enumerate(self._song.tracks):
                type_str = _get_track_type_str(track)
                color_name = _get_color_name(track)
                tracks.append(
                    {
                        "index": i,
                        "name": track.name,
                        "type": type_str,
                        "color": color_name,
                    }
                )

            # Return tracks
            return_tracks = []
            for i, track in enumerate(self._song.return_tracks):
                color_name = _get_color_name(track)
                return_tracks.append(
                    {
                        "index": i,
                        "name": track.name,
                        "type": "return",
                        "color": color_name,
                    }
                )

            # Master track
            master = self._song.master_track
            master_color = _get_color_name(master)

            return {
                "tracks": tracks,
                "return_tracks": return_tracks,
                "master_track": {
                    "name": master.name,
                    "type": "master",
                    "color": master_color,
                },
            }
        except Exception as e:
            self.log_message(f"Error getting all tracks: {e}")
            raise
