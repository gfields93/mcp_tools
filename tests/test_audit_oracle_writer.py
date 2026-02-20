"""Tests for audit/oracle_writer.py."""
import logging
import threading
from unittest.mock import MagicMock, patch

import pytest

from audit.oracle_writer import _write, write_audit_async
from audit.record import AuditRecord


def _make_record(**overrides) -> AuditRecord:
    defaults = dict(
        query_name="q",
        query_version=1,
        parameters={"id": 1},
        status="SUCCESS",
        error=None,
        row_count=0,
        duration_ms=10,
    )
    defaults.update(overrides)
    return AuditRecord(**defaults)


def _make_mock_conn():
    """Return a (conn, cur) pair wired up as context managers."""
    cur = MagicMock()
    cur_cm = MagicMock()
    cur_cm.__enter__ = MagicMock(return_value=cur)
    cur_cm.__exit__ = MagicMock(return_value=False)

    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor = MagicMock(return_value=cur_cm)
    return conn, cur


class TestWriteAuditAsync:
    def test_spawns_daemon_thread(self):
        with patch("threading.Thread") as mock_thread_cls:
            mock_thread = MagicMock()
            mock_thread_cls.return_value = mock_thread
            write_audit_async(_make_record())

        mock_thread_cls.assert_called_once()
        _, kwargs = mock_thread_cls.call_args
        assert kwargs.get("daemon") is True
        mock_thread.start.assert_called_once()

    def test_thread_target_is_write(self):
        with patch("threading.Thread") as mock_thread_cls:
            mock_thread_cls.return_value = MagicMock()
            write_audit_async(_make_record())

        _, kwargs = mock_thread_cls.call_args
        assert kwargs["target"] is _write

    def test_returns_none(self):
        with patch("threading.Thread") as mock_thread_cls:
            mock_thread_cls.return_value = MagicMock()
            result = write_audit_async(_make_record())
        assert result is None


class TestWriteSync:
    def test_inserts_into_audit_table(self):
        conn, cur = _make_mock_conn()
        with patch("audit.oracle_writer.get_connection", return_value=conn):
            _write(_make_record())

        cur.execute.assert_called_once()
        sql = cur.execute.call_args[0][0]
        assert "INSERT INTO query_audit_log" in sql

    def test_commits_after_insert(self):
        conn, _ = _make_mock_conn()
        with patch("audit.oracle_writer.get_connection", return_value=conn):
            _write(_make_record())
        conn.commit.assert_called_once()

    def test_passes_correct_values(self):
        conn, cur = _make_mock_conn()
        rec = _make_record(
            query_name="my_q",
            query_version=3,
            status="ERROR",
            error="boom",
            row_count=0,
            duration_ms=99,
            caller_id="u-1",
        )
        with patch("audit.oracle_writer.get_connection", return_value=conn):
            _write(rec)

        values = cur.execute.call_args[0][1]
        assert values[0] == "my_q"     # query_name
        assert values[1] == 3          # query_version
        assert values[3] == "ERROR"    # status
        assert values[4] == "boom"     # error
        assert values[5] == 0          # row_count
        assert values[6] == 99         # duration_ms
        assert values[7] == "u-1"      # caller_id

    def test_swallows_db_exception_and_logs_warning(self):
        # Patch _log directly: the 'audit' parent logger has propagate=False,
        # so caplog (which hooks the root logger) would never receive the record.
        with patch("audit.oracle_writer.get_connection", side_effect=RuntimeError("conn fail")), \
                patch("audit.oracle_writer._log") as mock_log:
            _write(_make_record())  # must NOT raise

        mock_log.warning.assert_called_once()
        assert "Audit write to Oracle failed" in mock_log.warning.call_args[0][0]

    def test_swallows_cursor_exception(self):
        conn, cur = _make_mock_conn()
        cur.execute.side_effect = Exception("ORA-00001")
        with patch("audit.oracle_writer.get_connection", return_value=conn), \
                patch("audit.oracle_writer._log") as mock_log:
            _write(_make_record())  # must NOT raise

        mock_log.warning.assert_called_once()
        assert "Audit write to Oracle failed" in mock_log.warning.call_args[0][0]
