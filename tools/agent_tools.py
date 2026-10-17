"""
claims_tools.py
---------------
Pure-Python business logic. No LLM involved here.
Every function returns either a Pydantic model or {"error": "..."}.
"""

import uuid
from datetime import date

from database.mock_data import (
    CLAIM_CASES,
    CLAIM_HISTORY,
    COVERAGE_PLANS,
    POLICIES,
    REQUIRED_DOCUMENTS,
    SUBMITTED_DOCUMENTS,
)
from src.schemas import (
    ClaimHistory,
    CoverageResult,
    DocumentCheck,
    IncidentType,
    PolicyInfo,
)


def _normalize(policy_number: str) -> str:
    return (policy_number or "").strip().upper()


def _error(message: str) -> dict:
    return {"error": message}


# ---------- Tool 1 ----------
def get_customer_policy(policy_number: str) -> PolicyInfo | dict:
    pid = _normalize(policy_number)
    policy = POLICIES.get(pid)
    if policy is None:
        return _error(f"Policy '{pid}' not found. Ask the customer to confirm the policy number.")
    return PolicyInfo(
        policy_number=pid,
        customer_name=policy["customer_name"],
        vehicle=policy["vehicle"],
        status=policy["status"],
        start_date=policy["start_date"],
        end_date=policy["end_date"],
    )


# ---------- Tool 2 ----------
def get_policy_coverage(policy_number: str, incident_type: str) -> CoverageResult | dict:
    pid = _normalize(policy_number)
    policy = POLICIES.get(pid)
    if policy is None:
        return _error(f"Policy '{pid}' not found.")
    try:
        incident = IncidentType(incident_type)
    except ValueError:
        valid = [i.value for i in IncidentType]
        return _error(f"Invalid incident_type '{incident_type}'. Valid values: {valid}")

    plan = COVERAGE_PLANS[policy["plan"]]
    covered = incident.value in plan["covered"]
    return CoverageResult(
        policy_number=pid,
        incident_type=incident,
        is_covered=covered,
        coverage_limit_egp=plan["limit_egp"],
        deductible_egp=plan["deductible_egp"],
        notes="" if covered else f"'{incident.value}' is not covered under the {policy['plan']} plan.",
    )


# ---------- Tool 3 ----------
def check_claim_history(policy_number: str) -> ClaimHistory | dict:
    pid = _normalize(policy_number)
    hist = CLAIM_HISTORY.get(pid)
    if hist is None:
        return _error(f"No claim history record for policy '{pid}'.")
    return ClaimHistory(policy_number=pid, **hist)


# ---------- Tool 4 ----------
def calculate_deductible(policy_number: str, estimated_damage_egp: float) -> dict:
    """Informational estimate only. It is NOT a promise of payment."""
    pid = _normalize(policy_number)
    policy = POLICIES.get(pid)
    if policy is None:
        return _error(f"Policy '{pid}' not found.")
    if estimated_damage_egp is None or estimated_damage_egp < 0:
        return _error("estimated_damage_egp must be a non-negative number.")

    plan = COVERAGE_PLANS[policy["plan"]]
    deductible = plan["deductible_egp"]
    limit = plan["limit_egp"]
    after_deductible = max(estimated_damage_egp - deductible, 0)
    estimated_payable = min(after_deductible, limit)
    return {
        "policy_number": pid,
        "estimated_damage_egp": estimated_damage_egp,
        "deductible_egp": deductible,
        "coverage_limit_egp": limit,
        "estimated_payable_egp": estimated_payable,
        "disclaimer": "Estimate for the adjuster only. Not a commitment to pay.",
    }


# ---------- Tool 5 ----------
def check_required_documents(policy_number: str, incident_type: str) -> DocumentCheck | dict:
    pid = _normalize(policy_number)
    if pid not in POLICIES:
        return _error(f"Policy '{pid}' not found.")
    try:
        incident = IncidentType(incident_type)
    except ValueError:
        return _error(f"Invalid incident_type '{incident_type}'.")

    required = REQUIRED_DOCUMENTS[incident.value]
    provided = SUBMITTED_DOCUMENTS.get(pid, [])
    missing = [d for d in required if d not in provided]
    return DocumentCheck(required=required, provided=provided, missing=missing)


# ---------- Tool 6 (PROTECTED ACTION) ----------
def create_claim_case(policy_number: str, incident_type: str, summary: str) -> dict:
    """
    Creates a case for human review. Protected: validates everything
    in Python before writing. The LLM cannot bypass these checks.
    """
    pid = _normalize(policy_number)
    policy = POLICIES.get(pid)
    if policy is None:
        return _error(f"Policy '{pid}' not found. Case NOT created.")
    if policy["status"] != "active":
        return _error(f"Policy '{pid}' is {policy['status']}. Case NOT created; escalate to a human.")
    try:
        incident = IncidentType(incident_type)
    except ValueError:
        return _error(f"Invalid incident_type '{incident_type}'. Case NOT created.")
    if not summary or len(summary.strip()) < 20:
        return _error("Summary must be at least 20 characters. Case NOT created.")

    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    CLAIM_CASES[case_id] = {
        "policy_number": pid,
        "incident_type": incident.value,
        "summary": summary.strip(),
        "status": "pending_human_review",
        "created_on": date.today().isoformat(),
    }
    return {"case_id": case_id, "status": "pending_human_review"}