"""Thread-safety tests for AbletonConnection.send_command."""

import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from MCP_Server.connection import AbletonConnection


class TestSendLockExists(unittest.TestCase):
    """Test 2: A fresh AbletonConnection instance has a _send_lock attribute."""

    def test_send_lock_is_threading_lock(self):
        conn = AbletonConnection(host="localhost", port=9877)
        self.assertTrue(
            hasattr(conn, "_send_lock"),
            "AbletonConnection must have a _send_lock attribute",
        )
        self.assertIsInstance(
            conn._send_lock,
            type(threading.Lock()),
            "_send_lock must be a threading.Lock instance",
        )


class TestSendCommandHappyPath(unittest.TestCase):
    """Test 3: Existing send_command happy-path returns correct response dict."""

    def test_send_command_returns_result(self):
        conn = AbletonConnection(host="localhost", port=9877)
        mock_sock = MagicMock()
        conn.sock = mock_sock

        fake_response = {"status": "ok", "result": {"bpm": 120}}

        with (
            patch("MCP_Server.connection.send_message") as mock_send,
            patch("MCP_Server.connection.recv_message", return_value=fake_response) as mock_recv,
        ):
            result = conn.send_command("get_session_info")

        self.assertEqual(result, {"bpm": 120})
        mock_send.assert_called_once()
        mock_recv.assert_called_once()


class TestConcurrentSendCommandSerializes(unittest.TestCase):
    """Test 1: Two threads calling send_command concurrently never interleave."""

    def test_no_interleaving_under_concurrency(self):
        """Verify that send/recv pairs are never interleaved across threads.

        Strategy: patch send_message and recv_message at the module level
        (before threads start) so both threads share the same mocks. Thread 0
        signals thread 1 from inside fake_send_message (while _send_lock is
        held), so thread 1 attempts to acquire the lock while thread 0 is
        mid-I/O. The lock must serialize them: log is ["send","recv","send","recv"]
        not ["send","send","recv","recv"].
        """
        conn = AbletonConnection(host="localhost", port=9877)
        mock_sock = MagicMock()
        conn.sock = mock_sock

        call_log = []
        log_lock = threading.Lock()

        # thread 0 sets this inside fake_send_message while holding _send_lock
        start_event = threading.Event()

        results = {}
        errors = {}

        def fake_send_message(sock, message):
            with log_lock:
                call_log.append("send")
            # Signal thread 1 to proceed (thread 0 still holds _send_lock here)
            start_event.set()
            # Give thread 1 time to block on _send_lock before recv runs
            time.sleep(0.05)

        def fake_recv_message(sock, timeout=None):
            with log_lock:
                call_log.append("recv")
            return {"status": "ok", "result": {}}

        def worker_0():
            try:
                results[0] = conn.send_command("ping")
            except Exception as e:
                errors[0] = e

        def worker_1():
            start_event.wait(timeout=5)
            try:
                results[1] = conn.send_command("ping")
            except Exception as e:
                errors[1] = e

        with (
            patch("MCP_Server.connection.send_message", side_effect=fake_send_message),
            patch("MCP_Server.connection.recv_message", side_effect=fake_recv_message),
        ):
            t0 = threading.Thread(target=worker_0)
            t1 = threading.Thread(target=worker_1)
            t0.start()
            t1.start()
            t0.join(timeout=5)
            t1.join(timeout=5)

        # No thread should have errored
        for thread_id, err in errors.items():
            self.fail(f"Thread {thread_id} raised: {err}")

        # Both threads completed
        self.assertEqual(
            len(results), 2, f"Not all threads finished. results={results}, errors={errors}"
        )

        # call_log must be ["send", "recv", "send", "recv"]
        # Any interleaving ["send", "send", ...] means the lock is missing.
        self.assertEqual(len(call_log), 4, f"Expected 4 log entries, got: {call_log}")

        for i in range(0, len(call_log), 2):
            self.assertEqual(
                call_log[i],
                "send",
                f"Expected 'send' at index {i}, got '{call_log[i]}'. Log: {call_log}",
            )
            self.assertEqual(
                call_log[i + 1],
                "recv",
                f"Expected 'recv' at index {i+1}, got '{call_log[i+1]}'. Log: {call_log}",
            )


if __name__ == "__main__":
    unittest.main()
