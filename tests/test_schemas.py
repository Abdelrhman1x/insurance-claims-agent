from src.schemas import ClaimFacts

facts = ClaimFacts(incident_type="collision", description="Rear-ended at a traffic light", estimated_amount_egp=15000)
print(facts)

try:
    ClaimFacts(incident_type="alien_attack", description="x")
except Exception as e:
    print("Rejected correctly:", type(e).__name__)