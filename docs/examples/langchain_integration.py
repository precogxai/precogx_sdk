"""
LangChain integration example for PrecogX SDK.

This example demonstrates how to:
1. Initialize the PrecogX client with LangChain
2. Set up a callback handler
3. Create and run a LangChain agent
4. Monitor agent interactions
"""

from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.tools import Tool
from precogx_langchain import PrecogXCallbackHandler
from precogx_sdk import PrecogXClient

def get_weather(location: str) -> str:
    """Get the weather for a location."""
    return f"The weather in {location} is currently 72°F and sunny."

def main():
    # Initialize the PrecogX client
    client = PrecogXClient(
        api_key="your-api-key",
        api_url="https://api.precogx.ai"
    )

    # Create the callback handler
    handler = PrecogXCallbackHandler(
        client=client,
        agent_id="weather-agent",
        session_id="session-123",
        metadata={
            "environment": "production",
            "version": "1.0.0"
        }
    )

    # Create tools
    tools = [
        Tool(
            name="get_weather",
            func=get_weather,
            description="Get the weather for a location"
        )
    ]

    # Initialize the LLM
    llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=0.7
    )

    # Initialize the agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        callbacks=[handler]
    )

    # Run the agent
    response = agent.run("What's the weather in New York?")
    print(f"Agent response: {response}")

if __name__ == "__main__":
    main() 