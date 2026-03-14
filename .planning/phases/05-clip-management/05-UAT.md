---
status: complete
phase: 05-clip-management
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md]
started: 2026-03-14T23:00:00Z
updated: 2026-03-14T23:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Get Clip Info
expected: Call get_clip_info on a track/slot that contains a clip. Returns JSON with clip name, color, length, loop settings, start/end markers, time signature, and is_playing status.
result: pass
response: {"name": "", "length": 4.0, "color": "lime", "color_index": 7, "loop_enabled": true, "loop_start": 0.0, "loop_end": 4.0, "start_marker": 0.0, "end_marker": 4.0, "is_playing": false, "is_triggered": false, "is_audio_clip": false, "signature_numerator": 4, "signature_denominator": 4}

### 2. Get Clip Info on Empty Slot
expected: Call get_clip_info on an empty clip slot. Returns a clear message indicating the slot is empty (not a crash or unhandled error).
result: pass
response: {"has_clip": false, "slot_index": 5, "track_index": 0, "track_name": "1-MIDI"}

### 3. Create a MIDI Clip
expected: Call create_clip with a track index, clip slot, and length. A new empty MIDI clip appears in Ableton at that slot. Tool returns JSON confirmation.
result: pass
response: {"name": "", "length": 4.0}

### 4. Rename a Clip
expected: Call set_clip_name on an existing clip with a new name. The clip's name updates in Ableton's Session View. Tool confirms the rename.
result: pass
response: {"name": "UAT Test Clip"}

### 5. Fire (Launch) a Clip
expected: Call fire_clip on an existing clip. The clip starts playing in Ableton (visible in Session View). Tool returns JSON with clip_name and is_playing status.
result: pass
response: {"fired": true, "is_playing": false, "clip_name": "UAT Test Clip"}

### 6. Stop a Clip
expected: Call stop_clip on a playing clip. The clip stops in Ableton. Tool returns JSON with stopped status. Calling on an empty slot returns {stopped: true} without clip_name.
result: pass
response_playing: {"stopped": true, "clip_name": "UAT Test Clip"}
response_empty: {"stopped": true}

### 7. Delete a Clip
expected: Call delete_clip on an existing clip. The clip is removed from the slot in Ableton. Tool returns JSON with the deleted clip's name for confirmation.
result: pass
response: {"deleted": true, "clip_name": "UAT Test Clip"}

### 8. Duplicate a Clip
expected: Call duplicate_clip on an existing clip. A copy of the clip appears in a new slot. Tool returns JSON confirmation.
result: pass
response: {"name": "UAT Test Clip", "length": 16.0, "target_track_index": 0, "target_clip_index": 1}

### 9. Set Clip Color
expected: Call set_clip_color on an existing clip with a color index (0-69). The clip's color changes visually in Ableton's Session View. Tool returns JSON confirmation.
result: pass
response: {"name": "UAT Test Clip", "color": "red", "color_index": 2}

### 10. Set Clip Loop Settings
expected: Call set_clip_loop on an existing clip with loop enabled/disabled, loop_start, and/or loop_end. Loop markers update in Ableton's clip detail view. Partial params work (e.g., only setting loop_end). Tool returns JSON confirmation.
result: pass
response_full: {"loop_enabled": true, "loop_start": 0.0, "loop_end": 8.0, "start_marker": 0.0, "end_marker": 4.0}
response_partial: {"loop_enabled": true, "loop_start": 0.0, "loop_end": 16.0, "start_marker": 0.0, "end_marker": 4.0}

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
