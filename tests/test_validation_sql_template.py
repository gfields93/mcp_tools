"""Tests for validation/sql_template.py — pure function, no DB required."""
import pytest

from validation.sql_template import render_sql


class TestRenderSql:
    def test_no_template_blocks_returned_unchanged(self):
        sql = "SELECT * FROM employees WHERE id = :id"
        assert render_sql(sql, {"id": 1}) == sql

    def test_block_included_when_variable_present(self):
        sql = "SELECT * FROM t/*[ WHERE status = :status]*/"
        result = render_sql(sql, {"status": "OPEN"})
        assert " WHERE status = :status" in result
        assert "/*[" not in result

    def test_block_stripped_when_variable_absent(self):
        sql = "SELECT * FROM t/*[ WHERE status = :status]*/"
        result = render_sql(sql, {})
        assert "status" not in result
        assert "/*[" not in result

    def test_block_stripped_when_variable_is_none(self):
        sql = "SELECT * FROM t/*[ WHERE status = :status]*/"
        result = render_sql(sql, {"status": None})
        assert "status" not in result

    def test_multiple_blocks_resolved_independently(self):
        sql = (
            "SELECT * FROM t"
            "/*[ WHERE dept = :dept]*/"
            "/*[ AND status = :status]*/"
        )
        result = render_sql(sql, {"dept": "Engineering"})
        assert "dept = :dept" in result
        assert "status" not in result

    def test_both_blocks_included_when_all_vars_present(self):
        sql = (
            "SELECT * FROM t"
            "/*[ WHERE dept = :dept]*/"
            "/*[ AND status = :status]*/"
        )
        result = render_sql(sql, {"dept": "Engineering", "status": "OPEN"})
        assert "dept = :dept" in result
        assert "AND status = :status" in result

    def test_block_with_multiple_variables_all_present_included(self):
        sql = "SELECT * FROM t/*[ WHERE d >= :start AND d <= :end]*/"
        result = render_sql(sql, {"start": "2024-01-01", "end": "2024-12-31"})
        assert ":start" in result
        assert ":end" in result

    def test_block_with_multiple_variables_one_absent_stripped(self):
        sql = "SELECT * FROM t/*[ WHERE d >= :start AND d <= :end]*/"
        result = render_sql(sql, {"start": "2024-01-01"})
        assert "start" not in result
        assert "end" not in result

    def test_block_with_no_variables_stripped(self):
        # A block with no bind variables is always stripped (no trigger to include)
        sql = "SELECT * FROM t/*[ ORDER BY name]*/"
        result = render_sql(sql, {"id": 1})
        assert "ORDER BY" not in result

    def test_empty_sql_returned_unchanged(self):
        assert render_sql("", {}) == ""

    def test_multiline_block_stripped(self):
        sql = "SELECT * FROM t/*[\n  WHERE id = :id\n  AND active = 1\n]*/"
        result = render_sql(sql, {})
        assert "WHERE" not in result

    def test_multiline_block_included(self):
        sql = "SELECT * FROM t/*[\n  WHERE id = :id\n  AND active = 1\n]*/"
        result = render_sql(sql, {"id": 42})
        assert "WHERE" in result
        assert ":id" in result

    def test_surrounding_sql_preserved(self):
        sql = "SELECT id, name FROM employees/*[ WHERE id = :id]*/ ORDER BY name"
        result = render_sql(sql, {})
        assert result.startswith("SELECT id, name FROM employees")
        assert result.endswith("ORDER BY name")
