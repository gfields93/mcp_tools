"""Tests for prompts/query_authoring.py."""

from prompts.query_authoring import query_authoring


class TestQueryAuthoring:
    def test_returns_string(self):
        result = query_authoring()
        assert isinstance(result, str)

    def test_enforces_no_select_star(self):
        result = query_authoring()
        assert "No SELECT *" in result

    def test_enforces_return_values(self):
        result = query_authoring()
        assert "return_values" in result

    def test_contains_parameter_type_rules(self):
        result = query_authoring()
        assert "NUMBER" in result
        assert "VARCHAR2" in result
        assert "DATE" in result
        assert "TIMESTAMP" in result

    def test_contains_template_syntax(self):
        result = query_authoring()
        assert "/*[" in result
        assert "]*/" in result

    def test_contains_insert_template(self):
        result = query_authoring()
        assert "INSERT INTO query_registry" in result

    def test_table_name_included_when_provided(self):
        result = query_authoring(table_name="VLS_DEAL")
        assert "VLS_DEAL" in result
        assert "Target table/view" in result

    def test_description_included_when_provided(self):
        result = query_authoring(query_description="Find deals by originator")
        assert "Find deals by originator" in result
        assert "Intended purpose" in result

    def test_no_context_when_no_params(self):
        result = query_authoring()
        assert "Target table/view" not in result
        assert "Intended purpose" not in result

    def test_both_params_included(self):
        result = query_authoring(
            table_name="VLS_FACILITY",
            query_description="List expired facilities",
        )
        assert "VLS_FACILITY" in result
        assert "List expired facilities" in result

    def test_mentions_naming_conventions(self):
        result = query_authoring()
        assert "snake_case" in result

    def test_mentions_oracle_quoting(self):
        result = query_authoring()
        assert "q'[" in result
