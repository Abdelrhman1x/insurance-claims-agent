import asyncio

from agents import Agent, Runner, trace

from src.config import get_model
from src.memory import get_session
from tools.agent_tools import ALL_TOOLS

SESSION_ID = "test-memory-1"


async def main():
    session = get_session(SESSION_ID)
    agent = Agent(
        name="Memory Test Agent",
        instructions="You are a car-insurance assistant. Use tools to look up facts. Never invent data.",
        model=get_model(),
        tools=ALL_TOOLS[:5],  # read-only tools, no case creation
    )

    with trace("memory_test", group_id=SESSION_ID):
        r1 = await Runner.run(agent, "Hi, my policy number is POL-1001 and my car was rear-ended.", session=session)
        print("TURN 1:", r1.final_output)

        r2 = await Runner.run(agent, "What is my policy number and who is the policy holder?", session=session)
        print("TURN 2:", r2.final_output)


asyncio.run(main())