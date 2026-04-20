"""
OBD InsightBot API - FastAPI Backend
=====================================
Production-ready API for the OBD InsightBot chatbot.
Designed to be deployed on a VM with proper health checks,
CORS support, and session management.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import uuid
import time
import logging
from datetime import datetime

# Import the chatbot core
from .chatbot_core import (
    ChatbotEngine,
    SessionManager,
    get_session_manager,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global engine instance
chatbot_engine: Optional[ChatbotEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - load model on startup"""
    global chatbot_engine
    logger.info("Starting OBD InsightBot API...")
    
    # Initialize the chatbot engine (loads the model)
    chatbot_engine = ChatbotEngine()
    await chatbot_engine.initialize()
    
    logger.info("OBD InsightBot API ready!")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down OBD InsightBot API...")
    if chatbot_engine:
        await chatbot_engine.cleanup()


# Create FastAPI app
app = FastAPI(
    title="OBD InsightBot API",
    description="AI-powered automotive diagnostic chatbot API using IBM Granite",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for your frontend
# SECURITY: Removed wildcard "*" - only allow specific origins
# In production, configure ALLOWED_ORIGINS environment variable
import os

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",") if os.environ.get("ALLOWED_ORIGINS") else [
    "http://localhost:3000",      # Local development
    "http://localhost:5000",      # ASP.NET default
    "http://localhost:5173",      # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Restrict to needed methods
    allow_headers=["Content-Type", "Authorization"],  # Restrict to needed headers
)


# ====================
# PYDANTIC MODELS
# ====================

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=1000, description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "How's my car doing?",
                "session_id": "abc123-def456"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="Bot's response")
    session_id: str = Field(..., description="Session ID for this conversation")
    timestamp: str = Field(..., description="Response timestamp")
    intent_detected: Optional[str] = Field(None, description="Detected intent (for debugging)")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Your car is running well. Fuel at 48%, engine temp normal.",
                "session_id": "abc123-def456",
                "timestamp": "2024-01-15T10:30:00Z",
                "intent_detected": "get_quick_summary",
                "processing_time_ms": 150.5
            }
        }


class VehicleData(BaseModel):
    """Vehicle data model for setting custom vehicle state"""
    mark: Optional[str] = Field(None, description="Vehicle make/brand")
    model: Optional[str] = Field(None, description="Vehicle model")
    car_year: Optional[int] = Field(None, description="Vehicle year")
    engine_power: Optional[float] = Field(None, description="Engine power/displacement in liters")
    automatic: Optional[str] = Field(None, description="Transmission type: 'y' for automatic, 'n' for manual")
    fuel_type: Optional[str] = Field(None, description="Fuel type (Electric, Petrol, Diesel, etc.)")
    fuel_level: Optional[float] = Field(None, ge=0, le=100, description="Fuel level percentage")
    engine_coolant_temp: Optional[float] = Field(None, description="Coolant temperature in Celsius")
    engine_rpm: Optional[int] = Field(None, ge=0, description="Engine RPM")
    speed: Optional[int] = Field(None, ge=0, description="Current speed in km/h")
    trouble_codes: Optional[List[str]] = Field(None, description="Active DTC codes")
    # Additional fields for complete data transfer
    engine_runtime: Optional[str] = Field(None, description="Engine runtime (HH:MM:SS)")
    engine_load: Optional[float] = Field(None, ge=0, le=100, description="Engine load percentage")
    fuel_pressure: Optional[float] = Field(None, ge=0, description="Fuel pressure in PSI")
    ambient_air_temp: Optional[float] = Field(None, description="Ambient air temperature in Celsius")
    air_intake_temp: Optional[float] = Field(None, description="Air intake temperature in Celsius")
    throttle_pos: Optional[float] = Field(None, ge=0, le=100, description="Throttle position percentage")


class CreateSessionRequest(BaseModel):
    """Request model for creating a session with optional vehicle data"""
    session_id: Optional[str] = Field(None, description="Session ID from C# backend")
    vehicle_data: Optional[VehicleData] = Field(None, description="Vehicle data from uploaded CSV")


class SessionInfo(BaseModel):
    """Session information response"""
    session_id: str
    created_at: str
    last_activity: str
    message_count: int
    vehicle_info: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    active_sessions: int
    uptime_seconds: float
    version: str


# ====================
# API ENDPOINTS
# ====================

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": "OBD InsightBot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns the current status of the API and model.
    """
    global chatbot_engine
    
    return HealthResponse(
        status="healthy" if chatbot_engine and chatbot_engine.is_ready else "degraded",
        model_loaded=chatbot_engine.is_ready if chatbot_engine else False,
        active_sessions=chatbot_engine.session_manager.get_active_count() if chatbot_engine else 0,
        uptime_seconds=chatbot_engine.get_uptime() if chatbot_engine else 0,
        version="1.0.0"
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    
    Send a message and receive a response from the OBD InsightBot.
    Include a session_id to maintain conversation context.
    """
    global chatbot_engine
    
    if not chatbot_engine or not chatbot_engine.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Chatbot engine not ready. Please try again in a moment."
        )
    
    start_time = time.time()
    
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process the message
        result = await chatbot_engine.process_message(
            message=request.message,
            session_id=session_id
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            intent_detected=result.get("intent"),
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        # SECURITY: Don't expose internal error details to clients
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your message. Please try again."
        )


@app.post("/session/create", tags=["Session"])
async def create_session(request: Optional[CreateSessionRequest] = None):
    """
    Create a new chat session with optional custom vehicle data.
    Accepts session_id from C# backend to link sessions correctly.
    """
    global chatbot_engine

    if not chatbot_engine:
        raise HTTPException(status_code=503, detail="Engine not ready")

    # Use provided session_id or generate a new one
    session_id = request.session_id if request and request.session_id else str(uuid.uuid4())

    # Create session with optional custom vehicle data
    custom_data = None
    if request and request.vehicle_data:
        custom_data = request.vehicle_data.model_dump(exclude_none=True)

    chatbot_engine.session_manager.create_session(session_id, custom_data)

    return {
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "message": "Session created successfully"
    }


@app.get("/session/{session_id}", response_model=SessionInfo, tags=["Session"])
async def get_session(session_id: str):
    """
    Get information about a specific session.
    """
    global chatbot_engine
    
    if not chatbot_engine:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    session = chatbot_engine.session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionInfo(
        session_id=session_id,
        created_at=session["created_at"],
        last_activity=session["last_activity"],
        message_count=session["message_count"],
        vehicle_info=session["vehicle_data"]
    )


@app.delete("/session/{session_id}", tags=["Session"])
async def delete_session(session_id: str):
    """
    Delete a chat session.
    """
    global chatbot_engine
    
    if not chatbot_engine:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    success = chatbot_engine.session_manager.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}


@app.put("/session/{session_id}/vehicle", tags=["Session"])
async def update_vehicle_data(session_id: str, vehicle_data: VehicleData):
    """
    Update vehicle data for an existing session.
    This allows simulating different vehicle states.
    """
    global chatbot_engine
    
    if not chatbot_engine:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    success = chatbot_engine.session_manager.update_vehicle_data(
        session_id,
        vehicle_data.model_dump(exclude_none=True)
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Vehicle data updated successfully"}


@app.get("/dtc-codes", tags=["Reference"])
async def list_dtc_codes():
    """
    List all known DTC codes and their information.
    Useful for reference and testing.
    """
    global chatbot_engine
    
    if not chatbot_engine:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    return chatbot_engine.get_dtc_database()


@app.get("/sensors", tags=["Reference"])
async def list_sensors():
    """
    List all available sensors and their normal ranges.
    """
    global chatbot_engine
    
    if not chatbot_engine:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    return chatbot_engine.get_sensor_ranges()


# ====================
# ERROR HANDLERS
# ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An internal error occurred",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
