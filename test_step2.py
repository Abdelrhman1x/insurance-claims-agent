import asyncio

from agents import Runner

from src.agents.evidence import documents_agent, history_agent, policy_agent
from src.agents.intake import intake_agent
from src.workflows.evaluator_loop import write_with_review
from tools.routing import assess_risk


async def main():
    msg = "عربيتي اتخبطت امبارح، رقم الوثيقة POL-1001، والخسارة حوالي 20 ألف جنيه"

    facts = (await Runner.run(intake_agent, msg)).final_output
    risk = assess_risk(facts)  # كود بايثون بس، من غير LLM
    print("RISK:", risk.model_dump_json(indent=2))

    if risk.route.value == "human_review":
        print("-> يروح لإنسان فورًا، مفيش كمل.")
        return

    prompt = (
        f"policy_number={facts.policy_number}, incident_type={facts.incident_type.value}, "
        f"estimated_damage_egp={facts.estimated_amount_egp}"
    )
    pol, hist, docs = await asyncio.gather(
        Runner.run(policy_agent, prompt),
        Runner.run(history_agent, prompt),
        Runner.run(documents_agent, prompt),
    )

    context = (
        f"FACTS:\n{facts.model_dump_json(indent=2)}\n\n"
        f"POLICY:\n{pol.final_output}\n\nHISTORY:\n{hist.final_output}\n\n"
        f"DOCUMENTS:\n{docs.final_output}\n\nRISK:\n{risk.model_dump_json()}"
    )
    result = await write_with_review(context)
    print("\n=== FINAL SUMMARY ===\n", result["summary"])
    print("approved:", result["approved"], "| attempts:", result["attempts"])


asyncio.run(main())