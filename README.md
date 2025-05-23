# PrecogX SDK

The official SDK for the PrecogX AI Agent Security Platform. This SDK provides tools to monitor, detect, and predict threats from AI agents.

## Installation

```bash
pip install precogx-sdk
```

For LangChain integration:
```bash
pip install "precogx-sdk[langchain]"
```

## Quick Start

### Basic Usage

```python
from precogx_sdk import PrecogXClient

# Initialize the client
client = PrecogXClient(
    api_key="your-api-key",
    api_url="https://api.precogx.ai"  # or your custom endpoint
)

# Send telemetry data
client.send_telemetry({
    "agent_id": "my-agent",
    "session_id": "session-123",
    "interactions": [...]
})
```

### LangChain Integration

```python
from langchain.agents import initialize_agent
from precogx_langchain import PrecogXCallbackHandler
from precogx_sdk import PrecogXClient

# Initialize the PrecogX client
client = PrecogXClient(api_key="your-api-key")

# Create the callback handler
handler = PrecogXCallbackHandler(
    client=client,
    agent_id="my-agent",
    session_id="session-123"
)

# Initialize your LangChain agent with the handler
agent = initialize_agent(
    tools=[...],
    llm=...,
    agent="zero-shot-react-description",
    callbacks=[handler]
)

# Run your agent
agent.run("What's the weather in New York?")
```

## Features

- Telemetry data collection
- LangChain integration
- Automatic threat detection
- Real-time monitoring
- Customizable detection rules

## Documentation

For detailed documentation, visit [docs.precogx.ai](https://docs.precogx.ai)

## License

MIT License 