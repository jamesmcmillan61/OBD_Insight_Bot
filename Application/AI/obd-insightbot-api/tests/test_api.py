"""
OBD InsightBot API - Test Suite
================================
Run with: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.chatbot_core import (
    IntentRecognizer,
    DialogManager,
    FunctionExecutor,
    ResponseHumanizer,
    DTC_DATABASE,
    DEFAULT_CAR_DATA,
)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def intent_recognizer():
    return IntentRecognizer()


@pytest.fixture
def executor():
    return FunctionExecutor(DEFAULT_CAR_DATA.copy())


class TestAPIEndpoints:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_chat_basic(self, client):
        response = client.post("/chat", json={"message": "How's my car?"})
        assert response.status_code == 200
        assert "response" in response.json()
        assert len(response.json()["response"]) > 0


class TestIntentRecognition:
    def test_greeting(self, intent_recognizer):
        intent = intent_recognizer.recognize("Hello!")
        assert intent is not None
        assert intent.function_name == "greet_user"

    def test_car_status(self, intent_recognizer):
        intent = intent_recognizer.recognize("How's my car?")
        assert intent is not None
        assert intent.function_name == "get_quick_summary"

    def test_specific_dtc(self, intent_recognizer):
        intent = intent_recognizer.recognize("What is P0300?")
        assert intent is not None
        assert intent.function_name == "explain_dtc_code"
        assert intent.arguments.get("code") == "P0300"


class TestFunctionExecutor:
    def test_greet_user(self, executor):
        response = executor.greet_user()
        assert "InsightBot" in response

    def test_get_vehicle_info(self, executor):
        response = executor.get_vehicle_info()
        assert "Chevrolet" in response

    def test_explain_dtc_code(self, executor):
        response = executor.explain_dtc_code("P0300", "general")
        assert "P0300" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
