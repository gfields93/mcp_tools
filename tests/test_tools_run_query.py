"""Tests for tools/run_query.py — Oracle and audit I/O are fully mocked."""
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

from db.registry import QueryRecord
from tools.run_query import run_query

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_SELECT_QUERY = QueryRecord(
    id=1,
    name="get_orders",
    description="desc",
    sql_text="SELECT * FROM orders WHERE id = :id",
    parameters=[{"name": "id", "type": "NUMBER", "required": True}],
    version=2,
    tags="orders",
)


def _make_cursor(cols: list[str], rows: list[tuple]) -> MagicMock:
    cur = MagicMock()
    cur.description = [(c,) for c in cols]
    cur.fetchmany.return_value = rows
    return cur


def _make_conn(cur: MagicMock) -> MagicMock:
    cur_cm = MagicMock()
    cur_cm.__enter__ = MagicMock(return_value=cur)
    cur_cm.__exit__ = MagicMock(return_value=False)

    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor = MagicMock(return_value=cur_cm)
    return conn


def _run_with_mocks(query_record, cur, params, **kwargs):
    """Helper: run run_query with fetch, connection, log, and write all mocked."""
    conn = _make_conn(cur)
    with ExitStack() as stack:
        stack.enter_context(
            patch("tools.run_query.fetch_query", return_value=query_record)
        )
        stack.enter_context(
            patch("tools.run_query.get_connection", return_value=conn)
        )
        mock_log = stack.enter_context(patch("tools.run_query.log_audit"))
        mock_write = stack.enter_context(patch("tools.run_query.write_audit_async"))
        result = run_query(query_record.name, params, **kwargs)
    return result, mock_log, mock_write, conn


# ---------------------------------------------------------------------------
# Successful SELECT execution
# ---------------------------------------------------------------------------


class TestRunQuerySuccess:
    def test_returns_list_of_row_dicts(self):
        cur = _make_cursor(["id", "name"], [(1, "Alice"), (2, "Bob")])
        result, _, _, _ = _run_with_mocks(_SELECT_QUERY, cur, {"id": 1})
        assert result == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    def test_empty_result_set(self):
        cur = _make_cursor(["id"], [])
        result, _, _, _ = _run_with_mocks(_SELECT_QUERY, cur, {"id": 1})
        assert result == []

    def test_audit_log_called_once_on_success(self):
        cur = _make_cursor(["id"], [(1,)])
        _, mock_log, _, _ = _run_with_mocks(_SELECT_QUERY, cur, {"id": 1})
        mock_log.assert_called_once()

    def test_audit_record_has_success_status(self):
        cur = _make_cursor(["id"], [(1,)])
        _, mock_log, _, _ = _run_with_mocks(_SELECT_QUERY, cur, {"id": 1})
        record = mock_log.call_args[0][0]
        assert record.status == "SUCCESS"
        assert record.error is None

    def test_audit_record_captures_row_count(self):
        cur = _make_cursor(["id"], [(1,), (2,), (3,)])
        _, mock_log, _, _ = _run_with_mocks(_SELECT_QUERY, cur, {"id": 1})
        record = mock_log.call_args[0][0]
        assert record.row_count == 3

    def test_audit_record_captures_query_name_and_version(self):
        cur = _make_cursor(["id"], [(1,)])
        _, mock_log, _, _ = _run_with_mocks(_SELECT_QUERY, cur, {"id": 1})
        record = mock_log.call_args[0][0]
        assert record.query_name == "get_orders"
        assert record.query_version == 2

    def test_write_audit_async_called_on_success(self):
        cur = _make_cursor(["id"], [(1,)])
        _, _, mock_write, _ = _run_with_mocks(_SELECT_QUERY, cur, {"id": 1})
        mock_write.assert_called_once()


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestRunQueryValidation:
    def test_missing_required_param_raises(self):
        with ExitStack() as stack:
            stack.enter_context(
                patch("tools.run_query.fetch_query", return_value=_SELECT_QUERY)
            )
            stack.enter_context(patch("tools.run_query.log_audit"))
            stack.enter_context(patch("tools.run_query.write_audit_async"))
            with pytest.raises(ValueError, match="Missing required parameter"):
                run_query("get_orders", {})

    def test_validation_error_does_not_open_db_connection(self):
        with ExitStack() as stack:
            stack.enter_context(
                patch("tools.run_query.fetch_query", return_value=_SELECT_QUERY)
            )
            mock_conn = stack.enter_context(patch("tools.run_query.get_connection"))
            stack.enter_context(patch("tools.run_query.log_audit"))
            stack.enter_context(patch("tools.run_query.write_audit_async"))
            with pytest.raises(ValueError):
                run_query("get_orders", {})
        mock_conn.assert_not_called()

    def test_type_mismatch_raises_type_error(self):
        with ExitStack() as stack:
            stack.enter_context(
                patch("tools.run_query.fetch_query", return_value=_SELECT_QUERY)
            )
            stack.enter_context(patch("tools.run_query.log_audit"))
            stack.enter_context(patch("tools.run_query.write_audit_async"))
            with pytest.raises(TypeError):
                run_query("get_orders", {"id": "not-a-number"})


# ---------------------------------------------------------------------------
# DB errors
# ---------------------------------------------------------------------------


class TestRunQueryDbError:
    def test_db_exception_is_reraised(self):
        cur = _make_cursor(["id"], [])
        cur.fetchmany.side_effect = RuntimeError("ORA-00942")
        conn = _make_conn(cur)
        with ExitStack() as stack:
            stack.enter_context(
                patch("tools.run_query.fetch_query", return_value=_SELECT_QUERY)
            )
            stack.enter_context(patch("tools.run_query.get_connection", return_value=conn))
            stack.enter_context(patch("tools.run_query.log_audit"))
            stack.enter_context(patch("tools.run_query.write_audit_async"))
            with pytest.raises(RuntimeError, match="ORA-00942"):
                run_query("get_orders", {"id": 1})

    def test_audit_record_has_error_status_on_db_failure(self):
        cur = _make_cursor(["id"], [])
        cur.fetchmany.side_effect = RuntimeError("ORA-00942")
        conn = _make_conn(cur)
        with ExitStack() as stack:
            stack.enter_context(
                patch("tools.run_query.fetch_query", return_value=_SELECT_QUERY)
            )
            stack.enter_context(patch("tools.run_query.get_connection", return_value=conn))
            mock_log = stack.enter_context(patch("tools.run_query.log_audit"))
            stack.enter_context(patch("tools.run_query.write_audit_async"))
            with pytest.raises(RuntimeError):
                run_query("get_orders", {"id": 1})

        record = mock_log.call_args[0][0]
        assert record.status == "ERROR"
        assert "ORA-00942" in record.error

    def test_audit_log_still_called_on_db_failure(self):
        cur = _make_cursor(["id"], [])
        cur.fetchmany.side_effect = RuntimeError("DB down")
        conn = _make_conn(cur)
        with ExitStack() as stack:
            stack.enter_context(
                patch("tools.run_query.fetch_query", return_value=_SELECT_QUERY)
            )
            stack.enter_context(patch("tools.run_query.get_connection", return_value=conn))
            mock_log = stack.enter_context(patch("tools.run_query.log_audit"))
            stack.enter_context(patch("tools.run_query.write_audit_async"))
            with pytest.raises(RuntimeError):
                run_query("get_orders", {"id": 1})

        mock_log.assert_called_once()


# ---------------------------------------------------------------------------
# max_rows / hard ceiling
# ---------------------------------------------------------------------------


class TestRunQueryRowLimits:
    def test_max_rows_capped_by_hard_max(self):
        cur = _make_cursor(["id"], [])
        conn = _make_conn(cur)
        with ExitStack() as stack:
            stack.enter_context(
                patch("tools.run_query.fetch_query", return_value=_SELECT_QUERY)
            )
            stack.enter_context(patch("tools.run_query.get_connection", return_value=conn))
            stack.enter_context(patch("tools.run_query.log_audit"))
            stack.enter_context(patch("tools.run_query.write_audit_async"))
            mock_settings = stack.enter_context(patch("tools.run_query.settings"))
            mock_settings.hard_max_rows = 100
            mock_settings.environment = "local"
            run_query("get_orders", {"id": 1}, max_rows=9999)

        cur.fetchmany.assert_called_once_with(100)

    def test_max_rows_below_hard_ceiling_used_as_is(self):
        cur = _make_cursor(["id"], [])
        conn = _make_conn(cur)
        with ExitStack() as stack:
            stack.enter_context(
                patch("tools.run_query.fetch_query", return_value=_SELECT_QUERY)
            )
            stack.enter_context(patch("tools.run_query.get_connection", return_value=conn))
            stack.enter_context(patch("tools.run_query.log_audit"))
            stack.enter_context(patch("tools.run_query.write_audit_async"))
            mock_settings = stack.enter_context(patch("tools.run_query.settings"))
            mock_settings.hard_max_rows = 2000
            mock_settings.environment = "local"
            run_query("get_orders", {"id": 1}, max_rows=50)

        cur.fetchmany.assert_called_once_with(50)
