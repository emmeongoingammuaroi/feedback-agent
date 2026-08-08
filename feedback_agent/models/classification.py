"""LLM-produced classification of a feedback submission."""

from typing import Literal

from pydantic import BaseModel, field_validator

Category = Literal[
    "bug_report",
    "billing_complaint",
    "feature_request",
    "praise",
    "churn_risk",
    "abuse_or_policy_violation",
    "general_inquiry",
]

Urgency = Literal["low", "medium", "high", "critical"]


class Classification(BaseModel):
    """The category, urgency, and confidence assigned to a feedback submission.

    Produced by a single dedicated Claude call (`nodes/classify.py`), kept
    separate from the `gather_context` tool-calling loop so a bad
    classification never poisons the tool-calling reasoning trace.
    """

    category: Category
    urgency: Urgency
    confidence: float
    rationale: str

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return value
