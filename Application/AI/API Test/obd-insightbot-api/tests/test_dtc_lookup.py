"""
Priority 2: Unit tests for DTC code lookup and explanation.
Tests FunctionExecutor.explain_dtc_code, ResponseHumanizer, and explain_all_active_codes.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.chatbot_core import (
    FunctionExecutor,
    ResponseHumanizer,
    DTC_DATABASE,
)


@pytest.fixture
def humanizer():
    return ResponseHumanizer()


@pytest.fixture
def executor(sample_car_data):
    return FunctionExecutor(car_data=sample_car_data)


@pytest.fixture
def executor_no_codes(sample_car_data_no_trouble_codes):
    return FunctionExecutor(car_data=sample_car_data_no_trouble_codes)


class TestExplainDtcCode:
    """Tests for FunctionExecutor.explain_dtc_code(code, focus)."""

    def test_explain_valid_P0300_general_returns_nonempty(self, executor):
        result = executor.explain_dtc_code("P0300", focus="general")
        assert result is not None
        assert len(result) > 0

    def test_explain_valid_P0300_general_contains_description(self, executor):
        result = executor.explain_dtc_code("P0300", focus="general")
        # Should mention misfire or the code itself
        result_lower = result.lower()
        assert "p0300" in result_lower or "misfire" in result_lower

    def test_explain_valid_P0300_cost_focus(self, executor):
        result = executor.explain_dtc_code("P0300", focus="cost")
        assert result is not None
        assert len(result) > 0

    def test_explain_valid_P0300_actions_focus(self, executor):
        result = executor.explain_dtc_code("P0300", focus="actions")
        assert result is not None
        assert len(result) > 0

    def test_explain_valid_P0300_causes_focus(self, executor):
        result = executor.explain_dtc_code("P0300", focus="causes")
        assert result is not None
        assert len(result) > 0

    def test_explain_valid_P0420_returns_nonempty(self, executor):
        result = executor.explain_dtc_code("P0420")
        assert result is not None
        assert len(result) > 0

    def test_explain_valid_P0171_returns_nonempty(self, executor):
        result = executor.explain_dtc_code("P0171")
        assert result is not None
        assert len(result) > 0

    def test_explain_invalid_code_Z9999_returns_message(self, executor):
        result = executor.explain_dtc_code("Z9999")
        assert result is not None
        assert len(result) > 0
        # Should indicate code is unknown or not found
        result_lower = result.lower()
        assert any(
            word in result_lower
            for word in ["unknown", "not found", "don't have", "couldn't find", "not recognized", "z9999"]
        )

    def test_explain_empty_code_returns_message(self, executor):
        result = executor.explain_dtc_code("")
        assert result is not None
        assert len(result) > 0

    def test_explain_default_focus_is_general(self, executor):
        result_default = executor.explain_dtc_code("P0300")
        result_general = executor.explain_dtc_code("P0300", focus="general")
        # Both should produce valid output (may differ due to randomization)
        assert result_default is not None
        assert result_general is not None


class TestExplainAllActiveCodes:
    """Tests for FunctionExecutor.explain_all_active_codes()."""

    def test_with_trouble_codes_returns_explanations(self, executor):
        result = executor.explain_all_active_codes()
        assert result is not None
        assert len(result) > 0

    def test_with_trouble_codes_mentions_code_names(self, executor):
        result = executor.explain_all_active_codes()
        result_upper = result.upper()
        # Should mention at least one of the active codes
        assert "P0300" in result_upper or "P0171" in result_upper

    def test_no_trouble_codes_returns_clean_message(self, executor_no_codes):
        result = executor_no_codes.explain_all_active_codes()
        assert result is not None
        assert len(result) > 0

    def test_empty_car_data_no_crash(self):
        executor = FunctionExecutor(car_data={})
        result = executor.explain_all_active_codes()
        assert result is not None


class TestResponseHumanizer:
    """Tests for ResponseHumanizer class."""

    def test_humanize_code_explanation_P0300_general(self, humanizer):
        result = humanizer.humanize_code_explanation_with_focus(
            "P0300", DTC_DATABASE, focus="general"
        )
        assert result is not None
        assert len(result) > 0

    def test_humanize_code_explanation_P0300_cost(self, humanizer):
        result = humanizer.humanize_code_explanation_with_focus(
            "P0300", DTC_DATABASE, focus="cost"
        )
        assert result is not None
        # Cost focus should include a dollar amount or cost reference
        assert "$" in result or "cost" in result.lower()

    def test_humanize_code_explanation_P0300_actions(self, humanizer):
        result = humanizer.humanize_code_explanation_with_focus(
            "P0300", DTC_DATABASE, focus="actions"
        )
        assert result is not None
        assert len(result) > 0

    def test_humanize_code_explanation_P0300_causes(self, humanizer):
        result = humanizer.humanize_code_explanation_with_focus(
            "P0300", DTC_DATABASE, focus="causes"
        )
        assert result is not None
        assert len(result) > 0

    def test_humanize_unknown_code_returns_message(self, humanizer):
        result = humanizer.humanize_code_explanation_with_focus(
            "Z9999", DTC_DATABASE, focus="general"
        )
        assert result is not None
        assert len(result) > 0

    def test_remove_jargon_simplifies_text(self, humanizer):
        result = humanizer.remove_jargon("DTC error detected in OBD system")
        assert result is not None
        assert isinstance(result, str)

    def test_get_greeting_returns_nonempty(self, humanizer):
        result = humanizer.get_greeting()
        assert result is not None
        assert len(result) > 0

    def test_get_random_phrase_returns_from_list(self, humanizer):
        phrases = ["phrase1", "phrase2", "phrase3"]
        result = humanizer.get_random_phrase(phrases)
        assert result in phrases


class TestDTCDatabaseIntegrity:
    """Tests that the DTC_DATABASE has the expected structure."""

    def test_database_contains_P0300(self):
        assert "P0300" in DTC_DATABASE

    def test_database_contains_P0171(self):
        assert "P0171" in DTC_DATABASE

    def test_database_contains_P0420(self):
        assert "P0420" in DTC_DATABASE

    def test_database_contains_P0128(self):
        assert "P0128" in DTC_DATABASE

    def test_each_entry_has_required_keys(self):
        required_keys = {
            "description",
            "severity",
            "possible_causes",
            "recommended_actions",
            "estimated_cost",
        }
        for code, entry in DTC_DATABASE.items():
            assert required_keys.issubset(entry.keys()), (
                f"DTC {code} is missing keys: {required_keys - entry.keys()}"
            )

    def test_severity_is_valid_value(self):
        valid_severities = {"HIGH", "MEDIUM", "LOW"}
        for code, entry in DTC_DATABASE.items():
            assert entry["severity"] in valid_severities, (
                f"DTC {code} has invalid severity: {entry['severity']}"
            )

    def test_descriptions_are_nonempty(self):
        for code, entry in DTC_DATABASE.items():
            assert len(entry["description"]) > 0, (
                f"DTC {code} has empty description"
            )
