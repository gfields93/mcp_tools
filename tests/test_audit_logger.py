"""Tests for audit/logger.py."""
import json
from unittest.mock import patch

from audit.logger import log_audit
from audit.record import AuditRecord


def _make_record(**overrides) -> AuditRecord:
    defaults = dict(
        query_name="test_query",
        query_version=1,
        parameters={"id": 5},
        status="SUCCESS",
        error=None,
        row_count=3,
        duration_ms=50,
    )
    defaults.update(overrides)
    return AuditRecord(**defaults)


class TestLogAudit:
    def test_calls_logger_info_once(self):
        with patch("audit.logger._audit_log") as mock_log:
            log_audit(_make_record())
        mock_log.info.assert_called_once()

    def test_logs_valid_json(self):
        with patch("audit.logger._audit_log") as mock_log:
            log_audit(_make_record())
        arg = mock_log.info.call_args[0][0]
        # Should not raise
        parsed = json.loads(arg)
        assert isinstance(parsed, dict)

    def test_logged_json_contains_query_name(self):
        with patch("audit.logger._audit_log") as mock_log:
            log_audit(_make_record(query_name="my_query"))
        arg = mock_log.info.call_args[0][0]
        assert json.loads(arg)["query_name"] == "my_query"

    def test_logged_json_contains_status(self):
        with patch("audit.logger._audit_log") as mock_log:
            log_audit(_make_record(status="ERROR", error="some error"))
        arg = mock_log.info.call_args[0][0]
        parsed = json.loads(arg)
        assert parsed["status"] == "ERROR"
        assert parsed["error"] == "some error"

    def test_logged_json_contains_parameters(self):
        with patch("audit.logger._audit_log") as mock_log:
            log_audit(_make_record(parameters={"customer_id": 99}))
        arg = mock_log.info.call_args[0][0]
        assert json.loads(arg)["parameters"] == {"customer_id": 99}

    def test_logged_json_contains_row_count_and_duration(self):
        with patch("audit.logger._audit_log") as mock_log:
            log_audit(_make_record(row_count=42, duration_ms=188))
        arg = mock_log.info.call_args[0][0]
        parsed = json.loads(arg)
        assert parsed["row_count"] == 42
        assert parsed["duration_ms"] == 188
