"""Tests for validation/parameters.py — pure functions, no DB required."""
import datetime

import pytest

from validation.parameters import _coerce, validate_and_bind


# ---------------------------------------------------------------------------
# _coerce — NUMBER
# ---------------------------------------------------------------------------


class TestCoerceNumber:
    def test_int_passthrough(self):
        assert _coerce("x", 42, "NUMBER") == 42

    def test_float_passthrough(self):
        assert _coerce("x", 3.14, "NUMBER") == 3.14

    def test_string_int_coerced(self):
        result = _coerce("x", "42", "NUMBER")
        assert result == 42
        assert isinstance(result, int)

    def test_string_float_coerced(self):
        result = _coerce("x", "3.14", "NUMBER")
        assert result == 3.14
        assert isinstance(result, float)

    def test_bool_raises(self):
        with pytest.raises(TypeError, match="bool"):
            _coerce("x", True, "NUMBER")

    def test_invalid_string_raises(self):
        with pytest.raises(TypeError, match="NUMBER"):
            _coerce("x", "not-a-number", "NUMBER")

    def test_list_raises(self):
        with pytest.raises(TypeError, match="NUMBER"):
            _coerce("x", [], "NUMBER")

    def test_none_raises(self):
        with pytest.raises(TypeError):
            _coerce("x", None, "NUMBER")


# ---------------------------------------------------------------------------
# _coerce — DATE
# ---------------------------------------------------------------------------


class TestCoerceDate:
    def test_date_passthrough(self):
        d = datetime.date(2024, 1, 15)
        assert _coerce("x", d, "DATE") == d

    def test_datetime_passthrough(self):
        dt = datetime.datetime(2024, 1, 15, 10, 30)
        assert _coerce("x", dt, "DATE") == dt

    def test_valid_iso_string(self):
        result = _coerce("x", "2024-01-15", "DATE")
        assert result == datetime.date(2024, 1, 15)

    def test_invalid_string_raises(self):
        with pytest.raises(TypeError, match="ISO date"):
            _coerce("x", "15/01/2024", "DATE")

    def test_non_date_type_raises(self):
        with pytest.raises(TypeError, match="DATE"):
            _coerce("x", 20240115, "DATE")


# ---------------------------------------------------------------------------
# _coerce — TIMESTAMP
# ---------------------------------------------------------------------------


class TestCoerceTimestamp:
    def test_datetime_passthrough(self):
        dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
        assert _coerce("x", dt, "TIMESTAMP") == dt

    def test_valid_iso_string(self):
        result = _coerce("x", "2024-01-15T10:30:00", "TIMESTAMP")
        assert result == datetime.datetime(2024, 1, 15, 10, 30, 0)

    def test_invalid_string_raises(self):
        with pytest.raises(TypeError, match="ISO datetime"):
            _coerce("x", "not-a-timestamp", "TIMESTAMP")

    def test_non_datetime_type_raises(self):
        with pytest.raises(TypeError, match="TIMESTAMP"):
            _coerce("x", 12345, "TIMESTAMP")

    def test_date_only_object_raises(self):
        # datetime.date is not datetime.datetime
        with pytest.raises(TypeError, match="TIMESTAMP"):
            _coerce("x", datetime.date(2024, 1, 15), "TIMESTAMP")


# ---------------------------------------------------------------------------
# _coerce — VARCHAR2 and unknown types
# ---------------------------------------------------------------------------


class TestCoerceVarchar2:
    def test_string_passthrough(self):
        assert _coerce("x", "hello", "VARCHAR2") == "hello"

    def test_non_string_raises(self):
        with pytest.raises(TypeError, match="VARCHAR2"):
            _coerce("x", 123, "VARCHAR2")

    def test_unknown_type_treated_as_varchar(self):
        # Unknown Oracle types fall through to the varchar branch
        assert _coerce("x", "hello", "CHAR") == "hello"

    def test_unknown_type_non_string_raises(self):
        with pytest.raises(TypeError):
            _coerce("x", 99, "CHAR")


# ---------------------------------------------------------------------------
# validate_and_bind
# ---------------------------------------------------------------------------


class TestValidateAndBind:
    def test_required_param_present(self):
        defs = [{"name": "id", "type": "NUMBER", "required": True}]
        assert validate_and_bind(defs, {"id": 1}) == {"id": 1}

    def test_required_param_missing_raises(self):
        defs = [{"name": "id", "type": "NUMBER", "required": True}]
        with pytest.raises(ValueError, match="Missing required parameter: 'id'"):
            validate_and_bind(defs, {})

    def test_optional_with_default_uses_default(self):
        defs = [{"name": "status", "type": "VARCHAR2", "required": False, "default": "OPEN"}]
        assert validate_and_bind(defs, {}) == {"status": "OPEN"}

    def test_optional_without_default_bound_as_none(self):
        # Optional params with no default are bound as None to enable the
        # Oracle NULL-bypass pattern: (:param IS NULL OR col = :param)
        defs = [{"name": "status", "type": "VARCHAR2", "required": False}]
        assert validate_and_bind(defs, {}) == {"status": None}

    def test_optional_without_default_provided_value_is_bound(self):
        defs = [{"name": "status", "type": "VARCHAR2", "required": False}]
        assert validate_and_bind(defs, {"status": "OPEN"}) == {"status": "OPEN"}

    def test_allowed_values_accepted(self):
        defs = [
            {
                "name": "status",
                "type": "VARCHAR2",
                "required": True,
                "allowed_values": ["OPEN", "CLOSED"],
            }
        ]
        assert validate_and_bind(defs, {"status": "OPEN"}) == {"status": "OPEN"}

    def test_disallowed_value_raises(self):
        defs = [
            {
                "name": "status",
                "type": "VARCHAR2",
                "required": True,
                "allowed_values": ["OPEN", "CLOSED"],
            }
        ]
        with pytest.raises(ValueError, match="must be one of"):
            validate_and_bind(defs, {"status": "PENDING"})

    def test_empty_definitions_returns_empty(self):
        assert validate_and_bind([], {"ignored": "value"}) == {}

    def test_multiple_params_all_bound(self):
        defs = [
            {"name": "id", "type": "NUMBER", "required": True},
            {"name": "name", "type": "VARCHAR2", "required": True},
        ]
        result = validate_and_bind(defs, {"id": 5, "name": "Alice"})
        assert result == {"id": 5, "name": "Alice"}

    def test_type_coercion_applied(self):
        defs = [{"name": "id", "type": "NUMBER", "required": True}]
        result = validate_and_bind(defs, {"id": "99"})
        assert result["id"] == 99
        assert isinstance(result["id"], int)

    def test_type_mismatch_raises(self):
        defs = [{"name": "id", "type": "NUMBER", "required": True}]
        with pytest.raises(TypeError):
            validate_and_bind(defs, {"id": "not-a-number"})

    def test_default_type_is_varchar2(self):
        # When "type" is omitted, falls back to VARCHAR2
        defs = [{"name": "x", "required": True}]
        assert validate_and_bind(defs, {"x": "hello"}) == {"x": "hello"}

    def test_date_param_coerced_from_string(self):
        defs = [{"name": "dt", "type": "DATE", "required": True}]
        result = validate_and_bind(defs, {"dt": "2024-06-01"})
        assert result["dt"] == datetime.date(2024, 6, 1)

    def test_timestamp_param_coerced_from_string(self):
        defs = [{"name": "ts", "type": "TIMESTAMP", "required": True}]
        result = validate_and_bind(defs, {"ts": "2024-06-01T12:00:00"})
        assert result["ts"] == datetime.datetime(2024, 6, 1, 12, 0, 0)

    def test_required_defaults_to_true_when_omitted(self):
        # If "required" key is absent, the param is treated as required
        defs = [{"name": "id", "type": "NUMBER"}]
        with pytest.raises(ValueError, match="Missing required parameter"):
            validate_and_bind(defs, {})
