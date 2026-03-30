---
status: complete
phase: 06-midi-editing
source: [06-01-SUMMARY.md, 06-02-SUMMARY.md]
started: 2026-03-14T23:50:00Z
updated: 2026-03-14T23:55:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Add Notes to a MIDI Clip
expected: Call the add_notes_to_clip tool with a track/clip containing a MIDI clip, providing notes as a JSON array (e.g. [{"pitch": 60, "start_time": 0, "duration": 0.5, "velocity": 100}]). The tool returns a JSON response (not an f-string) confirming the notes were added successfully. Notes appear in the clip in Ableton.
result: pass

### 2. Get Notes from a MIDI Clip
expected: Call the get_notes tool on a clip that has MIDI notes. The tool returns a JSON list of note objects, each with pitch, start_time, duration, velocity, and mute properties.
result: pass

### 3. Remove Notes from a MIDI Clip
expected: Call the remove_notes tool on a clip with notes. The tool returns a JSON confirmation. Verify with get_notes that the targeted notes have been removed from the clip.
result: pass

### 4. Quantize Notes
expected: Call the quantize_notes tool on a clip with notes at off-grid positions, specifying a grid value (e.g. 0.25 for sixteenth notes). The tool returns a JSON confirmation. Verify with get_notes that note start_times have been snapped to the nearest grid position.
result: pass

### 5. Transpose Notes
expected: Call the transpose_notes tool on a clip with notes, specifying a semitone offset (e.g. 12 for one octave up). The tool returns a JSON confirmation. Verify with get_notes that all note pitches have shifted by the specified amount. Notes near MIDI boundaries (0 or 127) should cause an error rather than partial transposition.
result: pass

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
