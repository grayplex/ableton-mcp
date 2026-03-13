"""Tests verifying thread-safe connection access and protocol adoption in source files.

These tests grep the actual source files to confirm:
- _connection_lock exists and is a threading.Lock in server.py
- send_command does not contain time.sleep calls
- server.py does not contain sendall(b'') pattern
- "ping" command handler exists in the Remote Script
- Both files use struct.pack for length-prefix framing
"""

import re


class TestConnectionLock:
    """Verify threading.Lock protects connection access."""

    def test_lock_serializes_access(self, server_source):
        """Verify _connection_lock exists and is a threading.Lock in server.py source."""
        # _connection_lock variable must exist
        assert "_connection_lock" in server_source, (
            "_connection_lock variable not found in server.py"
        )

        # Must be assigned as threading.Lock()
        assert "threading.Lock()" in server_source, (
            "threading.Lock() not found in server.py -- _connection_lock must use threading.Lock"
        )

        # Must be used with 'with' statement in get_ableton_connection
        assert "with _connection_lock" in server_source, (
            "'with _connection_lock' not found in server.py -- "
            "get_ableton_connection must use the lock as a context manager"
        )


class TestNoArtificialDelays:
    """Verify no time.sleep in send/receive path."""

    def test_no_time_sleep_in_send_command(self, server_source):
        """Verify send_command method does not contain time.sleep calls."""
        # Extract the send_command method body
        # Find "def send_command" and go until the next unindented "def "
        lines = server_source.splitlines()
        in_send_command = False
        send_command_body = []
        indent_level = None

        for line in lines:
            if "def send_command" in line:
                in_send_command = True
                # Calculate the indent level of the def line
                indent_level = len(line) - len(line.lstrip())
                send_command_body.append(line)
                continue

            if in_send_command:
                # Check if we've hit the next method/function at same or lesser indent
                stripped = line.lstrip()
                if stripped.startswith("def ") and (len(line) - len(stripped)) <= indent_level:
                    break
                # Also break on class-level definitions or top-level code
                if stripped and not line[0].isspace() and not stripped.startswith("#"):
                    break
                send_command_body.append(line)

        send_command_text = "\n".join(send_command_body)
        assert "time.sleep" not in send_command_text, (
            f"Found time.sleep in send_command method body -- "
            f"artificial delays must be removed from send/receive path"
        )


class TestNoSendallEmpty:
    """Verify sendall(b'') liveness test is removed."""

    def test_no_sendall_empty_bytes(self, server_source):
        """Verify server.py does not contain sendall(b'') or sendall(b\"\") pattern."""
        assert "sendall(b'')" not in server_source, (
            "Found sendall(b'') in server.py -- "
            "empty-bytes liveness test must be replaced with real ping command"
        )
        assert 'sendall(b"")' not in server_source, (
            'Found sendall(b"") in server.py -- '
            "empty-bytes liveness test must be replaced with real ping command"
        )


class TestPingCommand:
    """Verify ping command handler exists in Remote Script."""

    def test_ping_command_exists(self, remote_script_source):
        """Verify 'ping' appears in the Remote Script's command dispatch."""
        # Check for ping as a command type in the dispatch
        assert re.search(r'["\']ping["\']', remote_script_source), (
            "'ping' command not found in Remote Script source -- "
            "a ping handler must be registered in the command dispatch"
        )


class TestStructPackAdoption:
    """Verify both files use struct.pack for length-prefix framing."""

    def test_remote_script_uses_struct_pack(self, remote_script_source):
        """Verify Remote Script uses struct.pack for framing."""
        assert "struct.pack" in remote_script_source, (
            "struct.pack not found in Remote Script -- "
            "length-prefix framing must use struct.pack('>I', ...)"
        )
        assert "import struct" in remote_script_source, (
            "'import struct' not found in Remote Script"
        )

    def test_server_uses_struct_pack(self, server_source):
        """Verify MCP server uses struct.pack for framing."""
        assert "struct.pack" in server_source, (
            "struct.pack not found in server.py -- "
            "length-prefix framing must use struct.pack('>I', ...)"
        )
        assert "import struct" in server_source, (
            "'import struct' not found in server.py"
        )
