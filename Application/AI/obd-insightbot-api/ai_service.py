from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import time
from ai_core import get_model_response_with_context

app = FastAPI()

# In-memory session store: session_id -> {vehicle_data, history}
_sessions: Dict[str, Dict] = {}


# ── Models ────────────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    sessionId: str
    message: str
    carData: Dict[str, Any]
    history: List[HistoryItem] = []

class ChatResponse(BaseModel):
    reply: str

class SessionCreateRequest(BaseModel):
    session_id: str
    vehicle_data: Optional[Dict[str, Any]] = None

class LegacyChatRequest(BaseModel):
    message: str
    session_id: str

class LegacyChatResponse(BaseModel):
    response: str
    session_id: str
    intent_detected: Optional[str] = None
    processing_time_ms: float


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy"}


def _normalise_vehicle_data(data: dict) -> dict:
    """ai_core.py expects UPPERCASE keys (e.g. FUEL_LEVEL, ENGINE_RPM).
    The C# backend sends lowercase (fuel_level, engine_rpm), so uppercase everything."""
    return {k.upper(): v for k, v in data.items()}

@app.post("/session/create")
def session_create(req: SessionCreateRequest):
    """Called by the C# backend to register vehicle data for a session."""
    _sessions[req.session_id] = {
        "vehicle_data": _normalise_vehicle_data(req.vehicle_data) if req.vehicle_data else {},
        "history": [],
    }
    return {"session_id": req.session_id, "message": "Session created successfully"}


@app.post("/chat")
def chat(req: LegacyChatRequest):
    """Called by the C# backend. Looks up session vehicle data and history."""
    start = time.time()
    session = _sessions.get(req.session_id, {"vehicle_data": {}, "history": []})

    reply = get_model_response_with_context(
        user_query=req.message,
        history=session["history"],
        car_data=session["vehicle_data"],
        dialog_manager=None,
    )

    # Append to history for this session
    session["history"].append({"role": "user", "content": req.message})
    session["history"].append({"role": "assistant", "content": reply})
    _sessions[req.session_id] = session

    processing_time_ms = round((time.time() - start) * 1000, 2)
    return LegacyChatResponse(
        response=reply,
        session_id=req.session_id,
        processing_time_ms=processing_time_ms,
    )


@app.post("/chat/respond", response_model=ChatResponse)
def chat_respond(req: ChatRequest):
    """Direct endpoint passing full context per request (stateless)."""
    history_dicts = [{"role": h.role, "content": h.content} for h in req.history]
    reply = get_model_response_with_context(
        user_query=req.message,
        history=history_dicts,
        car_data=req.carData,
        dialog_manager=None,
    )
    return ChatResponse(reply=reply)
