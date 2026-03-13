# AbletonMCP/init.py
from _Framework.ControlSurface import ControlSurface
import socket
import struct
import json
import queue
import threading
import time
import traceback


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

# Browser category map -- fixes the 'nstruments' typo by using correct dict keys
_CATEGORY_MAP = {
    "instruments": "instruments",
    "sounds": "sounds",
    "drums": "drums",
    "audio_effects": "audio_effects",
    "midi_effects": "midi_effects",
    "max_for_live": "max_for_live",
    "plug_ins": "plug_ins",
    "clips": "clips",
    "samples": "samples",
    "packs": "packs",
}

def create_instance(c_instance):
    """Create and return the AbletonMCP script instance"""
    return AbletonMCP(c_instance)

class AbletonMCP(ControlSurface):
    """AbletonMCP Remote Script for Ableton Live"""

    def __init__(self, c_instance):
        """Initialize the control surface"""
        super().__init__(c_instance)
        self.log_message("AbletonMCP Remote Script initializing...")

        # Socket server for communication
        self.server = None
        self.client_threads = []
        self.server_thread = None
        self.running = False

        # Cache the song reference for easier access
        self._song = self.song()

        # Build command dispatch tables
        self._build_command_table()

        # Browser path cache (cleared on disconnect)
        self._browser_path_cache: dict = {}

        # Start the socket server
        self.start_server()

        self.log_message("AbletonMCP initialized")

        # Show a message in Ableton
        self.show_message(f"AbletonMCP: Listening for commands on port {DEFAULT_PORT}")

    def _build_command_table(self):
        """Build command dispatch tables. Read commands run on socket thread, write commands on main thread."""
        self._read_commands = {
            "get_session_info": self._get_session_info,
            "get_track_info": self._get_track_info,
            "get_browser_tree": self.get_browser_tree,
            "get_browser_items_at_path": self.get_browser_items_at_path,
            "get_browser_item": self._get_browser_item,
            "get_browser_categories": self._get_browser_categories,
            "get_browser_items": self._get_browser_items,
            "ping": self._ping,
        }
        self._write_commands = {
            "create_midi_track": self._create_midi_track,
            "set_track_name": self._set_track_name,
            "create_clip": self._create_clip,
            "add_notes_to_clip": self._add_notes_to_clip,
            "set_clip_name": self._set_clip_name,
            "set_tempo": self._set_tempo,
            "fire_clip": self._fire_clip,
            "stop_clip": self._stop_clip,
            "start_playback": self._start_playback,
            "stop_playback": self._stop_playback,
            "load_browser_item": self._load_browser_item,
            "set_device_parameter": self._set_device_parameter,
            "load_instrument_or_effect": self._load_instrument_or_effect,
        }

    def disconnect(self):
        """Called when Ableton closes or the control surface is removed"""
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
                # We don't join them as they might be stuck
                self.log_message("Client thread still alive during disconnect")

        super().disconnect()
        self.log_message("AbletonMCP disconnected")

    def start_server(self):
        """Start the socket server in a separate thread"""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((HOST, DEFAULT_PORT))
            self.server.listen(5)  # Allow up to 5 pending connections

            self.running = True
            self.server_thread = threading.Thread(target=self._server_thread)
            self.server_thread.daemon = True
            self.server_thread.start()

            self.log_message(f"Server started on port {DEFAULT_PORT}")
        except Exception as e:
            self.log_message(f"Error starting server: {e}")
            self.show_message(f"AbletonMCP: Error starting server - {e}")

    def _server_thread(self):
        """Server thread implementation - handles client connections"""
        try:
            self.log_message("Server thread started")
            # Set a timeout to allow regular checking of running flag
            self.server.settimeout(1.0)

            while self.running:
                try:
                    # Accept connections with timeout
                    client, address = self.server.accept()
                    self.log_message(f"Connection accepted from {address}")
                    self.show_message("AbletonMCP: Client connected")

                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                    # Keep track of client threads
                    self.client_threads.append(client_thread)

                    # Clean up finished client threads
                    self.client_threads = [t for t in self.client_threads if t.is_alive()]

                except socket.timeout:
                    # No connection yet, just continue
                    continue
                except Exception as e:
                    if self.running:  # Only log if still running
                        self.log_message(f"Server accept error: {e}")
                    time.sleep(0.5)

            self.log_message("Server thread stopped")
        except Exception as e:
            self.log_message(f"Server thread error: {e}")

    def _handle_client(self, client):
        """Handle communication with a connected client.

        Uses length-prefix framing for reliable message boundaries.
        Each message is a 4-byte big-endian length header followed by
        a UTF-8 JSON payload.
        """
        self.log_message("Client handler started")
        client.settimeout(None)  # No timeout for client socket

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

        Commands that manage their own threading (load_browser_item,
        load_instrument_or_effect) are called directly since they use
        schedule_message internally for multi-tick operations.
        """
        # These commands handle their own main-thread scheduling
        self_scheduling_commands = ("load_browser_item", "load_instrument_or_effect")
        if command_type in self_scheduling_commands:
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
            # If we're already on the main thread, execute directly
            main_thread_task()

        timeout = 30.0 if command_type in ("load_browser_item", "load_instrument_or_effect") else 10.0
        try:
            return response_queue.get(timeout=timeout)
        except queue.Empty:
            return {"status": "error", "message": f"Timeout waiting for {command_type} to complete"}

    # Command implementations

    def _ping(self, params=None):
        """Respond to health check with protocol and Ableton version."""
        try:
            ableton_version = str(self.application().get_major_version())
        except Exception:
            ableton_version = "unknown"
        return {
            "pong": True,
            "version": "1.0",
            "ableton_version": ableton_version,
        }

    def _get_session_info(self, params=None):
        """Get information about the current session"""
        try:
            result = {
                "tempo": self._song.tempo,
                "signature_numerator": self._song.signature_numerator,
                "signature_denominator": self._song.signature_denominator,
                "track_count": len(self._song.tracks),
                "return_track_count": len(self._song.return_tracks),
                "master_track": {
                    "name": "Master",
                    "volume": self._song.master_track.mixer_device.volume.value,
                    "panning": self._song.master_track.mixer_device.panning.value
                }
            }
            return result
        except Exception as e:
            self.log_message(f"Error getting session info: {e}")
            raise

    def _get_track_info(self, params):
        """Get information about a track"""
        track_index = params.get("track_index", 0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            # Get clip slots
            clip_slots = []
            for slot_index, slot in enumerate(track.clip_slots):
                clip_info = None
                if slot.has_clip:
                    clip = slot.clip
                    clip_info = {
                        "name": clip.name,
                        "length": clip.length,
                        "is_playing": clip.is_playing,
                        "is_recording": clip.is_recording
                    }

                clip_slots.append({
                    "index": slot_index,
                    "has_clip": slot.has_clip,
                    "clip": clip_info
                })

            # Get devices
            devices = []
            for device_index, device in enumerate(track.devices):
                devices.append({
                    "index": device_index,
                    "name": device.name,
                    "class_name": device.class_name,
                    "type": self._get_device_type(device)
                })

            result = {
                "index": track_index,
                "name": track.name,
                "is_audio_track": track.has_audio_input,
                "is_midi_track": track.has_midi_input,
                "mute": track.mute,
                "solo": track.solo,
                "arm": track.arm,
                "volume": track.mixer_device.volume.value,
                "panning": track.mixer_device.panning.value,
                "clip_slots": clip_slots,
                "devices": devices
            }
            return result
        except Exception as e:
            self.log_message(f"Error getting track info: {e}")
            raise

    def _create_midi_track(self, params):
        """Create a new MIDI track at the specified index"""
        index = params.get("index", -1)
        try:
            # Create the track
            self._song.create_midi_track(index)

            # Get the new track
            new_track_index = len(self._song.tracks) - 1 if index == -1 else index
            new_track = self._song.tracks[new_track_index]

            result = {
                "index": new_track_index,
                "name": new_track.name
            }
            return result
        except Exception as e:
            self.log_message(f"Error creating MIDI track: {e}")
            raise


    def _set_track_name(self, params):
        """Set the name of a track"""
        track_index = params.get("track_index", 0)
        name = params.get("name", "")
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            # Set the name
            track = self._song.tracks[track_index]
            track.name = name

            result = {
                "name": track.name
            }
            return result
        except Exception as e:
            self.log_message(f"Error setting track name: {e}")
            raise

    def _create_clip(self, params):
        """Create a new MIDI clip in the specified track and clip slot"""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        length = params.get("length", 4.0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            # Check if the clip slot already has a clip
            if clip_slot.has_clip:
                raise Exception("Clip slot already has a clip")

            # Create the clip
            clip_slot.create_clip(length)

            result = {
                "name": clip_slot.clip.name,
                "length": clip_slot.clip.length
            }
            return result
        except Exception as e:
            self.log_message(f"Error creating clip: {e}")
            raise

    def _add_notes_to_clip(self, params):
        """Add MIDI notes to a clip"""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        notes = params.get("notes", [])
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip

            # Convert note data to Live's format
            live_notes = []
            for note in notes:
                pitch = note.get("pitch", 60)
                start_time = note.get("start_time", 0.0)
                duration = note.get("duration", 0.25)
                velocity = note.get("velocity", 100)
                mute = note.get("mute", False)

                live_notes.append((pitch, start_time, duration, velocity, mute))

            # Add the notes
            clip.set_notes(tuple(live_notes))

            result = {
                "note_count": len(notes)
            }
            return result
        except Exception as e:
            self.log_message(f"Error adding notes to clip: {e}")
            raise

    def _set_clip_name(self, params):
        """Set the name of a clip"""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        name = params.get("name", "")
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip = clip_slot.clip
            clip.name = name

            result = {
                "name": clip.name
            }
            return result
        except Exception as e:
            self.log_message(f"Error setting clip name: {e}")
            raise

    def _set_tempo(self, params):
        """Set the tempo of the session"""
        tempo = params.get("tempo", 120.0)
        try:
            self._song.tempo = tempo

            result = {
                "tempo": self._song.tempo
            }
            return result
        except Exception as e:
            self.log_message(f"Error setting tempo: {e}")
            raise

    def _fire_clip(self, params):
        """Fire a clip"""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            if not clip_slot.has_clip:
                raise Exception("No clip in slot")

            clip_slot.fire()

            result = {
                "fired": True
            }
            return result
        except Exception as e:
            self.log_message(f"Error firing clip: {e}")
            raise

    def _stop_clip(self, params):
        """Stop a clip"""
        track_index = params.get("track_index", 0)
        clip_index = params.get("clip_index", 0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if clip_index < 0 or clip_index >= len(track.clip_slots):
                raise IndexError("Clip index out of range")

            clip_slot = track.clip_slots[clip_index]

            clip_slot.stop()

            result = {
                "stopped": True
            }
            return result
        except Exception as e:
            self.log_message(f"Error stopping clip: {e}")
            raise


    def _start_playback(self, params=None):
        """Start playing the session"""
        try:
            self._song.start_playing()

            result = {
                "playing": self._song.is_playing
            }
            return result
        except Exception as e:
            self.log_message(f"Error starting playback: {e}")
            raise

    def _stop_playback(self, params=None):
        """Stop playing the session"""
        try:
            self._song.stop_playing()

            result = {
                "playing": self._song.is_playing
            }
            return result
        except Exception as e:
            self.log_message(f"Error stopping playback: {e}")
            raise

    def _set_device_parameter(self, params):
        """Set a device parameter value"""
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        parameter_index = params.get("parameter_index", 0)
        value = params.get("value", 0.0)
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")

            track = self._song.tracks[track_index]

            if device_index < 0 or device_index >= len(track.devices):
                raise IndexError("Device index out of range")

            device = track.devices[device_index]
            parameters = device.parameters

            if parameter_index < 0 or parameter_index >= len(parameters):
                raise IndexError("Parameter index out of range")

            param = parameters[parameter_index]
            param.value = value

            return {
                "device_name": device.name,
                "parameter_name": param.name,
                "value": param.value,
            }
        except Exception as e:
            self.log_message(f"Error setting device parameter: {e}")
            raise

    def _get_browser_item(self, params):
        """Get a browser item by URI or path"""
        uri = params.get("uri", None)
        path = params.get("path", None)
        try:
            # Access the application's browser instance instead of creating a new one
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")

            result = {
                "uri": uri,
                "path": path,
                "found": False
            }

            # Try to find by URI first if provided
            if uri:
                item = self._find_browser_item_by_uri(app.browser, uri)
                if item:
                    result["found"] = True
                    result["item"] = {
                        "name": item.name,
                        "is_folder": item.is_folder,
                        "is_device": item.is_device,
                        "is_loadable": item.is_loadable,
                        "uri": item.uri
                    }
                    return result

            # If URI not provided or not found, try by path
            if path:
                # Parse the path and navigate to the specified item
                path_parts = path.split("/")

                # Use _CATEGORY_MAP dict for category resolution (fixes 'nstruments' typo)
                category_name = path_parts[0].lower()
                browser_attr = _CATEGORY_MAP.get(category_name, "")
                current_item = getattr(app.browser, browser_attr, None) if browser_attr else None

                if current_item is None:
                    # Default to instruments if not specified
                    current_item = app.browser.instruments
                    # Don't skip the first part in this case
                    path_parts = ["instruments"] + path_parts

                # Navigate through the path
                for i in range(1, len(path_parts)):
                    part = path_parts[i]
                    if not part:  # Skip empty parts
                        continue

                    found = False
                    for child in current_item.children:
                        if child.name.lower() == part.lower():
                            current_item = child
                            found = True
                            break

                    if not found:
                        result["error"] = f"Path part '{part}' not found"
                        return result

                # Found the item
                result["found"] = True
                result["item"] = {
                    "name": current_item.name,
                    "is_folder": current_item.is_folder,
                    "is_device": current_item.is_device,
                    "is_loadable": current_item.is_loadable,
                    "uri": current_item.uri
                }

            return result
        except Exception as e:
            self.log_message(f"Error getting browser item: {e}")
            self.log_message(traceback.format_exc())
            raise

    def _get_browser_categories(self, params):
        """Get browser categories.

        Args:
            params: dict with optional 'category_type' key (default 'all')
        """
        category_type = params.get("category_type", "all") if params else "all"
        # Delegate to get_browser_tree which handles category enumeration
        return self.get_browser_tree({"category_type": category_type})

    def _get_browser_items(self, params):
        """Get browser items at a path.

        Args:
            params: dict with 'path' key and optional 'item_type' key
        """
        path = params.get("path", "") if params else ""
        # Delegate to get_browser_items_at_path
        return self.get_browser_items_at_path({"path": path})

    def _load_browser_item(self, params):
        """Load a browser item onto a track by its URI.

        Uses same-callback pattern: selected_track assignment and load_item
        call happen in the same schedule_message callback to prevent the
        race condition where instruments load on the wrong track.

        Includes device count verification and one automatic retry.
        """
        track_index = params.get("track_index", 0)
        item_uri = params.get("item_uri", "")

        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")

        track = self._song.tracks[track_index]

        # Access the application's browser instance
        app = self.application()

        # Find the browser item by URI (check cache first)
        item = None
        if item_uri in self._browser_path_cache:
            try:
                cached = self._browser_path_cache[item_uri]
                # Validate the cached item is still accessible
                _ = cached.name
                item = cached
            except (AttributeError, KeyError, RuntimeError):
                # Stale cache entry -- remove it
                del self._browser_path_cache[item_uri]

        if item is None:
            item = self._find_browser_item_by_uri(app.browser, item_uri)
            if item:
                self._browser_path_cache[item_uri] = item

        if not item:
            raise ValueError(f"Browser item with URI '{item_uri}' not found")

        response_queue = queue.Queue()
        devices_before = len(track.devices)

        def do_load(retries_remaining=1):
            """Load item on main thread with same-callback pattern."""
            try:
                # CRITICAL: selected_track and load_item in the SAME callback
                self._song.view.selected_track = track
                app.browser.load_item(item)

                # Schedule verification on next tick
                self.schedule_message(
                    1,
                    lambda: self._verify_load(
                        track, devices_before, item_uri, item.name,
                        response_queue, retries_remaining
                    ),
                )
            except Exception as e:
                self.log_message(f"[ERROR] do_load failed: {e}")
                self.log_message(traceback.format_exc())
                response_queue.put({"status": "error", "message": str(e)})

        try:
            self.schedule_message(0, do_load)
        except AssertionError:
            do_load()

        try:
            result = response_queue.get(timeout=30.0)
            if result.get("status") == "error":
                raise Exception(result.get("message", "Unknown load error"))
            return result.get("result", result)
        except queue.Empty:
            return {"loaded": False, "error": "Timeout waiting for instrument load"}

    def _verify_load(self, track, devices_before, item_uri, item_name,
                     response_queue, retries_remaining):
        """Verify device count increased after load, retry once if not."""
        try:
            devices_after_count = len(track.devices)
            if devices_after_count > devices_before:
                # Success -- report device chain
                device_chain = [d.name for d in track.devices]
                response_queue.put({
                    "status": "success",
                    "result": {
                        "loaded": True,
                        "item_name": item_name,
                        "track_name": track.name,
                        "uri": item_uri,
                        "devices": device_chain,
                        "device_count": devices_after_count,
                    },
                })
            elif retries_remaining > 0:
                # Retry -- schedule another load attempt
                self.log_message(
                    f"[WARN] Load verify failed for {item_uri}, retrying "
                    f"({retries_remaining} retries left)"
                )
                app = self.application()
                item = self._browser_path_cache.get(item_uri)
                if not item:
                    item = self._find_browser_item_by_uri(app.browser, item_uri)

                if item:
                    def retry_load():
                        try:
                            self._song.view.selected_track = track
                            app.browser.load_item(item)
                            self.schedule_message(
                                1,
                                lambda: self._verify_load(
                                    track, devices_before, item_uri, item_name,
                                    response_queue, retries_remaining - 1
                                ),
                            )
                        except Exception as e:
                            response_queue.put({"status": "error", "message": str(e)})

                    self.schedule_message(0, retry_load)
                else:
                    response_queue.put({
                        "status": "error",
                        "message": f"Browser item '{item_uri}' not found on retry",
                    })
            else:
                # No retries left -- report failure
                device_chain = [d.name for d in track.devices]
                response_queue.put({
                    "status": "error",
                    "message": (
                        f"Load verification failed for '{item_name}' on track "
                        f"'{track.name}'. Device count unchanged "
                        f"({devices_after_count}). Devices: {device_chain}"
                    ),
                })
        except Exception as e:
            self.log_message(f"[ERROR] _verify_load: {e}")
            self.log_message(traceback.format_exc())
            response_queue.put({"status": "error", "message": str(e)})

    def _load_instrument_or_effect(self, params):
        """Load an instrument or effect by URI. Delegates to _load_browser_item."""
        # Normalize params: the server may send 'uri' instead of 'item_uri'
        if "item_uri" not in params and "uri" in params:
            params["item_uri"] = params["uri"]
        return self._load_browser_item(params)

    def _find_browser_item_by_uri(self, browser_or_item, uri, max_depth=10, current_depth=0):
        """Find a browser item by its URI"""
        try:
            # Check if this is the item we're looking for
            if hasattr(browser_or_item, 'uri') and browser_or_item.uri == uri:
                return browser_or_item

            # Stop recursion if we've reached max depth
            if current_depth >= max_depth:
                return None

            # Check if this is a browser with root categories
            if hasattr(browser_or_item, 'instruments'):
                # Check all main categories
                categories = [
                    browser_or_item.instruments,
                    browser_or_item.sounds,
                    browser_or_item.drums,
                    browser_or_item.audio_effects,
                    browser_or_item.midi_effects
                ]

                for category in categories:
                    item = self._find_browser_item_by_uri(category, uri, max_depth, current_depth + 1)
                    if item:
                        return item

                return None

            # Check if this item has children
            if hasattr(browser_or_item, 'children') and browser_or_item.children:
                for child in browser_or_item.children:
                    item = self._find_browser_item_by_uri(child, uri, max_depth, current_depth + 1)
                    if item:
                        return item

            return None
        except Exception as e:
            self.log_message(f"Error finding browser item by URI: {e}")
            return None

    # Helper methods

    def _get_device_type(self, device):
        """Get the type of a device"""
        try:
            # Simple heuristic - in a real implementation you'd look at the device class
            if device.can_have_drum_pads:
                return "drum_machine"
            elif device.can_have_chains:
                return "rack"
            elif "instrument" in device.class_display_name.lower():
                return "instrument"
            elif "audio_effect" in device.class_name.lower():
                return "audio_effect"
            elif "midi_effect" in device.class_name.lower():
                return "midi_effect"
            else:
                return "unknown"
        except Exception as e:
            self.log_message(f"[ERROR] Could not determine device type: {e}")
            return "unknown"

    def get_browser_tree(self, params=None):
        """
        Get a simplified tree of browser categories.

        Args:
            params: dict with optional 'category_type' key (default 'all')

        Returns:
            Dictionary with the browser tree structure
        """
        category_type = "all"
        if params:
            if isinstance(params, dict):
                category_type = params.get("category_type", "all")
            elif isinstance(params, str):
                category_type = params
        try:
            # Access the application's browser instance instead of creating a new one
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")

            # Check if browser is available
            if not hasattr(app, 'browser') or app.browser is None:
                raise RuntimeError("Browser is not available in the Live application")

            # Log available browser attributes to help diagnose issues
            browser_attrs = [attr for attr in dir(app.browser) if not attr.startswith('_')]
            self.log_message(f"Available browser attributes: {browser_attrs}")

            result = {
                "type": category_type,
                "categories": [],
                "available_categories": browser_attrs
            }

            # Helper function to process a browser item and its children
            def process_item(item, depth=0):
                if not item:
                    return None

                result = {
                    "name": item.name if hasattr(item, 'name') else "Unknown",
                    "is_folder": hasattr(item, 'children') and bool(item.children),
                    "is_device": hasattr(item, 'is_device') and item.is_device,
                    "is_loadable": hasattr(item, 'is_loadable') and item.is_loadable,
                    "uri": item.uri if hasattr(item, 'uri') else None,
                    "children": []
                }


                return result

            # Process based on category type and available attributes
            if (category_type == "all" or category_type == "instruments") and hasattr(app.browser, 'instruments'):
                try:
                    instruments = process_item(app.browser.instruments)
                    if instruments:
                        instruments["name"] = "Instruments"  # Ensure consistent naming
                        result["categories"].append(instruments)
                except Exception as e:
                    self.log_message(f"Error processing instruments: {e}")

            if (category_type == "all" or category_type == "sounds") and hasattr(app.browser, 'sounds'):
                try:
                    sounds = process_item(app.browser.sounds)
                    if sounds:
                        sounds["name"] = "Sounds"  # Ensure consistent naming
                        result["categories"].append(sounds)
                except Exception as e:
                    self.log_message(f"Error processing sounds: {e}")

            if (category_type == "all" or category_type == "drums") and hasattr(app.browser, 'drums'):
                try:
                    drums = process_item(app.browser.drums)
                    if drums:
                        drums["name"] = "Drums"  # Ensure consistent naming
                        result["categories"].append(drums)
                except Exception as e:
                    self.log_message(f"Error processing drums: {e}")

            if (category_type == "all" or category_type == "audio_effects") and hasattr(app.browser, 'audio_effects'):
                try:
                    audio_effects = process_item(app.browser.audio_effects)
                    if audio_effects:
                        audio_effects["name"] = "Audio Effects"  # Ensure consistent naming
                        result["categories"].append(audio_effects)
                except Exception as e:
                    self.log_message(f"Error processing audio_effects: {e}")

            if (category_type == "all" or category_type == "midi_effects") and hasattr(app.browser, 'midi_effects'):
                try:
                    midi_effects = process_item(app.browser.midi_effects)
                    if midi_effects:
                        midi_effects["name"] = "MIDI Effects"
                        result["categories"].append(midi_effects)
                except Exception as e:
                    self.log_message(f"Error processing midi_effects: {e}")

            # Try to process other potentially available categories
            for attr in browser_attrs:
                if attr not in ['instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects'] and \
                   (category_type == "all" or category_type == attr):
                    try:
                        item = getattr(app.browser, attr)
                        if hasattr(item, 'children') or hasattr(item, 'name'):
                            category = process_item(item)
                            if category:
                                category["name"] = attr.capitalize()
                                result["categories"].append(category)
                    except Exception as e:
                        self.log_message(f"Error processing {attr}: {e}")

            self.log_message(f"Browser tree generated for {category_type} with {len(result['categories'])} root categories")
            return result

        except Exception as e:
            self.log_message(f"Error getting browser tree: {e}")
            self.log_message(traceback.format_exc())
            raise

    def get_browser_items_at_path(self, params):
        """
        Get browser items at a specific path.

        Args:
            params: dict with 'path' key, or a string path
                   Path format: "category/folder/subfolder"
                   where category is one of: instruments, sounds, drums, audio_effects, midi_effects

        Returns:
            Dictionary with items at the specified path
        """
        if isinstance(params, str):
            path = params
        else:
            path = params.get("path", "") if params else ""
        try:
            # Access the application's browser instance instead of creating a new one
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")

            # Check if browser is available
            if not hasattr(app, 'browser') or app.browser is None:
                raise RuntimeError("Browser is not available in the Live application")

            # Log available browser attributes to help diagnose issues
            browser_attrs = [attr for attr in dir(app.browser) if not attr.startswith('_')]
            self.log_message(f"Available browser attributes: {browser_attrs}")

            # Parse the path
            path_parts = path.split("/")
            if not path_parts:
                raise ValueError("Invalid path")

            # Use _CATEGORY_MAP dict for category resolution (fixes 'nstruments' typo)
            root_category = path_parts[0].lower()
            browser_attr = _CATEGORY_MAP.get(root_category, "")
            current_item = getattr(app.browser, browser_attr, None) if browser_attr else None

            if current_item is None:
                # Try to find the category in other browser attributes
                found = False
                for attr in browser_attrs:
                    if attr.lower() == root_category:
                        try:
                            current_item = getattr(app.browser, attr)
                            found = True
                            break
                        except Exception as e:
                            self.log_message(f"Error accessing browser attribute {attr}: {e}")

                if not found:
                    # If we still haven't found the category, return available categories
                    return {
                        "path": path,
                        "error": f"Unknown or unavailable category: {root_category}",
                        "available_categories": browser_attrs,
                        "items": []
                    }

            # Navigate through the path
            for i in range(1, len(path_parts)):
                part = path_parts[i]
                if not part:  # Skip empty parts
                    continue

                if not hasattr(current_item, 'children'):
                    return {
                        "path": path,
                        "error": f"Item at '{'/'.join(path_parts[:i])}' has no children",
                        "items": []
                    }

                found = False
                for child in current_item.children:
                    if hasattr(child, 'name') and child.name.lower() == part.lower():
                        current_item = child
                        found = True
                        break

                if not found:
                    return {
                        "path": path,
                        "error": f"Path part '{part}' not found",
                        "items": []
                    }

            # Get items at the current path
            items = []
            if hasattr(current_item, 'children'):
                for child in current_item.children:
                    item_info = {
                        "name": child.name if hasattr(child, 'name') else "Unknown",
                        "is_folder": hasattr(child, 'children') and bool(child.children),
                        "is_device": hasattr(child, 'is_device') and child.is_device,
                        "is_loadable": hasattr(child, 'is_loadable') and child.is_loadable,
                        "uri": child.uri if hasattr(child, 'uri') else None
                    }
                    items.append(item_info)

            result = {
                "path": path,
                "name": current_item.name if hasattr(current_item, 'name') else "Unknown",
                "uri": current_item.uri if hasattr(current_item, 'uri') else None,
                "is_folder": hasattr(current_item, 'children') and bool(current_item.children),
                "is_device": hasattr(current_item, 'is_device') and current_item.is_device,
                "is_loadable": hasattr(current_item, 'is_loadable') and current_item.is_loadable,
                "items": items
            }

            self.log_message(f"Retrieved {len(items)} items at path: {path}")
            return result

        except Exception as e:
            self.log_message(f"Error getting browser items at path: {e}")
            self.log_message(traceback.format_exc())
            raise
