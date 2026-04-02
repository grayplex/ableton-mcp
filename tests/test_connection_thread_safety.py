"""Thread-safety tests for AbletonConnection.send_command."""

import threading
import time
import unittest
from unittest.mock import MagicMock, call, patch

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

        Strategy: use a Barrier to make both threads start simultaneously.
        Record the order of send_message and recv_message calls. After both
        complete, verify that between any two consecutive send_message calls
        there is exactly one recv_message (i.e., strict alternation).
        """
        conn = AbletonConnection(host="localhost", port=9877)
        mock_sock = MagicMock()
        conn.sock = mock_sock

        call_log = []
        log_lock = threading.Lock()
        barrier = threading.Barrier(2)

        THREAD_COUNT = 2
        results = {}
        errors = {}

        def fake_send_message(sock, message):
            barrier.wait()  # Both threads reach here before either proceeds
            with log_lock:
                call_log.append("send")

        def fake_recv_message(sock, timeout=None):
            with log_lock:
                call_log.append("recv")
            return {"status": "ok", "result": {}}

        def worker(thread_id):
            try:
                with (
                    patch("MCP_Server.connection.send_message", side_effect=fake_send_message),
                    patch("MCP_Server.connection.recv_message", side_effect=fake_recv_message),
                ):
                    results[thread_id] = conn.send_command("ping")
            except Exception as e:
                errors[thread_id] = e

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(THREAD_COUNT)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # No thread should have errored
        for thread_id, err in errors.items():
            self.fail(f"Thread {thread_id} raised: {err}")

        # Both threads completed
        self.assertEqual(len(results), THREAD_COUNT)

        # call_log should be exactly ["send", "recv", "send", "recv"] (or reversed pair order)
        # The key invariant: no two consecutive sends without an intervening recv.
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
