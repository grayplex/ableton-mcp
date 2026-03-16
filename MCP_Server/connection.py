"""Ableton connection management: socket lifecycle, timeouts, error formatting."""

import json
import logging
import socket
import threading
import time
from dataclasses import dataclass
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
    ]
)

# Commands that modify state (write operations)
_WRITE_COMMANDS = frozenset(
    [
        "create_midi_track",
        "create_audio_track",
        "create_return_track",
        "create_group_track",
        "set_track_name",
        "delete_track",
        "duplicate_track",
        "set_track_color",
        "set_group_fold",
        "create_clip",
        "add_notes_to_clip",
        "set_clip_name",
        "set_tempo",
        "fire_clip",
        "stop_clip",
        "set_device_parameter",
        "start_playback",
        "stop_playback",
        # Phase 4: Mixing Controls
        "set_track_volume",
        "set_track_pan",
        "set_track_mute",
        "set_track_solo",
        "set_track_arm",
        "set_send_level",
        # Phase 5: Clip Management
        "delete_clip",
        "duplicate_clip",
        "set_clip_color",
        "set_clip_loop",
        # Phase 6: MIDI Editing
        "remove_notes",
        "quantize_notes",
        "transpose_notes",
        # Phase 7: Device & Browser
        "delete_device",
        # Phase 8: Scene and Transport
        "create_scene",
        "set_scene_name",
        "fire_scene",
        "delete_scene",
        "continue_playback",
        "stop_all_clips",
        "set_time_signature",
        "set_loop_region",
        "undo",
        "redo",
        # Phase 9: Automation
        "insert_envelope_breakpoints",
        "clear_clip_envelopes",
    ]
)


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

    def send_command(self, command_type: str, params: dict[str, Any] = None) -> dict[str, Any]:
        """Send a command to Ableton and return the response.

        Uses length-prefix framing for reliable message boundaries.
        No artificial delays -- the framing protocol handles completeness.
        """
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Ableton")

        command = {"type": command_type, "params": params or {}}

        timeout = _timeout_for(command_type)

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
            logger.error("Socket timeout while waiting for response from Ableton")
            self.sock = None
            raise Exception("Timeout waiting for Ableton response") from e
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
