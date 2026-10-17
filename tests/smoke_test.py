import asyncio
from agents import Agent, Runner, function_tool
from src.config import get_model


@function_tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b


async def main():
    agent = Agent(
        name="Test Agent",
        instructions="You are a helpful assistant. Use tools when needed.",
        model=get_model(),
        tools=[add_numbers],
    )
    result = await Runner.run(agent, "What is 17 + 25? Use the tool.")
    print(result.final_output)


asyncio.run(main())