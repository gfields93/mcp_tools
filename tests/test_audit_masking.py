"""Tests for audit/masking.py — pure function, no DB required."""
import pytest

from audit.masking import MASKED, UPPER_ENVS, mask_parameters

_PARAM_DEFS = [
    {"name": "customer_id", "type": "NUMBER", "sensitive": False},
    {"name": "ssn", "type": "VARCHAR2", "sensitive": True},
    {"name": "status", "type": "VARCHAR2"},  # no 'sensitive' key — defaults False
]
_PARAMS = {"customer_id": 123, "ssn": "123-45-6789", "status": "OPEN"}


class TestMaskParametersLowerEnvironments:
    @pytest.mark.parametrize("env", ["local", "dev", "sit"])
    def test_returns_unchanged_params(self, env):
        result = mask_parameters(_PARAMS, _PARAM_DEFS, env)
        assert result == _PARAMS

    @pytest.mark.parametrize("env", ["local", "dev", "sit"])
    def test_returns_a_copy_not_original(self, env):
        result = mask_parameters(_PARAMS, _PARAM_DEFS, env)
        assert result is not _PARAMS

    def test_sensitive_not_masked_in_lower_env(self):
        result = mask_parameters(_PARAMS, _PARAM_DEFS, "dev")
        assert result["ssn"] == "123-45-6789"


class TestMaskParametersUpperEnvironments:
    @pytest.mark.parametrize("env", ["uat", "prod"])
    def test_sensitive_value_is_masked(self, env):
        result = mask_parameters(_PARAMS, _PARAM_DEFS, env)
        assert result["ssn"] == MASKED

    @pytest.mark.parametrize("env", ["uat", "prod"])
    def test_non_sensitive_value_preserved(self, env):
        result = mask_parameters(_PARAMS, _PARAM_DEFS, env)
        assert result["customer_id"] == 123

    @pytest.mark.parametrize("env", ["uat", "prod"])
    def test_untagged_value_preserved(self, env):
        # 'status' has no 'sensitive' key → treated as not sensitive
        result = mask_parameters(_PARAMS, _PARAM_DEFS, env)
        assert result["status"] == "OPEN"

    def test_all_non_sensitive_params_unchanged_in_prod(self):
        defs = [{"name": "x", "sensitive": False}, {"name": "y", "sensitive": False}]
        result = mask_parameters({"x": 1, "y": 2}, defs, "prod")
        assert result == {"x": 1, "y": 2}

    def test_all_sensitive_params_masked_in_prod(self):
        defs = [{"name": "a", "sensitive": True}, {"name": "b", "sensitive": True}]
        result = mask_parameters({"a": "secret1", "b": "secret2"}, defs, "prod")
        assert result == {"a": MASKED, "b": MASKED}


class TestMaskParametersEdgeCases:
    def test_empty_params_returns_empty(self):
        result = mask_parameters({}, _PARAM_DEFS, "prod")
        assert result == {}

    def test_empty_defs_no_masking(self):
        result = mask_parameters({"x": "value"}, [], "prod")
        assert result == {"x": "value"}

    def test_missing_sensitive_flag_defaults_to_false(self):
        defs = [{"name": "x"}]
        result = mask_parameters({"x": "value"}, defs, "prod")
        assert result["x"] == "value"

    def test_upper_envs_constant_contains_uat_and_prod(self):
        assert "uat" in UPPER_ENVS
        assert "prod" in UPPER_ENVS
        assert "local" not in UPPER_ENVS
        assert "dev" not in UPPER_ENVS
