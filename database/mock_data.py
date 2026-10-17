"""
mock_data.py
------------
Fake data used by the tools. No real customer information.
Each policy is designed to trigger a specific demo scenario.
"""

from datetime import date

# ---------- Policies ----------
POLICIES: dict[str, dict] = {
    "POL-1001": {
        "customer_name": "Omar Hassan",
        "vehicle": "Toyota Corolla 2021",
        "status": "active",
        "plan": "comprehensive",
        "start_date": date(2026, 1, 1),
        "end_date": date(2026, 12, 31),
    },
    "POL-1002": {
        "customer_name": "Sara Mahmoud",
        "vehicle": "Hyundai Elantra 2020",
        "status": "active",
        "plan": "comprehensive",
        "start_date": date(2026, 2, 1),
        "end_date": date(2027, 1, 31),
    },
    "POL-1003": {
        "customer_name": "Khaled Ibrahim",
        "vehicle": "Kia Sportage 2019",
        "status": "expired",
        "plan": "comprehensive",
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 12, 31),
    },
    "POL-1004": {
        "customer_name": "Nour Adel",
        "vehicle": "Nissan Sunny 2022",
        "status": "suspended",
        "plan": "comprehensive",
        "start_date": date(2026, 3, 1),
        "end_date": date(2027, 2, 28),
    },
    "POL-1005": {
        "customer_name": "Youssef Tarek",
        "vehicle": "Fiat Tipo 2018",
        "status": "active",
        "plan": "basic",
        "start_date": date(2026, 1, 15),
        "end_date": date(2027, 1, 14),
    },
    "POL-1006": {
        "customer_name": "Mona Samir",
        "vehicle": "BMW 320i 2023",
        "status": "active",
        "plan": "comprehensive",
        "start_date": date(2026, 4, 1),
        "end_date": date(2027, 3, 31),
    },
}

# ---------- Coverage per plan (EGP) ----------
# covered incident types, max payout, and deductible
COVERAGE_PLANS: dict[str, dict] = {
    "comprehensive": {
        "covered": ["collision", "theft", "fire", "vandalism", "natural_disaster"],
        "limit_egp": 500_000,
        "deductible_egp": 500,
    },
    "basic": {
        "covered": ["collision", "fire"],
        "limit_egp": 150_000,
        "deductible_egp": 1_000,
    },
}

# ---------- Claim history ----------
CLAIM_HISTORY: dict[str, dict] = {
    "POL-1001": {"previous_claims_count": 1, "claims_last_12_months": 0, "total_paid_egp": 8_000},
    "POL-1002": {"previous_claims_count": 6, "claims_last_12_months": 4, "total_paid_egp": 62_000},
    "POL-1003": {"previous_claims_count": 0, "claims_last_12_months": 0, "total_paid_egp": 0},
    "POL-1004": {"previous_claims_count": 2, "claims_last_12_months": 1, "total_paid_egp": 14_000},
    "POL-1005": {"previous_claims_count": 0, "claims_last_12_months": 0, "total_paid_egp": 0},
    "POL-1006": {"previous_claims_count": 0, "claims_last_12_months": 0, "total_paid_egp": 0},
}

# ---------- Required documents per incident type ----------
REQUIRED_DOCUMENTS: dict[str, list[str]] = {
    "collision": ["police_report", "photos_of_damage", "driver_license", "repair_estimate"],
    "theft": ["police_report", "vehicle_registration", "spare_key"],
    "fire": ["fire_department_report", "photos_of_damage", "repair_estimate"],
    "vandalism": ["police_report", "photos_of_damage"],
    "natural_disaster": ["photos_of_damage", "repair_estimate"],
    "other": ["photos_of_damage"],
}

# ---------- Documents each customer has already submitted ----------
SUBMITTED_DOCUMENTS: dict[str, list[str]] = {
    "POL-1001": ["driver_license", "photos_of_damage"],
    "POL-1002": ["driver_license"],
    "POL-1003": [],
    "POL-1004": ["driver_license", "photos_of_damage"],
    "POL-1005": ["driver_license"],
    "POL-1006": ["driver_license", "photos_of_damage", "police_report", "repair_estimate"],
}

# ---------- Created cases (filled at runtime by create_claim_case) ----------
CLAIM_CASES: dict[str, dict] = {}