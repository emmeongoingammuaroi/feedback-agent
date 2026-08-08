"""Customer feedback submission schema — the raw input to the pipeline."""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class FeedbackSubmission(BaseModel):
    """A single piece of customer feedback as it enters the pipeline.

    Validated by the `intake` node before any LLM call is made, so malformed
    input fails fast and cheaply, before any LLM spend.
    """

    feedback_id: str = Field(default_factory=lambda: str(uuid4()))
    customer_id: str | None = None
    channel: Literal["email", "web_form", "chat", "survey"]
    text: str = Field(min_length=1)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
