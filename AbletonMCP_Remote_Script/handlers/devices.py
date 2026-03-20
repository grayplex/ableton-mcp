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

    # --- Quick Task: WavetableDevice ---

    @command("get_wavetable_info")
    def _get_wavetable_info(self, params):
        """Get Wavetable device info including oscillator categories, voice config, and modulation targets.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            chain_index, chain_device_index: Optional chain navigation.
        """
        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "oscillator_wavetable_categories"):
                raise ValueError(f"Device '{device.name}' is not a Wavetable device")

            result = {
                "device_name": device.name,
                "oscillator_wavetable_categories": list(device.oscillator_wavetable_categories),
                "oscillator_1_wavetable_category": device.oscillator_1_wavetable_category,
                "oscillator_1_wavetable_index": device.oscillator_1_wavetable_index,
                "oscillator_2_wavetable_category": device.oscillator_2_wavetable_category,
                "oscillator_2_wavetable_index": device.oscillator_2_wavetable_index,
                "oscillator_1_wavetables": list(device.oscillator_1_wavetables),
                "oscillator_2_wavetables": list(device.oscillator_2_wavetables),
                "oscillator_1_effect_mode": device.oscillator_1_effect_mode,
                "oscillator_2_effect_mode": device.oscillator_2_effect_mode,
                "filter_routing": device.filter_routing,
                "mono_poly": device.mono_poly,
                "poly_voices": device.poly_voices,
                "unison_mode": device.unison_mode,
                "unison_voice_count": device.unison_voice_count,
                "visible_modulation_target_names": list(device.visible_modulation_target_names),
            }
            return result
        except Exception as e:
            self.log_message(f"Error getting wavetable info: {e}")
            raise

    @command("set_wavetable_oscillator", write=True)
    def _set_wavetable_oscillator(self, params):
        """Set oscillator wavetable selection on a Wavetable device.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            oscillator: 1 or 2.
            category: Optional int index for wavetable category.
            index: Optional int index for wavetable within category.
        """
        oscillator = params.get("oscillator")
        category = params.get("category")
        index = params.get("index")

        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "oscillator_wavetable_categories"):
                raise ValueError(f"Device '{device.name}' is not a Wavetable device")

            if oscillator not in (1, 2):
                raise ValueError(f"oscillator must be 1 or 2, got {oscillator}")

            if category is not None:
                setattr(device, f"oscillator_{oscillator}_wavetable_category", category)
            if index is not None:
                setattr(device, f"oscillator_{oscillator}_wavetable_index", index)

            return {
                "device_name": device.name,
                "oscillator": oscillator,
                "category": getattr(device, f"oscillator_{oscillator}_wavetable_category"),
                "index": getattr(device, f"oscillator_{oscillator}_wavetable_index"),
                "wavetables": list(getattr(device, f"oscillator_{oscillator}_wavetables")),
            }
        except Exception as e:
            self.log_message(f"Error setting wavetable oscillator: {e}")
            raise

    @command("set_wavetable_voice_config", write=True)
    def _set_wavetable_voice_config(self, params):
        """Set Wavetable voice configuration.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            mono_poly: Optional int.
            poly_voices: Optional int.
            unison_mode: Optional int.
            unison_voice_count: Optional int.
            filter_routing: Optional int.
            oscillator_1_effect_mode: Optional int.
            oscillator_2_effect_mode: Optional int.
        """
        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "oscillator_wavetable_categories"):
                raise ValueError(f"Device '{device.name}' is not a Wavetable device")

            settable = [
                "mono_poly", "poly_voices", "unison_mode", "unison_voice_count",
                "filter_routing", "oscillator_1_effect_mode", "oscillator_2_effect_mode",
            ]
            for prop in settable:
                val = params.get(prop)
                if val is not None:
                    setattr(device, prop, val)

            return {
                "device_name": device.name,
                "mono_poly": device.mono_poly,
                "poly_voices": device.poly_voices,
                "unison_mode": device.unison_mode,
                "unison_voice_count": device.unison_voice_count,
                "filter_routing": device.filter_routing,
                "oscillator_1_effect_mode": device.oscillator_1_effect_mode,
                "oscillator_2_effect_mode": device.oscillator_2_effect_mode,
            }
        except Exception as e:
            self.log_message(f"Error setting wavetable voice config: {e}")
            raise

    @command("add_wavetable_modulation", write=True)
    def _add_wavetable_modulation(self, params):
        """Add a parameter to the Wavetable modulation matrix.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            parameter_name: Optional str to identify parameter.
            parameter_index: Optional int to identify parameter.
        """
        parameter_name = params.get("parameter_name")
        parameter_index = params.get("parameter_index")

        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "oscillator_wavetable_categories"):
                raise ValueError(f"Device '{device.name}' is not a Wavetable device")

            if parameter_name is not None:
                name_lower = parameter_name.lower()
                param = None
                for p in device.parameters:
                    if p.name.lower() == name_lower:
                        param = p
                        break
                if param is None:
                    raise ValueError(f"Parameter '{parameter_name}' not found")
            elif parameter_index is not None:
                if parameter_index < 0 or parameter_index >= len(device.parameters):
                    raise IndexError(f"Parameter index {parameter_index} out of range")
                param = device.parameters[parameter_index]
            else:
                raise ValueError("Provide parameter_name or parameter_index")

            device.add_parameter_to_modulation_matrix(param)

            return {
                "device_name": device.name,
                "added_parameter": param.name,
            }
        except Exception as e:
            self.log_message(f"Error adding wavetable modulation: {e}")
            raise

    @command("set_wavetable_modulation_value", write=True)
    def _set_wavetable_modulation_value(self, params):
        """Set modulation amount for a parameter in Wavetable's modulation matrix.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            parameter_name/parameter_index: Identify the target parameter.
            modulation_target: str from visible_modulation_target_names.
            value: float modulation amount.
        """
        parameter_name = params.get("parameter_name")
        parameter_index = params.get("parameter_index")
        modulation_target = params.get("modulation_target")
        value = params.get("value")

        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "oscillator_wavetable_categories"):
                raise ValueError(f"Device '{device.name}' is not a Wavetable device")

            if parameter_name is not None:
                name_lower = parameter_name.lower()
                param = None
                for p in device.parameters:
                    if p.name.lower() == name_lower:
                        param = p
                        break
                if param is None:
                    raise ValueError(f"Parameter '{parameter_name}' not found")
            elif parameter_index is not None:
                if parameter_index < 0 or parameter_index >= len(device.parameters):
                    raise IndexError(f"Parameter index {parameter_index} out of range")
                param = device.parameters[parameter_index]
            else:
                raise ValueError("Provide parameter_name or parameter_index")

            device.set_modulation_value(param, modulation_target, value)

            return {
                "device_name": device.name,
                "parameter": param.name,
                "modulation_target": modulation_target,
                "value": value,
            }
        except Exception as e:
            self.log_message(f"Error setting wavetable modulation value: {e}")
            raise

    @command("get_wavetable_modulation_value")
    def _get_wavetable_modulation_value(self, params):
        """Get modulation value for a parameter in Wavetable's modulation matrix.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            parameter_name/parameter_index: Identify the target parameter.
            modulation_target: str from visible_modulation_target_names.
        """
        parameter_name = params.get("parameter_name")
        parameter_index = params.get("parameter_index")
        modulation_target = params.get("modulation_target")

        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "oscillator_wavetable_categories"):
                raise ValueError(f"Device '{device.name}' is not a Wavetable device")

            if parameter_name is not None:
                name_lower = parameter_name.lower()
                param = None
                for p in device.parameters:
                    if p.name.lower() == name_lower:
                        param = p
                        break
                if param is None:
                    raise ValueError(f"Parameter '{parameter_name}' not found")
            elif parameter_index is not None:
                if parameter_index < 0 or parameter_index >= len(device.parameters):
                    raise IndexError(f"Parameter index {parameter_index} out of range")
                param = device.parameters[parameter_index]
            else:
                raise ValueError("Provide parameter_name or parameter_index")

            mod_value = device.get_modulation_value(param, modulation_target)
            is_modulatable = device.is_parameter_modulatable(param)
            target_param_name = device.get_modulation_target_parameter_name(modulation_target)

            return {
                "device_name": device.name,
                "parameter": param.name,
                "modulation_target": modulation_target,
                "value": mod_value,
                "is_modulatable": is_modulatable,
                "target_parameter_name": target_param_name,
            }
        except Exception as e:
            self.log_message(f"Error getting wavetable modulation value: {e}")
            raise

    # --- Quick Task: CompressorDevice ---

    @command("get_compressor_sidechain")
    def _get_compressor_sidechain(self, params):
        """Get sidechain routing info for a Compressor device.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "available_input_routing_types"):
                raise ValueError(
                    f"Device '{device.name}' does not support sidechain routing"
                )

            return {
                "device_name": device.name,
                "available_input_routing_types": [
                    t.display_name for t in device.available_input_routing_types
                ],
                "available_input_routing_channels": [
                    c.display_name for c in device.available_input_routing_channels
                ],
                "input_routing_type": device.input_routing_type.display_name,
                "input_routing_channel": device.input_routing_channel.display_name,
            }
        except Exception as e:
            self.log_message(f"Error getting compressor sidechain: {e}")
            raise

    @command("set_compressor_sidechain", write=True)
    def _set_compressor_sidechain(self, params):
        """Set sidechain source on a Compressor device.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            routing_type_index: Optional int index into available_input_routing_types.
            routing_channel_index: Optional int index into available_input_routing_channels.
        """
        routing_type_index = params.get("routing_type_index")
        routing_channel_index = params.get("routing_channel_index")

        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "available_input_routing_types"):
                raise ValueError(
                    f"Device '{device.name}' does not support sidechain routing"
                )

            if routing_type_index is not None:
                types = device.available_input_routing_types
                if routing_type_index < 0 or routing_type_index >= len(types):
                    raise IndexError(
                        f"routing_type_index {routing_type_index} out of range "
                        f"(0-{len(types) - 1})"
                    )
                device.input_routing_type = types[routing_type_index]

            if routing_channel_index is not None:
                channels = device.available_input_routing_channels
                if routing_channel_index < 0 or routing_channel_index >= len(channels):
                    raise IndexError(
                        f"routing_channel_index {routing_channel_index} out of range "
                        f"(0-{len(channels) - 1})"
                    )
                device.input_routing_channel = channels[routing_channel_index]

            return {
                "device_name": device.name,
                "input_routing_type": device.input_routing_type.display_name,
                "input_routing_channel": device.input_routing_channel.display_name,
            }
        except Exception as e:
            self.log_message(f"Error setting compressor sidechain: {e}")
            raise

    # --- Quick Task: RackDevice Extended ---

    @command("get_rack_variations")
    def _get_rack_variations(self, params):
        """Get macro variation info for a rack device.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "variation_count"):
                raise ValueError(
                    f"Device '{device.name}' does not support macro variations"
                )

            return {
                "device_name": device.name,
                "variation_count": device.variation_count,
                "selected_variation_index": device.selected_variation_index,
                "visible_macro_count": device.visible_macro_count,
            }
        except Exception as e:
            self.log_message(f"Error getting rack variations: {e}")
            raise

    @command("rack_variation_action", write=True)
    def _rack_variation_action(self, params):
        """Manage rack macro variations (store, recall, recall_last, delete).

        Params:
            track_index, device_index, track_type: Standard device addressing.
            action: 'store', 'recall', 'recall_last', or 'delete'.
            index: Optional int for recall/delete.
        """
        action = params.get("action")
        index = params.get("index")

        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "variation_count"):
                raise ValueError(
                    f"Device '{device.name}' does not support macro variations"
                )

            if action == "store":
                device.store_variation()
            elif action == "recall":
                if index is not None:
                    device.selected_variation_index = index
                device.recall_selected_variation()
            elif action == "recall_last":
                device.recall_last_used_variation()
            elif action == "delete":
                if index is not None:
                    device.selected_variation_index = index
                device.delete_selected_variation()
            else:
                raise ValueError(
                    f"Invalid action '{action}'. Use 'store', 'recall', "
                    "'recall_last', or 'delete'."
                )

            return {
                "device_name": device.name,
                "action": action,
                "variation_count": device.variation_count,
                "selected_variation_index": device.selected_variation_index,
            }
        except Exception as e:
            self.log_message(f"Error performing rack variation action: {e}")
            raise

    @command("rack_macro_action", write=True)
    def _rack_macro_action(self, params):
        """Manage rack macros (add, remove, randomize).

        Params:
            track_index, device_index, track_type: Standard device addressing.
            action: 'add', 'remove', or 'randomize'.
        """
        action = params.get("action")

        try:
            device, _track = self._resolve_device(params)

            if action == "add":
                device.add_macro()
            elif action == "remove":
                device.remove_macro()
            elif action == "randomize":
                device.randomize_macros()
            else:
                raise ValueError(
                    f"Invalid action '{action}'. Use 'add', 'remove', or 'randomize'."
                )

            return {
                "device_name": device.name,
                "action": action,
                "visible_macro_count": device.visible_macro_count,
            }
        except Exception as e:
            self.log_message(f"Error performing rack macro action: {e}")
            raise

    @command("insert_rack_chain", write=True)
    def _insert_rack_chain(self, params):
        """Insert a new chain into a rack device.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            index: Optional int position to insert (default: end of chain list).
        """
        index = params.get("index")

        try:
            device, _track = self._resolve_device(params)
            if not device.can_have_chains:
                raise ValueError(
                    f"Device '{device.name}' is not a rack and cannot have chains"
                )

            insert_index = index if index is not None else len(device.chains)
            device.insert_chain(insert_index)

            chains = []
            for ci, chain in enumerate(device.chains):
                chains.append({"index": ci, "name": chain.name})

            return {
                "device_name": device.name,
                "inserted_at": insert_index,
                "chains": chains,
            }
        except Exception as e:
            self.log_message(f"Error inserting rack chain: {e}")
            raise

    @command("copy_drum_pad", write=True)
    def _copy_drum_pad(self, params):
        """Copy drum pad content from one pad to another.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            source_note: int MIDI note of the source pad.
            target_note: int MIDI note of the target pad.
        """
        source_note = params.get("source_note")
        target_note = params.get("target_note")

        try:
            device, _track = self._resolve_device(params)
            if not device.can_have_drum_pads:
                raise ValueError(f"Device '{device.name}' is not a Drum Rack")

            device.copy_pad(source_note, target_note)

            return {
                "device_name": device.name,
                "source_note": source_note,
                "target_note": target_note,
                "copied": True,
            }
        except Exception as e:
            self.log_message(f"Error copying drum pad: {e}")
            raise

    # --- Quick Task: DrumChain ---

    @command("get_drum_chain_config")
    def _get_drum_chain_config(self, params):
        """Get drum chain configuration (in_note, out_note, choke_group).

        Params:
            track_index, device_index, track_type: Standard device addressing.
            chain_index: Index of the chain within the drum rack.
        """
        chain_index = params.get("chain_index")

        try:
            device, _track = self._resolve_device(params)
            if not device.can_have_chains:
                raise ValueError(f"Device '{device.name}' does not have chains")

            if chain_index is None:
                raise ValueError("chain_index is required")
            if chain_index < 0 or chain_index >= len(device.chains):
                raise IndexError(
                    f"Chain index {chain_index} out of range "
                    f"(0-{len(device.chains) - 1})"
                )

            chain = device.chains[chain_index]
            if not hasattr(chain, "in_note"):
                raise ValueError(
                    f"Chain '{chain.name}' is not a DrumChain (no in_note property)"
                )

            return {
                "device_name": device.name,
                "chain_index": chain_index,
                "name": chain.name,
                "in_note": chain.in_note,
                "out_note": chain.out_note,
                "choke_group": chain.choke_group,
            }
        except Exception as e:
            self.log_message(f"Error getting drum chain config: {e}")
            raise

    @command("set_drum_chain_config", write=True)
    def _set_drum_chain_config(self, params):
        """Set drum chain properties (in_note, out_note, choke_group).

        Params:
            track_index, device_index, track_type: Standard device addressing.
            chain_index: Index of the chain within the drum rack.
            in_note: Optional int MIDI note for input.
            out_note: Optional int MIDI note for output.
            choke_group: Optional int choke group number.
        """
        chain_index = params.get("chain_index")
        in_note = params.get("in_note")
        out_note = params.get("out_note")
        choke_group = params.get("choke_group")

        try:
            device, _track = self._resolve_device(params)
            if not device.can_have_chains:
                raise ValueError(f"Device '{device.name}' does not have chains")

            if chain_index is None:
                raise ValueError("chain_index is required")
            if chain_index < 0 or chain_index >= len(device.chains):
                raise IndexError(
                    f"Chain index {chain_index} out of range "
                    f"(0-{len(device.chains) - 1})"
                )

            chain = device.chains[chain_index]
            if not hasattr(chain, "in_note"):
                raise ValueError(
                    f"Chain '{chain.name}' is not a DrumChain (no in_note property)"
                )

            if in_note is not None:
                chain.in_note = in_note
            if out_note is not None:
                chain.out_note = out_note
            if choke_group is not None:
                chain.choke_group = choke_group

            return {
                "device_name": device.name,
                "chain_index": chain_index,
                "name": chain.name,
                "in_note": chain.in_note,
                "out_note": chain.out_note,
                "choke_group": chain.choke_group,
            }
        except Exception as e:
            self.log_message(f"Error setting drum chain config: {e}")
            raise

    # --- Quick Task: DeviceParameter Extended ---

    @command("get_parameter_automation_state")
    def _get_parameter_automation_state(self, params):
        """Get parameter automation state (none, playing, overridden).

        Params:
            track_index, device_index, track_type: Standard device addressing.
            parameter_name/parameter_index: Identify the parameter.
        """
        parameter_name = params.get("parameter_name")
        parameter_index = params.get("parameter_index")

        try:
            device, _track = self._resolve_device(params)

            if parameter_name is not None:
                name_lower = parameter_name.lower()
                param = None
                matched_index = None
                for i, p in enumerate(device.parameters):
                    if p.name.lower() == name_lower:
                        param = p
                        matched_index = i
                        break
                if param is None:
                    raise ValueError(f"Parameter '{parameter_name}' not found")
            elif parameter_index is not None:
                if parameter_index < 0 or parameter_index >= len(device.parameters):
                    raise IndexError(f"Parameter index {parameter_index} out of range")
                param = device.parameters[parameter_index]
                matched_index = parameter_index
            else:
                raise ValueError("Provide parameter_name or parameter_index")

            result = {
                "device_name": device.name,
                "parameter_name": param.name,
                "parameter_index": matched_index,
            }

            if hasattr(param, "automation_state"):
                result["automation_state"] = param.automation_state
            if hasattr(param, "default_value"):
                result["default_value"] = param.default_value
            if hasattr(param, "is_enabled"):
                result["is_enabled"] = param.is_enabled
            if hasattr(param, "state"):
                result["state"] = param.state

            return result
        except Exception as e:
            self.log_message(f"Error getting parameter automation state: {e}")
            raise

    @command("re_enable_parameter_automation", write=True)
    def _re_enable_parameter_automation(self, params):
        """Re-enable overridden automation for a parameter.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            parameter_name/parameter_index: Identify the parameter.
        """
        parameter_name = params.get("parameter_name")
        parameter_index = params.get("parameter_index")

        try:
            device, _track = self._resolve_device(params)

            if parameter_name is not None:
                name_lower = parameter_name.lower()
                param = None
                matched_index = None
                for i, p in enumerate(device.parameters):
                    if p.name.lower() == name_lower:
                        param = p
                        matched_index = i
                        break
                if param is None:
                    raise ValueError(f"Parameter '{parameter_name}' not found")
            elif parameter_index is not None:
                if parameter_index < 0 or parameter_index >= len(device.parameters):
                    raise IndexError(f"Parameter index {parameter_index} out of range")
                param = device.parameters[parameter_index]
                matched_index = parameter_index
            else:
                raise ValueError("Provide parameter_name or parameter_index")

            param.re_enable_automation()

            result = {
                "device_name": device.name,
                "parameter_name": param.name,
                "parameter_index": matched_index,
                "re_enabled": True,
            }
            if hasattr(param, "automation_state"):
                result["automation_state"] = param.automation_state

            return result
        except Exception as e:
            self.log_message(f"Error re-enabling parameter automation: {e}")
            raise

    # --- Quick Task: DriftDevice ---

    @command("get_drift_mod_matrix")
    def _get_drift_mod_matrix(self, params):
        """Get Drift modulation matrix state for all 8 slots.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "mod_matrix_1_source_index"):
                raise ValueError(f"Device '{device.name}' is not a Drift device")

            slots = []
            for i in range(1, 9):
                slot = {"slot": i}
                slot["source_index"] = getattr(device, f"mod_matrix_{i}_source_index")
                if hasattr(device, f"mod_matrix_{i}_source_list"):
                    slot["source_list"] = list(
                        getattr(device, f"mod_matrix_{i}_source_list")
                    )
                slot["target_index"] = getattr(device, f"mod_matrix_{i}_target_index")
                if hasattr(device, f"mod_matrix_{i}_target_list"):
                    slot["target_list"] = list(
                        getattr(device, f"mod_matrix_{i}_target_list")
                    )
                slots.append(slot)

            return {
                "device_name": device.name,
                "slots": slots,
            }
        except Exception as e:
            self.log_message(f"Error getting Drift mod matrix: {e}")
            raise

    @command("set_drift_mod_matrix", write=True)
    def _set_drift_mod_matrix(self, params):
        """Set Drift modulation matrix slot source/target.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            slot: int 1-8 identifying the mod matrix slot.
            source_index: Optional int source index.
            target_index: Optional int target index.
        """
        slot = params.get("slot")
        source_index = params.get("source_index")
        target_index = params.get("target_index")

        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "mod_matrix_1_source_index"):
                raise ValueError(f"Device '{device.name}' is not a Drift device")

            if slot is None or slot < 1 or slot > 8:
                raise ValueError(f"slot must be 1-8, got {slot}")

            if source_index is not None:
                setattr(device, f"mod_matrix_{slot}_source_index", source_index)
            if target_index is not None:
                setattr(device, f"mod_matrix_{slot}_target_index", target_index)

            result = {
                "device_name": device.name,
                "slot": slot,
                "source_index": getattr(device, f"mod_matrix_{slot}_source_index"),
                "target_index": getattr(device, f"mod_matrix_{slot}_target_index"),
            }
            if hasattr(device, f"mod_matrix_{slot}_source_list"):
                result["source_list"] = list(
                    getattr(device, f"mod_matrix_{slot}_source_list")
                )
            if hasattr(device, f"mod_matrix_{slot}_target_list"):
                result["target_list"] = list(
                    getattr(device, f"mod_matrix_{slot}_target_list")
                )

            return result
        except Exception as e:
            self.log_message(f"Error setting Drift mod matrix: {e}")
            raise

    # --- Quick Task: LooperDevice ---

    @command("get_looper_info")
    def _get_looper_info(self, params):
        """Get Looper device state.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "overdub_after_record"):
                raise ValueError(f"Device '{device.name}' is not a Looper device")

            return {
                "device_name": device.name,
                "loop_length": device.loop_length,
                "overdub_after_record": device.overdub_after_record,
                "record_length_index": device.record_length_index,
                "record_length_list": list(device.record_length_list),
                "tempo": device.tempo,
            }
        except Exception as e:
            self.log_message(f"Error getting looper info: {e}")
            raise

    @command("looper_action", write=True)
    def _looper_action(self, params):
        """Execute a Looper action.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            action: One of 'record', 'overdub', 'play', 'stop', 'clear',
                    'undo', 'double_speed', 'half_speed', 'double_length',
                    'half_length'.
        """
        action = params.get("action")

        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "overdub_after_record"):
                raise ValueError(f"Device '{device.name}' is not a Looper device")

            action_map = {
                "record": "record",
                "overdub": "overdub",
                "play": "play",
                "stop": "stop",
                "clear": "clear",
                "undo": "undo",
                "double_speed": "double_speed",
                "half_speed": "half_speed",
                "double_length": "double_length",
                "half_length": "half_length",
            }

            if action not in action_map:
                raise ValueError(
                    f"Invalid action '{action}'. Valid actions: "
                    f"{list(action_map.keys())}"
                )

            getattr(device, action_map[action])()

            return {
                "device_name": device.name,
                "action": action,
                "performed": True,
            }
        except Exception as e:
            self.log_message(f"Error performing looper action: {e}")
            raise

    @command("looper_export_to_clip_slot", write=True)
    def _looper_export_to_clip_slot(self, params):
        """Export Looper content to a clip slot.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            scene_index: int index of the scene/clip slot to export to.
        """
        scene_index = params.get("scene_index")

        try:
            device, track = self._resolve_device(params)
            if not hasattr(device, "overdub_after_record"):
                raise ValueError(f"Device '{device.name}' is not a Looper device")

            if scene_index is None:
                raise ValueError("scene_index is required")

            if not hasattr(track, "clip_slots"):
                raise ValueError("Track does not have clip slots")

            if scene_index < 0 or scene_index >= len(track.clip_slots):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(track.clip_slots) - 1})"
                )

            device.export_to_clip_slot(track.clip_slots[scene_index])

            return {
                "device_name": device.name,
                "exported": True,
                "scene_index": scene_index,
                "track_name": track.name,
            }
        except Exception as e:
            self.log_message(f"Error exporting looper to clip slot: {e}")
            raise

    # --- Quick Task: SpectralResonatorDevice ---

    @command("get_spectral_resonator_info")
    def _get_spectral_resonator_info(self, params):
        """Get Spectral Resonator device configuration.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "frequency_dial_mode"):
                raise ValueError(
                    f"Device '{device.name}' is not a Spectral Resonator device"
                )

            return {
                "device_name": device.name,
                "frequency_dial_mode": device.frequency_dial_mode,
                "midi_gate": device.midi_gate,
                "mod_mode": device.mod_mode,
                "mono_poly": device.mono_poly,
                "pitch_mode": device.pitch_mode,
                "pitch_bend_range": device.pitch_bend_range,
                "polyphony": device.polyphony,
            }
        except Exception as e:
            self.log_message(f"Error getting spectral resonator info: {e}")
            raise

    @command("set_spectral_resonator_config", write=True)
    def _set_spectral_resonator_config(self, params):
        """Set Spectral Resonator device properties.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            frequency_dial_mode, midi_gate, mod_mode, mono_poly,
            pitch_mode, pitch_bend_range, polyphony: Optional values to set.
        """
        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "frequency_dial_mode"):
                raise ValueError(
                    f"Device '{device.name}' is not a Spectral Resonator device"
                )

            settable = [
                "frequency_dial_mode", "midi_gate", "mod_mode", "mono_poly",
                "pitch_mode", "pitch_bend_range", "polyphony",
            ]
            for prop in settable:
                val = params.get(prop)
                if val is not None:
                    setattr(device, prop, val)

            return {
                "device_name": device.name,
                "frequency_dial_mode": device.frequency_dial_mode,
                "midi_gate": device.midi_gate,
                "mod_mode": device.mod_mode,
                "mono_poly": device.mono_poly,
                "pitch_mode": device.pitch_mode,
                "pitch_bend_range": device.pitch_bend_range,
                "polyphony": device.polyphony,
            }
        except Exception as e:
            self.log_message(f"Error setting spectral resonator config: {e}")
            raise

    # --- Quick Task: Eq8Device ---

    @command("get_eq8_info")
    def _get_eq8_info(self, params):
        """Get EQ8 processing modes.

        Params:
            track_index, device_index, track_type: Standard device addressing.
        """
        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "edit_mode"):
                raise ValueError(f"Device '{device.name}' does not have edit_mode")

            return {
                "device_name": device.name,
                "class_name": device.class_name,
                "edit_mode": device.edit_mode,
                "global_mode": device.global_mode,
                "oversample": device.oversample,
            }
        except Exception as e:
            self.log_message(f"Error getting EQ8 info: {e}")
            raise

    @command("set_eq8_mode", write=True)
    def _set_eq8_mode(self, params):
        """Set EQ8 processing modes.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            edit_mode: Optional int.
            global_mode: Optional int.
            oversample: Optional bool.
        """
        edit_mode = params.get("edit_mode")
        global_mode = params.get("global_mode")
        oversample = params.get("oversample")

        try:
            device, _track = self._resolve_device(params)
            if not hasattr(device, "edit_mode"):
                raise ValueError(f"Device '{device.name}' does not have edit_mode")

            if edit_mode is not None:
                device.edit_mode = edit_mode
            if global_mode is not None:
                device.global_mode = global_mode
            if oversample is not None:
                device.oversample = oversample

            return {
                "device_name": device.name,
                "edit_mode": device.edit_mode,
                "global_mode": device.global_mode,
                "oversample": device.oversample,
            }
        except Exception as e:
            self.log_message(f"Error setting EQ8 mode: {e}")
            raise

    # --- Quick Task: TakeLane ---

    @command("get_take_lanes")
    def _get_take_lanes(self, params):
        """Get take lanes for a track.

        Params:
            track_index: Index of the track.
            track_type: "track", "return", or "master" (default "track").
        """
        track_index = params.get("track_index", 0)
        track_type = params.get("track_type", "track")

        try:
            track = _resolve_track(self._song, track_type, track_index)
            if not hasattr(track, "take_lanes"):
                raise ValueError(f"Track '{track.name}' does not support take lanes")

            lanes = []
            for i, lane in enumerate(track.take_lanes):
                lane_info = {"index": i, "name": lane.name}
                if hasattr(lane, "arrangement_clips"):
                    lane_info["clip_count"] = len(lane.arrangement_clips)
                lanes.append(lane_info)

            return {
                "track_name": track.name,
                "take_lane_count": len(lanes),
                "take_lanes": lanes,
            }
        except Exception as e:
            self.log_message(f"Error getting take lanes: {e}")
            raise

    @command("get_take_lane_clips")
    def _get_take_lane_clips(self, params):
        """Get arrangement clips in a take lane.

        Params:
            track_index: Index of the track.
            track_type: "track", "return", or "master" (default "track").
            lane_index: Index of the take lane.
        """
        track_index = params.get("track_index", 0)
        track_type = params.get("track_type", "track")
        lane_index = params.get("lane_index")

        try:
            track = _resolve_track(self._song, track_type, track_index)
            if not hasattr(track, "take_lanes"):
                raise ValueError(f"Track '{track.name}' does not support take lanes")

            if lane_index is None:
                raise ValueError("lane_index is required")
            if lane_index < 0 or lane_index >= len(track.take_lanes):
                raise IndexError(
                    f"Lane index {lane_index} out of range "
                    f"(0-{len(track.take_lanes) - 1})"
                )

            lane = track.take_lanes[lane_index]
            clips = []
            if hasattr(lane, "arrangement_clips"):
                for ci, clip in enumerate(lane.arrangement_clips):
                    clip_info = {"index": ci, "name": clip.name}
                    if hasattr(clip, "start_time"):
                        clip_info["start_time"] = clip.start_time
                    if hasattr(clip, "end_time"):
                        clip_info["end_time"] = clip.end_time
                    if hasattr(clip, "length"):
                        clip_info["length"] = clip.length
                    clips.append(clip_info)

            return {
                "track_name": track.name,
                "lane_index": lane_index,
                "lane_name": lane.name,
                "clips": clips,
            }
        except Exception as e:
            self.log_message(f"Error getting take lane clips: {e}")
            raise

    @command("create_take_lane_clip", write=True)
    def _create_take_lane_clip(self, params):
        """Create a clip in a take lane.

        Params:
            track_index: Index of the track.
            track_type: "track", "return", or "master" (default "track").
            lane_index: Index of the take lane.
            start_time: float start position in beats.
            length: float clip length in beats.
            clip_type: 'midi' or 'audio'.
        """
        track_index = params.get("track_index", 0)
        track_type = params.get("track_type", "track")
        lane_index = params.get("lane_index")
        start_time = params.get("start_time")
        length = params.get("length")
        clip_type = params.get("clip_type", "midi")

        try:
            track = _resolve_track(self._song, track_type, track_index)
            if not hasattr(track, "take_lanes"):
                raise ValueError(f"Track '{track.name}' does not support take lanes")

            if lane_index is None:
                raise ValueError("lane_index is required")
            if lane_index < 0 or lane_index >= len(track.take_lanes):
                raise IndexError(
                    f"Lane index {lane_index} out of range "
                    f"(0-{len(track.take_lanes) - 1})"
                )

            lane = track.take_lanes[lane_index]

            if clip_type == "midi":
                clip = lane.create_midi_clip(start_time, length)
            elif clip_type == "audio":
                clip = lane.create_audio_clip(start_time, length)
            else:
                raise ValueError(
                    f"Invalid clip_type '{clip_type}'. Use 'midi' or 'audio'."
                )

            return {
                "track_name": track.name,
                "lane_index": lane_index,
                "created": True,
                "clip_type": clip_type,
                "clip_name": clip.name,
                "start_time": start_time,
                "length": length,
            }
        except Exception as e:
            self.log_message(f"Error creating take lane clip: {e}")
            raise

    # --- Quick Task: TuningSystem ---

    @command("get_tuning_system")
    def _get_tuning_system(self, params=None):
        """Get tuning system info for the song.

        No device addressing needed -- song-level access.
        """
        try:
            if not hasattr(self._song, "tuning_system"):
                raise ValueError("Tuning system not available in this Live version")

            ts = self._song.tuning_system

            return {
                "name": ts.name,
                "pseudo_octave_in_cents": ts.pseudo_octave_in_cents,
                "lowest_note": ts.lowest_note,
                "highest_note": ts.highest_note,
                "reference_pitch": ts.reference_pitch,
                "note_tunings": list(ts.note_tunings),
            }
        except Exception as e:
            self.log_message(f"Error getting tuning system: {e}")
            raise

    @command("set_tuning_system", write=True)
    def _set_tuning_system(self, params):
        """Set tuning system properties.

        Params:
            reference_pitch: Optional float reference pitch.
            note_tunings: Optional list of float cent offsets.
        """
        reference_pitch = params.get("reference_pitch")
        note_tunings = params.get("note_tunings")

        try:
            if not hasattr(self._song, "tuning_system"):
                raise ValueError("Tuning system not available in this Live version")

            ts = self._song.tuning_system

            if reference_pitch is not None:
                ts.reference_pitch = reference_pitch
            if note_tunings is not None:
                ts.note_tunings = note_tunings

            return {
                "name": ts.name,
                "reference_pitch": ts.reference_pitch,
                "note_tunings": list(ts.note_tunings),
            }
        except Exception as e:
            self.log_message(f"Error setting tuning system: {e}")
            raise

    # --- Quick Task: Chain Direct Control ---

    @command("set_chain_mute_solo", write=True)
    def _set_chain_mute_solo(self, params):
        """Mute or solo a chain within a rack device.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            chain_index: Index of the chain.
            mute: Optional bool.
            solo: Optional bool.
        """
        chain_index = params.get("chain_index")
        mute = params.get("mute")
        solo = params.get("solo")

        try:
            device, _track = self._resolve_device(params)
            if not device.can_have_chains:
                raise ValueError(f"Device '{device.name}' does not have chains")

            if chain_index is None:
                raise ValueError("chain_index is required")
            if chain_index < 0 or chain_index >= len(device.chains):
                raise IndexError(
                    f"Chain index {chain_index} out of range "
                    f"(0-{len(device.chains) - 1})"
                )

            chain = device.chains[chain_index]

            if mute is not None:
                chain.mute = mute
            if solo is not None:
                chain.solo = solo

            return {
                "device_name": device.name,
                "chain_index": chain_index,
                "name": chain.name,
                "mute": chain.mute,
                "solo": chain.solo,
            }
        except Exception as e:
            self.log_message(f"Error setting chain mute/solo: {e}")
            raise

    @command("set_chain_name_color", write=True)
    def _set_chain_name_color(self, params):
        """Set chain name or color within a rack device.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            chain_index: Index of the chain.
            name: Optional str new name.
            color_index: Optional int color index.
        """
        chain_index = params.get("chain_index")
        name = params.get("name")
        color_index = params.get("color_index")

        try:
            device, _track = self._resolve_device(params)
            if not device.can_have_chains:
                raise ValueError(f"Device '{device.name}' does not have chains")

            if chain_index is None:
                raise ValueError("chain_index is required")
            if chain_index < 0 or chain_index >= len(device.chains):
                raise IndexError(
                    f"Chain index {chain_index} out of range "
                    f"(0-{len(device.chains) - 1})"
                )

            chain = device.chains[chain_index]

            if name is not None:
                chain.name = name
            if color_index is not None:
                chain.color_index = color_index

            return {
                "device_name": device.name,
                "chain_index": chain_index,
                "name": chain.name,
                "color_index": chain.color_index,
            }
        except Exception as e:
            self.log_message(f"Error setting chain name/color: {e}")
            raise

    @command("get_chain_info")
    def _get_chain_info(self, params):
        """Get detailed chain info including mixer state and devices.

        Params:
            track_index, device_index, track_type: Standard device addressing.
            chain_index: Index of the chain.
        """
        chain_index = params.get("chain_index")

        try:
            device, _track = self._resolve_device(params)
            if not device.can_have_chains:
                raise ValueError(f"Device '{device.name}' does not have chains")

            if chain_index is None:
                raise ValueError("chain_index is required")
            if chain_index < 0 or chain_index >= len(device.chains):
                raise IndexError(
                    f"Chain index {chain_index} out of range "
                    f"(0-{len(device.chains) - 1})"
                )

            chain = device.chains[chain_index]

            result = {
                "device_name": device.name,
                "chain_index": chain_index,
                "name": chain.name,
                "color_index": chain.color_index,
                "mute": chain.mute,
                "solo": chain.solo,
                "device_count": len(chain.devices),
            }

            if hasattr(chain, "is_auto_colored"):
                result["is_auto_colored"] = chain.is_auto_colored

            if hasattr(chain, "color"):
                result["color"] = chain.color

            if hasattr(chain, "mixer_device"):
                mixer = chain.mixer_device
                mixer_info = {}
                if hasattr(mixer, "volume"):
                    mixer_info["volume"] = mixer.volume.value
                if hasattr(mixer, "panning"):
                    mixer_info["panning"] = mixer.panning.value
                if hasattr(mixer, "sends"):
                    mixer_info["sends"] = [
                        {"index": i, "value": s.value}
                        for i, s in enumerate(mixer.sends)
                    ]
                result["mixer_device"] = mixer_info

            return result
        except Exception as e:
            self.log_message(f"Error getting chain info: {e}")
            raise

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
