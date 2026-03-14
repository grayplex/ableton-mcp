"""Device handlers: parameter control, device type detection."""

from AbletonMCP_Remote_Script.registry import command


class DeviceHandlers:
    """Mixin class for device command handlers."""

    @command("set_device_parameter", write=True)
    def _set_device_parameter(self, params):
        """Set a device parameter value."""
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        parameter_index = params.get("parameter_index", 0)
        value = params.get("value", 0.0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if device_index < 0 or device_index >= len(track.devices):
                raise IndexError("Device index out of range")

            device = track.devices[device_index]
            parameters = device.parameters

            if parameter_index < 0 or parameter_index >= len(parameters):
                raise IndexError("Parameter index out of range")

            param = parameters[parameter_index]
            param.value = value

            return {
                "device_name": device.name,
                "parameter_name": param.name,
                "value": param.value,
            }
        except Exception as e:
            self.log_message(f"Error setting device parameter: {e}")
            raise

    def _get_device_type(self, device):
        """Get the type of a device."""
        try:
            if device.can_have_drum_pads:
                return "drum_machine"
            elif device.can_have_chains:
                return "rack"
            elif "instrument" in device.class_display_name.lower():
                return "instrument"
            elif "audio_effect" in device.class_name.lower():
                return "audio_effect"
            elif "midi_effect" in device.class_name.lower():
                return "midi_effect"
            else:
                return "unknown"
        except Exception as e:
            self.log_message(f"[ERROR] Could not determine device type: {e}")
            return "unknown"
