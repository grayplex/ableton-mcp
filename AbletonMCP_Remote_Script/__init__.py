# AbletonMCP Remote Script
#
# Slim orchestrator: server, client handling, and registry integration.
# All command handlers live in the handlers/ package as mixin classes.

import json
import queue
import socket
import struct
import threading
import time
import traceback

from _Framework.ControlSurface import ControlSurface

# Importing handlers triggers @command decorator registration
import AbletonMCP_Remote_Script.handlers  # noqa: F401

from .handlers.base import BaseHandlers
from .handlers.audio_clips import AudioClipHandlers
from .handlers.automation import AutomationHandlers
from .handlers.browser import BrowserHandlers
from .handlers.grooves import GrooveHandlers
from .handlers.clips import ClipHandlers
from .handlers.devices import DeviceHandlers
from .handlers.mixer import MixerHandlers
from .handlers.notes import NoteHandlers
from .handlers.routing import RoutingHandlers
from .handlers.scenes import SceneHandlers
from .handlers.tracks import TrackHandlers
from .handlers.transport import TransportHandlers
from .registry import CommandRegistry

# --- Length-prefix framing protocol ---


def _recv_exact(sock, n):
    """Read exactly n bytes from socket."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def send_message(sock, data):
    """Send a length-prefixed JSON message."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    header = struct.pack(">I", len(payload))
    sock.sendall(header + payload)


def recv_message(sock, timeout=15.0):
    """Receive a length-prefixed JSON message."""
    sock.settimeout(timeout)
    header = _recv_exact(sock, 4)
    if not header:
        raise ConnectionError("Connection closed while reading header")
    length = struct.unpack(">I", header)[0]
    if length > 10 * 1024 * 1024:  # 10MB safety limit
        raise ValueError(f"Message too large: {length} bytes")
    payload = _recv_exact(sock, length)
    if not payload:
        raise ConnectionError("Connection closed while reading payload")
    return json.loads(payload.decode("utf-8"))


# Constants for socket communication
DEFAULT_PORT = 9877
HOST = "localhost"


def create_instance(c_instance):
    """Create and return the AbletonMCP script instance."""
    return AbletonMCP(c_instance)


class AbletonMCP(
    BaseHandlers,
    TransportHandlers,
    TrackHandlers,
    ClipHandlers,
    NoteHandlers,
    DeviceHandlers,
    MixerHandlers,
    SceneHandlers,
    AutomationHandlers,
    RoutingHandlers,
    AudioClipHandlers,
    GrooveHandlers,
    BrowserHandlers,
    ControlSurface,
):
    """AbletonMCP Remote Script for Ableton Live.

    Inherits handler methods from domain mixin classes and uses
    CommandRegistry to build dispatch tables at init time.
    """

    def __init__(self, c_instance):
        """Initialize the control surface."""
        super().__init__(c_instance)
        self.log_message("AbletonMCP Remote Script initializing...")

        # Socket server for communication
        self.server = None
        self.client_threads = []
        self.server_thread = None
        self.running = False

        # Cache the song reference for easier access
        self._song = self.song()

        # Build command dispatch tables from registry
        self._read_commands, self._write_commands, self._self_scheduling = (
            CommandRegistry.build_tables(self)
        )

        # Browser path cache (cleared on disconnect)
        self._browser_path_cache: dict = {}

        # Start the socket server
        self.start_server()

        self.log_message("AbletonMCP initialized")
        self.show_message(f"AbletonMCP: Listening for commands on port {DEFAULT_PORT}")

    def disconnect(self):
        """Called when Ableton closes or the control surface is removed."""
        self.log_message("AbletonMCP disconnecting...")
        self.running = False

        # Clear browser path cache
        self._browser_path_cache.clear()

        # Stop the server
        if self.server:
            try:
                self.server.close()
            except Exception as e:
                self.log_message(f"[ERROR] Error closing server socket: {e}")

        # Wait for the server thread to exit
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(1.0)

        # Clean up any client threads
        for client_thread in self.client_threads[:]:
            if client_thread.is_alive():
                self.log_message("Client thread still alive during disconnect")

        super().disconnect()
        self.log_message("AbletonMCP disconnected")

    def start_server(self):
        """Start the socket server in a separate thread."""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((HOST, DEFAULT_PORT))
            self.server.listen(5)

            self.running = True
            self.server_thread = threading.Thread(target=self._server_thread)
            self.server_thread.daemon = True
            self.server_thread.start()

            self.log_message(f"Server started on port {DEFAULT_PORT}")
        except Exception as e:
            self.log_message(f"Error starting server: {e}")
            self.show_message(f"AbletonMCP: Error starting server - {e}")

    def _server_thread(self):
        """Server thread implementation - handles client connections."""
        try:
            self.log_message("Server thread started")
            self.server.settimeout(1.0)

            while self.running:
                try:
                    client, address = self.server.accept()
                    self.log_message(f"Connection accepted from {address}")
                    self.show_message("AbletonMCP: Client connected")

                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,),
                    )
                    client_thread.daemon = True
                    client_thread.start()

                    self.client_threads.append(client_thread)
                    self.client_threads = [t for t in self.client_threads if t.is_alive()]

                except TimeoutError:
                    continue
                except Exception as e:
                    if self.running:
                        self.log_message(f"Server accept error: {e}")
                    time.sleep(0.5)

            self.log_message("Server thread stopped")
        except Exception as e:
            self.log_message(f"Server thread error: {e}")

    def _handle_client(self, client):
        """Handle communication with a connected client.

        Uses length-prefix framing for reliable message boundaries.
        """
        self.log_message("Client handler started")
        client.settimeout(None)

        try:
            while self.running:
                try:
                    command = recv_message(client)
                    self.log_message(f"Received command: {command.get('type', 'unknown')}")
                    response = self._process_command(command)
                    send_message(client, response)
                except (ConnectionError, ConnectionResetError, BrokenPipeError) as e:
                    self.log_message(f"Client connection lost: {e}")
                    break
                except Exception as e:
                    self.log_message(f"[ERROR] Error handling command: {e}")
                    self.log_message(traceback.format_exc())
                    try:
                        send_message(client, {"status": "error", "message": str(e)})
                    except Exception as send_err:
                        self.log_message(f"[ERROR] Failed to send error response: {send_err}")
                        break
        except Exception as e:
            self.log_message(f"Error in client handler: {e}")
        finally:
            try:
                client.close()
            except Exception as e:
                self.log_message(f"[ERROR] Error closing client socket: {e}")
            self.log_message("Client handler stopped")

    def _process_command(self, command):
        """Dispatch command to handler via dict lookup."""
        command_type = command.get("type", "")
        params = command.get("params", {})

        # Read commands -- run directly on socket thread
        if command_type in self._read_commands:
            handler = self._read_commands[command_type]
            try:
                result = handler(params)
                return {"status": "success", "result": result}
            except Exception as e:
                self.log_message(f"[ERROR] {command_type}: {e}")
                self.log_message(traceback.format_exc())
                return {"status": "error", "message": str(e)}

        # Write commands -- schedule on main thread
        if command_type in self._write_commands:
            return self._dispatch_write_command(command_type, params)

        # Unknown command
        return {"status": "error", "message": f"Unknown command: {command_type}"}

    def _dispatch_write_command(self, command_type, params):
        """Execute a write command on the main thread via schedule_message.

        Commands in self._self_scheduling manage their own threading
        (e.g., load_browser_item uses multi-tick schedule_message patterns).
        """
        if command_type in self._self_scheduling:
            handler = self._write_commands[command_type]
            try:
                result = handler(params)
                return {"status": "success", "result": result}
            except Exception as e:
                self.log_message(f"[ERROR] {command_type}: {e}")
                self.log_message(traceback.format_exc())
                return {"status": "error", "message": str(e)}

        handler = self._write_commands[command_type]
        response_queue = queue.Queue()

        def main_thread_task():
            try:
                result = handler(params)
                response_queue.put({"status": "success", "result": result})
            except Exception as e:
                self.log_message(f"[ERROR] {command_type}: {e}")
                self.log_message(traceback.format_exc())
                response_queue.put({"status": "error", "message": str(e)})

        try:
            self.schedule_message(0, main_thread_task)
        except AssertionError:
            main_thread_task()

        timeout = 30.0 if command_type in self._self_scheduling else 10.0
        try:
            return response_queue.get(timeout=timeout)
        except queue.Empty:
            return {"status": "error", "message": f"Timeout waiting for {command_type} to complete"}
