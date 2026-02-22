"""Tests for prompts/query_discovery.py."""

from prompts.query_discovery import query_discovery


class TestQueryDiscovery:
    def test_returns_string(self):
        result = query_discovery()
        assert isinstance(result, str)

    def test_contains_list_queries_instruction(self):
        result = query_discovery()
        assert "list_queries" in result

    def test_contains_get_query_instruction(self):
        result = query_discovery()
        assert "get_query" in result

    def test_contains_run_query_instruction(self):
        result = query_discovery()
        assert "run_query" in result

    def test_no_tags_omits_tag_filter(self):
        result = query_discovery()
        assert 'tags=' not in result

    def test_tags_included_in_list_queries_call(self):
        result = query_discovery(tags="deal,facility")
        assert 'tags="deal,facility"' in result

    def test_tags_included_in_focus_instruction(self):
        result = query_discovery(tags="reporting")
        assert "reporting" in result

    def test_contains_step_structure(self):
        result = query_discovery()
        assert "Step 1" in result
        assert "Step 2" in result
        assert "Step 3" in result
        assert "Step 4" in result

    def test_contains_guidelines_section(self):
        result = query_discovery()
        assert "Guidelines" in result

    def test_mentions_parameter_details(self):
        result = query_discovery()
        assert "Parameters" in result
        assert "Return values" in result
