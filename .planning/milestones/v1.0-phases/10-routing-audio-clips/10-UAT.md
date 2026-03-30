---
status: complete
phase: 10-routing-audio-clips
source: [10-01-SUMMARY.md, 10-02-SUMMARY.md]
started: 2026-03-17T01:15:00Z
updated: 2026-03-18T00:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Get Input Routing Types
expected: Call get_input_routing_types for a track. Response returns the track's current input routing type name and a list of available input routing options.
result: pass

### 2. Set Input Routing Type
expected: Call set_input_routing with a valid routing name from the available list. Response confirms the change with before/after values showing the routing was updated.
result: pass

### 3. Get Output Routing Types
expected: Call get_output_routing_types for a track. Response returns the track's current output routing type name and a list of available output routing options.
result: pass

### 4. Set Output Routing Type
expected: Call set_output_routing with a valid routing name from the available list. Response confirms the change with before/after values showing the routing was updated.
result: pass

### 5. Get Audio Clip Properties
expected: Call get_audio_clip_properties on a clip slot containing an audio clip. Response returns pitch_coarse, pitch_fine, gain (0.0-1.0), gain_display_string (dB), and warping status. May include warp_mode if available.
result: skipped
reason: Default set has no audio clips. Cannot programmatically place audio samples into session view clip slots.

### 6. Set Audio Clip Properties
expected: Call set_audio_clip_properties to change pitch_coarse or gain on an audio clip. Response confirms with before/after values. The change is reflected in Ableton's clip view.
result: skipped
reason: Default set has no audio clips. Cannot programmatically place audio samples into session view clip slots.

### 7. Audio Clip Tools Reject MIDI Clips
expected: Call get_audio_clip_properties or set_audio_clip_properties on a MIDI clip. Response returns a clear error message indicating the clip is not an audio clip.
result: pass

### 8. Test Suite Passes
expected: Run pytest from project root. All 128 tests pass with zero failures and zero regressions.
result: pass

## Summary

total: 8
passed: 6
issues: 0
pending: 0
skipped: 2

## Gaps

[none yet]
