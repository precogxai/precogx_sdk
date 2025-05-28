"""
LiteLLM integration example for PrecogX SDK.

This example demonstrates how to:
1. Initialize the PrecogX client with LiteLLM
2. Set up a callback function
3. Make API calls with telemetry
4. Handle responses and errors
"""

from litellm import completion
from precogx_sdk import PrecogXClient

def precogx_callback(response):
    """Callback function to send telemetry data."""
    client.send_telemetry({
        "agent_id": "weather-agent",
        "prompt": response.messages[-1].content,
        "response": response.choices[0].message.content,
        "metadata": {
            "model": response.model,
            "usage": response.usage,
            "environment": "production",
            "version": "1.0.0"
        }
    })

def main():
    # Initialize the PrecogX client
    client = PrecogXClient(
        api_key="your-api-key",
        api_url="https://api.precogx.ai"
    )

    try:
        # Make API call with callback
        response = completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "What's the weather in New York?"}],
            callbacks=[precogx_callback]
        )

        # Print response
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model: {response.model}")
        print(f"Usage: {response.usage}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 