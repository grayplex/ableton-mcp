"""Transport handlers: playback control, tempo."""

from AbletonMCP_Remote_Script.registry import command


class TransportHandlers:
    """Mixin class for transport command handlers."""

    @command("start_playback", write=True)
    def _start_playback(self, params=None):
        """Start playing the session."""
        try:
            self._song.start_playing()
            return {"playing": self._song.is_playing}
        except Exception as e:
            self.log_message(f"Error starting playback: {e}")
            raise

    @command("stop_playback", write=True)
    def _stop_playback(self, params=None):
        """Stop playing the session."""
        try:
            self._song.stop_playing()
            return {"playing": self._song.is_playing}
        except Exception as e:
            self.log_message(f"Error stopping playback: {e}")
            raise

    @command("set_tempo", write=True)
    def _set_tempo(self, params):
        """Set the tempo of the session."""
        tempo = params.get("tempo", 120.0)
        try:
            self._song.tempo = tempo
            return {"tempo": self._song.tempo}
        except Exception as e:
            self.log_message(f"Error setting tempo: {e}")
            raise
