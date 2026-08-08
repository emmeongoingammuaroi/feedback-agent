"""Final structured triage report — the pipeline's output artifact."""

from datetime import datetime

from pydantic import BaseModel

from feedback_agent.models.classification import Category, Urgency


class CustomerContextSummary(BaseModel):
    """Customer grounding as it appears in the final report."""

    found: bool
    summary: str


class PolicyReference(BaseModel):
    """A policy actually cited by the model while generating the report."""

    policy_id: str
    title: str
    relevance: str


class FeedbackReport(BaseModel):
    """The structured triage report produced by `generate_report`.

    Every field that references customer data or policy must be traceable to
    an actual tool result in `state["tool_call_log"]` — this is the grounding
    requirement. A report that states a customer or policy fact not backed by
    a tool result is a hallucination and a correctness bug, not a style issue.
    """

    feedback_id: str
    generated_at: datetime
    summary: str
    category: Category
    urgency: Urgency
    classification_confidence: float
    customer_context: CustomerContextSummary
    policy_references: list[PolicyReference]
    suggested_actions: list[str]
    requires_human_review: bool
    review_reason: str | None
    trace_ref: str

    def to_json(self) -> str:
        """Serialize the report as pretty-printed JSON for file/console output."""
        return self.model_dump_json(indent=2)
