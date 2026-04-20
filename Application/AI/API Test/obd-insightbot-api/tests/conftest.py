"""
Shared fixtures for OBD InsightBot unit tests.
"""
import pytest


@pytest.fixture
def sample_car_data():
    """Standard vehicle data matching DEFAULT_CAR_DATA structure."""
    return {
        "TIMESTAMP": 1502902504267,
        "MARK": "chevrolet",
        "MODEL": "agile",
        "CAR_YEAR": 2011,
        "ENGINE_POWER": 1.4,
        "AUTOMATIC": "n",
        "VEHICLE_ID": "car1",
        "BAROMETRIC_PRESSURE(KPA)": 100,
        "ENGINE_COOLANT_TEMP": 80,
        "FUEL_LEVEL": 48.60,
        "ENGINE_LOAD": 33.30,
        "AMBIENT_AIR_TEMP": 25,
        "ENGINE_RPM": 1009,
        "INTAKE_MANIFOLD_PRESSURE": 49,
        "MAF": 4.49,
        "FUEL_TYPE": "Biodiesel_Ethanol",
        "AIR_INTAKE_TEMP": 59,
        "FUEL_PRESSURE": 45,
        "SPEED": 0,
        "ENGINE_RUNTIME": "00:03:28",
        "THROTTLE_POS": 25,
        "DTC_NUMBER": "MIL is OFF 0 codes",
        "TROUBLE_CODES": ["P0300", "P0171"],
        "TIMING_ADVANCE": 56.9,
        "EQUIV_RATIO": 1.0,
        "TYRE_PRESSURE": 32,
    }


@pytest.fixture
def sample_car_data_empty():
    """Empty vehicle data for edge case testing."""
    return {}


@pytest.fixture
def sample_car_data_no_trouble_codes():
    """Vehicle data with no trouble codes."""
    return {
        "MARK": "toyota",
        "MODEL": "corolla",
        "CAR_YEAR": 2020,
        "ENGINE_POWER": 1.8,
        "FUEL_LEVEL": 75.0,
        "ENGINE_COOLANT_TEMP": 90,
        "ENGINE_RPM": 800,
        "SPEED": 60,
        "TROUBLE_CODES": [],
        "TYRE_PRESSURE": 32,
        "FUEL_PRESSURE": 40,
        "ENGINE_LOAD": 20.0,
        "THROTTLE_POS": 15.0,
    }


@pytest.fixture
def sample_car_data_critical():
    """Vehicle data with critical sensor values."""
    return {
        "MARK": "ford",
        "MODEL": "focus",
        "CAR_YEAR": 2015,
        "ENGINE_POWER": 2.0,
        "FUEL_LEVEL": 5.0,
        "ENGINE_COOLANT_TEMP": 120,
        "ENGINE_RPM": 5000,
        "SPEED": 0,
        "TROUBLE_CODES": ["P0300", "P0420", "P0171"],
        "TYRE_PRESSURE": 20,
        "FUEL_PRESSURE": 15,
        "ENGINE_LOAD": 95.0,
        "THROTTLE_POS": 90.0,
    }


@pytest.fixture
def sample_dtc_database():
    """Minimal DTC database matching the real DTC_DATABASE structure."""
    return {
        "P0300": {
            "description": "Random/Multiple Cylinder Misfire Detected",
            "severity": "HIGH",
            "possible_causes": [
                "Worn spark plugs",
                "Faulty ignition coils",
                "Vacuum leaks",
            ],
            "recommended_actions": [
                "Check and replace spark plugs",
                "Inspect ignition coils",
                "Check for vacuum leaks",
            ],
            "estimated_cost": "$100-$500",
        },
        "P0171": {
            "description": "System Too Lean (Bank 1)",
            "severity": "MEDIUM",
            "possible_causes": [
                "Vacuum leak",
                "Faulty MAF sensor",
                "Weak fuel pump",
            ],
            "recommended_actions": [
                "Check for vacuum leaks",
                "Clean or replace MAF sensor",
            ],
            "estimated_cost": "$50-$400",
        },
        "P0420": {
            "description": "Catalyst System Efficiency Below Threshold (Bank 1)",
            "severity": "MEDIUM",
            "possible_causes": [
                "Failing catalytic converter",
                "Oxygen sensor malfunction",
            ],
            "recommended_actions": [
                "Inspect catalytic converter",
                "Check oxygen sensors",
            ],
            "estimated_cost": "$500-$2000",
        },
        "P0128": {
            "description": "Coolant Thermostat (Coolant Temperature Below Thermostat Regulating Temperature)",
            "severity": "LOW",
            "possible_causes": [
                "Stuck-open thermostat",
                "Low coolant level",
            ],
            "recommended_actions": [
                "Replace thermostat",
                "Check coolant level",
            ],
            "estimated_cost": "$50-$200",
        },
    }
