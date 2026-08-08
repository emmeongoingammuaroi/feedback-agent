"""Node 1: validate the raw submission, assign a feedback_id if missing.

No LLM call — isolated so malformed input fails fast and cheaply, before any
LLM spend. Unlike the other three nodes, a validation failure here is not
treated as a recoverable/non-fatal error: it propagates (ValidationError),
because without a valid FeedbackSubmission nothing downstream can run
meaningfully, and this is the one node cheap enough to fail loudly at.
"""

import logging
from uuid import uuid4

from feedback_agent.models.feedback import FeedbackSubmission
from feedback_agent.state import AgentState
from feedback_agent.utils.tracing import log_step

logger = logging.getLogger(__name__)


def intake(state: AgentState) -> dict:
    """Validate/construct the FeedbackSubmission and assign a feedback_id if missing."""
    logger.info("Starting node: intake")
    trace = list(state.get("trace", []))
    errors = list(state.get("errors", []))

    raw_feedback = state["feedback"]
    feedback = (
        raw_feedback
        if isinstance(raw_feedback, FeedbackSubmission)
        else FeedbackSubmission.model_validate(raw_feedback)
    )

    if not feedback.feedback_id:
        feedback = feedback.model_copy(update={"feedback_id": str(uuid4())})

    log_step(trace, "node_end", node="intake", feedback_id=feedback.feedback_id)
    return {"feedback": feedback, "trace": trace, "errors": errors}
