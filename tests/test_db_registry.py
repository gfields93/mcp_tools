"""Tests for db/registry.py — Oracle interactions are fully mocked."""
import json
from unittest.mock import MagicMock, patch

import pytest

from db.registry import QueryRecord, _read_lob, fetch_all_queries, fetch_query


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cursor_cm(cursor: MagicMock) -> MagicMock:
    """Wrap a cursor mock in a context-manager mock."""
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cursor)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _make_conn(cursor: MagicMock) -> MagicMock:
    """Build a connection mock whose cursor() returns the given cursor."""
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor = MagicMock(return_value=_make_cursor_cm(cursor))
    return conn


def _make_cursor(fetchone=None, fetchall=None) -> MagicMock:
    cur = MagicMock()
    cur.fetchone.return_value = fetchone
    cur.fetchall.return_value = fetchall or []
    return cur


# ---------------------------------------------------------------------------
# _read_lob
# ---------------------------------------------------------------------------


class TestReadLob:
    def test_plain_string_passthrough(self):
        assert _read_lob("hello world") == "hello world"

    def test_none_returns_empty_string(self):
        assert _read_lob(None) == ""

    def test_empty_string_returns_empty_string(self):
        assert _read_lob("") == ""

    def test_lob_object_is_read(self):
        lob = MagicMock()
        lob.read.return_value = "lob content"
        assert _read_lob(lob) == "lob content"
        lob.read.assert_called_once()


# ---------------------------------------------------------------------------
# fetch_query
# ---------------------------------------------------------------------------


class TestFetchQuery:
    def _row(self, **overrides):
        defaults = {
            "id": 1,
            "name": "my_query",
            "desc": "A test query",
            "sql_text": "SELECT * FROM t WHERE id = :id",
            "params": json.dumps([{"name": "id", "type": "NUMBER"}]),
            "query_type": "SELECT",
            "version": 2,
            "tags": "finance,orders",
        }
        defaults.update(overrides)
        return (
            defaults["id"],
            defaults["name"],
            defaults["desc"],
            defaults["sql_text"],
            defaults["params"],
            defaults["query_type"],
            defaults["version"],
            defaults["tags"],
        )

    def test_returns_query_record_instance(self):
        cur = _make_cursor(fetchone=self._row())
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_query("my_query")
        assert isinstance(result, QueryRecord)

    def test_maps_all_fields_correctly(self):
        cur = _make_cursor(fetchone=self._row())
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_query("my_query")
        assert result.name == "my_query"
        assert result.description == "A test query"
        assert result.sql_text == "SELECT * FROM t WHERE id = :id"
        assert result.parameters == [{"name": "id", "type": "NUMBER"}]
        assert result.query_type == "SELECT"
        assert result.version == 2
        assert result.tags == "finance,orders"

    def test_raises_value_error_when_not_found(self):
        cur = _make_cursor(fetchone=None)
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            with pytest.raises(ValueError, match="No active query found"):
                fetch_query("missing_query")

    def test_null_parameters_becomes_empty_list(self):
        cur = _make_cursor(fetchone=self._row(params=None))
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_query("my_query")
        assert result.parameters == []

    def test_lob_sql_text_is_read(self):
        lob = MagicMock()
        lob.read.return_value = "SELECT 1 FROM DUAL"
        cur = _make_cursor(fetchone=self._row(sql_text=lob))
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_query("my_query")
        assert result.sql_text == "SELECT 1 FROM DUAL"

    def test_lob_parameters_is_read(self):
        params = [{"name": "x", "type": "VARCHAR2"}]
        lob = MagicMock()
        lob.read.return_value = json.dumps(params)
        cur = _make_cursor(fetchone=self._row(params=lob))
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_query("my_query")
        assert result.parameters == params

    def test_null_tags_preserved(self):
        cur = _make_cursor(fetchone=self._row(tags=None))
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_query("my_query")
        assert result.tags is None

    def test_dml_query_type_preserved(self):
        cur = _make_cursor(fetchone=self._row(query_type="DML"))
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_query("my_query")
        assert result.query_type == "DML"


# ---------------------------------------------------------------------------
# fetch_all_queries
# ---------------------------------------------------------------------------


class TestFetchAllQueries:
    def _row(self, name="q1", desc="desc1", params=None, tags="orders,finance"):
        if params is None:
            params = json.dumps([{"name": "id"}])
        return (name, desc, params, tags)

    def test_returns_list_of_dicts(self):
        cur = _make_cursor(fetchall=[self._row()])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_all_queries()
        assert len(result) == 1
        assert result[0]["name"] == "q1"

    def test_dict_has_expected_keys(self):
        cur = _make_cursor(fetchall=[self._row()])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_all_queries()
        assert set(result[0].keys()) == {"name", "description", "tags", "parameters"}

    def test_tags_split_into_list(self):
        cur = _make_cursor(fetchall=[self._row(tags="orders,finance")])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_all_queries()
        assert result[0]["tags"] == ["orders", "finance"]

    def test_null_tags_becomes_empty_list(self):
        cur = _make_cursor(fetchall=[self._row(tags=None)])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_all_queries()
        assert result[0]["tags"] == []

    def test_null_params_becomes_empty_list(self):
        # Construct the row tuple directly so params is truly None
        cur = _make_cursor(fetchall=[("q1", "desc1", None, "orders")])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_all_queries()
        assert result[0]["parameters"] == []

    def test_empty_result_set(self):
        cur = _make_cursor(fetchall=[])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_all_queries()
        assert result == []

    def test_multiple_rows_returned(self):
        rows = [self._row("q1"), self._row("q2"), self._row("q3")]
        cur = _make_cursor(fetchall=rows)
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_all_queries()
        assert len(result) == 3
        assert [r["name"] for r in result] == ["q1", "q2", "q3"]

    def test_tag_filter_injects_like_conditions(self):
        cur = _make_cursor(fetchall=[])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            fetch_all_queries(tags="finance,orders")

        sql, bind = cur.execute.call_args[0]
        assert "LIKE" in sql
        values = list(bind.values())
        assert "%finance%" in values
        assert "%orders%" in values

    def test_single_tag_filter(self):
        cur = _make_cursor(fetchall=[])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            fetch_all_queries(tags="finance")

        sql, bind = cur.execute.call_args[0]
        assert "LIKE" in sql
        assert "%finance%" in bind.values()

    def test_no_tags_runs_without_where_clause_extension(self):
        cur = _make_cursor(fetchall=[])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            fetch_all_queries(tags=None)

        sql, bind = cur.execute.call_args[0]
        assert "LIKE" not in sql
        assert bind == {}

    def test_lob_params_read_correctly(self):
        params = [{"name": "x"}]
        lob = MagicMock()
        lob.read.return_value = json.dumps(params)
        cur = _make_cursor(fetchall=[self._row(params=lob)])
        with patch("db.registry.get_connection", return_value=_make_conn(cur)):
            result = fetch_all_queries()
        assert result[0]["parameters"] == params
