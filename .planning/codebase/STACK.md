# Technology Stack

**Analysis Date:** 2026-03-10

## Languages

**Primary:**
- Python 3.13 - MCP server implementation, primary language for all server-side code
- Python 3.8-3.10 - Ableton Live Remote Script, compatible with Ableton's Python 2/3 environment

**Secondary:**
- JSON - All inter-process communication uses JSON serialization

## Runtime

**Environment:**
- Python 3.10+ (requires `>=3.10` per `pyproject.toml`)
- Alpine Linux 3.10 base in Docker

**Package Manager:**
- `uv` - Fast Python package manager (primary installation method)
- pip - Fallback package installation in Docker
- Lockfile: `uv.lock` present and committed

## Frameworks

**Core:**
- MCP (Model Context Protocol) 1.4.0 - Framework for Claude AI integration, provides tools and resources API
- FastMCP - Lightweight MCP server implementation within `mcp[cli]>=1.3.0`

**Build/Dev:**
- setuptools 61.0+ - Build system for Python packaging
- wheel - Distribution format

## Key Dependencies

**Critical:**
- mcp[cli] 1.4.0 - Core MCP framework with CLI support
  - Provides: `FastMCP`, `Context` for tool definitions
  - Includes: anyio, httpx for async operations

**Infrastructure:**
- anyio 4.8.0 - Async I/O abstraction layer for cross-platform async operations
- httpx 1.x - HTTP client library (included with mcp dependency)
- click 8.1.8 - CLI toolkit for command-line interface
- httpcore 1.0.7 - HTTP/1.1 networking
- certifi 2025.1.31 - CA certificate bundle for HTTPS

**Type Checking:**
- annotated-types 0.7.0 - Type annotations support
- typing-extensions - Backported typing features for Python <3.13

**Support Libraries:**
- colorama 0.4.6 - Cross-platform colored terminal output (Windows support)
- idna - International domain names in URLs
- sniffio - Async library detection

## Configuration

**Environment:**
- Python version: `.python-version` file specifies `3.13`
- Package configuration: `pyproject.toml` (PEP 517/518 compliant)
- Entry point: `ableton-mcp = "MCP_Server.server:main"` in project.scripts

**Build:**
- `pyproject.toml` - Project metadata, dependencies, build configuration
- `setup.py` - Generated from setuptools configuration in pyproject.toml
- `uv.lock` - Lockfile for reproducible builds

## Platform Requirements

**Development:**
- Python 3.10+ runtime
- uv package manager (recommended for installation)
- Ableton Live 10 or newer installed

**Production:**
- Docker deployment option available
- Container: Python 3.10 Alpine Linux
- Build dependencies installed: gcc, musl-dev, libffi-dev

## Communication Protocol

**Internal Socket Communication:**
- TCP sockets over localhost:9877
- JSON message format for command/response protocol
- Host: `localhost` hardcoded
- Port: `DEFAULT_PORT = 9877` (configured in `AbletonMCP_Remote_Script/__init__.py`)

**Timeout Configuration:**
- Standard receive timeout: 10.0 seconds
- State-modifying commands: 15.0 seconds
- Socket timeout on connection test: 1.0 seconds

---

*Stack analysis: 2026-03-10*
