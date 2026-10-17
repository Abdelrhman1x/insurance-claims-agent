"""
agent_tools.py
--------------
Thin wrappers that expose the pure functions to the LLM agents
via @function_tool. Docstrings matter: the model reads them.
"""

from agents import function_tool

from tools import claims_tools as ct


@function_tool
def get_customer_policy(policy_number: str) -> dict:
    """Look up a customer's policy by policy number (e.g. POL-1001).
    Returns customer name, vehicle, status (active/expired/suspended) and dates."""
    result = ct.get_customer_policy(policy_number)
    return result if isinstance(result, dict) else result.model_dump(mode="json")


@function_tool
def get_policy_coverage(policy_number: str, incident_type: str) -> dict:
    """Check whether an incident type is covered by the policy, plus the coverage
    limit and deductible in EGP. incident_type must be one of: collision, theft,
    fire, vandalism, natural_disaster, other."""
    result = ct.get_policy_coverage(policy_number, incident_type)
    return result if isinstance(result, dict) else result.model_dump(mode="json")


@function_tool
def check_claim_history(policy_number: str) -> dict:
    """Get the number of previous claims, claims in the last 12 months,
    and total amount paid for a policy."""
    result = ct.check_claim_history(policy_number)
    return result if isinstance(result, dict) else result.model_dump(mode="json")


@function_tool
def calculate_deductible(policy_number: str, estimated_damage_egp: float) -> dict:
    """Estimate what the insurer would pay after the deductible for a given damage
    amount in EGP. This is an internal estimate, never a promise to the customer."""
    return ct.calculate_deductible(policy_number, estimated_damage_egp)


@function_tool
def check_required_documents(policy_number: str, incident_type: str) -> dict:
    """List required, provided and missing documents for this incident type."""
    result = ct.check_required_documents(policy_number, incident_type)
    return result if isinstance(result, dict) else result.model_dump(mode="json")


@function_tool
def create_claim_case(policy_number: str, incident_type: str, summary: str) -> dict:
    """Create a claim case for HUMAN review. Only works for active policies.
    It does not approve or reject anything."""
    return ct.create_claim_case(policy_number, incident_type, summary)


ALL_TOOLS = [
    get_customer_policy,
    get_policy_coverage,
    check_claim_history,
    calculate_deductible,
    check_required_documents,
    create_claim_case,
]