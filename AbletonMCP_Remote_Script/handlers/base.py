"""Base handlers: ping, session info."""

from AbletonMCP_Remote_Script.registry import command


class BaseHandlers:
    """Mixin class for base/session command handlers."""

    @command("ping")
    def _ping(self, params=None):
        """Respond to health check with protocol and Ableton version."""
        try:
            ableton_version = str(self.application().get_major_version())
        except Exception:
            ableton_version = "unknown"
        return {
            "pong": True,
            "version": "1.0",
            "ableton_version": ableton_version,
        }

    @command("get_session_info")
    def _get_session_info(self, params=None):
        """Get information about the current session."""
        try:
            result = {
                "tempo": self._song.tempo,
                "signature_numerator": self._song.signature_numerator,
                "signature_denominator": self._song.signature_denominator,
                "track_count": len(self._song.tracks),
                "return_track_count": len(self._song.return_tracks),
                "master_track": {
                    "name": "Master",
                    "volume": self._song.master_track.mixer_device.volume.value,
                    "panning": self._song.master_track.mixer_device.panning.value,
                },
            }
            return result
        except Exception as e:
            self.log_message(f"Error getting session info: {e}")
            raise
