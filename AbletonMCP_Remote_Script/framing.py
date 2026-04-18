"""Length-prefix framing protocol for Ableton socket communication.

This is the canonical framing implementation for the Remote Script runtime.
The server-side canonical source is MCP_Server/protocol.py.

Both files MUST remain byte-for-byte identical in their framing logic.
If you change the framing protocol (e.g., max message size, header format),
update BOTH files and verify with tests/test_protocol.py::TestProtocolSync.
"""

import json
import socket
import struct


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
