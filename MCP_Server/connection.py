"""Ableton connection management: socket lifecycle, timeouts, error formatting."""

import json
import logging
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from MCP_Server.protocol import recv_message, send_message

logger = logging.getLogger("AbletonMCPServer")

# Timeout constants for different operation types
TIMEOUT_READ = 10.0
TIMEOUT_WRITE = 15.0
TIMEOUT_BROWSER = 30.0
TIMEOUT_PING = 5.0

# Commands that require longer timeouts (browser/load operations)
_BROWSER_COMMANDS = frozenset(
    [
        "get_browser_tree",
        "get_browser_items_at_path",
        "get_browser_item",
        "get_browser_categories",
        "get_browser_items",
        "load_browser_item",
        "load_instrument_or_effect",
        # Phase 7: Session State (iterates all tracks/devices)
        "get_session_state",
        # Phase 31: Recipe application (multi-device load)
        "apply_recipe",
    ]
)

# Commands that modify state (write operations).
# Derived from @command(write=True) registry entries at import time so the
# set stays in sync automatically when new handlers are added.
def _build_write_commands() -> frozenset:
    import sys
    import types

    # MCP_Server runs in a separate process from Ableton, so _Framework is absent.
    # Stub the one symbol that AbletonMCP_Remote_Script/__init__.py needs so the
    # handler modules can be imported and their @command decorators can fire.
    if "_Framework" not in sys.modules:
        _fw = types.ModuleType("_Framework")
        _fw_cs = types.ModuleType("_Framework.ControlSurface")
        _fw_cs.ControlSurface = object
        sys.modules["_Framework"] = _fw
        sys.modules["_Framework.ControlSurface"] = _fw_cs

    try:
        import AbletonMCP_Remote_Script.handlers  # noqa: F401 — triggers @command registrations
        from AbletonMCP_Remote_Script.registry import CommandRegistry
        return CommandRegistry.get_write_commands()
    except Exception as exc:
        logger.warning("Could not derive write commands from registry: %s", exc)
        return frozenset()


_WRITE_COMMANDS = _build_write_commands()


# --- AI-friendly error formatting ---


def format_error(message: str, detail: str = "", suggestion: str = "") -> str:
    """Format error for AI consumption. Clean message first, technical detail below."""
    parts = [f"Error: {message}"]
    if suggestion:
        parts.append(f"Suggestion: {suggestion}")
    if detail:
        parts.append(f"Debug: {detail}")
    return "\n".join(parts)


def _timeout_for(command_type: str) -> float:
    """Return the appropriate timeout for a command type."""
    if command_type == "ping":
        return TIMEOUT_PING
    if command_type in _BROWSER_COMMANDS:
        return TIMEOUT_BROWSER
    if command_type in _WRITE_COMMANDS:
        return TIMEOUT_WRITE
    return TIMEOUT_READ


@dataclass
class AbletonConnection:
    host: str
    port: int
    sock: socket.socket = None
    _send_lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False, compare=False
    )

    def connect(self) -> bool:
        """Connect to the Ableton Remote Script socket server."""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Ableton at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ableton: {str(e)}")
            self.sock = None
            return False

    def disconnect(self):
        """Disconnect from the Ableton Remote Script."""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Ableton: {str(e)}")
            finally:
                self.sock = None

    def send_command(self, command_type: str, params: dict[str, Any] = None, timeout: float | None = None) -> dict[str, Any]:
        """Send a command to Ableton and return the response.

        Uses length-prefix framing for reliable message boundaries.
        No artificial delays -- the framing protocol handles completeness.

        Args:
            command_type: The command to send.
            params: Optional parameters for the command.
            timeout: Optional per-call timeout override (seconds). When None,
                     uses the default timeout for the command type.
        """
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Ableton")

        command = {"type": command_type, "params": params or {}}

        if timeout is None:
            timeout = _timeout_for(command_type)

        with self._send_lock:
            try:
                logger.info(f"Sending command: {command_type} with params: {params}")

                # Send the command using length-prefix framing
                send_message(self.sock, command)
                logger.info("Command sent, waiting for response...")

                # Receive the response using length-prefix framing
                response = recv_message(self.sock, timeout=timeout)
                logger.info(f"Response received, status: {response.get('status', 'unknown')}")

                if response.get("status") == "error":
                    logger.error(f"Ableton error: {response.get('message')}")
                    raise Exception(response.get("message", "Unknown error from Ableton"))

                return response.get("result", {})
            except TimeoutError as e:
                logger.error(f"Socket timeout after {timeout:.0f}s waiting for '{command_type}'")
                self.sock = None
                raise Exception(
                    f"Timeout after {timeout:.0f}s waiting for Ableton to complete '{command_type}'. "
                    f"This may happen when Ableton is scanning plugins. Retry the command."
                ) from e
            except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                logger.error(f"Socket connection error: {str(e)}")
                self.sock = None
                raise Exception(f"Connection to Ableton lost: {str(e)}") from e
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from Ableton: {str(e)}")
                self.sock = None
                raise Exception(f"Invalid response from Ableton: {str(e)}") from e
            except Exception as e:
                logger.error(f"Error communicating with Ableton: {str(e)}")
                self.sock = None
                raise Exception(f"Communication error with Ableton: {str(e)}") from e


# Global connection for resources -- protected by _connection_lock
_ableton_connection = None
_connection_lock = threading.Lock()


def shutdown_connection():
    """Disconnect and clear the global Ableton connection. Called on server shutdown."""
    global _ableton_connection
    with _connection_lock:
        if _ableton_connection:
            _ableton_connection.disconnect()
            _ableton_connection = None


def get_ableton_connection():
    """Get or create a persistent Ableton connection.

    Thread-safe: all access to _ableton_connection is serialized
    by _connection_lock. Uses a real ping command for liveness testing
    instead of sending empty bytes.
    """
    global _ableton_connection

    with _connection_lock:
        if _ableton_connection is not None:
            try:
                # Test the connection with a real ping command
                _ableton_connection.send_command("ping")
                return _ableton_connection
            except Exception as e:
                logger.warning(f"Existing connection is no longer valid: {str(e)}")
                try:
                    _ableton_connection.disconnect()
                except Exception as cleanup_err:
                    logger.warning(f"Error during connection cleanup: {cleanup_err}")
                _ableton_connection = None

        # Connection doesn't exist or is invalid, create a new one
        # Try to connect up to 3 times with a short delay between attempts
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Connecting to Ableton (attempt {attempt}/{max_attempts})...")
                _ableton_connection = AbletonConnection(host="localhost", port=9877)
                if _ableton_connection.connect():
                    logger.info("Created new persistent connection to Ableton")

                    # Validate connection with a simple command
                    try:
                        _ableton_connection.send_command("get_session_info")
                        logger.info("Connection validated successfully")
                        return _ableton_connection
                    except Exception as e:
                        logger.error(f"Connection validation failed: {str(e)}")
                        _ableton_connection.disconnect()
                        _ableton_connection = None
                        # Continue to next attempt
                else:
                    _ableton_connection = None
            except Exception as e:
                logger.error(f"Connection attempt {attempt} failed: {str(e)}")
                if _ableton_connection:
                    _ableton_connection.disconnect()
                    _ableton_connection = None

            # Wait before trying again, but only if we have more attempts left
            if attempt < max_attempts:
                time.sleep(1.0)

        # If we get here, all connection attempts failed
        if _ableton_connection is None:
            logger.error("Failed to connect to Ableton after multiple attempts")
            raise Exception("Could not connect to Ableton. Make sure the Remote Script is running.")

    return _ableton_connection
