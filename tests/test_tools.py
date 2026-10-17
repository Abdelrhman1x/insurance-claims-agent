from tools import claims_tools as ct

print("1. valid policy:      ", ct.get_customer_policy("POL-1001"))
print("2. unknown policy:    ", ct.get_customer_policy("POL-9999"))
print("3. theft on basic:    ", ct.get_policy_coverage("POL-1005", "theft").is_covered)
print("4. bad incident type: ", ct.get_policy_coverage("POL-1001", "alien"))
print("5. history suspicious:", ct.check_claim_history("POL-1002").claims_last_12_months)
print("6. deductible:        ", ct.calculate_deductible("POL-1001", 15000))
print("7. missing docs:      ", ct.check_required_documents("POL-1001", "collision").missing)
print("8. case on active:    ", ct.create_claim_case("POL-1001", "collision", "Rear-ended at a traffic light, bumper damaged"))
print("9. case on expired:   ", ct.create_claim_case("POL-1003", "collision", "Rear-ended at a traffic light, bumper damaged"))