# Deferred Items - Phase 02

## From Plan 02-02 (MCP Server Module Split)

### Test Fixture Updates for Remote Script Handler Extraction (from 02-01)

7 tests grep `AbletonMCP_Remote_Script/__init__.py` for functions that were moved to handler sub-modules by plan 02-01. These tests need their `remote_script_source` fixtures updated to read from the appropriate handler files:

- `test_dispatch.py::TestDictDispatchExists::test_read_commands_dict_exists` - looks for `_read_commands` dict in `__init__.py`
- `test_dispatch.py::TestDictDispatchExists::test_write_commands_dict_exists` - looks for `_write_commands` dict in `__init__.py`
- `test_dispatch.py::TestPingInReadCommands::test_ping_in_read_commands` - looks for ping in `_read_commands`
- `test_instrument_loading.py::TestSameCallbackPattern::test_load_browser_item_same_callback` - looks for `_load_browser_item`/`do_load` in `__init__.py`
- `test_instrument_loading.py::TestVerifyLoadRetry::test_verify_load_has_retry` - looks for `_verify_load` in `__init__.py`
- `test_instrument_loading.py::TestDeviceChainReporting::test_load_success_reports_device_chain` - looks for device chain in `_verify_load`
- `test_instrument_loading.py::TestPingAbletonVersion::test_ping_returns_ableton_version` - looks for `_ping` in `__init__.py`

**Root cause:** Plan 02-01 extracted handlers into `handlers/` sub-modules but did not update the corresponding test fixtures.
**Recommended fix:** Plan 02-03 should update test fixtures to read the correct handler source files.
