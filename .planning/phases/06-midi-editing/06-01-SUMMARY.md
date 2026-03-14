---
phase: 06-midi-editing
plan: 01
subsystem: api
tags: [midi, live-api, notes, clip, midiNoteSpecification]

requires:
  - phase: 05-clip-management
    provides: "_resolve_clip_slot helper, clip handler patterns"
provides:
  - "5 @command handlers for MIDI note operations (add, get, remove, quantize, transpose)"
  - "4 new write command timeout entries in _WRITE_COMMANDS"
  - "Live 11+ API usage: add_new_notes, get_notes_extended, remove_notes_extended"
affects: [06-midi-editing]

tech-stack:
  added: [Live.Clip.MidiNoteSpecification]
  patterns: [read-modify-write for quantize/transpose, pre-validation before mutation]

key-files:
  created: []
  modified:
    - AbletonMCP_Remote_Script/handlers/notes.py
    - MCP_Server/connection.py
    - tests/test_registry.py

key-decisions:
  - "Live.Clip imported inside method bodies (not module level) for test compatibility outside Ableton runtime"
  - "Pre-validation pattern for transpose: check all notes before modifying any to prevent partial mutations"
  - "Quantize uses read-modify-write: read all notes, compute new positions, remove all, add back"

patterns-established:
  - "Deferred import pattern: import Live.Clip inside handler methods that use MidiNoteSpecification"
  - "Read-modify-write pattern for note mutations: get_notes_extended -> remove_notes_extended -> add_new_notes"

requirements-completed: [MIDI-01, MIDI-02, MIDI-03, MIDI-04, MIDI-05]

duration: 3min
completed: 2026-03-14
---

# Phase 6 Plan 01: Note Handlers Summary

**5 Live 11+ MIDI command handlers with MidiNoteSpecification append-mode API, read-modify-write mutation pattern, and pre-validation for transpose**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T23:35:16Z
- **Completed:** 2026-03-14T23:38:18Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Rewrote add_notes_to_clip from deprecated set_notes to Live 11+ add_new_notes with MidiNoteSpecification objects
- Added 4 new note handlers: get_notes, remove_notes, quantize_notes, transpose_notes
- Registry test updated and passing with 44 total commands
- _WRITE_COMMANDS updated with 3 new write operations (get_notes correctly excluded as read)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite NoteHandlers mixin with 5 Live 11+ command handlers** - `37ba899` (feat)
2. **Task 2: Add new note commands to _WRITE_COMMANDS and update registry test** - `9e936c6` (feat)

## Files Created/Modified
- `AbletonMCP_Remote_Script/handlers/notes.py` - 5 @command handlers for MIDI note operations using Live 11+ APIs
- `MCP_Server/connection.py` - Added remove_notes, quantize_notes, transpose_notes to _WRITE_COMMANDS
- `tests/test_registry.py` - Updated expected count to 44, added 4 new note command names

## Decisions Made
- Live.Clip imported inside method bodies rather than at module level -- the `Live` module is only available inside Ableton's Python runtime, and module-level import breaks the test suite
- Pre-validation pattern for transpose: iterate all notes checking pitch range before any mutation to prevent partial state changes
- Quantize and transpose use read-modify-write pattern (get_notes_extended -> remove_notes_extended -> add_new_notes) since Live API has no in-place note modification

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Moved Live.Clip import from module level to method bodies**
- **Found during:** Task 2 (registry test verification)
- **Issue:** Module-level `import Live.Clip` causes ModuleNotFoundError when running tests outside Ableton runtime, breaking all registry tests
- **Fix:** Moved import inside the 3 method bodies that use MidiNoteSpecification (add_notes_to_clip, quantize_notes, transpose_notes)
- **Files modified:** AbletonMCP_Remote_Script/handlers/notes.py
- **Verification:** All 4 registry tests pass, module imports cleanly with stubbed Live module
- **Committed in:** 9e936c6 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for test compatibility. No scope creep.

## Issues Encountered
None beyond the import fix documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 note command handlers ready for MCP tool exposure in Plan 06-02
- Read-modify-write pattern established for future mutation operations
- Registry test infrastructure supports new command additions

## Self-Check: PASSED

All files exist. All commit hashes verified.

---
*Phase: 06-midi-editing*
*Completed: 2026-03-14*
