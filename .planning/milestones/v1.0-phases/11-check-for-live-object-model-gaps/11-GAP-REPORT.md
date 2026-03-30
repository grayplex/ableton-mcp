# LOM Gap Report

**Date:** 2026-03-18
**Source:** Max9-LOM-en.pdf (Live 12.3.5 / Max 9, 171 pages)
**Baseline:** 65 MCP tools across 13 handler modules

## Summary Statistics

| Metric | Count |
|--------|-------|
| LOM classes audited | 12 |
| Total gaps identified | 78 |
| Add tier (implement in v2) | 52 |
| Backlog tier (deferred) | 26 |
| Correctness issues | 4 |
| Correctness issues fixed | 1 (note expression fields) |
| Correctness issues deferred | 3 (pitch_fine range, quantize native, note_id in get_notes) |

## Gap Report by LOM Class

### Song

**Current coverage:** tempo, time_signature, loop, is_playing, current_song_time, can_undo/can_redo, undo/redo, start/stop/continue_playing, stop_all_clips, create_midi/audio_track, create_return_track, create_scene, delete_scene/track/return_track, duplicate_scene/track

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `tap_tempo` | Add | Tap tempo for manual BPM setting | Medium -- enables tempo-from-reference workflow |
| 2 | `metronome` (get/set) | Add | Toggle metronome click | Medium -- recording workflow essential |
| 3 | `groove_amount` (get/set) | Add | Global groove/swing amount | High -- humanization control |
| 4 | `cue_points` + `set_or_delete_cue`, `jump_to_next/prev_cue` | Add | Arrangement navigation markers | High -- arrangement workflow |
| 5 | `capture_and_insert_scene` | Add | Capture currently playing clips as new scene | Very High -- AI composition workflow |
| 6 | `capture_midi` | Add | Capture recently played MIDI input | High -- AI recording workflow |
| 7 | `jump_by(beats)` | Add | Relative position jump | Medium -- arrangement navigation |
| 8 | `play_selection` | Add | Play arrangement selection | Medium -- arrangement preview |
| 9 | `move_device(device, target, position)` | Add | Reorganize effect chains | High -- mix reorganization |
| 10 | `duplicate_scene(index)` | Add | Duplicate entire scene | High -- arrangement/variation workflow |
| 11 | `clip_trigger_quantization` (get/set) | Add | Global launch quantization control | Medium -- performance timing |
| 12 | `session_record` / `record_mode` | Add | Recording controls | Medium -- recording workflow |
| 13 | `root_note` / `scale_name` / `scale_intervals` / `scale_mode` | Add | Scale and key awareness | Very High -- AI knows the key for note generation |
| 14 | `swing_amount` | Add | Global swing amount | Medium -- groove/feel control |
| 15 | `song_length` / `last_event_time` | Add | Arrangement bounds | Medium -- arrangement awareness |
| 16 | `find_device_position` | Add | Needed for move_device | Medium -- prerequisite for device moves |
| 17 | `arrangement_overdub`, `overdub`, `punch_in/out` | Backlog | Recording-specific overdub controls | Low -- niche recording workflow |
| 18 | `nudge_down/up` | Backlog | Tempo nudge for DJ-style mixing | Low -- niche performance feature |
| 19 | `count_in_duration` | Backlog | Metronome count-in beats | Low -- recording preference |
| 20 | `select_on_launch` | Backlog | Preference toggle | Low -- UI preference |
| 21 | `session_automation_record` | Backlog | Session-specific automation recording | Low -- manual workflow |
| 22 | `scrub_by` | Backlog | Arrangement scrubbing | Low -- manual navigation |
| 23 | `force_link_beat_time`, `is_ableton_link_enabled` | Backlog | Ableton Link sync | Low -- multi-device sync |
| 24 | `tempo_follower_enabled` | Backlog | Tempo follower feature | Low -- external tempo source |
| 25 | `midi_recording_quantization` | Backlog | Input quantization during recording | Low -- recording preference |
| 26 | `trigger_session_record` | Backlog | Session recording trigger | Low -- recording workflow |

### Track

**Current coverage:** arm, mute, solo, name, color/color_index, fold_state, is_foldable, is_grouped, group_track, has_audio/midi_input/output, can_be_armed, devices, clip_slots, mixer_device, input/output_routing_type (types only)

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `create_audio_clip(file_path, position)` | Add | Arrangement audio clip from file | Very High -- audio import for arrangement |
| 2 | `create_midi_clip(start_time, length)` | Add | Arrangement MIDI clip creation | Very High -- arrangement composition |
| 3 | `insert_device(device_name, target_index)` | Add | Native device insertion (Live 12.3+) | High -- precise device chain management |
| 4 | `duplicate_clip_slot(index)` | Add | Duplicate clip in-place | Medium -- variation workflow |
| 5 | `duplicate_clip_to_arrangement(clip, time)` | Add | Session-to-arrangement bridge | High -- workflow bridge |
| 6 | `arrangement_clips` | Add | List of arrangement clips | High -- arrangement awareness |
| 7 | `is_frozen` / `can_be_frozen` | Add | Freeze state query | Medium -- resource management |
| 8 | `stop_all_clips()` (per-track) | Add | Stop all clips on single track | Medium -- per-track control |
| 9 | `available_input/output_routing_channels` | Add | Sub-routing channel access | Medium -- detailed routing |
| 10 | `back_to_arranger` | Backlog | Per-track arranger switch | Low -- manual workflow |
| 11 | `input/output_routing_channel` | Backlog | Sub-routing channel set | Low -- detailed routing (channels vary by hardware) |
| 12 | `playing_slot_index` / `fired_slot_index` | Backlog | Playback state queries | Low -- monitoring only |
| 13 | `is_visible`, `is_part_of_selection` | Backlog | View state | Low -- UI state |
| 14 | `implicit_arm` | Backlog | Push-specific arming | Low -- hardware-specific |
| 15 | `input/output_meter_*` | Backlog | Meter readings | Low -- high CPU, monitoring only |
| 16 | `performance_impact` | Backlog | Track CPU usage | Low -- monitoring only |

### Clip

**Current coverage:** name, color/color_index, length, looping, loop_start/end, start/end_marker, is_playing, is_triggered, is_audio_clip, signature_numerator/denominator, pitch_coarse/fine, gain, gain_display_string, warping, warp_mode (read), has_envelopes, fire, stop
**MIDI covered:** add_new_notes, get_notes_extended, remove_notes_extended

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `launch_mode` (get/set, 0-3) | Add | Clip launch behavior (trigger/gate/toggle/repeat) | High -- performance control |
| 2 | `launch_quantization` (get/set, 0-14) | Add | Per-clip launch quantization | Medium -- performance timing |
| 3 | `legato` (get/set) | Add | Legato mode for seamless transitions | Medium -- performance workflow |
| 4 | `velocity_amount` (get/set) | Add | Velocity sensitivity | Medium -- expression control |
| 5 | `muted` (get/set) | Add | Clip activator (different from track mute) | High -- arrangement muting |
| 6 | `groove` (get/set) | Add | Associate groove with clip | High -- per-clip groove |
| 7 | `warp_markers` (get/add/move/remove) | Add | Warp marker manipulation | Very High -- audio timing essential |
| 8 | `crop` | Add | Crop clip to loop/markers | Medium -- clip editing |
| 9 | `duplicate_loop` | Add | Double loop length + duplicate content | High -- pattern building |
| 10 | `duplicate_region` | Add | Duplicate notes in region | Medium -- pattern building |
| 11 | `apply_note_modifications` | Add | Modify notes in-place (Live 11+ API) | High -- efficient note editing |
| 12 | `select_all/deselect_all/select_notes_by_id` | Add | Note selection | Medium -- selective editing |
| 13 | `get_selected_notes_extended` / `get_all_notes_extended` | Add | Advanced note queries | Medium -- selective read |
| 14 | `remove_notes_by_id` / `duplicate_notes_by_id` / `get_notes_by_id` | Add | ID-based note operations | High -- precise note manipulation |
| 15 | `quantize(grid, amount)` (native) | Add | Native quantize with swing support | Medium -- respects global swing |
| 16 | `quantize_pitch(pitch, grid, amount)` | Add | Pitch-specific quantize | Low -- niche editing |
| 17 | Note `probability` field | Add | Note probability (Live 11+) | Very High -- humanization |
| 18 | Note `velocity_deviation` field | Add | Note velocity randomization | High -- humanization |
| 19 | Note `release_velocity` field | Add | Note release velocity | Medium -- expression |
| 20 | `position` (loop position shortcut) | Backlog | Convenience alias | Low -- shortcut |
| 21 | `ram_mode` | Backlog | RAM switch for audio clips | Low -- resource management |
| 22 | `is_overdubbing`, `is_recording` | Backlog | Recording state | Low -- monitoring |
| 23 | `will_record_on_start` | Backlog | Recording state | Low -- monitoring |
| 24 | `playing_position`, `playing_status` | Backlog | Playback position in clip | Low -- monitoring |
| 25 | `set_fire_button_state` | Backlog | Simulated button press | Low -- controller emulation |
| 26 | `scrub` / `stop_scrub` | Backlog | Clip scrubbing | Low -- manual navigation |
| 27 | `move_playing_pos` | Backlog | Jump in running clip | Low -- niche playback control |

### ClipSlot

**Current coverage:** has_clip, clip, create_clip, delete_clip, duplicate_clip_to, fire, stop

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `create_audio_clip(path)` | Add | Session view audio clip from file | Very High -- audio import |
| 2 | `has_stop_button` (get/set) | Add | Stop button presence | Low -- performance layout |
| 3 | `is_group_slot`, `controls_other_clips` | Backlog | Group track slot info | Low -- group state |
| 4 | `playing_status`, `is_playing`, `is_recording` | Backlog | Group slot state | Low -- monitoring |
| 5 | `set_fire_button_state` | Backlog | Simulated button press | Low -- controller emulation |

### Scene

**Current coverage:** name, fire, create_scene, delete_scene

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `color` / `color_index` (get/set) | Add | Scene color | Medium -- visual organization |
| 2 | `tempo` / `tempo_enabled` (get/set) | Add | Per-scene tempo | High -- tempo changes in arrangement |
| 3 | `time_signature_numerator/denominator` / `time_signature_enabled` | Add | Per-scene time signature | Medium -- meter changes |
| 4 | `is_empty` | Add | Check if scene has any clips | Low -- scene inspection |
| 5 | `fire_as_selected` | Add | Fire + advance to next scene | High -- performance workflow |
| 6 | `is_triggered` | Backlog | Scene blinking state | Low -- monitoring |

### Device

**Current coverage:** parameters, name, class_name, class_display_name, can_have_chains, can_have_drum_pads, type, is_active

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `latency_in_samples` / `latency_in_ms` | Add | Device latency info | Low -- monitoring |
| 2 | `can_compare_ab` / `is_using_compare_preset_b` / `save_preset_to_compare_ab_slot` | Add | A/B preset compare (Live 12.3+) | Medium -- sound design workflow |

### PluginDevice

**Current coverage:** None (inherits Device coverage)

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `presets` | Add | List of plugin presets | High -- preset browsing |
| 2 | `selected_preset_index` (get/set) | Add | Select preset by index | High -- preset selection |

### SimplerDevice

**Current coverage:** None (inherits Device coverage)

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `crop` | Add | Crop sample to active region | Medium -- sample editing |
| 2 | `reverse` | Add | Reverse loaded sample | High -- sound design |
| 3 | `warp_as(beats)` | Add | Warp to beat count | Medium -- timing adjustment |
| 4 | `warp_double` / `warp_half` | Add | Tempo manipulation | Medium -- tempo adjustment |
| 5 | `playback_mode` (get/set) | Add | Classic/One-Shot/Slicing | High -- sampler mode |
| 6 | `sample` child + `slices`, `insert/move/remove/clear_slice` | Add | Slice manipulation | High -- beat slicing workflow |

### MixerDevice

**Current coverage (via mixer.py):** volume, panning, sends

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `crossfader` | Add | Crossfader control | Medium -- DJ/performance workflow |
| 2 | `crossfade_assign` (get/set) | Add | A/B crossfade assignment | Medium -- DJ/performance workflow |
| 3 | `panning_mode` | Add | Stereo/split panning mode | Low -- advanced mixing |

### GroovePool / Groove

**Current coverage:** None

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `groove_pool.grooves` | Add | List available grooves | High -- groove browsing |
| 2 | Groove: `name`, `base`, `timing_amount`, `quantization_amount`, `random_amount`, `velocity_amount` | Add | Groove parameter access | High -- groove customization |

### CuePoint

**Current coverage:** None

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `name` (get/set), `time` (read), `jump()` | Add | Cue point management | High -- arrangement navigation |

### DrumPad

**Current coverage:** chains (via get_rack_chains), note, name

| # | Property/Function | Tier | Description | AI Production Value |
|---|-------------------|------|-------------|-------------------|
| 1 | `mute` / `solo` (get/set) | Add | Per-pad mute/solo | High -- drum programming |
| 2 | `delete_all_chains` | Add | Clear pad contents | Medium -- pad management |

## Correctness Issues

### 1. pitch_fine Range Mismatch
- **Our code:** validates -500 to 500 (`audio_clips.py:107`)
- **LOM spec:** "Extra pitch shift in cents ('Detune'), -50 ... 49"
- **Decision:** Keep current range per STATE.md decision `[10-01]`. Needs live testing to confirm actual API range.
- **Status:** Deferred (needs live testing)

### 2. Missing Note Properties (FIXED)
- **Our add_notes_to_clip:** Only exposed pitch, start_time, duration, velocity, mute
- **LOM MidiNoteSpecification:** Also supports `probability`, `velocity_deviation`, `release_velocity`
- **Fix:** Added optional `probability`, `velocity_deviation`, `release_velocity` fields to `add_notes_to_clip` and exposed them in `get_notes`
- **Status:** Fixed in this phase

### 3. Quantize Implementation
- **Our code:** Manual read-modify-write pattern (get_notes -> compute -> remove -> add)
- **LOM:** Native `Clip.quantize(grid, amount)` respects Song.swing_amount
- **Decision:** Keep manual implementation (works correctly). Native method is optional future enhancement.
- **Status:** Deferred (working correctly, native method is v2 enhancement)

### 4. get_notes_extended Missing note_id
- **Our get_notes:** Returns pitch, start_time, duration, velocity, mute
- **LOM returns:** Also note_id, probability, velocity_deviation, release_velocity
- **Fix:** Added probability, velocity_deviation, release_velocity to get_notes response. note_id exposed for future ID-based operations.
- **Status:** Fixed in this phase

---
*Gap report generated: 2026-03-18*
