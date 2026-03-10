# External Integrations

**Analysis Date:** 2026-03-10

## APIs & External Services

**Claude AI Integration:**
- Model Context Protocol (MCP) - Enables Claude to invoke Ableton tools
  - SDK: `mcp[cli]` >= 1.4.0
  - Integration: Server exposes tools via FastMCP decorator pattern
  - Transport: stdio (command-line standard input/output)

**Ableton Live Integration:**
- Ableton Live DAW (Digital Audio Workstation) 10.0+
  - Communication: TCP socket connection on localhost:9877
  - Protocol: Custom JSON-based command/response format
  - Auth: No authentication (localhost-only connection)

## Data Storage

**Databases:**
- None - Stateless design, all data ephemeral during session

**File Storage:**
- Local filesystem only - No cloud storage integration

**Caching:**
- In-memory connection pooling: Single persistent socket connection to Ableton (`_ableton_connection` global variable in `MCP_Server/server.py`)
- No external cache service

## Authentication & Identity

**Auth Provider:**
- None - Localhost-only communication, no authentication layer
- Connection restricted to: `host="localhost"` hardcoded in `AbletonConnection.__init__()` at line 222

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking integration

**Logs:**
- Python standard `logging` module
  - Logger: `AbletonMCPServer`
  - Format: `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`
  - Level: INFO (hardcoded at `logging.basicConfig()` line 11-12)
  - Output: stdout via Python logging

**Log Coverage:**
- Connection lifecycle events (connect, disconnect, reconnect attempts)
- Command send/receive operations with byte counts
- Timeout and error conditions
- JSON parsing failures with raw response preview

## CI/CD & Deployment

**Hosting:**
- Smithery registry integration for automated installation
  - Registry: `@ahujasid/ableton-mcp` on smithery.ai
  - Installation: `npx -y @smithery/cli install @ahujasid/ableton-mcp --client claude`

**Distribution:**
- PyPI package (installable via `pip install ableton-mcp`)
- Installation via uv: `uvx ableton-mcp`
- Docker container support (Dockerfile provided, Python 3.10 Alpine base)

**CI Pipeline:**
- Not detected - Smithery configuration present but no CI workflow files found

## Environment Configuration

**Connection Parameters (hardcoded):**
- Host: `localhost` - Ableton connection restricted to local machine
- Port: `9877` - Fixed port for Remote Script socket server

**Required env vars:**
- None required - All configuration hardcoded or provided at runtime

**Secrets location:**
- No secrets management - Localhost connection only, no API keys or credentials needed

**Configuration File:**
- `smithery.yaml` - Smithery MCP registry configuration
  - Defines: startCommand, configSchema, commandFunction, exampleConfig
  - Entry: Python `-m MCP_Server.server` module execution

## Webhooks & Callbacks

**Incoming:**
- None - Ableton Remote Script initiates socket server on port 9877, MCP server connects to it

**Outgoing:**
- None - All communication is request/response over TCP socket

## Remote Script Integration

**Ableton Remote Script:**
- File: `AbletonMCP_Remote_Script/__init__.py` (46KB file)
- Type: MIDI Remote Script for Ableton Live
- Purpose: Creates socket server listening on localhost:9877
- Framework: Inherits from `_Framework.ControlSurface` (Ableton's remote control API)
- Python compatibility: 2 and 3 (conditional imports for Queue module)

**Command Protocol:**
JSON message structure:
```json
{
  "type": "command_name",
  "params": {
    "key": "value"
  }
}
```

Response structure:
```json
{
  "status": "success|error",
  "result": {},
  "message": "optional error message"
}
```

## Tool Categories

**Session Tools:**
- `get_session_info()` - Query Ableton session state
- `get_track_info(track_index)` - Query specific track information
- `set_tempo(tempo)` - Modify session tempo

**Track Management:**
- `create_midi_track(index)` - Create new MIDI track
- `create_audio_track(index)` - Create new audio track (command exists but not exposed as tool)
- `set_track_name(track_index, name)` - Rename track

**Clip Operations:**
- `create_clip(track_index, clip_index, length)` - Create MIDI clip
- `add_notes_to_clip(track_index, clip_index, notes)` - Insert MIDI notes
- `set_clip_name(track_index, clip_index, name)` - Rename clip
- `fire_clip(track_index, clip_index)` - Start clip playback
- `stop_clip(track_index, clip_index)` - Stop clip playback

**Device/Instrument Loading:**
- `load_instrument_or_effect(track_index, uri)` - Load device from browser URI
- `load_drum_kit(track_index, rack_uri, kit_path)` - Multi-step drum rack loading
- `get_browser_tree(category_type)` - Query instrument/sound browser structure
- `get_browser_items_at_path(path)` - Query specific browser location

**Transport Control:**
- `start_playback()` - Start Ableton playback
- `stop_playback()` - Stop Ableton playback

**Set Device Parameter:**
- `set_device_parameter(track_index, device_index, param_id, value)` - Modify effect/instrument parameters (command infrastructure exists)

---

*Integration audit: 2026-03-10*
