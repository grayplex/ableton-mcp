"""Device handlers: parameter control, rack chain navigation, device deletion, session state."""

from AbletonMCP_Remote_Script.handlers.mixer_helpers import _to_db, _pan_label
from AbletonMCP_Remote_Script.handlers.tracks import (
    _get_color_name,
    _get_track_type_str,
    _resolve_track,
)
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

    @command("delete_device", write=True)
    def _delete_device(self, params):
        """Delete a device from a track or chain device list.

        Params:
            track_index: Index of the track (default 0).
            device_index: Index of the device on the track (default 0).
            track_type: "track", "return", or "master" (default "track").
            chain_index: Optional chain index for rack chain deletion.
            chain_device_index: Optional device index within a chain to delete.

        Returns:
            deleted_device_name, track_name, track_type, updated_devices list.
        """
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        track_type = params.get("track_type", "track")
        chain_index = params.get("chain_index", None)
        chain_device_index = params.get("chain_device_index", None)

        try:
            track = _resolve_track(self._song, track_type, track_index)

            if device_index < 0 or device_index >= len(track.devices):
                raise IndexError(
                    f"Device index {device_index} out of range "
                    f"(0-{len(track.devices) - 1})"
                )

            if chain_index is not None:
                # Deleting a device from within a rack chain
                device = track.devices[device_index]
                if not device.can_have_chains:
                    raise ValueError(
                        f"Device '{device.name}' is not a rack and does not "
                        f"have chains"
                    )
                if chain_index < 0 or chain_index >= len(device.chains):
                    raise IndexError(
                        f"Chain index {chain_index} out of range "
                        f"(0-{len(device.chains) - 1})"
                    )
                chain = device.chains[chain_index]

                if chain_device_index is None:
                    raise ValueError(
                        "chain_device_index is required when deleting from a chain"
                    )
                if chain_device_index < 0 or chain_device_index >= len(chain.devices):
                    raise IndexError(
                        f"Chain device index {chain_device_index} out of range "
                        f"(0-{len(chain.devices) - 1})"
                    )

                deleted_name = chain.devices[chain_device_index].name
                chain.delete_device(chain_device_index)

                # Build updated chain device list
                updated_devices = [
                    {
                        "index": i,
                        "name": d.name,
                        "type": self._get_device_type(d),
                    }
                    for i, d in enumerate(chain.devices)
                ]
            else:
                # Deleting a top-level device from the track
                deleted_name = track.devices[device_index].name
                track.delete_device(device_index)

                # Build updated track device list
                updated_devices = [
                    {
                        "index": i,
                        "name": d.name,
                        "type": self._get_device_type(d),
                    }
                    for i, d in enumerate(track.devices)
                ]

            return {
                "deleted_device_name": deleted_name,
                "track_name": track.name,
                "track_type": track_type,
                "updated_devices": updated_devices,
            }
        except Exception as e:
            self.log_message(f"Error deleting device: {e}")
            raise

    @command("get_rack_chains")
    def _get_rack_chains(self, params):
        """Get chain information for a rack device.

        For Instrument/Effect Racks: returns chain names, indices, and devices.
        For Drum Racks: returns pad details (note, name) with chain devices,
        filtering out empty pads.

        Params:
            track_index: Index of the track (default 0).
            device_index: Index of the rack device on the track (default 0).
            track_type: "track", "return", or "master" (default "track").
            chain_index: Optional chain index for navigating to a nested rack.
            chain_device_index: Optional device index within a chain (nested rack).

        Returns:
            device_name, device_type, and either chains list or pads list.
        """
        try:
            device, _track = self._resolve_device(params)

            if not device.can_have_chains:
                raise ValueError(
                    f"Device '{device.name}' is not a rack and does not have chains"
                )

            if device.can_have_drum_pads:
                # Drum Rack -- expose pads with content only
                pads = []
                for pad in device.drum_pads:
                    if pad.chains and len(pad.chains) > 0:
                        pad_chains = []
                        for chain in pad.chains:
                            chain_devices = []
                            for di, d in enumerate(chain.devices):
                                chain_devices.append({
                                    "index": di,
                                    "name": d.name,
                                    "type": self._get_device_type(d),
                                    "can_have_chains": d.can_have_chains,
                                })
                            pad_chains.append({
                                "name": chain.name,
                                "devices": chain_devices,
                            })
                        pads.append({
                            "note": pad.note,
                            "name": pad.name,
                            "chains": pad_chains,
                        })

                return {
                    "device_name": device.name,
                    "device_type": self._get_device_type(device),
                    "pads": pads,
                }
            else:
                # Instrument/Effect Rack -- expose chains
                chains = []
                for ci, chain in enumerate(device.chains):
                    chain_devices = []
                    for di, d in enumerate(chain.devices):
                        chain_devices.append({
                            "index": di,
                            "name": d.name,
                            "type": self._get_device_type(d),
                            "can_have_chains": d.can_have_chains,
                        })
                    chains.append({
                        "index": ci,
                        "name": chain.name,
                        "devices": chain_devices,
                    })

                return {
                    "device_name": device.name,
                    "device_type": self._get_device_type(device),
                    "chains": chains,
                }
        except Exception as e:
            self.log_message(f"Error getting rack chains: {e}")
            raise

    @command("insert_device", write=True)
    def _insert_device(self, params):
        """Insert a native Ableton device by name at a specific position.

        Params:
            track_index: Index of the track.
            device_name: Name of the device to insert (e.g., "Wavetable", "EQ Eight").
            position: Position in the device chain (0-based).
            track_type: "track", "return", or "master" (default "track").

        Returns:
            inserted, device_name, position, track_name.
        """
        track_index = params.get("track_index", 0)
        device_name = params.get("device_name")
        position = params.get("position", 0)
        track_type = params.get("track_type", "track")

        try:
            if device_name is None:
                raise ValueError("device_name parameter is required")

            track = _resolve_track(self._song, track_type, track_index)
            track.insert_device(device_name, position)

            return {
                "inserted": True,
                "device_name": device_name,
                "position": position,
                "track_name": track.name,
            }
        except Exception as e:
            self.log_message(f"Error inserting device: {e}")
            raise

    @command("move_device", write=True)
    def _move_device(self, params):
        """Move a device from one track/position to another.

        Params:
            source_track_index: Index of the source track.
            device_index: Index of the device on the source track.
            target_track_index: Index of the target track.
            target_position: Position in the target track's device chain.
            source_track_type: "track", "return", or "master" (default "track").
            target_track_type: "track", "return", or "master" (default "track").

        Returns:
            moved, device_name, target_track, position.
        """
        source_track_index = params.get("source_track_index", 0)
        device_index = params.get("device_index", 0)
        target_track_index = params.get("target_track_index", 0)
        target_position = params.get("target_position", 0)
        source_track_type = params.get("source_track_type", "track")
        target_track_type = params.get("target_track_type", "track")

        try:
            # Resolve source device using existing _resolve_device pattern
            device, _source_track = self._resolve_device({
                "track_index": source_track_index,
                "device_index": device_index,
                "track_type": source_track_type,
            })

            # Resolve target track
            target = _resolve_track(self._song, target_track_type, target_track_index)

            self._song.move_device(device, target, target_position)

            return {
                "moved": True,
                "device_name": device.name,
                "target_track": target.name,
                "position": target_position,
            }
        except Exception as e:
            self.log_message(f"Error moving device: {e}")
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

    @command("get_session_state")
    def _get_session_state(self, params=None):
        """Get a bulk session state dump.

        Params:
            detailed: bool (default False). If True, includes all device
                parameter values for every device.

        Returns:
            Dictionary with transport, tracks, return_tracks, and master_track.
            Lightweight mode: track names, device names, occupied clips, mixer.
            Detailed mode: adds all device parameter values.
        """
        detailed = (params or {}).get("detailed", False)

        try:
            result = {
                "transport": {
                    "tempo": self._song.tempo,
                    "signature_numerator": self._song.signature_numerator,
                    "signature_denominator": self._song.signature_denominator,
                    "is_playing": self._song.is_playing,
                    "loop_enabled": self._song.loop,
                    "loop_start": self._song.loop_start,
                    "loop_length": self._song.loop_length,
                },
                "tracks": [],
                "return_tracks": [],
                "master_track": {},
            }

            def build_track_state(track, track_type_hint=None):
                """Build state dict for a single track."""
                type_str = _get_track_type_str(track, track_type_hint=track_type_hint)
                color = _get_color_name(track)

                state = {
                    "name": track.name,
                    "type": type_str,
                    "color": color,
                    "volume": track.mixer_device.volume.value,
                    "volume_db": _to_db(track.mixer_device.volume.value),
                    "pan": track.mixer_device.panning.value,
                    "pan_label": _pan_label(track.mixer_device.panning.value),
                }

                # Mute/solo (not on master — LOM raises non-AttributeError,
                # so hasattr() doesn't work; use try/except instead)
                try:
                    state["mute"] = track.mute
                except Exception:
                    pass
                try:
                    state["solo"] = track.solo
                except Exception:
                    pass

                # Arm (only for armable tracks)
                try:
                    if track.can_be_armed:
                        state["arm"] = track.arm
                except Exception:
                    pass

                # Devices
                devices = []
                for di, d in enumerate(track.devices):
                    dev_info = {
                        "index": di,
                        "name": d.name,
                        "type": self._get_device_type(d),
                    }
                    if detailed:
                        dev_info["parameters"] = [
                            {
                                "name": p.name,
                                "value": p.value,
                                "min": p.min,
                                "max": p.max,
                            }
                            for p in d.parameters
                        ]
                    devices.append(dev_info)
                state["devices"] = devices

                # Clips -- only occupied slots
                if hasattr(track, "clip_slots"):
                    clips = []
                    for si, slot in enumerate(track.clip_slots):
                        if slot.has_clip:
                            clip = slot.clip
                            clips.append({
                                "scene_index": si,
                                "name": clip.name,
                                "color": clip.color_index,
                                "is_playing": clip.is_playing,
                            })
                    if clips:
                        state["clips"] = clips

                # Sends (not on master)
                if track_type_hint != "master" and hasattr(track.mixer_device, "sends"):
                    sends = [
                        {"return_index": i, "level": s.value}
                        for i, s in enumerate(track.mixer_device.sends)
                    ]
                    if sends:
                        state["sends"] = sends

                return state

            # Regular tracks
            for i, track in enumerate(self._song.tracks):
                track_state = build_track_state(track)
                track_state["index"] = i
                result["tracks"].append(track_state)

            # Return tracks
            for i, track in enumerate(self._song.return_tracks):
                track_state = build_track_state(track, "return")
                track_state["index"] = i
                result["return_tracks"].append(track_state)

            # Master track
            result["master_track"] = build_track_state(
                self._song.master_track, "master"
            )

            return result
        except Exception as e:
            self.log_message(f"Error getting session state: {e}")
            raise
