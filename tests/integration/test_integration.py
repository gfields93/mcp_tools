"""
Integration tests — full round-trip through tool → registry → in-memory SQLite.

The 'registry' fixture (defined in conftest.py) wires up an in-memory SQLite
database seeded with a small employee table and several registered queries.
All Oracle I/O is replaced by the SQLite adapter; audit side-effects are mocked.
"""
import json
from unittest.mock import patch, call

import pytest

from tools.get_query import get_query
from tools.list_queries import list_queries
from tools.run_query import run_query


# ===========================================================================
# list_queries
# ===========================================================================


class TestListQueriesIntegration:
    def test_returns_all_active_queries(self, registry):
        result = list_queries()
        names = {r["name"] for r in result}
        # inactive_query must be absent; all others present
        assert "inactive_query" not in names
        assert names == {
            "get_employee_by_id",
            "list_by_department",
            "list_all_employees",
            "list_employees_optional_dept",
        }

    def test_each_entry_has_required_keys(self, registry):
        for entry in list_queries():
            assert {"name", "description", "tags", "parameters"} <= entry.keys()

    def test_tags_are_parsed_to_list(self, registry):
        results = {r["name"]: r for r in list_queries()}
        assert results["get_employee_by_id"]["tags"] == ["hr", "employees"]
        assert results["list_all_employees"]["tags"] == ["hr"]

    def test_null_tags_returns_empty_list(self, registry):
        # inactive_query has null tags — verify it is excluded
        names = {r["name"] for r in list_queries()}
        assert "inactive_query" not in names

    def test_parameters_deserialised_from_json(self, registry):
        results = {r["name"]: r for r in list_queries()}
        params = results["get_employee_by_id"]["parameters"]
        assert isinstance(params, list)
        assert params[0]["name"] == "id"
        assert params[0]["type"] == "NUMBER"

    def test_no_params_query_has_empty_parameters(self, registry):
        results = {r["name"]: r for r in list_queries()}
        assert results["list_all_employees"]["parameters"] == []

    def test_tag_filter_returns_matching_queries_only(self, registry):
        result = list_queries(tags="employees")
        names = {r["name"] for r in result}
        assert "get_employee_by_id" in names
        assert "list_by_department" in names
        assert "list_all_employees" not in names

    def test_tag_filter_no_matches_returns_empty(self, registry):
        result = list_queries(tags="nonexistent_tag")
        assert result == []

    def test_multi_tag_filter_returns_union(self, registry):
        result = list_queries(tags="employees,hr")
        names = {r["name"] for r in result}
        # "hr" matches all active queries; "employees" matches get_ and list_by_
        assert "get_employee_by_id" in names
        assert "list_by_department" in names
        assert "list_all_employees" in names


# ===========================================================================
# get_query
# ===========================================================================


class TestGetQueryIntegration:
    def test_returns_correct_fields(self, registry):
        result = get_query("get_employee_by_id")
        assert result["name"] == "get_employee_by_id"
        assert result["description"] == "Fetch one employee by primary key"
        assert result["version"] == 1

    def test_tags_parsed_to_list(self, registry):
        result = get_query("get_employee_by_id")
        assert result["tags"] == ["hr", "employees"]

    def test_null_tags_returns_empty_list(self, registry):
        result = get_query("list_all_employees")
        assert isinstance(result["tags"], list)

    def test_parameters_returned_correctly(self, registry):
        result = get_query("list_by_department")
        params = result["parameters"]
        assert len(params) == 1
        assert params[0]["name"] == "department"
        assert params[0]["allowed_values"] == ["Engineering", "Finance"]

    def test_no_params_query_returns_empty_list(self, registry):
        result = get_query("list_all_employees")
        assert result["parameters"] == []

    def test_not_found_raises_value_error(self, registry):
        with pytest.raises(ValueError, match="No active query found"):
            get_query("nonexistent_query")

    def test_inactive_query_raises_value_error(self, registry):
        with pytest.raises(ValueError, match="No active query found"):
            get_query("inactive_query")


# ===========================================================================
# run_query — SELECT execution
# ===========================================================================


class TestRunQuerySelectIntegration:
    def test_returns_row_for_existing_employee(self, registry):
        result = run_query("get_employee_by_id", {"id": 1})
        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        assert result[0]["department"] == "Engineering"

    def test_returns_empty_list_for_no_match(self, registry):
        result = run_query("get_employee_by_id", {"id": 999})
        assert result == []

    def test_returns_multiple_rows(self, registry):
        result = run_query("list_by_department", {"department": "Engineering"})
        assert len(result) == 2
        names = {r["name"] for r in result}
        assert names == {"Alice", "Carol"}

    def test_column_names_match_select_list(self, registry):
        result = run_query("get_employee_by_id", {"id": 2})
        assert set(result[0].keys()) == {"id", "name", "department"}

    def test_no_params_query_returns_all_rows(self, registry):
        result = run_query("list_all_employees", {})
        assert len(result) == 3

    def test_string_id_coerced_to_number(self, registry):
        # validate_and_bind coerces "1" → 1 before binding
        result = run_query("get_employee_by_id", {"id": "1"})
        assert result[0]["name"] == "Alice"

    def test_max_rows_caps_result(self, registry):
        result = run_query("list_all_employees", {}, max_rows=2)
        assert len(result) == 2

    def test_allowed_values_enforced(self, registry):
        with pytest.raises(ValueError, match="must be one of"):
            run_query("list_by_department", {"department": "Marketing"})

    def test_missing_required_param_raises(self, registry):
        with pytest.raises(ValueError, match="Missing required parameter"):
            run_query("get_employee_by_id", {})

    def test_type_mismatch_raises(self, registry):
        with pytest.raises(TypeError):
            run_query("get_employee_by_id", {"id": "not-a-number"})

    def test_inactive_query_raises_value_error(self, registry):
        with pytest.raises(ValueError, match="No active query found"):
            run_query("inactive_query", {})

    def test_nonexistent_query_raises_value_error(self, registry):
        with pytest.raises(ValueError, match="No active query found"):
            run_query("ghost_query", {})


# ===========================================================================
# run_query — audit record
# ===========================================================================


class TestRunQueryAuditIntegration:
    def test_audit_log_called_on_success(self, registry):
        with patch("tools.run_query.log_audit") as mock_log:
            run_query("get_employee_by_id", {"id": 1})
        mock_log.assert_called_once()

    def test_audit_record_success_fields(self, registry):
        with patch("tools.run_query.log_audit") as mock_log:
            run_query("get_employee_by_id", {"id": 1})
        record = mock_log.call_args[0][0]
        assert record.status == "SUCCESS"
        assert record.query_name == "get_employee_by_id"
        assert record.query_version == 1
        assert record.row_count == 1
        assert record.error is None

    def test_audit_record_error_fields_on_failure(self, registry):
        # Force a DB error by seeding a broken SQL query
        registry.execute(
            """INSERT INTO query_registry
               (name, description, sql_text, parameters, version, is_active, tags)
               VALUES ('broken_query', 'bad sql', 'SELECT * FROM nonexistent_table',
                       NULL, 1, 1, NULL)"""
        )
        registry.commit()

        with patch("tools.run_query.log_audit") as mock_log:
            with pytest.raises(Exception):
                run_query("broken_query", {})

        record = mock_log.call_args[0][0]
        assert record.status == "ERROR"
        assert record.error is not None

    def test_audit_record_duration_is_non_negative(self, registry):
        with patch("tools.run_query.log_audit") as mock_log:
            run_query("list_all_employees", {})
        record = mock_log.call_args[0][0]
        assert record.duration_ms >= 0


# ===========================================================================
# run_query — dynamic query (template blocks + NULL-bypass)
# ===========================================================================


class TestRunQueryDynamicIntegration:
    def test_optional_param_omitted_returns_all_rows(self, registry):
        # No department supplied → template block stripped → all employees returned
        result = run_query("list_employees_optional_dept", {})
        assert len(result) == 3

    def test_optional_param_supplied_filters_rows(self, registry):
        result = run_query("list_employees_optional_dept", {"department": "Engineering"})
        assert len(result) == 2
        names = {r["name"] for r in result}
        assert names == {"Alice", "Carol"}

    def test_optional_param_finance_filters_rows(self, registry):
        result = run_query("list_employees_optional_dept", {"department": "Finance"})
        assert len(result) == 1
        assert result[0]["name"] == "Bob"

    def test_optional_param_invalid_value_raises(self, registry):
        with pytest.raises(ValueError, match="must be one of"):
            run_query("list_employees_optional_dept", {"department": "Marketing"})
