"""Automation handlers: read, write, and clear clip automation envelopes."""

from AbletonMCP_Remote_Script.handlers.clips import _resolve_clip_slot
from AbletonMCP_Remote_Script.registry import command


class AutomationHandlers:
    """Mixin class for automation envelope command handlers."""

    @command("get_clip_envelope")
    def _get_clip_envelope(self, params):
        """Get automation envelope data for a device parameter in a clip.

        Dual mode:
        - List mode (no parameter_name/parameter_index): returns all parameters
          with automation on the specified device.
        - Detail mode (parameter_name or parameter_index): returns sampled
          breakpoint data for that parameter's envelope.
        """
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        parameter_name = params.get("parameter_name", None)
        parameter_index = params.get("parameter_index", None)
        sample_interval = params.get("sample_interval", 0.25)

        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            # List mode: return which parameters have automation
            if parameter_name is None and parameter_index is None:
                if not clip.has_envelopes:
                    return {
                        "has_envelopes": False,
                        "parameters_with_automation": [],
                    }

                device, _ = self._resolve_device(params)
                automated = []
                for i, param in enumerate(device.parameters):
                    env = clip.automation_envelope(param)
                    if env is not None:
                        automated.append({
                            "name": param.name,
                            "index": i,
                            "min": param.min,
                            "max": param.max,
                        })

                return {
                    "has_envelopes": True,
                    "device_name": device.name,
                    "parameters_with_automation": automated,
                }

            # Detail mode: return sampled breakpoint data
            device, _ = self._resolve_device(params)
            param, matched_index = self._resolve_parameter(
                device, parameter_name, parameter_index
            )

            envelope = clip.automation_envelope(param)

            if envelope is None:
                return {
                    "parameter_name": param.name,
                    "device_name": device.name,
                    "has_automation": False,
                    "breakpoints": [],
                    "min": param.min,
                    "max": param.max,
                    "value": param.value,
                }

            # Sample envelope at regular intervals
            breakpoints = []
            t = 0.0
            while t <= clip.length:
                val = envelope.value_at_time(t)
                breakpoints.append({
                    "time": round(t, 4),
                    "value": round(val, 6),
                })
                t += sample_interval

            return {
                "parameter_name": param.name,
                "device_name": device.name,
                "has_automation": True,
                "sample_interval": sample_interval,
                "breakpoints": breakpoints,
                "min": param.min,
                "max": param.max,
                "value": param.value,
            }
        except Exception as e:
            self.log_message(f"Error getting clip envelope: {e}")
            raise

    @command("insert_envelope_breakpoints", write=True)
    def _insert_envelope_breakpoints(self, params):
        """Insert automation breakpoints into a clip envelope.

        Accepts a list of {time, value} pairs and inserts them using
        envelope.insert_step(). Values are clamped to param.min/max.
        """
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        parameter_name = params.get("parameter_name", None)
        parameter_index = params.get("parameter_index", None)
        breakpoints = params.get("breakpoints", [])
        step_length = params.get("step_length", 0.0)

        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            if parameter_name is None and parameter_index is None:
                raise ValueError(
                    "Provide parameter_name or parameter_index to identify "
                    "the parameter to automate"
                )

            device, _ = self._resolve_device(params)
            param, matched_index = self._resolve_parameter(
                device, parameter_name, parameter_index
            )

            envelope = clip.automation_envelope(param)

            if envelope is None:
                try:
                    envelope = clip.create_automation_envelope(param)
                except Exception:
                    raise ValueError(
                        f"Cannot create automation envelope for '{param.name}' "
                        f"on this clip. Verify the clip is a Session View clip "
                        f"and the parameter belongs to a device on the same "
                        f"track."
                    )

            # Clamp breakpoint values to param.min/param.max
            clamped = False
            for bp in breakpoints:
                if bp["value"] < param.min:
                    bp["value"] = param.min
                    clamped = True
                elif bp["value"] > param.max:
                    bp["value"] = param.max
                    clamped = True

            # Insert each breakpoint
            for bp in breakpoints:
                envelope.insert_step(bp["time"], bp["value"], step_length)

            # Sample total breakpoints by reading envelope across clip length
            total_count = 0
            t = 0.0
            while t <= clip.length:
                envelope.value_at_time(t)
                total_count += 1
                t += 0.25

            result = {
                "parameter_name": param.name,
                "device_name": device.name,
                "breakpoints_inserted": len(breakpoints),
                "total_breakpoints": total_count,
            }
            if clamped:
                result["warning"] = (
                    f"Some values were clamped to parameter range "
                    f"[{param.min}, {param.max}]"
                )
            return result
        except Exception as e:
            self.log_message(f"Error inserting envelope breakpoints: {e}")
            raise

    @command("clear_clip_envelopes", write=True)
    def _clear_clip_envelopes(self, params):
        """Clear automation envelopes from a clip.

        Dual mode:
        - Clear all mode (no device_index, parameter_name, parameter_index):
          clears ALL envelopes on the clip.
        - Clear single mode (device_index + parameter_name or parameter_index):
          clears only that parameter's envelope.
        """
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        device_index = params.get("device_index", None)
        parameter_name = params.get("parameter_name", None)
        parameter_index = params.get("parameter_index", None)

        try:
            clip_slot, track = _resolve_clip_slot(
                self._song, track_index, clip_index
            )

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            # Clear all mode
            if (device_index is None
                    and parameter_name is None
                    and parameter_index is None):
                clip.clear_all_envelopes()
                return {
                    "cleared": "all",
                    "envelopes_cleared": "all",
                }

            # Clear single parameter mode
            device, _ = self._resolve_device(params)
            param, matched_index = self._resolve_parameter(
                device, parameter_name, parameter_index
            )

            clip.clear_envelope(param)

            return {
                "cleared": param.name,
                "device_name": device.name,
                "envelopes_cleared": 1,
            }
        except Exception as e:
            self.log_message(f"Error clearing clip envelopes: {e}")
            raise

    def _resolve_parameter(self, device, parameter_name, parameter_index):
        """Resolve a device parameter by name or index.

        Returns:
            (param, matched_index) tuple.

        Raises:
            ValueError: If parameter_name not found.
            IndexError: If parameter_index out of range.
        """
        if parameter_name is not None:
            name_lower = parameter_name.lower()
            for i, p in enumerate(device.parameters):
                if p.name.lower() == name_lower:
                    return p, i
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
            return device.parameters[parameter_index], parameter_index
        else:
            raise ValueError(
                "Provide parameter_name or parameter_index to identify "
                "the parameter"
            )
