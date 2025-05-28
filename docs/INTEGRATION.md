# Framework Integration Guide

This guide provides detailed instructions for integrating PrecogX SDK with various AI frameworks and tools.

## Framework Support Matrix

| Framework | Status | Notes |
|-----------|--------|-------|
| LangChain | ✅ | Full support with callback handler |
| LiteLLM | ✅ | Full support with callback system |
| OpenAI | ✅ | Direct API support |
| Anthropic | ✅ | Direct API support |
| Cohere | 🔜 | Coming soon |
| HuggingFace | 🔜 | Coming soon |

## LangChain Integration

### Installation

```bash
pip install "precogx-sdk[langchain]"
```

### Basic Usage

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
```

### Advanced Usage

```python
# Custom detection rules
handler = PrecogXCallbackHandler(
    client=client,
    agent_id="my-agent",
    session_id="session-123",
    detection_rules={
        "custom_rule": {
            "pattern": "sensitive_pattern",
            "severity": "high"
        }
    }
)

# Custom metadata
handler = PrecogXCallbackHandler(
    client=client,
    agent_id="my-agent",
    session_id="session-123",
    metadata={
        "environment": "production",
        "version": "1.0.0"
    }
)
```

## LiteLLM Integration

### Installation

```bash
pip install "precogx-sdk[litellm]"
```

### Basic Usage

```python
from litellm import completion
from precogx_sdk import PrecogXClient

# Initialize client
client = PrecogXClient(api_key="your-api-key")

# Create callback
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

## Direct API Integration

### OpenAI

```python
from openai import OpenAI
from precogx_sdk import PrecogXClient

# Initialize clients
openai_client = OpenAI()
precogx_client = PrecogXClient(api_key="your-api-key")

# Make API call
response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in New York?"}]
)

# Send telemetry
precogx_client.send_telemetry({
    "agent_id": "my-agent",
    "prompt": "What's the weather in New York?",
    "response": response.choices[0].message.content,
    "metadata": {
        "model": "gpt-4",
        "usage": response.usage
    }
})
```

### Anthropic

```python
from anthropic import Anthropic
from precogx_sdk import PrecogXClient

# Initialize clients
anthropic_client = Anthropic()
precogx_client = PrecogXClient(api_key="your-api-key")

# Make API call
response = anthropic_client.messages.create(
    model="claude-3-opus-20240229",
    messages=[{"role": "user", "content": "What's the weather in New York?"}]
)

# Send telemetry
precogx_client.send_telemetry({
    "agent_id": "my-agent",
    "prompt": "What's the weather in New York?",
    "response": response.content[0].text,
    "metadata": {
        "model": "claude-3-opus-20240229"
    }
})
```

## Best Practices

1. Always include relevant metadata
2. Use consistent agent IDs
3. Implement error handling
4. Monitor rate limits
5. Use session IDs for tracking conversations

## Troubleshooting

Common issues and solutions:

1. Rate Limiting
   - Implement exponential backoff
   - Use batch processing for high volume

2. Authentication
   - Verify API key permissions
   - Check tenant access

3. Integration Issues
   - Check framework version compatibility
   - Verify callback implementation

## Support

- Documentation: [docs.precogx.ai](https://docs.precogx.ai)
- GitHub Issues: [github.com/precogx/precogx-sdk](https://github.com/precogx/precogx-sdk)
- Email: support@precogx.ai 