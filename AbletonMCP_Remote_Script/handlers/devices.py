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

    # --- Phase 13: Simpler, DrumPad, Plugin, A/B Compare ---

    def _resolve_drum_pad(self, device, note):
        """Find a drum pad by MIDI note number.

        Args:
            device: A Drum Rack device.
            note: MIDI note number to find.

        Returns:
            The DrumPad with matching note.

        Raises:
            ValueError: If no pad with the given note exists.
        """
        for pad in device.drum_pads:
            if pad.note == note:
                return pad
        raise ValueError(
            f"No drum pad with note {note} found in '{device.name}'. "
            f"Available notes: {[p.note for p in device.drum_pads if p.chains]}"
        )

    @command("crop_simpler", write=True)
    def _crop_simpler(self, params):
        """Crop a Simpler device's sample to its active region.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        device, _track = self._resolve_device(params)
        if not hasattr(device, "playback_mode"):
            raise ValueError(f"Device '{device.name}' is not a Simpler device")
        if device.sample is None:
            raise ValueError("No sample loaded in Simpler")
        device.crop()
        return {"cropped": True, "device_name": device.name}

    @command("reverse_simpler", write=True)
    def _reverse_simpler(self, params):
        """Reverse a Simpler device's loaded sample.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        device, _track = self._resolve_device(params)
        if not hasattr(device, "playback_mode"):
            raise ValueError(f"Device '{device.name}' is not a Simpler device")
        if device.sample is None:
            raise ValueError("No sample loaded in Simpler")
        device.reverse()
        return {"reversed": True, "device_name": device.name}

    @command("warp_simpler", write=True)
    def _warp_simpler(self, params):
        """Warp a Simpler device's sample.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            mode: 'as' (warp to beats), 'double', or 'half'.
            beats: Required when mode='as', float number of beats.
        """
        mode = params.get("mode")
        beats = params.get("beats")

        device, _track = self._resolve_device(params)
        if not hasattr(device, "playback_mode"):
            raise ValueError(f"Device '{device.name}' is not a Simpler device")
        if device.sample is None:
            raise ValueError("No sample loaded in Simpler")

        if mode == "as":
            if not device.can_warp_as:
                raise ValueError("Warp As is not available for this sample")
            if beats is None:
                raise ValueError("beats parameter is required when mode='as'")
            device.warp_as(beats)
        elif mode == "double":
            if not device.can_warp_double:
                raise ValueError("Warp Double is not available for this sample")
            device.warp_double()
        elif mode == "half":
            if not device.can_warp_half:
                raise ValueError("Warp Half is not available for this sample")
            device.warp_half()
        else:
            raise ValueError(
                f"Invalid warp mode '{mode}'. Use 'as', 'double', or 'half'."
            )

        return {"warped": True, "device_name": device.name, "mode": mode}

    @command("get_simpler_info")
    def _get_simpler_info(self, params):
        """Get Simpler device info: playback mode, warp caps, and sample details.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        device, _track = self._resolve_device(params)
        if not hasattr(device, "playback_mode"):
            raise ValueError(f"Device '{device.name}' is not a Simpler device")

        result = {
            "device_name": device.name,
            "playback_mode": device.playback_mode,
            "playback_mode_label": {0: "Classic", 1: "One-Shot", 2: "Slicing"}.get(
                device.playback_mode, "unknown"
            ),
            "can_warp_as": device.can_warp_as,
            "can_warp_double": device.can_warp_double,
            "can_warp_half": device.can_warp_half,
        }

        if device.sample is not None:
            result["sample"] = {
                "file_path": device.sample.file_path,
                "length": device.sample.length,
                "sample_rate": device.sample.sample_rate,
                "slices": list(device.sample.slices),
                "slicing_sensitivity": device.sample.slicing_sensitivity,
                "slicing_style": device.sample.slicing_style,
            }
        else:
            result["sample"] = None

        return result

    @command("set_simpler_playback_mode", write=True)
    def _set_simpler_playback_mode(self, params):
        """Set Simpler playback mode (0=Classic, 1=One-Shot, 2=Slicing).

        Params:
            track_index, device_index, track_type: Standard device addressing.
            mode: int (0, 1, or 2).
        """
        mode = params.get("mode")

        device, _track = self._resolve_device(params)
        if not hasattr(device, "playback_mode"):
            raise ValueError(f"Device '{device.name}' is not a Simpler device")

        if mode not in {0, 1, 2}:
            raise ValueError(
                f"Invalid playback mode {mode}. "
                "Use 0=Classic, 1=One-Shot, or 2=Slicing."
            )

        device.playback_mode = mode

        return {
            "device_name": device.name,
            "playback_mode": device.playback_mode,
            "playback_mode_label": {0: "Classic", 1: "One-Shot", 2: "Slicing"}.get(
                device.playback_mode, "unknown"
            ),
        }

    @command("insert_simpler_slice", write=True)
    def _insert_simpler_slice(self, params):
        """Insert a slice marker in a Simpler sample.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            time: Position in sample frames.
        """
        time = params.get("time")

        device, _track = self._resolve_device(params)
        if not hasattr(device, "playback_mode"):
            raise ValueError(f"Device '{device.name}' is not a Simpler device")
        if device.sample is None:
            raise ValueError("No sample loaded in Simpler")

        device.sample.insert_slice(time)

        return {
            "inserted": True,
            "device_name": device.name,
            "time": time,
            "slices": list(device.sample.slices),
        }

    @command("move_simpler_slice", write=True)
    def _move_simpler_slice(self, params):
        """Move a slice marker from one position to another.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            source_time: Current position in sample frames.
            destination_time: New position in sample frames.
        """
        source_time = params.get("source_time")
        destination_time = params.get("destination_time")

        device, _track = self._resolve_device(params)
        if not hasattr(device, "playback_mode"):
            raise ValueError(f"Device '{device.name}' is not a Simpler device")
        if device.sample is None:
            raise ValueError("No sample loaded in Simpler")

        device.sample.move_slice(source_time, destination_time)

        return {
            "moved": True,
            "device_name": device.name,
            "source_time": source_time,
            "destination_time": destination_time,
            "slices": list(device.sample.slices),
        }

    @command("remove_simpler_slice", write=True)
    def _remove_simpler_slice(self, params):
        """Remove a slice marker at a position.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            time: Position in sample frames.
        """
        time = params.get("time")

        device, _track = self._resolve_device(params)
        if not hasattr(device, "playback_mode"):
            raise ValueError(f"Device '{device.name}' is not a Simpler device")
        if device.sample is None:
            raise ValueError("No sample loaded in Simpler")

        device.sample.remove_slice(time)

        return {
            "removed": True,
            "device_name": device.name,
            "time": time,
            "slices": list(device.sample.slices),
        }

    @command("clear_simpler_slices", write=True)
    def _clear_simpler_slices(self, params):
        """Clear all slice markers from a Simpler sample.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        device, _track = self._resolve_device(params)
        if not hasattr(device, "playback_mode"):
            raise ValueError(f"Device '{device.name}' is not a Simpler device")
        if device.sample is None:
            raise ValueError("No sample loaded in Simpler")

        device.sample.clear_slices()

        return {
            "cleared": True,
            "device_name": device.name,
            "slices": list(device.sample.slices),
        }

    @command("set_drum_pad_mute", write=True)
    def _set_drum_pad_mute(self, params):
        """Mute or unmute a drum pad by MIDI note number.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            note: MIDI note number of the drum pad.
            mute: True to mute, False to unmute.
        """
        note = params.get("note")
        mute = params.get("mute")

        device, _track = self._resolve_device(params)
        if not device.can_have_drum_pads:
            raise ValueError(f"Device '{device.name}' is not a Drum Rack")

        pad = self._resolve_drum_pad(device, note)
        pad.mute = mute

        return {"note": note, "name": pad.name, "mute": pad.mute}

    @command("set_drum_pad_solo", write=True)
    def _set_drum_pad_solo(self, params):
        """Solo or unsolo a drum pad by MIDI note number.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            note: MIDI note number of the drum pad.
            solo: True to solo, False to unsolo.
            exclusive: If True and solo=True, unsolo all other pads first.
        """
        note = params.get("note")
        solo = params.get("solo")
        exclusive = params.get("exclusive", False)

        device, _track = self._resolve_device(params)
        if not device.can_have_drum_pads:
            raise ValueError(f"Device '{device.name}' is not a Drum Rack")

        pad = self._resolve_drum_pad(device, note)

        if exclusive and solo:
            for p in device.drum_pads:
                p.solo = False

        pad.solo = solo

        return {
            "note": note,
            "name": pad.name,
            "solo": pad.solo,
            "note_text": (
                "DrumPad solo does not auto-unsolo other pads. "
                "Use exclusive=True to solo exclusively."
            ),
        }

    @command("delete_drum_pad_chains", write=True)
    def _delete_drum_pad_chains(self, params):
        """Clear all chains from a drum pad, removing its content.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            note: MIDI note number of the drum pad.
        """
        note = params.get("note")

        device, _track = self._resolve_device(params)
        if not device.can_have_drum_pads:
            raise ValueError(f"Device '{device.name}' is not a Drum Rack")

        pad = self._resolve_drum_pad(device, note)
        pad.delete_all_chains()

        return {"deleted": True, "note": note, "name": pad.name}

    @command("list_plugin_presets")
    def _list_plugin_presets(self, params):
        """List available presets for a VST/AU plugin device.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        device, _track = self._resolve_device(params)
        if not hasattr(device, "presets"):
            raise ValueError(
                f"Device '{device.name}' is not a plugin device (VST/AU). "
                "Only plugin devices have presets."
            )

        return {
            "device_name": device.name,
            "presets": list(device.presets),
            "selected_preset_index": device.selected_preset_index,
            "preset_count": len(device.presets),
        }

    @command("set_plugin_preset", write=True)
    def _set_plugin_preset(self, params):
        """Select a preset by index for a VST/AU plugin device.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            preset_index: Index of the preset to select.
        """
        preset_index = params.get("preset_index")

        device, _track = self._resolve_device(params)
        if not hasattr(device, "presets"):
            raise ValueError(
                f"Device '{device.name}' is not a plugin device (VST/AU). "
                "Only plugin devices have presets."
            )

        if preset_index < 0 or preset_index >= len(device.presets):
            raise IndexError(
                f"Preset index {preset_index} out of range "
                f"(0-{len(device.presets) - 1})"
            )

        device.selected_preset_index = preset_index

        return {
            "device_name": device.name,
            "selected_preset_index": device.selected_preset_index,
            "preset_name": device.presets[device.selected_preset_index],
        }

    @command("compare_ab", write=True)
    def _compare_ab(self, params):
        """A/B preset comparison (Live 12.3+).

        Params:
            track_index, device_index, track_type: Standard device addressing.
            action: Optional. 'save' to save preset to compare slot, or omit for info.
        """
        action = params.get("action")

        device, _track = self._resolve_device(params)
        if not device.can_compare_ab:
            raise ValueError(
                f"Device '{device.name}' does not support A/B comparison"
            )

        if action == "save":
            device.save_preset_to_compare_ab_slot()

        return {
            "device_name": device.name,
            "can_compare_ab": device.can_compare_ab,
            "is_using_compare_preset_b": device.is_using_compare_preset_b,
            "action": action or "info",
        }

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
