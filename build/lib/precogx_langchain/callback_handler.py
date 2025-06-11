from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult, Generation
from langchain_core.messages import BaseMessage
from ..precogx_sdk.emitter import PrecogXEmitter

# Import the shared schemas
from ..precogx_sdk.schemas import InteractionEvent, Prompt, Response, ToolCall

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
    
    def on_chain_start(self, serialized: Dict[str, Any], tags: Optional[List[str]] = None, **kwargs: Any) -> Any:
        """Run when chain starts running."""
        # Initialize a new InteractionEvent
        self._current_interaction = InteractionEvent(
            agent_id=self.agent_id,
            session_id=self.session_id, # session_id is now part of interaction_metadata in schema
            interaction_metadata={
                "session_id": self.session_id,
                "tags": tags,
                "chain_type": serialized.get("lc_serializable", {}).get("type")
            }
        )
        self._tool_calls_in_progress = {} # Reset tool calls in progress for a new chain
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        """Run when LLM starts running."""
        if self._current_interaction and prompts:
            # Capture the prompt. Assuming the first prompt in the list is the main one.
            self._current_interaction.prompt = Prompt(text=prompts[0])
            # You might want to capture more details from serialized if needed
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""
        if self._current_interaction and response.generations and response.generations[0]:
            # Capture the response text
            self._current_interaction.response.text = response.generations[0][0].text
            # You might want to capture more details from response, like tool_calls if they are in the response. 
            # LangChain sometimes includes tool calls in the LLM response before on_tool_start.
            # This is a simplification for now.
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        """Run when tool starts running."""
        if self._current_interaction:
            tool_name = serialized.get("name", "unknown_tool")
            tool_call_id = str(uuid.uuid4()) # Assign a unique ID to track this tool call
            tool_call = ToolCall(
                tool_name=tool_name,
                tool_input=input_str,
                metadata={
                    "timestamp_start": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
                }
            )
            self._current_interaction.tool_calls.append(tool_call) # Add to the interaction's list
            self._tool_calls_in_progress[tool_call_id] = tool_call # Track for on_tool_end
    
    def on_tool_end(self, output: str, name: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        # Find the corresponding tool call in _tool_calls_in_progress and update it
        # This assumes a simple case where the last tool_call_in_progress with matching name is the one that just ended.
        # A more robust approach might require more complex state tracking if tools can run in parallel or are nested.
        for tool_call_id, tool_call in reversed(list(self._tool_calls_in_progress.items())):
            if tool_call.tool_name == name and tool_call.tool_output is None:
                tool_call.tool_output = output
                tool_call.metadata["timestamp_end"] = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
                # We can optionally remove it from _tool_calls_in_progress if we are sure it's finished
                # del self._tool_calls_in_progress[tool_call_id]
                break # Assume the most recent matching tool call ended
    
    def on_text(self, text: str, **kwargs: Any) -> Any:
        """Run on arbitrary text."""
        if self._current_interaction:
            # Append to chain of thought
            if self._current_interaction.chain_of_thought is None:
                self._current_interaction.chain_of_thought = ""
            self._current_interaction.chain_of_thought += text + "\n"
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""
        if self._current_interaction:
            # You might want to add final output to response here if applicable
            # e.g., if outputs contains the final answer not captured by on_llm_end
            # self._current_interaction.response.text = outputs.get("output", self._current_interaction.response.text)

            # Send the finalized interaction event
            self.emitter.send_interaction(self._current_interaction)
            self._current_interaction = None # Reset for the next interaction
            self._tool_calls_in_progress = {} # Clear any remaining tool calls in progress
    
    def on_chain_error(self, error: Exception, tags: Optional[List[str]] = None, **kwargs: Any) -> Any:
        """Run when chain errors."""
        print(f"LangChain chain error for agent {self.agent_id}: {error}")
        if self._current_interaction:
             # Add error information to metadata
             self._current_interaction.interaction_metadata["error"] = str(error)
             self._current_interaction.interaction_metadata["error_type"] = type(error).__name__

             # Send the interaction event even if there was an error
             self.emitter.send_interaction(self._current_interaction)

             self._current_interaction = None # Reset
             self._tool_calls_in_progress = {} # Clear 