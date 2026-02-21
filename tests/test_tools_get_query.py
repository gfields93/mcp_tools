"""Tests for tools/get_query.py."""
from unittest.mock import patch

from db.registry import QueryRecord
from tools.get_query import get_query


def _make_record(**overrides) -> QueryRecord:
    defaults = dict(
        id=1,
        name="my_query",
        description="Returns all orders for a customer",
        sql_text="SELECT * FROM orders WHERE customer_id = :customer_id",
        parameters=[{"name": "customer_id", "type": "NUMBER", "required": True}],
        version=2,
        tags="finance,orders",
    )
    defaults.update(overrides)
    return QueryRecord(**defaults)


class TestGetQuery:
    def test_returns_dict_with_expected_keys(self):
        with patch("tools.get_query.fetch_query", return_value=_make_record()):
            result = get_query("my_query")
        assert set(result.keys()) == {
            "name",
            "description",
            "parameters",
            "version",
            "tags",
        }

    def test_name_passed_to_fetch_query(self):
        with patch("tools.get_query.fetch_query", return_value=_make_record()) as mock_fetch:
            get_query("my_query")
        mock_fetch.assert_called_once_with("my_query")

    def test_field_values_mapped_correctly(self):
        with patch("tools.get_query.fetch_query", return_value=_make_record()):
            result = get_query("my_query")
        assert result["name"] == "my_query"
        assert result["description"] == "Returns all orders for a customer"
        assert result["version"] == 2

    def test_tags_string_split_into_list(self):
        with patch("tools.get_query.fetch_query", return_value=_make_record(tags="a,b,c")):
            result = get_query("my_query")
        assert result["tags"] == ["a", "b", "c"]

    def test_tags_strips_whitespace(self):
        with patch("tools.get_query.fetch_query", return_value=_make_record(tags="a , b , c")):
            result = get_query("my_query")
        assert result["tags"] == ["a", "b", "c"]

    def test_null_tags_returns_empty_list(self):
        with patch("tools.get_query.fetch_query", return_value=_make_record(tags=None)):
            result = get_query("my_query")
        assert result["tags"] == []

    def test_parameters_included_unchanged(self):
        params = [{"name": "id", "type": "NUMBER", "required": True}]
        with patch("tools.get_query.fetch_query", return_value=_make_record(parameters=params)):
            result = get_query("my_query")
        assert result["parameters"] == params

    def test_propagates_value_error_from_fetch(self):
        import pytest

        with patch(
            "tools.get_query.fetch_query", side_effect=ValueError("No active query found")
        ):
            with pytest.raises(ValueError, match="No active query found"):
                get_query("nonexistent")
