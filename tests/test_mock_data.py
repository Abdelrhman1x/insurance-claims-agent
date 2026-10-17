from database.mock_data import POLICIES, COVERAGE_PLANS, CLAIM_HISTORY, REQUIRED_DOCUMENTS

print("Policies:", len(POLICIES))
for pid, p in POLICIES.items():
    plan = COVERAGE_PLANS[p["plan"]]
    hist = CLAIM_HISTORY[pid]
    print(pid, p["status"], p["plan"], "| deductible:", plan["deductible_egp"], "| claims 12m:", hist["claims_last_12_months"])