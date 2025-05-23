from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import datetime
import uuid

# Assuming these match the backend schemas defined in precogx_product/app/core/telemetry/schemas.py

class Prompt(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None # e.g., base64 encoded or URL
    audio: Optional[str] = None # e.g., base64 encoded or URL
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Response(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None # e.g., base64 encoded or URL
    audio: Optional[str] = None # e.g., base64 encoded or URL
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[str] = None

class InteractionEvent(BaseModel):
    agent_id: str
    prompt: str
    response: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Note: risk_score and detection_flags will be added by the backend
    risk_score: Optional[float] = None
    detection_flags: Optional[Dict[str, Any]] = None

# Need to add import for uuid
import uuid 