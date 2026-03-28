# Deferred Items - Phase 28

## Pre-existing Issues (Out of Scope)

1. **test_registry.py::TestFullRegistry::test_all_commands_registered** - Expects 178 commands but finds 181. Phase 27 added 3 scaffold commands (create_locator_at, get_arrangement_state, scaffold_tracks) but the test count was not updated. Not caused by Phase 28 changes.
