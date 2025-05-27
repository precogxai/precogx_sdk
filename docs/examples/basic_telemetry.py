"""
Basic telemetry example for PrecogX SDK.

This example demonstrates how to:
1. Initialize the PrecogX client
2. Send basic telemetry data
3. Handle the response
4. Add custom metadata
"""

from precogx_sdk import PrecogXClient

def main():
    # Initialize the client
    client = PrecogXClient(
        api_key="your-api-key",
        api_url="https://api.precogx.ai"  # Optional: defaults to production URL
    )

    # Basic telemetry data
    telemetry_data = {
        "agent_id": "weather-agent",
        "prompt": "What's the weather in New York?",
        "response": "The weather in New York is currently 72°F and sunny.",
        "tool_calls": [],
        "metadata": {
            "model": "gpt-4",
            "temperature": 0.7,
            "environment": "production",
            "version": "1.0.0"
        }
    }

    # Send telemetry and get response
    response = client.send_telemetry(telemetry_data)

    # Print results
    print(f"Telemetry sent successfully!")
    print(f"Risk Score: {response.risk_score}")
    print(f"Flags: {response.flags}")
    print(f"Detection Events: {response.detection_events}")

if __name__ == "__main__":
    main() 