---
status: complete
phase: 03-track-management
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md]
started: 2026-03-14T16:00:00Z
updated: 2026-03-14T16:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Get All Tracks Overview
expected: Call the get_all_tracks MCP tool. Returns JSON array with lightweight summary of every track in the session — each entry includes index, name, type, and color. No clip/device details.
result: pass

### 2. Get Track Info (Regular Track)
expected: Call get_track_info with a regular track index. Returns detailed info including name, color, arm status (if armable), devices, and clip slots. No fold_state field for non-group tracks.
result: pass

### 3. Get Track Info (Return Track)
expected: Call get_track_info with track_type="return" and a valid return track index. Returns return track details (name, color, sends). No arm field since return tracks can't be armed.
result: pass

### 4. Get Track Info (Master Track)
expected: Call get_track_info with track_type="master". Returns master track details (name, color). No index required — only one master track exists.
result: issue
reported: "Crashes with error: Main track has no 'mute' property! The _get_track_info handler accesses track.mute unconditionally but Ableton's master track does not have a mute attribute."
severity: blocker

### 5. Create Audio Track
expected: Call create_audio_track. A new audio track appears in Ableton's track list. Tool returns JSON with the new track's index and name.
result: pass

### 6. Create Return Track
expected: Call create_return_track. A new return track appears in Ableton's sends/returns section. Tool returns JSON confirmation.
result: pass

### 7. Set Track Name (Regular Track)
expected: Call set_track_name with a track index and new name. The track's name visibly changes in Ableton. Tool returns confirmation with the new name.
result: pass

### 8. Set Track Name (Return Track)
expected: Call set_track_name with track_type="return", a return track index, and a new name. The return track's name changes in Ableton. Tool returns confirmation including type "return".
result: pass

### 9. Set Track Color
expected: Call set_track_color with a track index and a friendly color name (e.g. "ocean_blue", "warm_red"). The track's color visibly changes in Ableton. If an invalid color name is used, returns error listing all 70 valid color names.
result: pass

### 10. Duplicate Track
expected: Call duplicate_track with a track index. A copy of the track appears next to the original in Ableton. Optionally provide new_name to rename the duplicate. Tool returns JSON with the new track info.
result: pass

### 11. Delete Track
expected: Call delete_track with a track index. The track is removed from Ableton's track list. Tool returns JSON confirmation.
result: pass

## Summary

total: 11
passed: 10
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "get_track_info with track_type='master' returns master track details"
  status: failed
  reason: "User reported: Crashes with error: Main track has no 'mute' property! The _get_track_info handler accesses track.mute unconditionally but Ableton's master track does not have a mute attribute."
  severity: blocker
  test: 4
  root_cause: "_get_track_info in handlers/tracks.py line 489 accesses track.mute and track.solo unconditionally in the common fields block, but Ableton's master track does not expose mute/solo properties"
  artifacts:
    - path: "AbletonMCP_Remote_Script/handlers/tracks.py"
      issue: "Line 489: 'mute': track.mute crashes for master track"
  missing:
    - "Guard mute/solo access with hasattr() or conditional on track_type != 'master'"
  debug_session: ""
