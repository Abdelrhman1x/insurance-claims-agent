"""
routing.py
----------
Deterministic (code-orchestrated) routing. NO LLM here.
Decides: standard workflow or human review.
Auditable and safety-critical, so it must stay plain Python.
"""

from src.schemas import ClaimFacts, RiskAssessment, RiskLevel, Route
from tools import claims_tools as ct

HIGH_AMOUNT_EGP = 100_000
SUSPICIOUS_CLAIMS_12M = 3


def assess_risk(facts: ClaimFacts) -> RiskAssessment:
    reasons: list[str] = []
    level = RiskLevel.LOW

    def raise_to(new: RiskLevel):
        nonlocal level
        order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
        if order.index(new) > order.index(level):
            level = new

    # Rule 0: no policy number -> cannot verify anything
    if not facts.policy_number:
        reasons.append("No policy number provided.")
        raise_to(RiskLevel.MEDIUM)
        return _result(level, reasons)

    # Rule 1: policy must exist and be active
    policy = ct.get_customer_policy(facts.policy_number)
    if isinstance(policy, dict):
        reasons.append(f"Policy lookup failed: {policy['error']}")
        raise_to(RiskLevel.HIGH)
        return _result(level, reasons)
    if policy.status != "active":
        reasons.append(f"Policy status is '{policy.status}'.")
        raise_to(RiskLevel.HIGH)

    # Rule 2: incident date must fall inside the policy period
    if facts.incident_date and not (policy.start_date <= facts.incident_date <= policy.end_date):
        reasons.append("Incident date is outside the policy period.")
        raise_to(RiskLevel.HIGH)

    # Rule 3: suspicious claim frequency
    history = ct.check_claim_history(facts.policy_number)
    if not isinstance(history, dict) and history.claims_last_12_months >= SUSPICIOUS_CLAIMS_12M:
        reasons.append(f"{history.claims_last_12_months} claims in the last 12 months.")
        raise_to(RiskLevel.HIGH)

    # Rule 4: incident type not covered
    coverage = ct.get_policy_coverage(facts.policy_number, facts.incident_type.value)
    if not isinstance(coverage, dict) and not coverage.is_covered:
        reasons.append(coverage.notes)
        raise_to(RiskLevel.MEDIUM)

    # Rule 5: very large amount
    if facts.estimated_amount_egp and facts.estimated_amount_egp > HIGH_AMOUNT_EGP:
        reasons.append(f"Estimated amount {facts.estimated_amount_egp:,.0f} EGP exceeds {HIGH_AMOUNT_EGP:,} EGP.")
        raise_to(RiskLevel.HIGH)

    return _result(level, reasons)


def _result(level: RiskLevel, reasons: list[str]) -> RiskAssessment:
    route = Route.STANDARD if level == RiskLevel.LOW else Route.HUMAN_REVIEW
    return RiskAssessment(risk_level=level, route=route, reasons=reasons)