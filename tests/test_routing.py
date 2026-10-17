from datetime import date
from src.schemas import ClaimFacts
from tools.routing import assess_risk


def run(label, **kw):
    facts = ClaimFacts(description="Test claim description here", **kw)
    r = assess_risk(facts)
    print(f"{label:24} -> {r.route.value:13} {r.risk_level.value:7} {r.reasons}")


run("happy path", policy_number="POL-1001", incident_type="collision", incident_date=date(2026, 6, 1), estimated_amount_egp=15000)
run("frequent claimant", policy_number="POL-1002", incident_type="collision", incident_date=date(2026, 6, 1), estimated_amount_egp=9000)
run("expired policy", policy_number="POL-1003", incident_type="collision", incident_date=date(2025, 6, 1))
run("suspended policy", policy_number="POL-1004", incident_type="collision", incident_date=date(2026, 6, 1))
run("theft on basic plan", policy_number="POL-1005", incident_type="theft", incident_date=date(2026, 6, 1))
run("huge amount", policy_number="POL-1006", incident_type="collision", incident_date=date(2026, 6, 1), estimated_amount_egp=250000)
run("unknown policy", policy_number="POL-9999", incident_type="collision")
run("no policy number", incident_type="collision")