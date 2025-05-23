import os
import httpx
from typing import Optional
import json

from .schemas import InteractionEvent # Import the schema

class PrecogXEmitter:
    def __init__(self, backend_url: str, api_key: str):
        if not backend_url or not api_key:
            raise ValueError("backend_url and api_key must be provided.")

        self.backend_url = backend_url.rstrip('/') # Remove trailing slash if present
        self.api_key = api_key
        self._client = httpx.Client()

    def send_interaction(self, interaction_event: InteractionEvent): # Accept InteractionEvent
        """Sends a single interaction event to the backend."""
        url = f"{self.backend_url}/api/v1/telemetry/ingest"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            # Convert to dict and print for debugging
            payload = interaction_event.model_dump()
            print("\nSending payload to backend:")
            print(json.dumps(payload, indent=2))
            
            # Send the request asynchronously in a real SDK, but sync for simplicity here
            response = self._client.post(url, json=payload, timeout=5.0, headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes
            print(f"Telemetry sent successfully: {response.status_code}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP error sending telemetry: {e}")
            if e.response is not None:
                print(f"Response body: {e.response.text}")
            # TODO: Add retry logic or error handling
        except httpx.RequestError as e:
            print(f"Error sending telemetry request: {e}")
            # TODO: Add retry logic or error handling

    def __del__(self):
        """Ensure the client is closed when the emitter is garbage collected."""
        # Only close if the client exists and is not closed
        if hasattr(self, '_client') and not self._client.is_closed:
             self._client.close()

# Example usage (for testing purposes, not part of the SDK itself)
# if __name__ == "__main__":
#     import uuid
#     import datetime
#     from .schemas import Prompt, Response, ToolCall, InteractionEvent

#     # Replace with actual URL and API Key or environment variables
#     PRECOGX_BACKEND_URL = os.environ.get("PRECOGX_BACKEND_URL", "http://localhost:8000")
#     PRECOGX_API_KEY = os.environ.get("PRECOGX_API_KEY", "your-default-api-key") # Use a secure way to manage keys

#     if PRECOGX_API_KEY == "your-default-api-key":
#          print("WARNING: Using default API key. Set PRECOGX_API_KEY environment variable.")

#     emitter = PrecogXEmitter(backend_url=PRECOGX_BACKEND_URL, api_key=PRECOGX_API_KEY)

#     # Example dummy data using the schema
#     dummy_interaction = InteractionEvent(
#         agent_id="test-agent-123",
#         prompt=Prompt(text="What is the weather?"),
#         response=Response(text="It is sunny."),
#         tool_calls=[ToolCall(tool_name="weather_tool", tool_input="London", tool_output="Sunny")],
#         chain_of_thought="Thinking step by step...",
#         interaction_metadata={"session_id": "session-xyz"}
#     )

#     emitter.send_interaction(dummy_interaction) 