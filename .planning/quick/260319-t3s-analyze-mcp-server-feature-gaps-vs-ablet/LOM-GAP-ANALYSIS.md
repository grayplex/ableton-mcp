# LOM Gap Analysis: Ableton MCP Server vs. Live Object Model

**Date:** 2026-03-19
**LOM Source:** Max9-LOM-en.pdf (Live 12.3.5 / Max 9, 171 pages, 43 LOM classes)
**Baseline:** 144 Remote Script commands across 15 handler modules, 141 MCP tools across 14 tool modules
**Prior Audit:** Phase 11 audited 12 core classes (Song, Track, Clip, ClipSlot, Scene, Device, PluginDevice, SimplerDevice, MixerDevice, GroovePool, CuePoint, DrumPad)

---

## Section 1: Current Implementation Inventory

### Summary Statistics

| Metric | Count |
|--------|-------|
| Remote Script handler modules | 15 (+ mixer_helpers) |
| MCP tool modules | 14 (+ session) |
| Total Remote Script commands | 144 |
| Total MCP tools | 141 |
| Domains covered | 15 |

### 1.1 Session / Base (base.py / session.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `ping` | `get_connection_status` | Read | Connection health check |
| 2 | `get_session_info` | `get_session_info` | Read | Session metadata (tempo, tracks, etc.) |
| 3 | `get_session_state` | `get_session_state` | Read | Bulk session dump (tracks, clips, devices, mixer) |

### 1.2 Track Management (tracks.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `get_track_info` | `get_track_info` | Read | Detailed track info (devices, clips, mixer) |
| 2 | `get_all_tracks` | `get_all_tracks` | Read | Summary of all tracks |
| 3 | `create_midi_track` | `create_midi_track` | Write | Create new MIDI track |
| 4 | `create_audio_track` | `create_audio_track` | Write | Create new audio track |
| 5 | `create_return_track` | `create_return_track` | Write | Create new return track |
| 6 | `create_group_track` | `create_group_track` | Write | Create group track |
| 7 | `set_track_name` | `set_track_name` | Write | Rename a track |
| 8 | `delete_track` | `delete_track` | Write | Delete a track |
| 9 | `duplicate_track` | `duplicate_track` | Write | Duplicate a track |
| 10 | `set_track_color` | `set_track_color` | Write | Set track color by name |
| 11 | `set_group_fold` | `set_group_fold` | Write | Fold/unfold group tracks |
| 12 | `stop_track_clips` | `stop_track_clips` | Write | Stop all clips on a track |
| 13 | `get_track_freeze_state` | `get_track_freeze_state` | Read | Query frozen/can_be_frozen state |

### 1.3 Clip Management (clips.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `create_clip` | `create_clip` | Write | Create MIDI clip in session view |
| 2 | `set_clip_name` | `set_clip_name` | Write | Rename a clip |
| 3 | `fire_clip` | `fire_clip` | Write | Launch a clip |
| 4 | `stop_clip` | `stop_clip` | Write | Stop a clip |
| 5 | `delete_clip` | `delete_clip` | Write | Delete a clip |
| 6 | `duplicate_clip` | `duplicate_clip` | Write | Duplicate clip to another slot |
| 7 | `get_clip_info` | `get_clip_info` | Read | Get clip properties |
| 8 | `set_clip_color` | `set_clip_color` | Write | Set clip color by name |
| 9 | `set_clip_loop` | `set_clip_loop` | Write | Set loop/marker positions |
| 10 | `get_clip_launch_settings` | `get_clip_launch_settings` | Read | Get launch mode/quantization/legato/velocity |
| 11 | `set_clip_launch_settings` | `set_clip_launch_settings` | Write | Set launch mode/quantization/legato/velocity |
| 12 | `set_clip_muted` | `set_clip_muted` | Write | Set clip activator on/off |
| 13 | `crop_clip` | `crop_clip` | Write | Crop clip to loop/markers |
| 14 | `duplicate_clip_loop` | `duplicate_clip_loop` | Write | Double loop + duplicate content |
| 15 | `duplicate_clip_region` | `duplicate_clip_region` | Write | Duplicate a region within a clip |
| 16 | `set_clip_groove` | `set_clip_groove` | Write | Assign/clear groove on clip |
| 17 | `create_session_audio_clip` | `create_session_audio_clip` | Write | Create audio clip in session from file |

### 1.4 MIDI / Note Editing (notes.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `add_notes_to_clip` | `add_notes_to_clip` | Write | Add MIDI notes (incl. expression fields) |
| 2 | `get_notes` | `get_notes` | Read | Get all notes (incl. note_id, probability, etc.) |
| 3 | `remove_notes` | `remove_notes` | Write | Remove notes by pitch/time range |
| 4 | `quantize_notes` | `quantize_notes` | Write | Manual quantize to grid |
| 5 | `transpose_notes` | `transpose_notes` | Write | Transpose all notes by semitones |
| 6 | `apply_note_modifications` | `apply_note_modifications` | Write | Modify notes in-place by ID |
| 7 | `select_all_notes` | `select_all_notes` | Write | Select all notes |
| 8 | `deselect_all_notes` | `deselect_all_notes` | Write | Deselect all notes |
| 9 | `select_notes_by_id` | `select_notes_by_id` | Write | Select specific notes by ID |
| 10 | `get_notes_by_id` | `get_notes_by_id` | Read | Get specific notes by ID |
| 11 | `remove_notes_by_id` | `remove_notes_by_id` | Write | Remove specific notes by ID |
| 12 | `duplicate_notes_by_id` | `duplicate_notes_by_id` | Write | Duplicate specific notes by ID |
| 13 | `get_selected_notes` | `get_selected_notes` | Read | Get currently selected notes |
| 14 | `native_quantize` | `native_quantize` | Write | Native Ableton quantize (respects swing) |

### 1.5 Device / Instrument Control (devices.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `get_device_parameters` | `get_device_parameters` | Read | Get all parameters of a device |
| 2 | `set_device_parameter` | `set_device_parameter` | Write | Set parameter by name or index |
| 3 | `delete_device` | `delete_device` | Write | Delete a device from chain |
| 4 | `get_rack_chains` | `get_rack_chains` | Read | Get rack chain structure |
| 5 | `insert_device` | `insert_device` | Write | Insert native device by name (Live 12.3+) |
| 6 | `move_device` | `move_device` | Write | Move device between tracks/positions |
| 7 | `crop_simpler` | `crop_simpler` | Write | Crop Simpler sample |
| 8 | `reverse_simpler` | `reverse_simpler` | Write | Reverse Simpler sample |
| 9 | `warp_simpler` | `warp_simpler` | Write | Warp Simpler sample (as/double/half) |
| 10 | `get_simpler_info` | `get_simpler_info` | Read | Get Simpler mode, warp, sample info |
| 11 | `set_simpler_playback_mode` | `set_simpler_playback_mode` | Write | Set Classic/One-Shot/Slicing mode |
| 12 | `insert_simpler_slice` | `insert_simpler_slice` | Write | Insert slice marker |
| 13 | `move_simpler_slice` | `move_simpler_slice` | Write | Move slice marker |
| 14 | `remove_simpler_slice` | `remove_simpler_slice` | Write | Remove slice marker |
| 15 | `clear_simpler_slices` | `clear_simpler_slices` | Write | Clear all slice markers |
| 16 | `set_drum_pad_mute` | `set_drum_pad_mute` | Write | Mute/unmute drum pad |
| 17 | `set_drum_pad_solo` | `set_drum_pad_solo` | Write | Solo/unsolo drum pad |
| 18 | `delete_drum_pad_chains` | `delete_drum_pad_chains` | Write | Clear drum pad content |
| 19 | `list_plugin_presets` | `list_plugin_presets` | Read | List VST/AU plugin presets |
| 20 | `set_plugin_preset` | `set_plugin_preset` | Write | Select plugin preset by index |
| 21 | `compare_ab` | `compare_ab` | Write | A/B preset comparison (Live 12.3+) |
| 22 | `get_session_state` | -- (in session.py) | Read | Bulk session state dump |

### 1.6 Mixer (mixer.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `set_track_volume` | `set_track_volume` | Write | Set track volume (0.0-1.0) |
| 2 | `set_track_pan` | `set_track_pan` | Write | Set track pan (-1.0 to 1.0) |
| 3 | `set_track_mute` | `set_track_mute` | Write | Mute/unmute track |
| 4 | `set_track_solo` | `set_track_solo` | Write | Solo/unsolo track (with exclusive option) |
| 5 | `set_track_arm` | `set_track_arm` | Write | Arm/disarm track for recording |
| 6 | `set_send_level` | `set_send_level` | Write | Set send level to return track |
| 7 | `set_crossfader` | `set_crossfader` | Write | Set crossfader position |
| 8 | `set_crossfade_assign` | `set_crossfade_assign` | Write | Set A/B crossfade assignment |
| 9 | `get_panning_mode` | `get_panning_mode` | Read | Get stereo/split panning mode |

### 1.7 Scene Management (scenes.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `create_scene` | `create_scene` | Write | Create new scene |
| 2 | `set_scene_name` | `set_scene_name` | Write | Rename a scene |
| 3 | `fire_scene` | `fire_scene` | Write | Launch a scene |
| 4 | `delete_scene` | `delete_scene` | Write | Delete a scene |
| 5 | `duplicate_scene` | `duplicate_scene` | Write | Duplicate a scene |
| 6 | `set_scene_color` | `set_scene_color` | Write | Set scene color |
| 7 | `get_scene_color` | `get_scene_color` | Read | Get scene color |
| 8 | `set_scene_tempo` | `set_scene_tempo` | Write | Set per-scene tempo |
| 9 | `set_scene_time_signature` | `set_scene_time_signature` | Write | Set per-scene time signature |
| 10 | `fire_scene_as_selected` | `fire_scene_as_selected` | Write | Fire + advance to next scene |
| 11 | `get_scene_is_empty` | `get_scene_is_empty` | Read | Check if scene has clips |

### 1.8 Transport / Song Controls (transport.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `start_playback` | `start_playback` | Write | Play from start marker |
| 2 | `stop_playback` | `stop_playback` | Write | Stop playback |
| 3 | `continue_playback` | `continue_playback` | Write | Resume from current position |
| 4 | `stop_all_clips` | `stop_all_clips` | Write | Stop all playing clips |
| 5 | `set_tempo` | `set_tempo` | Write | Set session tempo |
| 6 | `set_time_signature` | `set_time_signature` | Write | Set time signature |
| 7 | `set_loop_region` | `set_loop_region` | Write | Set song loop region |
| 8 | `get_playback_position` | `get_playback_position` | Read | Get current position |
| 9 | `get_transport_state` | `get_transport_state` | Read | Get full transport state |
| 10 | `undo` | `undo` | Write | Undo last action |
| 11 | `redo` | `redo` | Write | Redo last undone action |
| 12 | `get_scale_info` | `get_scale_info` | Read | Get root_note, scale_name, intervals, mode |
| 13 | `set_scale` | `set_scale` | Write | Set scale/key properties |
| 14 | `get_cue_points` | `get_cue_points` | Read | Get all arrangement cue points |
| 15 | `set_or_delete_cue` | `set_or_delete_cue` | Write | Toggle cue point at position |
| 16 | `jump_to_cue` | `jump_to_cue` | Write | Jump to next/prev/indexed cue |
| 17 | `capture_scene` | `capture_scene` | Write | Capture playing clips as new scene |
| 18 | `capture_midi` | `capture_midi` | Write | Capture recently played MIDI |
| 19 | `tap_tempo` | `tap_tempo` | Write | Tap tempo |
| 20 | `set_metronome` | `set_metronome` | Write | Toggle metronome |
| 21 | `set_groove_amount` | `set_groove_amount` | Write | Set global groove amount |
| 22 | `set_swing_amount` | `set_swing_amount` | Write | Set global swing amount |
| 23 | `set_clip_trigger_quantization` | `set_clip_trigger_quantization` | Write | Set global clip launch quantization |
| 24 | `set_session_record` | `set_session_record` | Write | Enable/disable session recording |
| 25 | `jump_by` | `jump_by` | Write | Jump forward/backward by beats |
| 26 | `play_selection` | `play_selection` | Write | Play arrangement selection |
| 27 | `get_song_length` | `get_song_length` | Read | Get song length / last event time |

### 1.9 Automation (automation.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `get_clip_envelope` | `get_clip_envelope` | Read | Get/list automation envelopes |
| 2 | `insert_envelope_breakpoints` | `insert_envelope_breakpoints` | Write | Insert automation breakpoints |
| 3 | `clear_clip_envelopes` | `clear_clip_envelopes` | Write | Clear automation from clip |

### 1.10 Browser (browser.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `get_browser_tree` | `get_browser_tree` | Read | Browse categories/folders |
| 2 | `get_browser_items_at_path` | `get_browser_items_at_path` | Read | Browse items at path |
| 3 | `get_browser_item` | -- | Read | Get single browser item (internal) |
| 4 | `get_browser_categories` | -- | Read | Get categories (stub) |
| 5 | `get_browser_items` | -- | Read | Get items (stub) |
| 6 | `load_browser_item` | `load_instrument_or_effect` | Write | Load device via URI/path |
| 7 | `load_instrument_or_effect` | -- | Write | Alias for load_browser_item |

### 1.11 Routing (routing.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `get_input_routing_types` | `get_input_routing_types` | Read | Available input routing types |
| 2 | `set_input_routing` | `set_input_routing` | Write | Set input routing type |
| 3 | `get_output_routing_types` | `get_output_routing_types` | Read | Available output routing types |
| 4 | `set_output_routing` | `set_output_routing` | Write | Set output routing type |
| 5 | `get_input_routing_channels` | `get_input_routing_channels` | Read | Available input sub-channels |
| 6 | `get_output_routing_channels` | `get_output_routing_channels` | Read | Available output sub-channels |

### 1.12 Audio Clips (audio_clips.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `get_audio_clip_properties` | `get_audio_clip_properties` | Read | Get pitch, gain, warping |
| 2 | `set_audio_clip_properties` | `set_audio_clip_properties` | Write | Set pitch, gain, warping |
| 3 | `get_warp_markers` | `get_warp_markers` | Read | Get all warp markers |
| 4 | `insert_warp_marker` | `insert_warp_marker` | Write | Insert warp marker |
| 5 | `move_warp_marker` | `move_warp_marker` | Write | Move warp marker |
| 6 | `remove_warp_marker` | `remove_warp_marker` | Write | Remove warp marker |

### 1.13 Arrangement (arrangement.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `create_arrangement_midi_clip` | `create_arrangement_midi_clip` | Write | Create MIDI clip in arrangement |
| 2 | `create_arrangement_audio_clip` | `create_arrangement_audio_clip` | Write | Create audio clip in arrangement |
| 3 | `get_arrangement_clips` | `get_arrangement_clips` | Read | List arrangement clips |
| 4 | `duplicate_clip_to_arrangement` | `duplicate_clip_to_arrangement` | Write | Copy session clip to arrangement |

### 1.14 Grooves (grooves.py)

| # | Remote Script Command | MCP Tool | R/W | Description |
|---|----------------------|----------|-----|-------------|
| 1 | `list_grooves` | `list_grooves` | Read | List grooves in pool |
| 2 | `get_groove_params` | `get_groove_params` | Read | Get groove parameters |
| 3 | `set_groove_params` | `set_groove_params` | Write | Set groove parameters |

---

## Section 2: LOM Classes - Full Catalog

The PDF documents 43 LOM classes. Below is our coverage status for each.

### Coverage Summary

| Coverage Level | Classes | Count |
|----------------|---------|-------|
| Fully Covered | Song, Track, Clip, ClipSlot, Scene, MixerDevice, GroovePool, Groove, CuePoint | 9 |
| Substantially Covered | Device, PluginDevice, SimplerDevice, DrumPad, RackDevice, Sample | 6 |
| Partially Covered | DeviceParameter, Chain, ChainMixerDevice, DeviceIO | 4 |
| Not Covered (View classes) | Application.View, Clip.View, Device.View, Eq8Device.View, RackDevice.View, SimplerDevice.View, Song.View, Track.View | 8 |
| Not Covered (App/Control) | Application, ControlSurface, this_device | 3 |
| Not Covered (Device-specific) | CompressorDevice, DriftDevice, DrumCellDevice, DrumChain, Eq8Device, HybridReverbDevice, LooperDevice, MaxDevice, MeldDevice, RoarDevice, ShifterDevice, SpectralResonatorDevice, WavetableDevice | 13 |
| Not Covered (Other) | TakeLane, TuningSystem | 2 |

### 2.1 Song (FULLY COVERED)

All significant Song properties and functions are implemented through our transport and session modules. Coverage includes: tempo, time_signature, loop, playback controls, undo/redo, cue_points, capture_scene, capture_midi, scale/key, groove_amount, swing_amount, clip_trigger_quantization, session_record, jump_by, play_selection, song_length, metronome, tap_tempo, create_track/scene, delete_track/scene, duplicate_track/scene.

### 2.2 Track (FULLY COVERED)

All high-value Track properties and functions implemented: arm, mute, solo, name, color, fold_state, devices, clip_slots, mixer_device, routing types/channels, create_audio_clip/midi_clip (arrangement), insert_device, delete_device, duplicate_clip_slot, duplicate_clip_to_arrangement, stop_all_clips, is_frozen/can_be_frozen, group_track.

### 2.3 Clip (FULLY COVERED)

All high-value Clip properties and functions implemented: name, color, length, looping, loop_start/end, start/end_marker, gain, pitch_coarse/fine, warping, warp_mode, warp_markers, signature, fire, stop, notes (add/get/remove/modify/select), launch_mode, launch_quantization, legato, velocity_amount, muted, groove, crop, duplicate_loop, duplicate_region, has_envelopes.

### 2.4 ClipSlot (FULLY COVERED)

Implemented: has_clip, clip, create_clip, delete_clip, duplicate_clip_to, fire, stop, create_audio_clip.

### 2.5 Scene (FULLY COVERED)

Implemented: name, color, color_index, fire, create_scene, delete_scene, duplicate_scene, tempo/tempo_enabled, time_signature, fire_as_selected, is_empty.

### 2.6 Device (SUBSTANTIALLY COVERED)

Implemented: parameters, name, class_name, class_display_name, can_have_chains, can_have_drum_pads, type, is_active, can_compare_ab, is_using_compare_preset_b, save_preset_to_compare_ab_slot, delete_device, insert_device.

**Not implemented (low value):** latency_in_samples, latency_in_ms (monitoring), store_chosen_bank (hardware control surface specific).

### 2.7 PluginDevice (SUBSTANTIALLY COVERED)

Implemented: presets, selected_preset_index (via list_plugin_presets / set_plugin_preset).

### 2.8 SimplerDevice (SUBSTANTIALLY COVERED)

Implemented: playback_mode, crop, reverse, warp_as/double/half, sample (slices, insert/move/remove/clear_slice), get_simpler_info.

**Not implemented (low value):** guess_playback_length (niche), pad_slicing (niche), retrigger (accessible via parameters), voices (accessible via parameters), playing_position (monitoring), multi_sample_mode (read-only).

### 2.9 MixerDevice (FULLY COVERED)

Implemented: volume, panning, sends, crossfader, crossfade_assign, panning_mode.

**Not implemented:** cue_volume (master-only, niche), left_split_stereo / right_split_stereo (accessible when panning_mode=Split Stereo, could be set via parameters), song_tempo (available through set_tempo), track_activator (same as mute).

### 2.10 GroovePool (FULLY COVERED)

Implemented: grooves list access.

### 2.11 Groove (FULLY COVERED)

Implemented: name, base, timing_amount, quantization_amount, random_amount, velocity_amount.

### 2.12 CuePoint (FULLY COVERED via transport commands)

Implemented: name, time (via get_cue_points), jump (via jump_to_cue), set_or_delete_cue.

### 2.13 DrumPad (SUBSTANTIALLY COVERED)

Implemented: chains (via get_rack_chains), name, note, mute, solo, delete_all_chains.

### 2.14 RackDevice (SUBSTANTIALLY COVERED)

Implemented: chains, drum_pads, visible_drum_pads (via get_rack_chains), chain_selector (accessible via parameters), insert_chain (not directly, but chains come from loading devices).

**Not implemented (medium value):** copy_pad, variation_count/selected_variation_index/store_variation/recall_selected_variation/recall_last_used_variation/delete_selected_variation (macro variations, Live 11+), add_macro/remove_macro, randomize_macros, insert_chain, return_chains.

### 2.15 Sample (SUBSTANTIALLY COVERED via SimplerDevice tools)

Implemented through Simpler: slices, insert_slice, move_slice, remove_slice, clear_slices, warp_markers, warp_mode, warping.

**Not implemented:** beats_granulation_resolution, beats_transient_envelope, beats_transient_loop_mode, complex_pro_envelope, complex_pro_formants, texture_flux, texture_grain_size, tones_grain_size (all accessible via generic DeviceParameter), slicing_sensitivity/slicing_style/slicing_beat_division/slicing_region_count (advanced slicing config).

### 2.16 DeviceParameter (PARTIALLY COVERED)

We read and write parameter values through get_device_parameters / set_device_parameter. We read name, min, max, value, display_value, is_quantized, value_items.

**Not implemented:** automation_state (useful for checking if automation is overridden), default_value, is_enabled, original_name, state, re_enable_automation, str_for_value.

### 2.17 Chain (PARTIALLY COVERED via get_rack_chains)

We expose chain devices, name, and basic properties through rack chain listing.

**Not implemented as direct controls:** color/color_index, mute, solo, is_auto_colored, delete_device (within chain), insert_device (within chain). Note: device operations within chains ARE supported via chain_index/chain_device_index parameters.

### 2.18 ChainMixerDevice (PARTIALLY COVERED)

Chain mixer volume/panning/sends are accessible through the chain's mixer_device parameters, but we don't expose dedicated chain mixer tools.

### 2.19 DeviceIO (PARTIALLY COVERED)

DeviceIO routing is used internally by CompressorDevice and MaxDevice for sidechain routing, but not directly exposed.

### 2.20 Application.View (NOT COVERED - View class)

Properties: browse_mode, focused_document_view. Functions: focus_view, hide_view, is_view_visible, scroll_view, show_view, toggle_browse, zoom_view.

**AI value:** Low. View management is UI-centric and not directly useful for AI music production. An AI doesn't need to switch views.

### 2.21 Application (NOT COVERED - App level)

Properties: current_dialog_button_count, current_dialog_message, open_dialog_count, average_process_usage, peak_process_usage. Functions: get_version_string, press_current_dialog_button.

**AI value:** Low. Version info available via ping; CPU monitoring and dialog handling are not AI production tasks.

### 2.22 Clip.View (NOT COVERED - View class)

Properties: grid_is_triplet, grid_quantization. Functions: hide_envelope, select_envelope_parameter, show_envelope, show_loop.

**AI value:** Low. Clip view state is UI-specific. Grid settings could have niche use for clip display.

### 2.23 Device.View (NOT COVERED - View class)

Properties: is_collapsed.

**AI value:** Low. Device collapsed/expanded state is visual only.

### 2.24 Eq8Device.View (NOT COVERED - View class)

Properties: selected_band.

**AI value:** Low. EQ band selection is UI state.

### 2.25 RackDevice.View (NOT COVERED - View class)

Children: selected_drum_pad, selected_chain. Properties: drum_pads_scroll_position, is_showing_chain_devices.

**AI value:** Low. Rack view state is UI-specific.

### 2.26 SimplerDevice.View (NOT COVERED - View class)

Properties: selected_slice.

**AI value:** Low. Simpler view state is UI-specific.

### 2.27 Song.View (NOT COVERED - View class)

Children: detail_clip, highlighted_clip_slot, selected_chain, selected_parameter, selected_scene, selected_track. Properties: draw_mode, follow_song. Functions: select_device.

**AI value:** Low-Medium. `select_device` could be useful to focus the UI on a device the AI is working with, but not essential for audio production.

### 2.28 Track.View (NOT COVERED - View class)

Children: selected_device. Properties: device_insert_mode, is_collapsed. Functions: select_instrument.

**AI value:** Low. Track view state is UI-specific.

### 2.29 ControlSurface (NOT COVERED - Hardware specific)

Properties: pad_layout. Functions: get_control, get_control_names, grab_control, grab_midi, register_midi_control, release_control, release_midi, send_midi, send_receive_sysex.

**AI value:** None for AI music production. This is for hardware control surface integration.

### 2.30 this_device (NOT COVERED - Max for Live specific)

Root path for Max for Live devices to reference themselves.

**AI value:** None. Only relevant for Max for Live devices.

### 2.31 CompressorDevice (NOT COVERED - Device specific)

Properties: available_input_routing_channels, available_input_routing_types, input_routing_channel, input_routing_type.

**AI value:** Medium. Sidechain routing for the Compressor is a common production technique. All regular parameters are accessible via generic DeviceParameter access. The unique value is sidechain source selection, which cannot be done through generic parameters.

### 2.32 DriftDevice (NOT COVERED - Device specific)

Properties: 24 mod_matrix_* properties (source/target indices and lists for modulation matrix).

**AI value:** Medium. Drift's modulation matrix is unique to this device and not accessible via generic parameters. Useful for sound design but niche.

### 2.33 DrumCellDevice (NOT COVERED - Device specific)

A DrumCellDevice (Drum Sampler) inherits from Device. The PDF doesn't list unique members beyond what Device provides.

**AI value:** Low. All parameters accessible via generic DeviceParameter.

### 2.34 DrumChain (NOT COVERED - Device specific)

Properties: in_note, out_note, choke_group. Inherits from Chain.

**AI value:** Medium. in_note (MIDI trigger assignment) and choke_group are Drum Rack specific and cannot be set through generic parameters. Useful for drum rack programming.

### 2.35 Eq8Device (NOT COVERED - Device specific)

Properties: edit_mode, global_mode, oversample.

**AI value:** Low. EQ Eight's mode switches are niche. All EQ parameters accessible via generic DeviceParameter. edit_mode/global_mode are stereo processing modes.

### 2.36 HybridReverbDevice (NOT COVERED - Device specific)

Properties: ir_attack_time, ir_category_index, ir_category_list, ir_decay_time, ir_file_index, ir_file_list, ir_size_factor, ir_time_shaping_on.

**AI value:** Medium. IR (impulse response) selection and time-shaping are unique to Hybrid Reverb and useful for reverb design. The category/file lists provide browsable IR selection not available via parameters.

### 2.37 LooperDevice (NOT COVERED - Device specific)

Properties: loop_length, overdub_after_record, record_length_index, record_length_list, tempo. Functions: clear, double_speed, half_speed, double_length, half_length, record, overdub, play, stop, undo, export_to_clip_slot.

**AI value:** Medium. Looper device has many unique functions (record, overdub, export_to_clip_slot) that could enable live looping workflows. However, this is primarily a performance tool.

### 2.38 MaxDevice (NOT COVERED - Device specific)

Properties: audio_inputs, audio_outputs, midi_inputs, midi_outputs. Functions: get_bank_count, get_bank_name, get_bank_parameters.

**AI value:** Low. Max for Live device I/O inspection and bank navigation. All parameters accessible via generic DeviceParameter.

### 2.39 MeldDevice (NOT COVERED - Device specific)

Properties: selected_engine, unison_voices, mono_poly, poly_voices.

**AI value:** Low. Meld's engine/voice settings are niche. Accessible through generic parameters in most cases.

### 2.40 RoarDevice (NOT COVERED - Device specific)

Properties: routing_mode_index, routing_mode_list, env_listen.

**AI value:** Low. Roar's routing mode selection is niche.

### 2.41 ShifterDevice (NOT COVERED - Device specific)

Inherits from Device. The PDF shows ShifterDevice as a type of Device with standard properties.

**AI value:** Low. All parameters accessible via generic DeviceParameter.

### 2.42 SpectralResonatorDevice (NOT COVERED - Device specific)

Properties: frequency_dial_mode, midi_gate, mod_mode, mono_poly, pitch_mode, pitch_bend_range, polyphony.

**AI value:** Low-Medium. Spectral Resonator's mode switches could be useful for sound design. Most are niche settings.

### 2.43 WavetableDevice (NOT COVERED - Device specific)

Properties: filter_routing, mono_poly, oscillator_1/2_effect_mode, oscillator_1/2_wavetable_category/index, oscillator_1/2_wavetables, oscillator_wavetable_categories, poly_voices, unison_mode, unison_voice_count, visible_modulation_target_names. Functions: add_parameter_to_modulation_matrix, get_modulation_target_parameter_name, get_modulation_value, is_parameter_modulatable, set_modulation_value.

**AI value:** High. Wavetable is Ableton's flagship synth. Wavetable selection (oscillator categories/indices) and modulation matrix access are unique and not available through generic parameters. An AI could design sounds by selecting wavetables and setting modulation routing.

### 2.44 TakeLane (NOT COVERED)

Properties: name. Children: arrangement_clips. Functions: create_audio_clip, create_midi_clip.

**AI value:** Low-Medium. Take lanes are used for comping in arrangement view. Could be useful for multi-take workflows but niche.

### 2.45 TuningSystem (NOT COVERED)

Properties: name, pseudo_octave_in_cents, lowest_note, highest_note, reference_pitch, note_tunings.

**AI value:** Low-Medium. Microtuning/alternative tuning systems. Niche but interesting for experimental music production.

---

## Section 3: Gap Analysis - Unimplemented LOM Features

### Tier 1: High Value - Would significantly enhance AI music production

| # | LOM Class | Feature | Description | Why High Value |
|---|-----------|---------|-------------|----------------|
| 1 | WavetableDevice | Wavetable selection | oscillator_1/2_wavetable_category, oscillator_1/2_wavetable_index, oscillator_wavetable_categories, oscillator_1/2_wavetables | Ableton's flagship synth; wavetable browsing/selection not available via generic params |
| 2 | WavetableDevice | Modulation matrix | add_parameter_to_modulation_matrix, set/get_modulation_value, visible_modulation_target_names | Unique to Wavetable; enables AI sound design through mod routing |
| 3 | RackDevice | Macro variations | variation_count, selected_variation_index, store/recall/delete_variation | AI can create and recall preset snapshots within racks |
| 4 | RackDevice | Macro management | add_macro, remove_macro, randomize_macros, visible_macro_count | AI can configure rack macros |
| 5 | RackDevice | insert_chain | Insert new chains into racks programmatically | Enables AI to build rack structures from scratch |
| 6 | RackDevice | copy_pad | Copy drum pad content between pads | Useful for drum kit building |
| 7 | CompressorDevice | Sidechain routing | available_input_routing_types/channels, input_routing_type/channel | Sidechain compression is essential for modern production |
| 8 | HybridReverbDevice | IR selection | ir_category_index/list, ir_file_index/list | Browse and select impulse responses programmatically |
| 9 | DrumChain | in_note / choke_group | MIDI trigger note assignment and choke groups | Essential for custom drum rack programming |
| 10 | DeviceParameter | automation_state | Check if parameter has active/overridden automation | Important for automation workflow awareness |
| 11 | DeviceParameter | re_enable_automation | Re-enable overridden automation | Needed to fix automation state |

### Tier 2: Medium Value - Useful but not essential

| # | LOM Class | Feature | Description | Why Medium Value |
|---|-----------|---------|-------------|------------------|
| 1 | DriftDevice | Modulation matrix | 24 mod_matrix_* properties | Sound design in Drift synth |
| 2 | LooperDevice | Looper controls | record, overdub, play, stop, clear, export_to_clip_slot | Live looping workflow |
| 3 | LooperDevice | Speed/length | double_speed, half_speed, double_length, half_length | Looper manipulation |
| 4 | HybridReverbDevice | IR time shaping | ir_attack_time, ir_decay_time, ir_size_factor, ir_time_shaping_on | Reverb impulse response sculpting |
| 5 | SpectralResonatorDevice | Mode settings | frequency_dial_mode, midi_gate, mod_mode, pitch_mode, polyphony | Sound design modes |
| 6 | Eq8Device | Processing modes | edit_mode, global_mode, oversample | L/R, M/S, and oversampling control |
| 7 | TakeLane | Take lane clips | create_audio/midi_clip, arrangement_clips, name | Comping workflow |
| 8 | TuningSystem | Microtuning | name, pseudo_octave_in_cents, reference_pitch, note_tunings | Alternative tuning systems |
| 9 | Sample | Warp mode params | beats_granulation_resolution, texture_flux, texture_grain_size, etc. | Fine-grained warp mode config (most via DeviceParameter) |
| 10 | Sample | Slicing config | slicing_sensitivity, slicing_style, slicing_beat_division, slicing_region_count | Advanced slicing configuration |
| 11 | Chain | Direct chain control | color, mute, solo, name (as direct operations) | Chain mute/solo for rack management |
| 12 | DeviceParameter | default_value / state | Query default value and active state | Useful for parameter inspection |
| 13 | MeldDevice | Engine selection | selected_engine, unison_voices, mono_poly | Meld synth engine control |
| 14 | RoarDevice | Routing mode | routing_mode_index/list | Roar effect routing |
| 15 | Song.View | select_device | Focus UI on a specific device | UI convenience for the user |
| 16 | WavetableDevice | Voice settings | mono_poly, poly_voices, unison_mode, unison_voice_count | Synth voice configuration |

### Tier 3: Low Value / Out of Scope

| # | LOM Class | Feature | Reason for Low Value |
|---|-----------|---------|---------------------|
| 1 | Application | CPU monitoring | average_process_usage, peak_process_usage - monitoring only |
| 2 | Application | Dialog handling | press_current_dialog_button - UI interaction |
| 3 | Application.View | View management | All functions - UI navigation not needed for AI |
| 4 | Clip.View | Grid settings | grid_is_triplet, grid_quantization - visual display only |
| 5 | Device.View | Collapsed state | is_collapsed - visual only |
| 6 | RackDevice.View | Pad/chain selection | selected_drum_pad, selected_chain - UI state |
| 7 | SimplerDevice.View | Slice selection | selected_slice - UI state |
| 8 | Track.View | Track collapse | is_collapsed, device_insert_mode - UI state |
| 9 | ControlSurface | Hardware control | All - hardware controller integration |
| 10 | this_device | Max4Live self-ref | Only for M4L devices |
| 11 | MaxDevice | M4L I/O | audio/midi inputs/outputs - M4L specific |
| 12 | DrumCellDevice | (none unique) | All params via generic DeviceParameter |
| 13 | ShifterDevice | (none unique) | All params via generic DeviceParameter |
| 14 | DeviceIO | Bus routing | Sidechain routing for devices - covered by CompressorDevice |
| 15 | ChainMixerDevice | Chain mixer | volume/panning/sends - accessible via chain parameters |

---

## Section 4: Previously Identified Backlog Items (Phase 11)

The following 26 items were identified in Phase 11's gap report and deferred to backlog:

### Song Backlog (10 items)
| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | `arrangement_overdub`, `overdub`, `punch_in/out` | Recording overdub controls | Deferred -- niche recording |
| 2 | `nudge_down/up` | Tempo nudge for DJ mixing | Deferred -- niche performance |
| 3 | `count_in_duration` | Metronome count-in beats | Deferred -- recording preference |
| 4 | `select_on_launch` | Preference toggle | Deferred -- UI preference |
| 5 | `session_automation_record` | Session automation recording | Deferred -- manual workflow |
| 6 | `scrub_by` | Arrangement scrubbing | Deferred -- manual navigation |
| 7 | `force_link_beat_time`, `is_ableton_link_enabled` | Ableton Link sync | Deferred -- multi-device |
| 8 | `tempo_follower_enabled` | Tempo follower | Deferred -- external tempo |
| 9 | `midi_recording_quantization` | Input quantization | Deferred -- recording pref |
| 10 | `trigger_session_record` | Session recording trigger | Deferred -- recording |

### Track Backlog (6 items)
| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | `back_to_arranger` | Per-track arranger switch | Deferred |
| 2 | `input/output_routing_channel` (set) | Sub-routing channel set | Deferred -- hardware dependent |
| 3 | `playing_slot_index`, `fired_slot_index` | Playback state queries | Deferred -- monitoring |
| 4 | `is_visible`, `is_part_of_selection` | View state | Deferred -- UI state |
| 5 | `implicit_arm` | Push-specific arming | Deferred -- hardware |
| 6 | `input/output_meter_*`, `performance_impact` | Meter readings + CPU | Deferred -- monitoring/CPU |

### Clip Backlog (8 items)
| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | `position` | Loop position shortcut | Deferred -- convenience alias |
| 2 | `ram_mode` | RAM switch for audio clips | Deferred -- resource mgmt |
| 3 | `is_overdubbing`, `is_recording` | Recording state | Deferred -- monitoring |
| 4 | `will_record_on_start` | Recording state | Deferred -- monitoring |
| 5 | `playing_position`, `playing_status` | Playback position in clip | Deferred -- monitoring |
| 6 | `set_fire_button_state` | Simulated button press | Deferred -- controller emulation |
| 7 | `scrub`, `stop_scrub` | Clip scrubbing | Deferred -- manual navigation |
| 8 | `move_playing_pos` | Jump in running clip | Deferred -- niche |

### Other Backlog (2 items)
| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | ClipSlot `has_stop_button`, `is_group_slot`, `controls_other_clips` | Slot state queries | Deferred |
| 2 | Scene `is_triggered` | Scene blinking state | Deferred -- monitoring |

---

## Section 5: Recommended Next Priorities

Top 15 highest-impact unimplemented features, ranked by AI music production value:

### Priority 1: Wavetable Sound Design (WavetableDevice)
**Impact: Very High** -- Wavetable is Ableton's flagship synthesizer. Currently, an AI can load Wavetable and tweak its knobs via generic DeviceParameter, but cannot browse/select wavetables or configure modulation routing. Implementing wavetable category/index selection and modulation matrix access would unlock programmatic sound design.
- oscillator_1/2_wavetable_category, oscillator_1/2_wavetable_index
- oscillator_wavetable_categories, oscillator_1/2_wavetables
- add_parameter_to_modulation_matrix, set/get_modulation_value

### Priority 2: Compressor Sidechain Routing (CompressorDevice)
**Impact: High** -- Sidechain compression is one of the most common production techniques. An AI currently cannot set the sidechain source. This single feature would enable "sidechain the bass to the kick" and similar standard workflows.
- available_input_routing_types/channels, input_routing_type/channel

### Priority 3: Rack Macro Variations (RackDevice)
**Impact: High** -- Macro variations allow saving/recalling snapshots of rack macro values. An AI could create multiple sound presets within a single rack and switch between them, enabling A/B testing and performance variation.
- store_variation, recall_selected_variation, delete_selected_variation
- variation_count, selected_variation_index

### Priority 4: Drum Rack Chain Configuration (DrumChain)
**Impact: High** -- When building custom drum racks, the AI needs to assign MIDI notes to chains and configure choke groups (e.g., open/closed hi-hat choking). Currently not possible.
- in_note, out_note, choke_group

### Priority 5: Rack Chain Management (RackDevice)
**Impact: High** -- insert_chain, copy_pad, add_macro, remove_macro enable building rack devices from scratch. The AI could construct instrument/effect racks programmatically.
- insert_chain, copy_pad, add_macro, remove_macro, randomize_macros

### Priority 6: Hybrid Reverb IR Selection (HybridReverbDevice)
**Impact: Medium-High** -- Impulse response selection for convolution reverb. The AI can adjust parameters but cannot browse/select impulse responses. IR selection is key to reverb design.
- ir_category_index/list, ir_file_index/list, ir_attack/decay_time

### Priority 7: Parameter Automation State (DeviceParameter)
**Impact: Medium-High** -- Knowing whether a parameter has automation (and whether it's overridden) is important context for an AI editing automation. re_enable_automation prevents the common "automation disabled" issue.
- automation_state, re_enable_automation

### Priority 8: Drift Modulation Matrix (DriftDevice)
**Impact: Medium** -- Drift is a popular synth with a unique modulation matrix. Exposing mod source/target selection enables AI sound design within Drift.
- mod_matrix_*_source/target_index/list properties

### Priority 9: Looper Device Control (LooperDevice)
**Impact: Medium** -- Looper has many unique functions for live recording workflows. export_to_clip_slot is particularly interesting for converting loops to clips.
- record, overdub, play, stop, clear, export_to_clip_slot

### Priority 10: Spectral Resonator Modes (SpectralResonatorDevice)
**Impact: Medium** -- Creative sound design device with mode settings not accessible via generic parameters.
- frequency_dial_mode, midi_gate, mod_mode, pitch_mode

### Priority 11: Take Lane Support (TakeLane)
**Impact: Medium** -- Comping workflow for arrangement recording. Create clips on take lanes, access arrangement clips per lane.
- create_audio/midi_clip, arrangement_clips

### Priority 12: EQ Eight Processing Modes (Eq8Device)
**Impact: Medium** -- L/R and M/S processing modes for stereo EQ. Useful for mix engineering.
- edit_mode, global_mode, oversample

### Priority 13: Wavetable Voice Configuration (WavetableDevice)
**Impact: Medium** -- Poly/mono, unison, and voice count settings for Wavetable.
- mono_poly, poly_voices, unison_mode, unison_voice_count, filter_routing

### Priority 14: TuningSystem (TuningSystem)
**Impact: Low-Medium** -- Alternative tuning systems for experimental music. Niche but enables unique creative possibilities.
- name, pseudo_octave_in_cents, reference_pitch, note_tunings

### Priority 15: Chain Direct Control (Chain)
**Impact: Low-Medium** -- Direct chain mute/solo/color operations. Currently chains are accessible through rack navigation but lack dedicated control tools.
- mute, solo, color, name

---

## Section 6: Summary Statistics

| Metric | Count |
|--------|-------|
| **Total LOM classes in PDF** | 43 |
| **Classes with full coverage** | 9 (Song, Track, Clip, ClipSlot, Scene, MixerDevice, GroovePool, Groove, CuePoint) |
| **Classes with substantial coverage** | 6 (Device, PluginDevice, SimplerDevice, DrumPad, RackDevice, Sample) |
| **Classes with partial coverage** | 4 (DeviceParameter, Chain, ChainMixerDevice, DeviceIO) |
| **Classes with no coverage** | 24 |
| -- View classes (low AI value) | 8 |
| -- App/Control classes (out of scope) | 3 |
| -- Device-specific classes | 13 |
| **Total implemented commands** | 144 |
| **Total implemented MCP tools** | 141 |
| **Phase 11 backlog items (deferred)** | 26 |
| **New high-value gaps identified** | 11 |
| **New medium-value gaps identified** | 16 |
| **New low-value / out-of-scope items** | 15+ |
| **Estimated remaining high-value gaps** | 11 features across 6 LOM classes |
| **Estimated remaining medium-value gaps** | 16 features across 10 LOM classes |

### Coverage by Domain

| Domain | Implemented | Remaining High-Value | Remaining Medium-Value |
|--------|------------|---------------------|----------------------|
| Song / Session | 30 commands | 0 | 0 |
| Track | 13 commands | 0 | 0 |
| Clip / Notes | 31 commands | 0 | 0 |
| Scene | 11 commands | 0 | 0 |
| Device (generic) | 22 commands | 2 (DeviceParameter state) | 1 (default_value) |
| Mixer | 9 commands | 0 | 0 |
| Automation | 3 commands | 0 | 0 |
| Browser | 7 commands | 0 | 0 |
| Routing | 6 commands | 0 | 0 |
| Audio Clips | 6 commands | 0 | 0 |
| Arrangement | 4 commands | 0 | 1 (TakeLane) |
| Grooves | 3 commands | 0 | 0 |
| WavetableDevice | 0 | 3 (wavetable + mod matrix + voice) | 0 |
| CompressorDevice | 0 | 1 (sidechain) | 0 |
| RackDevice (extended) | 0 | 3 (variations + chains + macros) | 0 |
| DrumChain | 0 | 1 (in_note + choke) | 0 |
| HybridReverbDevice | 0 | 1 (IR selection) | 1 (time shaping) |
| Other devices | 0 | 0 | 7 (Drift, Looper, Spectral, EQ8, Meld, Roar, TuningSystem) |

### Conclusion

The MCP server has **excellent coverage** of the Ableton LOM for AI music production. The 9 fully-covered core classes (Song, Track, Clip, ClipSlot, Scene, MixerDevice, GroovePool, Groove, CuePoint) plus 6 substantially-covered classes represent the vast majority of music production workflows.

The highest-impact remaining gaps are:
1. **WavetableDevice** -- wavetable browsing and modulation matrix (sound design)
2. **CompressorDevice** -- sidechain routing (mixing essential)
3. **RackDevice** -- macro variations and chain management (preset/rack building)
4. **DrumChain** -- note assignment and choke groups (drum programming)

The 8 View classes, 3 Application/ControlSurface classes, and many device-specific classes (DrumCellDevice, ShifterDevice, etc.) are low priority because they either serve UI management purposes (not useful for an AI) or expose parameters already accessible through the generic DeviceParameter interface.

---

*Generated: 2026-03-19 by gap analysis task 260319-t3s*
