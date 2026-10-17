"""
schemas.py
----------
Shared data contracts (Pydantic models) for the whole project.
Both teammates import from here, so changes must be agreed on first.
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


# ---------- Enums (fixed sets of allowed values) ----------

class IncidentType(str, Enum):
    COLLISION = "collision"
    THEFT = "theft"
    FIRE = "fire"
    VANDALISM = "vandalism"
    NATURAL_DISASTER = "natural_disaster"
    OTHER = "other"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Route(str, Enum):
    STANDARD = "standard"            # normal evidence-gathering workflow
    HUMAN_REVIEW = "human_review"    # stop and send to a human adjuster


# ---------- Step 1: facts extracted from the customer's message ----------

class ClaimFacts(BaseModel):
    """Output of the intake step (LLM extracts these from free text)."""
    policy_number: str | None = Field(None, description="e.g. POL-1001, if the customer mentioned it")
    incident_type: IncidentType
    incident_date: date | None = None
    description: str = Field(..., min_length=10, description="Short neutral summary of what happened")
    estimated_amount_egp: float | None = Field(None, ge=0, description="Estimated damage in EGP")
    police_report_mentioned: bool = False
    missing_information: list[str] = Field(default_factory=list)


# ---------- Step 2: tool results (filled by Person A's tools) ----------

class PolicyInfo(BaseModel):
    policy_number: str
    customer_name: str
    vehicle: str
    status: str                       # "active" | "expired" | "suspended"
    start_date: date
    end_date: date


class CoverageResult(BaseModel):
    policy_number: str
    incident_type: IncidentType
    is_covered: bool
    coverage_limit_egp: float = Field(..., ge=0)
    deductible_egp: float = Field(..., ge=0)
    notes: str = ""


class ClaimHistory(BaseModel):
    policy_number: str
    previous_claims_count: int = Field(..., ge=0)
    claims_last_12_months: int = Field(..., ge=0)
    total_paid_egp: float = Field(..., ge=0)


class DocumentCheck(BaseModel):
    required: list[str]
    provided: list[str]
    missing: list[str]


# ---------- Step 3: routing decision (made by Python code, not the LLM) ----------

class RiskAssessment(BaseModel):
    risk_level: RiskLevel
    route: Route
    reasons: list[str] = Field(default_factory=list)


# ---------- Final output: the file handed to the human adjuster ----------

class ClaimAssessment(BaseModel):
    """Final result. It NEVER contains an approve/reject decision."""
    case_id: str | None = None
    summary: str = Field(..., min_length=20)
    facts: ClaimFacts
    coverage_evidence: str = Field(..., description="What the policy data shows, grounded in tool results")
    estimated_payable_egp: float | None = Field(None, ge=0, description="Informational only, NOT a promise")
    missing_documents: list[str] = Field(default_factory=list)
    risk: RiskAssessment
    recommended_next_steps: list[str] = Field(default_factory=list)
    requires_human_decision: bool = True   # always True in this project