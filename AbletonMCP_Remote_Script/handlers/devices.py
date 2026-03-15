"""Device handlers: parameter control, rack chain navigation, device deletion."""

from AbletonMCP_Remote_Script.handlers.tracks import _resolve_track
from AbletonMCP_Remote_Script.registry import command


class DeviceHandlers:
    """Mixin class for device command handlers."""

    def _resolve_device(self, params):
        """Resolve a device from params, supporting chain navigation.

        Extracts track_index, device_index, track_type, chain_index,
        chain_device_index from params. Uses _resolve_track for track
        resolution, then navigates into rack chains if chain params provided.

        Returns:
            (device, track) tuple for the resolved device.
        """
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        track_type = params.get("track_type", "track")
        chain_index = params.get("chain_index", None)
        chain_device_index = params.get("chain_device_index", None)

        track = _resolve_track(self._song, track_type, track_index)

        if device_index < 0 or device_index >= len(track.devices):
            raise IndexError(
                f"Device index {device_index} out of range "
                f"(0-{len(track.devices) - 1})"
            )

        device = track.devices[device_index]

        if chain_index is not None:
            if not device.can_have_chains:
                raise ValueError(
                    f"Device '{device.name}' is not a rack and does not have chains"
                )
            if chain_index < 0 or chain_index >= len(device.chains):
                raise IndexError(
                    f"Chain index {chain_index} out of range "
                    f"(0-{len(device.chains) - 1})"
                )
            chain = device.chains[chain_index]

            if chain_device_index is not None:
                if chain_device_index < 0 or chain_device_index >= len(chain.devices):
                    raise IndexError(
                        f"Chain device index {chain_device_index} out of range "
                        f"(0-{len(chain.devices) - 1})"
                    )
                device = chain.devices[chain_device_index]

        return device, track

    @command("get_device_parameters")
    def _get_device_parameters(self, params):
        """Get all parameters of a device.

        Params:
            track_index: Index of the track (default 0).
            device_index: Index of the device on the track (default 0).
            track_type: "track", "return", or "master" (default "track").
            chain_index: Optional chain index for rack chain navigation.
            chain_device_index: Optional device index within a chain.

        Returns:
            device_name, device_type, class_name, parameter_count, parameters list.
        """
        try:
            device, _track = self._resolve_device(params)

            parameters = []
            for i, param in enumerate(device.parameters):
                parameters.append({
                    "index": i,
                    "name": param.name,
                    "value": param.value,
                    "min": param.min,
                    "max": param.max,
                    "is_quantized": param.is_quantized,
                })

            return {
                "device_name": device.name,
                "device_type": self._get_device_type(device),
                "class_name": device.class_name,
                "parameter_count": len(parameters),
                "parameters": parameters,
            }
        except Exception as e:
            self.log_message(f"Error getting device parameters: {e}")
            raise

    @command("set_device_parameter", write=True)
    def _set_device_parameter(self, params):
        """Set a device parameter value by name or index with clamping.

        Params:
            track_index: Index of the track (default 0).
            device_index: Index of the device on the track (default 0).
            track_type: "track", "return", or "master" (default "track").
            value: The value to set.
            parameter_name: Optional case-insensitive parameter name (first match).
            parameter_index: Optional parameter index.
            chain_index: Optional chain index for rack chain navigation.
            chain_device_index: Optional device index within a chain.

        Returns:
            device_name, parameter_name, parameter_index, value (actual),
            min, max, is_quantized. Includes "warning" key if value was clamped.
        """
        value = params.get("value")
        parameter_name = params.get("parameter_name", None)
        parameter_index = params.get("parameter_index", None)

        try:
            device, _track = self._resolve_device(params)

            # Resolve parameter by name or index
            if parameter_name is not None:
                # Case-insensitive first-match lookup
                name_lower = parameter_name.lower()
                param = None
                matched_index = None
                for i, p in enumerate(device.parameters):
                    if p.name.lower() == name_lower:
                        param = p
                        matched_index = i
                        break
                if param is None:
                    available = [p.name for p in device.parameters]
                    raise ValueError(
                        f"Parameter '{parameter_name}' not found on device "
                        f"'{device.name}'. Available parameters: {available}"
                    )
            elif parameter_index is not None:
                if parameter_index < 0 or parameter_index >= len(device.parameters):
                    raise IndexError(
                        f"Parameter index {parameter_index} out of range "
                        f"(0-{len(device.parameters) - 1})"
                    )
                param = device.parameters[parameter_index]
                matched_index = parameter_index
            else:
                raise ValueError(
                    "Provide parameter_name or parameter_index to identify "
                    "the parameter to set"
                )

            # Clamp value to min/max with warning
            warning = None
            if value < param.min:
                warning = f"Value {value} clamped to min {param.min}"
                value = param.min
            elif value > param.max:
                warning = f"Value {value} clamped to max {param.max}"
                value = param.max

            param.value = value

            result = {
                "device_name": device.name,
                "parameter_name": param.name,
                "parameter_index": matched_index,
                "value": param.value,
                "min": param.min,
                "max": param.max,
                "is_quantized": param.is_quantized,
            }
            if warning:
                result["warning"] = warning
            return result
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
