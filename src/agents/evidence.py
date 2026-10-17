from agents import Agent, function_tool

from src.config import get_model
from tools import claims_tools as ct

# لفّ دوال زميلك كـ tools للـ Agents
policy_tool = function_tool(
    ct.get_customer_policy,
    name_override="get_customer_policy",
    description_override="Get policy details (status, dates, vehicle) by policy number.",
)
coverage_tool = function_tool(
    ct.get_policy_coverage,
    name_override="get_policy_coverage",
    description_override="Check if an incident type is covered; returns limit and deductible.",
)
history_tool = function_tool(
    ct.check_claim_history,
    name_override="check_claim_history",
    description_override="Get the customer's previous claims count and totals.",
)
deductible_tool = function_tool(
    ct.calculate_deductible,
    name_override="calculate_deductible",
    description_override="Informational payable estimate for the adjuster. NOT a promise.",
)
documents_tool = function_tool(
    ct.check_required_documents,
    name_override="check_required_documents",
    description_override="List required, provided, and missing documents for a claim.",
)

COMMON_RULES = (
    "Use ONLY the tool results. Never invent data. If a tool returns an error, "
    "report the error as-is. Reply in short English bullet points. "
    "Never approve, deny, or promise compensation."
)

policy_agent = Agent(
    name="Policy Agent",
    instructions=(
        "You verify the policy and its coverage for the claim. Call get_customer_policy, "
        "then get_policy_coverage, then calculate_deductible if an amount is given. "
        + COMMON_RULES
    ),
    model=get_model(),
    tools=[policy_tool, coverage_tool, deductible_tool],
)

history_agent = Agent(
    name="History Agent",
    instructions=(
        "You review the customer's claim history. Call check_claim_history and "
        "summarize the numbers and anything unusual. " + COMMON_RULES
    ),
    model=get_model(),
    tools=[history_tool],
)

documents_agent = Agent(
    name="Documents Agent",
    instructions=(
        "You check which documents are required, provided, and missing. "
        "Call check_required_documents. " + COMMON_RULES
    ),
    model=get_model(),
    tools=[documents_tool],
)