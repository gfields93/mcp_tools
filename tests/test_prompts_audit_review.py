"""Tests for prompts/audit_review.py."""

from prompts.audit_review import audit_review


class TestAuditReview:
    def test_returns_string(self):
        result = audit_review()
        assert isinstance(result, str)

    def test_default_time_range_is_24h(self):
        result = audit_review()
        assert "24 hours" in result

    def test_custom_time_range_1h(self):
        result = audit_review(time_range="1h")
        assert "1 hour" in result
        assert "lookback_hours=1" in result

    def test_custom_time_range_7d(self):
        result = audit_review(time_range="7d")
        assert "7 days" in result
        assert "lookback_hours=168" in result

    def test_custom_time_range_30d(self):
        result = audit_review(time_range="30d")
        assert "30 days" in result
        assert "lookback_hours=720" in result

    def test_unknown_time_range_falls_back_to_24h(self):
        result = audit_review(time_range="99x")
        assert "24 hours" in result

    def test_contains_audit_query_references(self):
        result = audit_review()
        assert "audit_execution_summary" in result
        assert "audit_recent_errors" in result
        assert "audit_slow_queries" in result
        assert "audit_most_used" in result

    def test_query_name_focus_included(self):
        result = audit_review(query_name="deal_list_active")
        assert "deal_list_active" in result
        assert "focus specifically" in result

    def test_no_query_name_omits_focus(self):
        result = audit_review()
        assert "focus specifically" not in result

    def test_contains_recommendations_section(self):
        result = audit_review()
        assert "Recommendations" in result

    def test_mentions_query_audit_log(self):
        result = audit_review()
        assert "query_audit_log" in result

    def test_contains_step_structure(self):
        result = audit_review()
        assert "Step 1" in result
        assert "Step 5" in result

    def test_mentions_authoring_fallback(self):
        result = audit_review()
        assert "Query Authoring" in result
