from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
from ..precogx_sdk.client import PrecogXClient
from ..precogx_sdk.models import ToolCall, Interaction, TelemetryData

class PrecogXCallbackHandler(BaseCallbackHandler):
    """Callback handler for PrecogX telemetry collection."""
    
    def __init__(
        self,
        client: PrecogXClient,
        agent_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the callback handler.
        
        Args:
            client: PrecogXClient instance
            agent_id: Unique identifier for the agent
            session_id: Optional session identifier. If not provided, a UUID will be generated.
            metadata: Optional metadata to include with all telemetry data
        """
        self.client = client
        self.agent_id = agent_id
        self.session_id = session_id or str(uuid.uuid4())
        self.metadata = metadata or {}
        
        # State tracking
        self.current_interaction: Optional[Interaction] = None
        self.pending_tool_calls: Dict[str, ToolCall] = {}
    
    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Called when the agent is about to execute an action."""
        # Create a new tool call
        tool_call = ToolCall(
            tool_name=action.tool,
            tool_input=action.tool_input,
            metadata={
                "thought": action.log,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Store the tool call with a unique ID
        tool_id = str(uuid.uuid4())
        self.pending_tool_calls[tool_id] = tool_call
        
        # If this is the first tool call in a new interaction, create the interaction
        if not self.current_interaction:
            self.current_interaction = Interaction(
                tool_calls=[tool_call],
                metadata=self.metadata
            )
        else:
            self.current_interaction.tool_calls.append(tool_call)
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool execution ends."""
        # Find the most recent pending tool call
        if not self.pending_tool_calls:
            return
            
        # Get the most recent tool call
        tool_id = list(self.pending_tool_calls.keys())[-1]
        tool_call = self.pending_tool_calls.pop(tool_id)
        
        # Update the tool call with the output
        tool_call.tool_output = output
        
        # If this was the last tool call in the interaction, send the telemetry
        if not self.pending_tool_calls and self.current_interaction:
            self._send_telemetry()
    
    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Called when the agent finishes."""
        # Send any remaining telemetry
        if self.current_interaction:
            self._send_telemetry()
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Called when the LLM starts."""
        # We could track LLM inputs here if needed
        pass
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when the LLM ends."""
        # We could track LLM outputs here if needed
        pass
    
    def _send_telemetry(self) -> None:
        """Send the current interaction as telemetry data."""
        if not self.current_interaction:
            return
            
        try:
            # Create the telemetry data
            telemetry_data = TelemetryData(
                agent_id=self.agent_id,
                session_id=self.session_id,
                interactions=[self.current_interaction],
                metadata=self.metadata
            )
            
            # Send the data
            self.client.send_telemetry(telemetry_data.model_dump())
            
            # Reset the current interaction
            self.current_interaction = None
            
        except Exception as e:
            # Log the error but don't raise it to avoid disrupting the agent
            print(f"Error sending telemetry: {str(e)}") 