"""Tests for prompts/data_exploration.py."""

from prompts.data_exploration import data_exploration


class TestDataExploration:
    def test_returns_string(self):
        result = data_exploration()
        assert isinstance(result, str)

    def test_contains_deal_facility_outstanding_references(self):
        result = data_exploration()
        assert "VLS_DEAL" in result
        assert "VLS_FACILITY" in result
        assert "VLS_OUTSTANDING" in result

    def test_no_params_offers_all_identification_options(self):
        result = data_exploration()
        assert "deal_search_by_name" in result
        assert "deal_get_by_cusip" in result
        assert "deal_list_active" in result

    def test_deal_name_uses_search_query(self):
        result = data_exploration(deal_name="Acme Corp")
        assert "deal_search_by_name" in result
        assert "Acme Corp" in result

    def test_deal_name_extracts_deal_id_instruction(self):
        result = data_exploration(deal_name="Acme Corp")
        assert "deal ID" in result

    def test_cusip_uses_deal_get_by_cusip(self):
        result = data_exploration(cusip="123456789")
        assert "deal_get_by_cusip" in result
        assert "123456789" in result

    def test_cusip_mentions_facility_cusip_fallback(self):
        result = data_exploration(cusip="123456789")
        assert "facility_get_by_cusip" in result

    def test_cusip_takes_precedence_over_deal_name(self):
        result = data_exploration(deal_name="Acme Corp", cusip="123456789")
        assert "123456789" in result
        assert "deal_search_by_name" not in result

    def test_contains_deal_get_by_id_step(self):
        result = data_exploration()
        assert "deal_get_by_id" in result

    def test_contains_facility_step(self):
        result = data_exploration()
        assert "facility_list_by_deal" in result

    def test_contains_outstanding_step(self):
        result = data_exploration()
        assert "outstanding_list_by_deal" in result

    def test_contains_summary_step(self):
        result = data_exploration()
        assert "deal_facility_outstanding_summary" in result

    def test_contains_additional_exploration_suggestions(self):
        result = data_exploration()
        assert "outstanding_summary_by_currency" in result
        assert "facility_list_maturing" in result

    def test_contains_step_structure(self):
        result = data_exploration()
        assert "Step 1" in result
        assert "Step 6" in result

    def test_contains_guidelines(self):
        result = data_exploration()
        assert "Guidelines" in result
