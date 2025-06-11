from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

class ToolCall(BaseModel):
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = None

class Interaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: List[ToolCall]
    metadata: Optional[Dict[str, Any]] = None

class Detection(BaseModel):
    type: str
    score: float
    details: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TelemetryData(BaseModel):
    agent_id: str
    session_id: str
    interactions: List[Interaction]
    detections: Optional[List[Detection]] = None
    metadata: Optional[Dict[str, Any]] = None 