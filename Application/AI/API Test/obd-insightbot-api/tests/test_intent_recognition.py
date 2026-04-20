"""
Priority 1: Unit tests for IntentRecognizer.
Tests the rule-based intent recognition system — no mocking needed.
"""
import pytest
from app.chatbot_core import IntentRecognizer, Intent


@pytest.fixture
def recognizer():
    return IntentRecognizer()


class TestRecognizeGreetings:
    """Tests that greeting inputs are correctly identified."""

    def test_recognize_hello_returns_greet(self, recognizer):
        result = recognizer.recognize("hello")
        assert result is not None
        assert result.function_name == "greet"

    def test_recognize_hi_there_returns_greet(self, recognizer):
        result = recognizer.recognize("hi there")
        assert result is not None
        assert result.function_name == "greet"

    def test_recognize_good_morning_returns_greet(self, recognizer):
        result = recognizer.recognize("good morning")
        assert result is not None
        assert result.function_name == "greet"

    def test_recognize_hey_returns_greet(self, recognizer):
        result = recognizer.recognize("hey")
        assert result is not None
        assert result.function_name == "greet"


class TestRecognizeDTCCodes:
    """Tests that DTC code queries extract the correct code."""

    def test_recognize_uppercase_P0300_returns_dtc(self, recognizer):
        result = recognizer.recognize("what does P0300 mean")
        assert result is not None
        assert "P0300" in str(result.arguments.get("code", "")).upper()

    def test_recognize_lowercase_p0300_returns_dtc(self, recognizer):
        result = recognizer.recognize("explain p0300")
        assert result is not None
        assert "P0300" in str(result.arguments.get("code", "")).upper()

    def test_recognize_body_code_B0100(self, recognizer):
        result = recognizer.recognize("what is B0100")
        assert result is not None
        assert "B0100" in str(result.arguments.get("code", "")).upper()

    def test_recognize_chassis_code_C0035(self, recognizer):
        result = recognizer.recognize("tell me about C0035")
        assert result is not None
        assert "C0035" in str(result.arguments.get("code", "")).upper()

    def test_recognize_network_code_U0100(self, recognizer):
        result = recognizer.recognize("U0100 error")
        assert result is not None
        assert "U0100" in str(result.arguments.get("code", "")).upper()

    def test_recognize_dtc_with_cost_focus(self, recognizer):
        result = recognizer.recognize("how much does P0300 cost to fix")
        assert result is not None
        assert "P0300" in str(result.arguments.get("code", "")).upper()

    def test_recognize_dtc_with_action_focus(self, recognizer):
        result = recognizer.recognize("what should I do about P0420")
        assert result is not None
        assert "P0420" in str(result.arguments.get("code", "")).upper()

    def test_recognize_dtc_with_cause_focus(self, recognizer):
        result = recognizer.recognize("what causes P0171")
        assert result is not None
        assert "P0171" in str(result.arguments.get("code", "")).upper()


class TestRecognizeInvalidDTCCodes:
    """Tests that invalid DTC patterns are NOT matched."""

    def test_invalid_prefix_X9999_no_dtc(self, recognizer):
        result = recognizer.recognize("X9999")
        if result is not None:
            assert result.arguments.get("code") is None or "X9999" not in str(
                result.arguments.get("code", "")
            ).upper()

    def test_too_short_P03_no_dtc(self, recognizer):
        result = recognizer.recognize("P03 code")
        if result is not None:
            assert result.arguments.get("code") is None or "P03" != str(
                result.arguments.get("code", "")
            ).upper()

    def test_too_long_P03001_extracts_P0300(self, recognizer):
        """P03001 should not be treated as a valid 4-digit DTC."""
        result = recognizer.recognize("P03001")
        # The regex \b([PCBU][0-9]{4})\b should NOT match P03001
        if result is not None and result.arguments.get("code"):
            code = str(result.arguments["code"]).upper()
            assert code != "P03001"


class TestRecognizeSensorQueries:
    """Tests for sensor-related query detection."""

    def test_recognize_rpm_query(self, recognizer):
        result = recognizer.recognize("what is my RPM")
        assert result is not None

    def test_recognize_fuel_level_query(self, recognizer):
        result = recognizer.recognize("how much fuel do I have")
        assert result is not None
        assert result.function_name in ("fuel_status", "get_fuel_status")

    def test_recognize_engine_temperature(self, recognizer):
        result = recognizer.recognize("what is the engine temperature")
        assert result is not None
        assert result.function_name in (
            "temperature_check",
            "check_temperature_systems",
            "engine_status",
        )

    def test_recognize_tyre_pressure(self, recognizer):
        result = recognizer.recognize("check my tyre pressure")
        assert result is not None
        assert result.function_name in ("tyre_pressure", "check_tyre_pressure")


class TestRecognizeStatusQueries:
    """Tests for general vehicle status queries."""

    def test_recognize_car_status_how_is_my_car(self, recognizer):
        result = recognizer.recognize("how is my car doing")
        assert result is not None
        assert result.function_name in (
            "car_status",
            "get_quick_summary",
        )

    def test_recognize_vehicle_info(self, recognizer):
        result = recognizer.recognize("what car do I have")
        assert result is not None
        assert result.function_name in (
            "vehicle_info",
            "get_vehicle_info",
        )

    def test_recognize_all_error_codes(self, recognizer):
        result = recognizer.recognize("show me all error codes")
        assert result is not None
        assert result.function_name in (
            "explain_all_codes",
            "explain_all_active_codes",
        )

    def test_recognize_engine_status(self, recognizer):
        result = recognizer.recognize("how is my engine performing")
        assert result is not None
        assert result.function_name in (
            "engine_status",
            "get_engine_status",
        )


class TestRecognizeEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_recognize_empty_string_no_crash(self, recognizer):
        result = recognizer.recognize("")
        # Should return None or a fallback intent, not crash
        assert result is None or isinstance(result, Intent)

    def test_recognize_special_characters_no_crash(self, recognizer):
        result = recognizer.recognize("!@#$%^&*()")
        assert result is None or isinstance(result, Intent)

    def test_recognize_very_long_input_no_crash(self, recognizer):
        result = recognizer.recognize("a" * 10000)
        assert result is None or isinstance(result, Intent)

    def test_recognize_whitespace_only_no_crash(self, recognizer):
        result = recognizer.recognize("   ")
        assert result is None or isinstance(result, Intent)

    def test_recognize_numeric_only_no_crash(self, recognizer):
        result = recognizer.recognize("12345")
        assert result is None or isinstance(result, Intent)


class TestRecognizeAmbiguity:
    """Tests that ambiguous inputs resolve to the most specific intent."""

    def test_greeting_with_dtc_prioritizes_dtc(self, recognizer):
        result = recognizer.recognize("hello, what does P0300 mean")
        assert result is not None
        # DTC code should take priority over greeting
        assert result.arguments.get("code") is not None

    def test_multiple_intents_returns_one(self, recognizer):
        result = recognizer.recognize("check my engine and fuel")
        assert result is not None
        assert isinstance(result, Intent)


class TestRecognizeWithContext:
    """Tests intent recognition with conversation context."""

    def test_recognize_with_empty_context(self, recognizer):
        result = recognizer.recognize("hello", context={})
        assert result is not None

    def test_recognize_with_none_context(self, recognizer):
        result = recognizer.recognize("hello", context=None)
        assert result is not None

    def test_recognize_returns_intent_dataclass(self, recognizer):
        result = recognizer.recognize("hello")
        assert result is not None
        assert hasattr(result, "name")
        assert hasattr(result, "confidence")
        assert hasattr(result, "function_name")
        assert hasattr(result, "arguments")

    def test_recognize_confidence_between_0_and_1(self, recognizer):
        result = recognizer.recognize("what is P0300")
        assert result is not None
        assert 0.0 <= result.confidence <= 1.0
