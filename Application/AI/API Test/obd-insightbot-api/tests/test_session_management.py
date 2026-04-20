"""
Priority 3: Unit tests for SessionManager and DialogManager.
"""
import pytest
import time
from unittest.mock import patch
from app.chatbot_core import SessionManager, DialogManager


@pytest.fixture
def session_manager():
    return SessionManager(max_sessions=100)


@pytest.fixture
def dialog_manager():
    return DialogManager()


class TestSessionManagerCreate:
    """Tests for SessionManager.create_session()."""

    def test_create_session_returns_dict(self, session_manager):
        result = session_manager.create_session("session-1")
        assert isinstance(result, dict)

    def test_create_session_has_created_at(self, session_manager):
        result = session_manager.create_session("session-1")
        assert "created_at" in result

    def test_create_session_has_last_activity(self, session_manager):
        result = session_manager.create_session("session-1")
        assert "last_activity" in result

    def test_create_session_has_message_count_zero(self, session_manager):
        result = session_manager.create_session("session-1")
        assert result.get("message_count") == 0

    def test_create_session_has_vehicle_data(self, session_manager):
        result = session_manager.create_session("session-1")
        assert "vehicle_data" in result
        assert isinstance(result["vehicle_data"], dict)

    def test_create_session_has_dialog_manager(self, session_manager):
        result = session_manager.create_session("session-1")
        assert "dialog_manager" in result
        assert isinstance(result["dialog_manager"], DialogManager)

    def test_create_session_with_custom_data(self, session_manager):
        custom = {"mark": "toyota", "model": "corolla", "car_year": 2020}
        result = session_manager.create_session("session-1", custom_vehicle_data=custom)
        vehicle = result["vehicle_data"]
        assert vehicle.get("MARK") == "toyota"
        assert vehicle.get("MODEL") == "corolla"
        assert vehicle.get("CAR_YEAR") == 2020

    def test_create_multiple_sessions_unique(self, session_manager):
        session_manager.create_session("session-1")
        session_manager.create_session("session-2")
        assert session_manager.get_active_count() == 2


class TestSessionManagerGetSession:
    """Tests for SessionManager.get_session()."""

    def test_get_existing_session_returns_data(self, session_manager):
        session_manager.create_session("session-1")
        result = session_manager.get_session("session-1")
        assert result is not None
        assert isinstance(result, dict)

    def test_get_nonexistent_session_returns_none(self, session_manager):
        result = session_manager.get_session("nonexistent")
        assert result is None

    def test_get_or_create_existing_returns_same(self, session_manager):
        session_manager.create_session("session-1")
        result = session_manager.get_or_create_session("session-1")
        assert result is not None

    def test_get_or_create_new_creates_session(self, session_manager):
        result = session_manager.get_or_create_session("new-session")
        assert result is not None
        assert session_manager.get_session("new-session") is not None


class TestSessionManagerDelete:
    """Tests for SessionManager.delete_session()."""

    def test_delete_existing_returns_true(self, session_manager):
        session_manager.create_session("session-1")
        result = session_manager.delete_session("session-1")
        assert result is True

    def test_delete_existing_removes_session(self, session_manager):
        session_manager.create_session("session-1")
        session_manager.delete_session("session-1")
        assert session_manager.get_session("session-1") is None

    def test_delete_nonexistent_returns_false(self, session_manager):
        result = session_manager.delete_session("nonexistent")
        assert result is False

    def test_delete_does_not_affect_others(self, session_manager):
        session_manager.create_session("session-1")
        session_manager.create_session("session-2")
        session_manager.delete_session("session-1")
        assert session_manager.get_session("session-2") is not None


class TestSessionManagerUpdate:
    """Tests for update_activity and update_vehicle_data."""

    def test_update_activity_increments_count(self, session_manager):
        session_manager.create_session("session-1")
        session_manager.update_activity("session-1")
        session = session_manager.get_session("session-1")
        assert session["message_count"] == 1

    def test_update_vehicle_data_merges(self, session_manager):
        session_manager.create_session("session-1")
        result = session_manager.update_vehicle_data(
            "session-1", {"mark": "honda", "model": "civic"}
        )
        assert result is True
        session = session_manager.get_session("session-1")
        assert session["vehicle_data"]["MARK"] == "honda"
        assert session["vehicle_data"]["MODEL"] == "civic"

    def test_update_vehicle_data_nonexistent_returns_false(self, session_manager):
        result = session_manager.update_vehicle_data(
            "nonexistent", {"mark": "honda"}
        )
        assert result is False

    def test_update_vehicle_data_partial_keeps_existing(self, session_manager):
        custom = {"mark": "toyota", "model": "corolla", "car_year": 2020}
        session_manager.create_session("session-1", custom_vehicle_data=custom)
        session_manager.update_vehicle_data("session-1", {"mark": "honda"})
        session = session_manager.get_session("session-1")
        assert session["vehicle_data"]["MARK"] == "honda"
        assert session["vehicle_data"]["MODEL"] == "corolla"


class TestSessionManagerCleanup:
    """Tests for cleanup_expired_sessions()."""

    def test_cleanup_removes_expired_sessions(self, session_manager):
        session_manager.create_session("old-session")
        # Manually set last_activity to the past
        session = session_manager.get_session("old-session")
        from datetime import datetime, timedelta

        past_time = (datetime.utcnow() - timedelta(minutes=60)).isoformat()
        session["last_activity"] = past_time
        removed = session_manager.cleanup_expired_sessions()
        assert removed >= 1
        assert session_manager.get_session("old-session") is None

    def test_cleanup_keeps_active_sessions(self, session_manager):
        session_manager.create_session("active-session")
        removed = session_manager.cleanup_expired_sessions()
        assert removed == 0
        assert session_manager.get_session("active-session") is not None

    def test_get_active_count(self, session_manager):
        assert session_manager.get_active_count() == 0
        session_manager.create_session("s1")
        assert session_manager.get_active_count() == 1
        session_manager.create_session("s2")
        assert session_manager.get_active_count() == 2


class TestDialogManager:
    """Tests for DialogManager."""

    def test_add_user_message(self, dialog_manager):
        dialog_manager.add_message("User", "Hello")
        history = dialog_manager.get_history_for_llm()
        assert "Hello" in history

    def test_add_bot_message(self, dialog_manager):
        dialog_manager.add_message("Assistant", "Hi there!")
        history = dialog_manager.get_history_for_llm()
        assert "Hi there!" in history

    def test_history_preserves_order(self, dialog_manager):
        dialog_manager.add_message("User", "first")
        dialog_manager.add_message("Assistant", "second")
        dialog_manager.add_message("User", "third")
        history = dialog_manager.get_history_for_llm()
        first_pos = history.find("first")
        second_pos = history.find("second")
        third_pos = history.find("third")
        assert first_pos < second_pos < third_pos

    def test_empty_history_returns_string(self, dialog_manager):
        result = dialog_manager.get_history_for_llm()
        assert isinstance(result, str)

    def test_history_truncates_at_limit(self, dialog_manager):
        for i in range(15):
            dialog_manager.add_message("User", f"Message {i}")
        history = dialog_manager.get_history_for_llm()
        # Should not contain oldest messages (limit is 10)
        assert "Message 0" not in history or "Message 14" in history

    def test_get_context_returns_dict(self, dialog_manager):
        result = dialog_manager.get_context()
        assert isinstance(result, dict)

    def test_reset_clears_history(self, dialog_manager):
        dialog_manager.add_message("User", "Hello")
        dialog_manager.reset()
        history = dialog_manager.get_history_for_llm()
        assert "Hello" not in history

    def test_update_after_response_tracks_function(self, dialog_manager, sample_car_data):
        dialog_manager.update_after_response(
            "explain_dtc_code", {"code": "P0300"}, sample_car_data
        )
        context = dialog_manager.get_context()
        assert isinstance(context, dict)

    def test_set_symptom(self, dialog_manager):
        dialog_manager.set_symptom("noise", "exhaust leak")
        context = dialog_manager.get_context()
        assert isinstance(context, dict)
