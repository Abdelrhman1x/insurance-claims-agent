from datetime import date

from agents import Agent

from src.config import get_model
from src.guardrails.guards import input_safety_guardrail
from src.schemas import ClaimFacts

intake_agent = Agent(
    name="Intake Agent",
    instructions=(
        f"Today's date is {date.today().isoformat()}. "
        "You extract facts from an insurance claim message written by a customer "
        "(it may be in Arabic or English). Fill the ClaimFacts fields.\n"
        "Rules:\n"
        "- Only extract what is stated. Never guess or invent values.\n"
        "- Resolve relative dates like 'yesterday' into YYYY-MM-DD using today's date.\n"
        "- incident_type must be one of: collision, theft, fire, vandalism, "
        "natural_disaster, other.\n"
        "- Write the description in English, short and neutral.\n"
        "- Put important missing items (policy number, date, amount, police report) "
        "in missing_information.\n"
        "- Never approve, deny, or promise compensation."
    ),
    model=get_model(),
    output_type=ClaimFacts,
    input_guardrails=[input_safety_guardrail],
)