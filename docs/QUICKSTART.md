# PrecogX SDK Quick Start Guide

Get started with PrecogX SDK in less than 5 minutes.

## Installation

```bash
# Basic installation
pip install precogx-sdk

# With LangChain support
pip install "precogx-sdk[langchain]"

# With LiteLLM support
pip install "precogx-sdk[litellm]"
```

## Basic Usage

### 1. Initialize the Client

```python
from precogx_sdk import PrecogXClient

client = PrecogXClient(
    api_key="your-api-key",
    api_url="https://api.precogx.ai"  # Optional: defaults to production URL
)
```

### 2. Send Telemetry Data

```python
# Basic telemetry
client.send_telemetry({
    "agent_id": "my-agent",
    "prompt": "What's the weather in New York?",
    "response": "The weather in New York is...",
    "tool_calls": [],
    "metadata": {
        "model": "gpt-4",
        "temperature": 0.7
    }
})

# With detection results
response = client.send_telemetry({
    "agent_id": "my-agent",
    "prompt": "What's the weather in New York?",
    "response": "The weather in New York is...",
    "tool_calls": [],
    "metadata": {
        "model": "gpt-4",
        "temperature": 0.7
    }
})

print(f"Risk Score: {response.risk_score}")
print(f"Flags: {response.flags}")
```

## LangChain Integration

```python
from langchain.agents import initialize_agent
from precogx_langchain import PrecogXCallbackHandler
from precogx_sdk import PrecogXClient

# Initialize client
client = PrecogXClient(api_key="your-api-key")

# Create callback handler
handler = PrecogXCallbackHandler(
    client=client,
    agent_id="my-agent",
    session_id="session-123"
)

# Initialize LangChain agent
agent = initialize_agent(
    tools=[...],
    llm=...,
    agent="zero-shot-react-description",
    callbacks=[handler]
)

# Run agent
agent.run("What's the weather in New York?")
```

## LiteLLM Integration

```python
from litellm import completion
from precogx_sdk import PrecogXClient

# Initialize client
client = PrecogXClient(api_key="your-api-key")

# Create LiteLLM callback
def precogx_callback(response):
    client.send_telemetry({
        "agent_id": "my-agent",
        "prompt": response.messages[-1].content,
        "response": response.choices[0].message.content,
        "metadata": {
            "model": response.model,
            "usage": response.usage
        }
    })

# Use with LiteLLM
response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in New York?"}],
    callbacks=[precogx_callback]
)
```

## Next Steps

1. Check out our [examples](examples/) for more detailed usage
2. Read the [integration guide](INTEGRATION.md) for framework-specific setup
3. Learn about [contributing](CONTRIBUTING.md) to the SDK

## Support

- Documentation: [docs.precogx.ai](https://docs.precogx.ai)
- GitHub Issues: [github.com/precogx/precogx-sdk](https://github.com/precogx/precogx-sdk)
- Email: support@precogx.ai 