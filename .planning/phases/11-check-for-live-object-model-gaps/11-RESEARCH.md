# Phase 11 Research: Live Object Model Gap Analysis

**Date:** 2026-03-18
**Source:** Max9-LOM-en.pdf (Live 12.3.5 / Max 9, 171 pages)
**Baseline:** 65 MCP tools across 13 handler modules

## Current Implementation Inventory

### Handler Modules (13 files, ~65 commands)
| Module | Commands | LOM Classes Covered |
|--------|----------|-------------------|
| base.py | ping, get_session_info | Application, Song |
| tracks.py | create_midi/audio/return/group_track, set_track_name/color, delete/duplicate_track, set_group_fold, get_track_info, get_all_tracks | Song, Track |
| clips.py | create_clip, set_clip_name, fire/stop_clip, delete/duplicate_clip, get_clip_info, set_clip_color, set_clip_loop | Clip, ClipSlot |
| notes.py | add_notes_to_clip, get_notes, remove_notes, quantize_notes, transpose_notes | Clip (MIDI) |
| mixer.py | set_track_volume/pan/mute/solo/arm, set_send_level | MixerDevice, Track |
| devices.py | get_device_parameters, set_device_parameter, delete_device, get_rack_chains, get_session_state | Device, RackDevice, DrumPad |
| scenes.py | create/delete_scene, set_scene_name, fire_scene | Scene |
| transport.py | start/stop/continue_playback, stop_all_clips, set_tempo, set_time_signature, set_loop_region, get_playback_position, get_transport_state, undo, redo | Song |
| automation.py | get_clip_envelope, insert_envelope_breakpoints, clear_clip_envelopes | Clip, DeviceParameter |
| routing.py | get_input/output_routing_types, set_input/output_routing | Track |
| audio_clips.py | get/set_audio_clip_properties | Clip (audio) |
| browser.py | get_browser_tree/items/item/categories, get_browser_items_at_path, load_browser_item, load_instrument_or_effect | Browser (Application) |

## Gap Analysis by LOM Class

### Song
**Covered:** tempo, time_signature, loop, is_playing, current_song_time, can_undo/can_redo, undo/redo, start/stop/continue_playing, stop_all_clips, create_midi/audio_track, create_return_track, create_scene, delete_scene/track/return_track, duplicate_scene/track
**Gaps (Add tier):**
- `tap_tempo` — already in v2 as SESS-03
- `metronome` (get/set) — already in v2 as SESS-04
- `groove_amount` (get/set) — already in v2 as SESS-05
- `cue_points` + `set_or_delete_cue`, `jump_to_next/prev_cue` — already in v2 as SESS-01
- `capture_and_insert_scene` — captures currently playing clips as new scene (AI composition workflow)
- `capture_midi` — captures recently played MIDI (AI recording workflow)
- `jump_by(beats)` — relative position jump for arrangement navigation
- `play_selection` — play arrangement selection
- `move_device(device, target, position)` — reorganize effect chains
- `duplicate_scene(index)` — duplicate entire scene (arrangement workflow)
- `clip_trigger_quantization` (get/set) — control launch quantization globally
- `session_record` / `record_mode` — recording controls
- `root_note` / `scale_name` / `scale_intervals` / `scale_mode` — scale & key awareness
- `swing_amount` — global swing
- `song_length` / `last_event_time` — arrangement bounds
- `find_device_position` — needed for move_device

**Gaps (Backlog):**
- `arrangement_overdub`, `overdub`, `punch_in/out` — recording-specific
- `nudge_down/up` — tempo nudge (niche)
- `count_in_duration` — metronome count-in
- `select_on_launch` — preference toggle
- `session_automation_record` — session-specific recording
- `scrub_by` — arrangement scrubbing
- `force_link_beat_time` — Ableton Link
- `is_ableton_link_enabled` — Ableton Link
- `tempo_follower_enabled` — tempo follower
- `midi_recording_quantization` — recording quantization
- `trigger_session_record` — session recording

### Track
**Covered:** arm, mute, solo, name, color/color_index, fold_state, is_foldable, is_grouped, group_track, has_audio/midi_input/output, can_be_armed, devices, clip_slots, mixer_device, input/output_routing_type/channel (types only, not channels)
**Gaps (Add tier):**
- `create_audio_clip(file_path, position)` — arrangement audio clip from file
- `create_midi_clip(start_time, length)` — arrangement MIDI clip
- `insert_device(device_name, target_index)` — Live 12.3+ native device insertion
- `delete_device(index)` — already implemented on Track; also on Chain
- `duplicate_clip_slot(index)` — duplicate clip in-place
- `duplicate_clip_to_arrangement(clip, destination_time)` — session→arrangement bridge
- `arrangement_clips` — list of arrangement clips
- `is_frozen` / `can_be_frozen` — freeze state (TRKA-01)
- `stop_all_clips()` — stop all clips on single track
- `available_input/output_routing_channels` — sub-routing (Backlog per CONTEXT.md)

**Gaps (Backlog):**
- `back_to_arranger` — per-track (CONTEXT.md says Skip)
- `input/output_routing_channel` — sub-routing channels
- `playing_slot_index` / `fired_slot_index` — playback state queries
- `is_visible`, `is_part_of_selection` — view state
- `implicit_arm` — Push-specific
- `input/output_meter_*` — meter readings (high CPU load per LOM docs)
- `performance_impact` — track performance

### Clip
**Covered:** name, color/color_index, length, looping, loop_start/end, start/end_marker, is_playing, is_triggered, is_audio_clip, signature_numerator/denominator, pitch_coarse/fine, gain, gain_display_string, warping, warp_mode (read), has_envelopes, fire, stop
**MIDI covered:** add_new_notes, get_notes_extended, remove_notes_extended
**Gaps (Add tier):**
- `launch_mode` (get/set, 0-3) — clip launch behavior (trigger/gate/toggle/repeat)
- `launch_quantization` (get/set, 0-14) — per-clip launch quantization
- `legato` (get/set) — legato mode
- `velocity_amount` (get/set) — velocity sensitivity
- `muted` (get/set) — clip activator (different from track mute!)
- `groove` (get/set) — associate groove with clip
- `warp_markers` (get/add/move/remove) — essential for audio timing
- `add_warp_marker`, `move_warp_marker`, `remove_warp_marker` — warp marker manipulation
- `crop` — crop clip to loop/markers
- `duplicate_loop` — double loop length + duplicate content
- `duplicate_region` — duplicate notes in region
- `apply_note_modifications` — modify notes in-place (Live 11+ replacement for remove+add pattern)
- `select_all_notes` / `deselect_all_notes` / `select_notes_by_id` — note selection (MIDA-01)
- `get_selected_notes_extended` / `get_all_notes_extended` — advanced note queries
- `remove_notes_by_id` / `duplicate_notes_by_id` / `get_notes_by_id` — ID-based note ops
- `quantize(grid, amount)` — native quantize with swing (vs our manual implementation)
- `quantize_pitch(pitch, grid, amount)` — pitch-specific quantize
- Note `probability` field — not exposed in our add_notes (available since Live 11.0)
- Note `velocity_deviation` field — not exposed in our add_notes
- Note `release_velocity` field — not exposed in our add_notes

**Gaps (Backlog):**
- `position` (loop position with preserved length) — convenience alias
- `ram_mode` — RAM switch
- `is_overdubbing`, `is_recording` — recording state
- `will_record_on_start` — recording state
- `playing_position`, `playing_status` — playback position queries
- `set_fire_button_state` — simulated button press
- `scrub` / `stop_scrub` — clip scrubbing
- `move_playing_pos` — jump in running clip

### ClipSlot
**Covered:** has_clip, clip, create_clip, delete_clip, duplicate_clip_to, fire, stop
**Gaps (Add tier):**
- `create_audio_clip(path)` — session view audio clip from file
- `has_stop_button` (get/set) — stop button presence

**Gaps (Backlog):**
- `is_group_slot`, `controls_other_clips` — group track info
- `playing_status`, `is_playing`, `is_recording` — group slot state
- `set_fire_button_state` — simulated button press

### Scene
**Covered:** name, fire, create_scene, delete_scene
**Gaps (Add tier):**
- `color` / `color_index` (get/set) — scene color
- `tempo` / `tempo_enabled` (get/set) — per-scene tempo (TRKA-03)
- `time_signature_numerator/denominator` / `time_signature_enabled` — per-scene time sig
- `is_empty` — check if scene has any clips
- `fire_as_selected` — fire + advance to next scene

**Gaps (Backlog):**
- `is_triggered` — scene blinking state

### Device
**Covered:** parameters, name, class_name, class_display_name, can_have_chains, can_have_drum_pads, type, is_active
**Gaps (Add tier):**
- `latency_in_samples` / `latency_in_ms` — device latency info
- `can_compare_ab` / `is_using_compare_preset_b` / `save_preset_to_compare_ab_slot` — A/B compare (Live 12.3+)

**Gaps (Backlog):**
- `store_chosen_bank` — control surface specific

### PluginDevice
**Gaps (Add tier):**
- `presets` — list of plugin presets
- `selected_preset_index` (get/set) — select preset by index

### SimplerDevice
**Gaps (Add tier):**
- `crop` — crop sample to active region
- `reverse` — reverse loaded sample
- `warp_as(beats)` — warp to beat count
- `warp_double` / `warp_half` — tempo manipulation
- `playback_mode` (get/set) — Classic/One-Shot/Slicing
- `sample` child — access to Sample object
- Sample: `slices`, `insert_slice`, `move_slice`, `remove_slice`, `clear_slices`

### MixerDevice
**Covered (via mixer.py):** volume, panning, sends
**Gaps (Add tier):**
- `crossfader` — crossfader control (DeviceParameter)
- `crossfade_assign` (get/set) — A/B crossfade assignment
- `panning_mode` — stereo/split panning mode

### GroovePool / Groove
**Gaps (Add tier):**
- `groove_pool.grooves` — list grooves
- Groove: `name`, `base`, `timing_amount`, `quantization_amount`, `random_amount`, `velocity_amount`

### CuePoint
**Gaps (Add tier):**
- `name` (get/set), `time` (read), `jump()` — cue point management

### DrumPad
**Covered:** chains (via get_rack_chains), note, name
**Gaps (Add tier):**
- `mute` / `solo` (get/set) — per-pad mute/solo
- `delete_all_chains` — clear pad

## Correctness Issues Found

### 1. pitch_fine Range Mismatch
- **Our code:** validates -500 to 500 (`audio_clips.py:107`)
- **LOM spec:** "Extra pitch shift in cents ('Detune'), -50 ... 49"
- **Analysis:** The LOM says -50 to 49, but the actual Live API accepts -500 to 500 (centitones). Our STATE.md decision `[10-01]` says "documented API range, not UI range." The LOM may be documenting the UI range while the actual parameter accepts wider. This needs live testing. **Recommendation:** Keep current range but add a comment noting the discrepancy.

### 2. Missing Note Properties
- **Our add_notes_to_clip:** Only exposes pitch, start_time, duration, velocity, mute
- **LOM MidiNoteSpecification:** Also supports `probability`, `velocity_deviation`, `release_velocity`
- **Impact:** Medium — probability and velocity_deviation are powerful for humanization

### 3. Quantize Implementation
- **Our code:** Manual read-modify-write pattern (get_notes → compute → remove → add)
- **LOM:** Native `Clip.quantize(grid, amount)` respects Song.swing_amount
- **Impact:** Low — our approach works but doesn't respect global swing. Native method is simpler.

### 4. get_notes_extended Missing Fields
- **Our get_notes:** Returns pitch, start_time, duration, velocity, mute
- **LOM returns:** Also note_id, probability, velocity_deviation, release_velocity
- **Impact:** Medium — note_id enables ID-based operations

## Validation Architecture

No validation tests needed for this audit phase. The gap report and REQUIREMENTS.md updates are the deliverables. Correctness fixes (if any) will be validated by existing tests.

---
*Research completed: 2026-03-18*
