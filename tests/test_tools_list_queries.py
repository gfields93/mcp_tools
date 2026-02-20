"""Tests for tools/list_queries.py."""
from unittest.mock import patch

from tools.list_queries import list_queries

_SAMPLE = [
    {"name": "q1", "description": "First query", "tags": ["orders"], "parameters": []},
    {"name": "q2", "description": "Second query", "tags": ["finance"], "parameters": []},
]


class TestListQueries:
    def test_returns_fetch_all_result(self):
        with patch("tools.list_queries.fetch_all_queries", return_value=_SAMPLE):
            result = list_queries()
        assert result == _SAMPLE

    def test_passes_none_tags_by_default(self):
        with patch("tools.list_queries.fetch_all_queries", return_value=[]) as mock_fetch:
            list_queries()
        mock_fetch.assert_called_once_with(tags=None)

    def test_passes_tags_argument_through(self):
        with patch("tools.list_queries.fetch_all_queries", return_value=[]) as mock_fetch:
            list_queries(tags="finance,orders")
        mock_fetch.assert_called_once_with(tags="finance,orders")

    def test_returns_empty_list_when_no_queries(self):
        with patch("tools.list_queries.fetch_all_queries", return_value=[]):
            result = list_queries()
        assert result == []

    def test_result_is_passed_through_unchanged(self):
        with patch("tools.list_queries.fetch_all_queries", return_value=_SAMPLE):
            result = list_queries(tags="orders")
        assert result is _SAMPLE
