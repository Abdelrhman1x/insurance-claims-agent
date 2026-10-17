import asyncio

from agents import Runner

from src.agents.evidence import documents_agent, history_agent, policy_agent
from src.agents.intake import intake_agent


async def main():
    msg = "عربيتي اتخبطت امبارح، رقم الوثيقة POL-1001، والخسارة حوالي 20 ألف جنيه"
    intake = await Runner.run(intake_agent, msg)
    facts = intake.final_output
    print("FACTS:", facts.model_dump_json(indent=2))

    prompt = (
        f"policy_number={facts.policy_number}, "
        f"incident_type={facts.incident_type.value}, "
        f"estimated_damage_egp={facts.estimated_amount_egp}"
    )
    results = await asyncio.gather(
        Runner.run(policy_agent, prompt),
        Runner.run(history_agent, prompt),
        Runner.run(documents_agent, prompt),
    )
    for name, r in zip(["POLICY", "HISTORY", "DOCUMENTS"], results):
        print(f"\n--- {name} ---\n{r.final_output}")


asyncio.run(main())