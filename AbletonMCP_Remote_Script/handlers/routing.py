"""Routing handlers: get/set input and output routing types for all track types."""

from AbletonMCP_Remote_Script.registry import command
from AbletonMCP_Remote_Script.handlers.tracks import _resolve_track


class RoutingHandlers:
    """Mixin class for track routing command handlers.

    Provides input/output routing inspection and control
    for regular, return, and master tracks.
    """

    @command("get_input_routing_types")
    def _get_input_routing_types(self, params):
        """Get available input routing types for a track."""
        track_type = params.get("track_type", "track")
        track_index = params.get("track_index", 0)

        try:
            track = _resolve_track(self._song, track_type, track_index)
            available = [rt.display_name for rt in track.available_input_routing_types]
            current = track.input_routing_type.display_name

            result = {
                "track_name": track.name,
                "track_type": track_type,
                "current": current,
                "available": available,
            }
            if track_type != "master":
                result["track_index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error getting input routing types: {e}")
            raise

    @command("set_input_routing", write=True)
    def _set_input_routing(self, params):
        """Set the input routing type for a track by display name."""
        track_type = params.get("track_type", "track")
        track_index = params.get("track_index", 0)
        routing_name = params.get("routing_name")

        try:
            if routing_name is None:
                raise ValueError("routing_name parameter is required")

            track = _resolve_track(self._song, track_type, track_index)
            previous = track.input_routing_type.display_name

            # Case-insensitive match against available routing types
            name_lower = routing_name.lower()
            for rt in track.available_input_routing_types:
                if rt.display_name.lower() == name_lower:
                    track.input_routing_type = rt
                    result = {
                        "previous": previous,
                        "current": track.input_routing_type.display_name,
                        "track_name": track.name,
                        "track_type": track_type,
                    }
                    if track_type != "master":
                        result["track_index"] = track_index
                    return result

            # No match found -- list available for AI self-correction
            available = [rt.display_name for rt in track.available_input_routing_types]
            raise ValueError(
                f"Routing type '{routing_name}' not found. Available: {available}"
            )
        except Exception as e:
            self.log_message(f"Error setting input routing: {e}")
            raise

    @command("get_output_routing_types")
    def _get_output_routing_types(self, params):
        """Get available output routing types for a track."""
        track_type = params.get("track_type", "track")
        track_index = params.get("track_index", 0)

        try:
            track = _resolve_track(self._song, track_type, track_index)
            available = [rt.display_name for rt in track.available_output_routing_types]
            current = track.output_routing_type.display_name

            result = {
                "track_name": track.name,
                "track_type": track_type,
                "current": current,
                "available": available,
            }
            if track_type != "master":
                result["track_index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error getting output routing types: {e}")
            raise

    @command("set_output_routing", write=True)
    def _set_output_routing(self, params):
        """Set the output routing type for a track by display name."""
        track_type = params.get("track_type", "track")
        track_index = params.get("track_index", 0)
        routing_name = params.get("routing_name")

        try:
            if routing_name is None:
                raise ValueError("routing_name parameter is required")

            track = _resolve_track(self._song, track_type, track_index)
            previous = track.output_routing_type.display_name

            # Case-insensitive match against available routing types
            name_lower = routing_name.lower()
            for rt in track.available_output_routing_types:
                if rt.display_name.lower() == name_lower:
                    track.output_routing_type = rt
                    result = {
                        "previous": previous,
                        "current": track.output_routing_type.display_name,
                        "track_name": track.name,
                        "track_type": track_type,
                    }
                    if track_type != "master":
                        result["track_index"] = track_index
                    return result

            # No match found -- list available for AI self-correction
            available = [rt.display_name for rt in track.available_output_routing_types]
            raise ValueError(
                f"Routing type '{routing_name}' not found. Available: {available}"
            )
        except Exception as e:
            self.log_message(f"Error setting output routing: {e}")
            raise

    @command("get_input_routing_channels")
    def _get_input_routing_channels(self, params):
        """Get available input sub-routing channels for a track.

        Params:
            track_index: Index of the track.
            track_type: "track", "return", or "master" (default "track").

        Returns:
            track_name, current channel, available channels list.
        """
        track_type = params.get("track_type", "track")
        track_index = params.get("track_index", 0)

        try:
            track = _resolve_track(self._song, track_type, track_index)

            result = {
                "track_name": track.name,
                "current": track.input_routing_channel.display_name,
                "available": [
                    ch.display_name
                    for ch in track.available_input_routing_channels
                ],
            }
            if track_type != "master":
                result["track_index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error getting input routing channels: {e}")
            raise

    @command("get_output_routing_channels")
    def _get_output_routing_channels(self, params):
        """Get available output sub-routing channels for a track.

        Params:
            track_index: Index of the track.
            track_type: "track", "return", or "master" (default "track").

        Returns:
            track_name, current channel, available channels list.
        """
        track_type = params.get("track_type", "track")
        track_index = params.get("track_index", 0)

        try:
            track = _resolve_track(self._song, track_type, track_index)

            result = {
                "track_name": track.name,
                "current": track.output_routing_channel.display_name,
                "available": [
                    ch.display_name
                    for ch in track.available_output_routing_channels
                ],
            }
            if track_type != "master":
                result["track_index"] = track_index
            return result
        except Exception as e:
            self.log_message(f"Error getting output routing channels: {e}")
            raise
