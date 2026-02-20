"""Tests for audit/record.py — pure dataclass, no DB required."""
import json
from datetime import datetime, timezone

from audit.record import AuditRecord


def _make_record(**overrides) -> AuditRecord:
    defaults = dict(
        query_name="test_query",
        query_version=1,
        parameters={"customer_id": 42, "status": "OPEN"},
        status="SUCCESS",
        error=None,
        row_count=5,
        duration_ms=123,
    )
    defaults.update(overrides)
    return AuditRecord(**defaults)


class TestAuditRecordParametersJson:
    def test_serialises_dict_to_json(self):
        rec = _make_record(parameters={"id": 42, "status": "OPEN"})
        parsed = json.loads(rec.parameters_json)
        assert parsed == {"id": 42, "status": "OPEN"}

    def test_empty_parameters(self):
        rec = _make_record(parameters={})
        assert rec.parameters_json == "{}"

    def test_nested_parameters(self):
        rec = _make_record(parameters={"nested": {"key": "val"}})
        parsed = json.loads(rec.parameters_json)
        assert parsed["nested"] == {"key": "val"}


class TestAuditRecordToDict:
    def test_returns_all_expected_keys(self):
        expected = {
            "query_name",
            "query_version",
            "executed_at",
            "parameters",
            "status",
            "error",
            "row_count",
            "duration_ms",
            "caller_id",
        }
        assert set(_make_record().to_dict().keys()) == expected

    def test_success_values(self):
        rec = _make_record(query_name="q", query_version=3, row_count=10, duration_ms=55)
        d = rec.to_dict()
        assert d["query_name"] == "q"
        assert d["query_version"] == 3
        assert d["row_count"] == 10
        assert d["duration_ms"] == 55
        assert d["status"] == "SUCCESS"
        assert d["error"] is None

    def test_error_values(self):
        rec = _make_record(status="ERROR", error="ORA-00942: table or view does not exist")
        d = rec.to_dict()
        assert d["status"] == "ERROR"
        assert "ORA-00942" in d["error"]

    def test_caller_id_included(self):
        rec = _make_record(caller_id="user-abc123")
        assert rec.to_dict()["caller_id"] == "user-abc123"

    def test_caller_id_defaults_to_none(self):
        rec = _make_record()
        assert rec.caller_id is None
        assert rec.to_dict()["caller_id"] is None

    def test_executed_at_is_valid_isoformat(self):
        rec = _make_record()
        # Should not raise
        parsed = datetime.fromisoformat(rec.to_dict()["executed_at"])
        assert parsed.tzinfo is not None

    def test_executed_at_defaults_to_utc(self):
        rec = _make_record()
        assert rec.executed_at.tzinfo == timezone.utc

    def test_parameters_dict_preserved_in_to_dict(self):
        params = {"id": 1, "name": "Alice"}
        rec = _make_record(parameters=params)
        assert rec.to_dict()["parameters"] == params
