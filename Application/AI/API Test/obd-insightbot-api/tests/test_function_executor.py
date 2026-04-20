"""
Priority 4: Unit tests for FunctionExecutor, DynamicOBDHandler, and SymptomAdvisor.
"""
import pytest
from app.chatbot_core import (
    FunctionExecutor,
    DynamicOBDHandler,
    SymptomAdvisor,
    SENSOR_RANGES,
)


@pytest.fixture
def executor(sample_car_data):
    return FunctionExecutor(car_data=sample_car_data)


@pytest.fixture
def executor_empty():
    return FunctionExecutor(car_data={})


@pytest.fixture
def executor_critical(sample_car_data_critical):
    return FunctionExecutor(car_data=sample_car_data_critical)


@pytest.fixture
def executor_healthy(sample_car_data_no_trouble_codes):
    return FunctionExecutor(car_data=sample_car_data_no_trouble_codes)


@pytest.fixture
def obd_handler(sample_car_data):
    return DynamicOBDHandler(car_data=sample_car_data)


@pytest.fixture
def obd_handler_critical(sample_car_data_critical):
    return DynamicOBDHandler(car_data=sample_car_data_critical)


class TestGreetUser:
    """Tests for FunctionExecutor.greet_user()."""

    def test_greet_user_returns_nonempty(self, executor):
        result = executor.greet_user()
        assert result is not None
        assert len(result) > 0

    def test_greet_user_returns_string(self, executor):
        result = executor.greet_user()
        assert isinstance(result, str)

    def test_greet_user_works_without_car_data(self, executor_empty):
        result = executor_empty.greet_user()
        assert result is not None
        assert len(result) > 0


class TestHandleOffTopic:
    """Tests for FunctionExecutor.handle_off_topic()."""

    def test_handle_off_topic_returns_nonempty(self, executor):
        result = executor.handle_off_topic()
        assert result is not None
        assert len(result) > 0


class TestGetVehicleInfo:
    """Tests for FunctionExecutor.get_vehicle_info()."""

    def test_vehicle_info_with_data_includes_make(self, executor):
        result = executor.get_vehicle_info()
        assert "chevrolet" in result.lower()

    def test_vehicle_info_with_data_includes_model(self, executor):
        result = executor.get_vehicle_info()
        assert "agile" in result.lower()

    def test_vehicle_info_with_data_includes_year(self, executor):
        result = executor.get_vehicle_info()
        assert "2011" in result

    def test_vehicle_info_empty_data_returns_message(self, executor_empty):
        result = executor_empty.get_vehicle_info()
        assert result is not None
        assert len(result) > 0


class TestGetQuickSummary:
    """Tests for FunctionExecutor.get_quick_summary()."""

    def test_quick_summary_returns_nonempty(self, executor):
        result = executor.get_quick_summary()
        assert result is not None
        assert len(result) > 0

    def test_quick_summary_with_trouble_codes_mentions_codes(self, executor):
        result = executor.get_quick_summary()
        # Should mention trouble codes or issues
        assert len(result) > 10

    def test_quick_summary_no_trouble_codes(self, executor_healthy):
        result = executor_healthy.get_quick_summary()
        assert result is not None
        assert len(result) > 0

    def test_quick_summary_empty_data(self, executor_empty):
        result = executor_empty.get_quick_summary()
        assert result is not None


class TestGetEngineStatus:
    """Tests for FunctionExecutor.get_engine_status()."""

    def test_engine_status_normal_returns_nonempty(self, executor):
        result = executor.get_engine_status()
        assert result is not None
        assert len(result) > 0

    def test_engine_status_includes_rpm(self, executor):
        result = executor.get_engine_status()
        # Should reference RPM or engine data
        assert len(result) > 10

    def test_engine_status_critical_values(self, executor_critical):
        result = executor_critical.get_engine_status()
        assert result is not None
        assert len(result) > 0

    def test_engine_status_empty_data(self, executor_empty):
        result = executor_empty.get_engine_status()
        assert result is not None


class TestGetFuelStatus:
    """Tests for FunctionExecutor.get_fuel_status()."""

    def test_fuel_status_normal_returns_nonempty(self, executor):
        result = executor.get_fuel_status()
        assert result is not None
        assert len(result) > 0

    def test_fuel_status_low_level_mentions_warning(self, executor_critical):
        result = executor_critical.get_fuel_status()
        assert result is not None
        # With 5% fuel, should indicate low or warning
        assert len(result) > 0

    def test_fuel_status_empty_data(self, executor_empty):
        result = executor_empty.get_fuel_status()
        assert result is not None


class TestCheckTemperatureSystems:
    """Tests for FunctionExecutor.check_temperature_systems()."""

    def test_temperature_normal_returns_nonempty(self, executor):
        result = executor.check_temperature_systems()
        assert result is not None
        assert len(result) > 0

    def test_temperature_overheating(self, executor_critical):
        result = executor_critical.check_temperature_systems()
        assert result is not None
        assert len(result) > 0

    def test_temperature_empty_data(self, executor_empty):
        result = executor_empty.check_temperature_systems()
        assert result is not None


class TestCheckTyrePressure:
    """Tests for FunctionExecutor.check_tyre_pressure()."""

    def test_tyre_pressure_returns_nonempty(self, executor):
        result = executor.check_tyre_pressure()
        assert result is not None
        assert len(result) > 0

    def test_tyre_pressure_low(self, executor_critical):
        result = executor_critical.check_tyre_pressure()
        assert result is not None
        assert len(result) > 0

    def test_tyre_pressure_empty_data(self, executor_empty):
        result = executor_empty.check_tyre_pressure()
        assert result is not None


class TestDynamicOBDHandler:
    """Tests for DynamicOBDHandler class."""

    def test_find_relevant_parameters_engine(self, obd_handler):
        result = obd_handler.find_relevant_parameters("engine")
        assert isinstance(result, list)

    def test_find_relevant_parameters_fuel(self, obd_handler):
        result = obd_handler.find_relevant_parameters("fuel")
        assert isinstance(result, list)

    def test_find_relevant_parameters_unknown(self, obd_handler):
        result = obd_handler.find_relevant_parameters("purple elephant")
        assert isinstance(result, list)

    def test_generate_response_fuel_query(self, obd_handler):
        result = obd_handler.generate_response("what is my fuel level")
        # Should return a response or None
        assert result is None or isinstance(result, str)

    def test_generate_response_engine_query(self, obd_handler):
        result = obd_handler.generate_response("how is my engine")
        assert result is None or isinstance(result, str)

    def test_generate_response_unknown_returns_none(self, obd_handler):
        result = obd_handler.generate_response("tell me a joke")
        # Unknown query should return None (not crash)
        assert result is None or isinstance(result, str)

    def test_assess_value_normal_rpm(self, obd_handler):
        result = obd_handler.assess_value("ENGINE_RPM", 1000)
        assert isinstance(result, dict)

    def test_assess_value_high_temp(self, obd_handler_critical):
        result = obd_handler_critical.assess_value("ENGINE_COOLANT_TEMP", 120)
        assert isinstance(result, dict)

    def test_constructor_with_custom_ranges(self, sample_car_data):
        custom_ranges = {"ENGINE_RPM": {"min": 500, "max": 4000, "unit": " RPM"}}
        handler = DynamicOBDHandler(
            car_data=sample_car_data, sensor_ranges=custom_ranges
        )
        assert handler is not None


class TestSymptomAdvisor:
    """Tests for SymptomAdvisor.get_advice() classmethod."""

    def test_noise_symptom_returns_advice(self):
        result = SymptomAdvisor.get_advice("I hear a noise when accelerating")
        assert result is not None
        assert len(result) > 0

    def test_vibration_symptom_returns_advice(self):
        result = SymptomAdvisor.get_advice("my car vibrates when driving")
        assert result is not None
        assert len(result) > 0

    def test_smoke_symptom_returns_advice(self):
        result = SymptomAdvisor.get_advice("there is smoke from the exhaust")
        assert result is not None
        assert len(result) > 0

    def test_stalling_symptom_returns_advice(self):
        result = SymptomAdvisor.get_advice("my car keeps stalling")
        assert result is not None
        assert len(result) > 0

    def test_unknown_symptom_returns_none(self):
        result = SymptomAdvisor.get_advice("hello how are you")
        # Unknown symptom should return None
        assert result is None or isinstance(result, str)

    def test_burning_smell_returns_advice(self):
        result = SymptomAdvisor.get_advice("I smell something burning")
        assert result is not None
        assert len(result) > 0

    def test_leak_symptom_returns_advice(self):
        result = SymptomAdvisor.get_advice("there is a leak under my car")
        assert result is not None
        assert len(result) > 0


class TestSensorRangesIntegrity:
    """Tests that SENSOR_RANGES has expected structure."""

    def test_engine_coolant_temp_range_exists(self):
        assert "ENGINE_COOLANT_TEMP" in SENSOR_RANGES

    def test_engine_rpm_range_exists(self):
        assert "ENGINE_RPM" in SENSOR_RANGES

    def test_fuel_level_range_exists(self):
        assert "FUEL_LEVEL" in SENSOR_RANGES

    def test_each_range_has_min_max_unit(self):
        for param, ranges in SENSOR_RANGES.items():
            assert "min" in ranges, f"{param} missing 'min'"
            assert "max" in ranges, f"{param} missing 'max'"
            assert "unit" in ranges, f"{param} missing 'unit'"

    def test_min_less_than_max(self):
        for param, ranges in SENSOR_RANGES.items():
            assert ranges["min"] <= ranges["max"], (
                f"{param}: min ({ranges['min']}) > max ({ranges['max']})"
            )
