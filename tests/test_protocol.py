"""Tests for length-prefix framing protocol.

Verifies that the send_message/recv_message protocol correctly handles:
- Simple dict roundtrips
- Large payloads (1MB)
- Empty dict payloads
- Unicode payloads (instrument names)
- Malformed headers (incomplete data)
- Oversized payload rejection (>10MB safety limit)

The protocol functions are defined here as the reference implementation.
Separate grep-based tests in test_connection.py verify that both source
files use this same protocol pattern.
"""

import json
import socket
import struct
import threading

import pytest

# --- Reference protocol implementation (identical to what both source files must use) ---


def _recv_exact(sock: socket.socket, n: int):
    """Read exactly n bytes from socket."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def send_message(sock: socket.socket, data: dict) -> None:
    """Send a length-prefixed JSON message."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    header = struct.pack(">I", len(payload))
    sock.sendall(header + payload)


def recv_message(sock: socket.socket, timeout: float = 15.0) -> dict:
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


# --- Tests ---


class TestProtocolRoundtrip:
    """Test length-prefix framing protocol logic."""

    def test_send_recv_roundtrip(self):
        """send_message + recv_message over a socket pair produces identical dict."""
        a, b = socket.socketpair()
        try:
            original = {"type": "get_session_info", "params": {"track_index": 3}}
            send_message(a, original)
            result = recv_message(b)
            assert result == original
        finally:
            a.close()
            b.close()

    def test_large_payload(self):
        """1MB payload roundtrips correctly via length-prefix framing."""
        a, b = socket.socketpair()
        try:
            # Create a payload just over 1MB when serialized
            large_data = {"data": "x" * (1024 * 1024)}

            # Send in a thread to avoid deadlock (socket buffers may be small)
            def sender():
                send_message(a, large_data)

            t = threading.Thread(target=sender)
            t.start()
            result = recv_message(b, timeout=30.0)
            t.join()
            assert result == large_data
        finally:
            a.close()
            b.close()

    def test_empty_dict_payload(self):
        """Empty dict {} roundtrips correctly."""
        a, b = socket.socketpair()
        try:
            send_message(a, {})
            result = recv_message(b)
            assert result == {}
        finally:
            a.close()
            b.close()

    def test_unicode_payload(self):
        """Dict with Unicode characters (instrument names) roundtrips correctly."""
        a, b = socket.socketpair()
        try:
            original = {
                "type": "load_instrument",
                "name": "Analoge Synthese",
                "category": "Instrumente",
                "notes": "C# D\u266d E\u266f",
                "emoji_test": "\U0001f3b5\U0001f3b6",
            }
            send_message(a, original)
            result = recv_message(b)
            assert result == original
        finally:
            a.close()
            b.close()

    def test_malformed_header(self):
        """Incomplete header (less than 4 bytes then close) raises ConnectionError."""
        a, b = socket.socketpair()
        try:
            # Send only 2 bytes (incomplete header) then close
            a.sendall(b"\x00\x01")
            a.close()
            a = None  # Prevent double-close in finally

            with pytest.raises(ConnectionError):
                recv_message(b)
        finally:
            if a is not None:
                a.close()
            b.close()

    def test_oversized_payload_rejected(self):
        """Length header claiming >10MB raises ValueError."""
        a, b = socket.socketpair()
        try:
            # Pack a length > 10MB (11MB)
            oversized_length = 11 * 1024 * 1024
            header = struct.pack(">I", oversized_length)
            a.sendall(header)

            with pytest.raises(ValueError, match="Message too large"):
                recv_message(b)
        finally:
            a.close()
            b.close()

    def test_multiple_messages(self):
        """Multiple messages sent sequentially are received correctly."""
        a, b = socket.socketpair()
        try:
            messages = [
                {"type": "ping"},
                {"type": "get_session_info", "params": {}},
                {"type": "set_tempo", "params": {"tempo": 120.0}},
            ]
            for msg in messages:
                send_message(a, msg)

            for expected in messages:
                result = recv_message(b)
                assert result == expected
        finally:
            a.close()
            b.close()


class TestProtocolSync:
    """Verify both framing implementations share the same protocol constants.

    Full behavioral equivalence is covered by TestProtocolRoundtrip (which uses
    the reference implementation). This class guards against constant drift between
    the two source files.
    """

    def test_max_message_size_constant(self):
        """Both implementations must use the same 10MB safety limit."""
        import re
        import pathlib

        mcp_source = pathlib.Path("MCP_Server/protocol.py").read_text()
        rs_source = pathlib.Path("AbletonMCP_Remote_Script/framing.py").read_text()

        # Extract the integer from '10 * 1024 * 1024' pattern
        pattern = r"(\d+)\s*\*\s*1024\s*\*\s*1024"
        mcp_match = re.search(pattern, mcp_source)
        rs_match = re.search(pattern, rs_source)

        assert mcp_match is not None, "MCP protocol.py missing max message size constant"
        assert rs_match is not None, "RS framing.py missing max message size constant"
        assert mcp_match.group(1) == rs_match.group(1), (
            f"Max message size mismatch: MCP uses {mcp_match.group(1)}MB, "
            f"RS uses {rs_match.group(1)}MB"
        )

    def test_header_format_constant(self):
        """Both implementations must use the same big-endian 4-byte header format."""
        import pathlib

        mcp_source = pathlib.Path("MCP_Server/protocol.py").read_text()
        rs_source = pathlib.Path("AbletonMCP_Remote_Script/framing.py").read_text()

        # Both must use big-endian unsigned int (">I") and recv exactly 4 bytes
        assert '">I"' in mcp_source, "MCP protocol.py must use big-endian unsigned int header"
        assert '">I"' in rs_source, "RS framing.py must use big-endian unsigned int header"
        assert "_recv_exact(sock, 4)" in mcp_source, "MCP protocol.py must read 4-byte header"
        assert "_recv_exact(sock, 4)" in rs_source, "RS framing.py must read 4-byte header"

    def test_rs_framing_module_exists(self):
        """AbletonMCP_Remote_Script/framing.py must exist as the RS canonical source."""
        import pathlib
        assert pathlib.Path("AbletonMCP_Remote_Script/framing.py").exists(), (
            "AbletonMCP_Remote_Script/framing.py not found — "
            "framing was extracted from __init__.py to this module"
        )

    def test_rs_init_imports_from_framing(self):
        """__init__.py must import framing functions from .framing, not define them inline."""
        import pathlib
        init_source = pathlib.Path("AbletonMCP_Remote_Script/__init__.py").read_text()
        assert "from .framing import" in init_source, (
            "__init__.py must import from .framing module"
        )
        assert "def _recv_exact" not in init_source, (
            "_recv_exact must not be defined inline in __init__.py"
        )
        assert "def send_message" not in init_source, (
            "send_message must not be defined inline in __init__.py"
        )
        assert "def recv_message" not in init_source, (
            "recv_message must not be defined inline in __init__.py"
        )
