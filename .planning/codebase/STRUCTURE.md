# Codebase Structure

**Analysis Date:** 2026-03-10

## Directory Layout

```
ableton-mcp/
├── MCP_Server/                          # MCP framework server (Claude-facing)
│   ├── __init__.py                      # Package initialization, exports
│   └── server.py                        # Main server implementation
├── AbletonMCP_Remote_Script/            # Ableton Live Remote Script (DAW-facing)
│   └── __init__.py                      # Remote script implementation
├── .planning/                           # GSD analysis documents
│   └── codebase/
├── pyproject.toml                       # Project metadata and dependencies
├── smithery.yaml                        # Smithery integration config
├── uv.lock                              # UV package manager lockfile
├── Dockerfile                           # Docker container configuration
├── README.md                            # Documentation
├── LICENSE                              # MIT License
└── .python-version                      # Python version specification

```

## Directory Purposes

**MCP_Server:**
- Purpose: FastMCP server implementation for Model Context Protocol
- Contains: Tool definitions, connection management, command handlers
- Key files: `server.py` (660 lines)

**AbletonMCP_Remote_Script:**
- Purpose: MIDI Remote Script embedded in Ableton Live
- Contains: Socket server, command processing, Ableton Live API interaction
- Key files: `__init__.py` (1062 lines)

## Key File Locations

**Entry Points:**
- `MCP_Server/server.py:main()`: MCP server startup (line 655)
- `MCP_Server/__init__.py`: Package exports (line 6)
- `AbletonMCP_Remote_Script/__init__.py:create_instance()`: Ableton Remote Script creation (line 21)

**Configuration:**
- `pyproject.toml`: Project metadata, dependencies, console script definition
- `smithery.yaml`: Smithery server registration
- `.python-version`: Required Python version (3.10+)
- `Dockerfile`: Container deployment configuration

**Core Logic:**
- `MCP_Server/server.py:AbletonConnection`: Socket communication class (line 16)
- `MCP_Server/server.py:get_ableton_connection()`: Connection lifecycle manager (line 195)
- `MCP_Server/server.py:@mcp.tool()` decorators: Tool definitions (lines 260-653)
- `AbletonMCP_Remote_Script/__init__.py:AbletonMCP`: Remote Script class (line 25)
- `AbletonMCP_Remote_Script/__init__.py:_process_command()`: Command router (line 210)

**Testing:**
- Not detected (no test files)

## Naming Conventions

**Files:**
- `server.py`: Main implementation file
- `__init__.py`: Package initialization and exports
- Capitalized directory names: `MCP_Server`, `AbletonMCP_Remote_Script`

**Directories:**
- `MCP_Server`: Upper CamelCase with underscore
- `AbletonMCP_Remote_Script`: Upper CamelCase with underscore
- `.planning/codebase/`: Dot-prefixed for hidden directories

**Python Classes:**
- `AbletonConnection`: Upper CamelCase, dataclass representing connection
- `AbletonMCP`: Upper CamelCase, inherits from ControlSurface

**Python Functions:**
- `get_ableton_connection()`: Snake case, getter function
- `create_instance()`: Snake case, factory function
- `send_command()`: Snake case, action method
- Tool handlers: Snake case with leading underscore for private methods

**Tool Names (MCP):**
- `get_session_info`: Verb-noun pattern, snake case
- `create_midi_track`: Verb-noun pattern, snake case
- `add_notes_to_clip`: Verb-noun-object pattern, snake case

## Where to Add New Code

**New Feature (e.g., new Ableton command):**

1. **Add MCP tool in** `MCP_Server/server.py`:
   - Add `@mcp.tool()` decorated function (follow pattern of lines 260-500)
   - Call `get_ableton_connection().send_command()` with command type
   - Wrap in try/except, return string response

2. **Add handler in Remote Script** `AbletonMCP_Remote_Script/__init__.py`:
   - Add case in `_process_command()` routing (line 229-232)
   - Implement `_<command_name>()` handler method
   - For state-modifying commands: use `schedule_message()` and response queue pattern (lines 237-310)
   - For query commands: call directly and return result

3. **Register command type in connection check:**
   - If state-modifying: add to `is_modifying_command` list (lines 104-109)
   - Adds automatic delays and longer timeout

**New Component/Module:**
- Create new Python file in `MCP_Server/` if logic > 100 lines
- Export via `MCP_Server/__init__.py`
- Follow existing class patterns (AbletonConnection as model)

**Utilities:**
- Shared socket helpers: `MCP_Server/server.py` (socket-level utilities currently inline)
- Shared Ableton helpers: `AbletonMCP_Remote_Script/__init__.py` (API interaction patterns currently inline)
- Consider extraction if > 3 uses

**Browser-related Tools:**
- Special pattern in `MCP_Server/server.py:get_browser_tree()` (line 502)
- Recursive tree formatting with indentation (lines 525-549)
- Error handling for unavailable browser (lines 553-562)

## Special Directories

**`.planning/codebase/`:**
- Purpose: GSD (Get Shit Done) analysis documents
- Generated: Yes (by GSD mapping commands)
- Committed: Yes
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md

**`.git/`:**
- Purpose: Git version control
- Generated: Yes
- Committed: No (standard .gitignore entry)

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes
- Committed: No

## File Size and Complexity

**MCP_Server/server.py:**
- 660 lines
- Key sections: Connection class (120 lines), tool handlers (390 lines)
- Complexity: Medium (JSON protocol, socket management)

**AbletonMCP_Remote_Script/__init__.py:**
- 1062 lines
- Key sections: Socket server (140 lines), command router (130 lines), Ableton API handlers (700+ lines)
- Complexity: High (threading, Ableton API, main thread scheduling)

## Installation & Deployment Locations

**For Development:**
- Clone to any directory
- Run: `uvx ableton-mcp` (via uv package manager)

**For Ableton Integration (Production):**
- Remote Script deployment: `~/.config/Ableton/Live <VERSION>/Preferences/User Remote Scripts/AbletonMCP/`
- MCP Server: Configured in Claude Desktop config at `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

---

*Structure analysis: 2026-03-10*
