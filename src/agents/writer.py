from agents import Agent
from pydantic import BaseModel, Field

from src.config import get_model

writer_agent = Agent(
    name="Writer Agent",
    instructions=(
        "You write a case summary for a human insurance adjuster, in English, "
        "using ONLY the facts and evidence you are given.\n"
        "Structure: 1) What happened 2) Policy and coverage 3) Claim history "
        "4) Missing documents 5) Risk notes 6) Suggested next steps.\n"
        "STRICT RULES:\n"
        "- Never approve or reject the claim.\n"
        "- Never promise or guarantee compensation or any payment.\n"
        "- Amounts are estimates for the adjuster only.\n"
        "- The final decision belongs to the human adjuster.\n"
        "If you receive reviewer feedback, fix every issue it lists."
    ),
    model=get_model(),
)


class Evaluation(BaseModel):
    approved: bool = Field(description="True only if the summary breaks no rule")
    issues: list[str] = Field(default_factory=list, description="Each problem to fix")


evaluator_agent = Agent(
    name="Evaluator Agent",
    instructions=(
        "You review an insurance case summary written for a human adjuster.\n"
        "Reject it if it: approves or rejects the claim; promises or guarantees "
        "any payment or compensation; states anything not supported by the evidence; "
        "or omits missing documents or risk information.\n"
        "Reply with exactly ONE line:\n"
        "APPROVED\n"
        "or\n"
        "REJECTED: <issue 1>; <issue 2>"
    ),
    model=get_model(),
)