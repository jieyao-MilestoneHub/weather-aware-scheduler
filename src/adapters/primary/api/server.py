from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.graph.builder import build_graph
from src.models.state import SchedulerState
from src.models.outputs import EventSummary

app = FastAPI(
    title="Weather-Aware Scheduler API",
    description="Primary Adapter for Weather-Aware Scheduler",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScheduleRequest(BaseModel):
    input: str

class ScheduleResponse(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    clarification_needed: bool = False
    missing_fields: Optional[List[str]] = None

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/schedule", response_model=ScheduleResponse)
async def schedule_event(request: ScheduleRequest):
    try:
        # Build the graph (Port)
        graph = build_graph()
        
        # Initialize state (Domain Object)
        initial_state = SchedulerState(input_text=request.input)
        
        # Invoke the graph (Use Case)
        result_state = graph.invoke(initial_state)
        
        # Transform Domain Output to API Response
        if result_state.get("event_summary"):
            summary_dict = result_state["event_summary"]
            return ScheduleResponse(
                status="success",
                result=summary_dict
            )
        elif result_state.get("error"):
             return ScheduleResponse(
                status="error",
                error=result_state["error"]
            )
        else:
             # Check for clarification needed (if implemented in graph)
             # For now, treat no summary/no error as generic error or partial state
             return ScheduleResponse(
                status="error",
                error="No result generated"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
