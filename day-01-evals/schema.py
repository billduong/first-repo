# schema.py
from typing import Literal
from pydantic import BaseModel, Field, field_validator

# Simulated database/registry of approved internal codes
ACTIVE_APPROVED_CODES = {"FIN-900", "SEC-001", "OPS-200"}

class TriageRecord(BaseModel):
    client_name: str
    ticket_category: Literal["BILLING", "TECHNICAL_BUG", "ACCOUNT_SECURITY", "FEATURE_REQUEST"]
    urgency_score: int = Field(ge=1, le=5, description="1 is low, 5 is critical emergency")
    
    # Layer 1 Enforcement: Syntax/Regex check
    routing_code: str = Field(
        pattern=r"^[A-Z]{2,3}-\d{3}$",
        description="Internal department routing code in format IT-101 or SEC-404"
    )
    action_required: bool
    summary: str

    # Layer 2 Enforcement: Semantic / Business Logic check
    @field_validator("routing_code")
    @classmethod
    def verify_active_code(cls, v: str) -> str:
        if v not in ACTIVE_APPROVED_CODES:
            raise ValueError(
                f"Code '{v}' is not active in company registry. Must be one of: {sorted(list(ACTIVE_APPROVED_CODES))}"
            )
        return v
