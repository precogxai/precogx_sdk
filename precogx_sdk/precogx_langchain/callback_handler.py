from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult, Generation
from langchain_core.messages import BaseMessage
from ..emitter import PrecogXEmitter

# Import the shared schemas
from ..schemas import InteractionEvent, Prompt, Response, ToolCall

class PrecogXCallbackHandler(BaseCallbackHandler):
    """Callback handler for PrecogX telemetry collection."""
    
    def __init__(self, emitter: PrecogXEmitter, agent_id: str, session_id: Optional[str] = None):
        """
        Initialize the callback handler.
        
        Args:
            emitter: PrecogXEmitter instance
            agent_id: Unique identifier for the agent
            session_id: Optional session identifier. If not provided, a UUID will be generated.
        """
        self.emitter = emitter
        self.agent_id = agent_id
        self.session_id = session_id or str(uuid.uuid4())
        self._current_interaction: Optional[InteractionEvent] = None # Use the Pydantic model
        self._tool_calls_in_progress: Dict[str, ToolCall] = {} # To track tool calls
        self._chain_of_thought: List[str] = [] # Store chain of thought separately
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Run when chain starts running."""
        # Initialize a new InteractionEvent
        chain_type = None
        if serialized and isinstance(serialized, dict):
            lc_serializable = serialized.get("lc_serializable", {})
            if isinstance(lc_serializable, dict):
                chain_type = lc_serializable.get("type")

        self._current_interaction = InteractionEvent(
            agent_id=self.agent_id,
            prompt="",  # Will be set in on_llm_start
            response="",  # Will be set in on_llm_end
            metadata={
                "session_id": self.session_id,
                "tags": kwargs.get("tags", []),
                "chain_type": chain_type,
                "inputs": inputs
            }
        )
        self._tool_calls_in_progress = {} # Reset tool calls in progress for a new chain
        self._chain_of_thought = [] # Reset chain of thought
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        """Run when LLM starts running."""
        if self._current_interaction and prompts:
            # Capture the prompt. Assuming the first prompt in the list is the main one.
            self._current_interaction.prompt = prompts[0]
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""
        if self._current_interaction and response.generations and response.generations[0]:
            # Capture the response text
            self._current_interaction.response = response.generations[0][0].text
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        """Run when tool starts running."""
        if self._current_interaction:
            tool_name = serialized.get("name", "unknown_tool")
            tool_call_id = str(uuid.uuid4()) # Assign a unique ID to track this tool call
            tool_call = ToolCall(
                tool_name=tool_name,
                parameters={"input": input_str},
                result=None
            )
            self._current_interaction.tool_calls.append(tool_call) # Add to the interaction's list
            self._tool_calls_in_progress[tool_call_id] = tool_call # Track for on_tool_end
    
    def on_tool_end(self, output: str, name: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        # Find the corresponding tool call in _tool_calls_in_progress and update it
        for tool_call_id, tool_call in reversed(list(self._tool_calls_in_progress.items())):
            if tool_call.tool_name == name and tool_call.result is None:
                tool_call.result = output
                break # Assume the most recent matching tool call ended
    
    def on_text(self, text: str, **kwargs: Any) -> Any:
        """Run on arbitrary text."""
        # Store chain of thought separately
        self._chain_of_thought.append(text)
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""
        if self._current_interaction:
            # Add chain of thought to metadata if we have any
            if self._chain_of_thought:
                self._current_interaction.metadata["chain_of_thought"] = "\n".join(self._chain_of_thought)

            # Send the finalized interaction event
            self.emitter.send_interaction(self._current_interaction)
            self._current_interaction = None # Reset for the next interaction
            self._tool_calls_in_progress = {} # Clear any remaining tool calls in progress
            self._chain_of_thought = [] # Clear chain of thought
    
    def on_chain_error(self, error: Exception, tags: Optional[List[str]] = None, **kwargs: Any) -> Any:
        """Run when chain errors."""
        print(f"LangChain chain error for agent {self.agent_id}: {error}")
        if self._current_interaction:
             # Add error information to metadata
             self._current_interaction.metadata["error"] = str(error)
             self._current_interaction.metadata["error_type"] = type(error).__name__

             # Send the interaction event even if there was an error
             self.emitter.send_interaction(self._current_interaction)

             self._current_interaction = None # Reset
             self._tool_calls_in_progress = {} # Clear
             self._chain_of_thought = [] # Clear chain of thought 