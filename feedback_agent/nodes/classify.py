"""Node 2: single, tool-free Claude call — category + urgency."""

import logging

from anthropic import AnthropicBedrock

from feedback_agent.clients.claude_client import AgentError, call_json
from feedback_agent.config import Settings
from feedback_agent.models.classification import Classification
from feedback_agent.prompts.classify import build_classify_prompt
from feedback_agent.state import AgentState
from feedback_agent.utils.tracing import log_step

logger = logging.getLogger(__name__)

_FALLBACK_RATIONALE = "classification failed — see errors"


def classify(state: AgentState) -> dict:
    """Classify the feedback into a category, urgency, and confidence.

    Kept as a single tool-free call, isolated from the gather_context loop —
    see CLAUDE.md's "Why classification is a separate LLM call". On
    AgentError (already retried once inside call_json/call_with_retry),
    falls back to a low-confidence general_inquiry classification rather
    than crashing the pipeline — generate_report will still run and flag the
    report for human review.
    """
    logger.info("Starting node: classify")
    trace = list(state.get("trace", []))
    errors = list(state.get("errors", []))

    settings = Settings()
    client = AnthropicBedrock(aws_region=settings.aws_region)
    system, user = build_classify_prompt(state["feedback"])

    try:
        classification = call_json(client, settings.anthropic_model, system, user, Classification)
    except AgentError as e:
        logger.warning("classify: falling back after AgentError: %s", e)
        errors.append(f"classify: {e}")
        classification = Classification(
            category="general_inquiry",
            urgency="medium",
            confidence=0.0,
            rationale=_FALLBACK_RATIONALE,
        )

    log_step(
        trace,
        "node_end",
        node="classify",
        category=classification.category,
        urgency=classification.urgency,
        confidence=classification.confidence,
    )
    return {"classification": classification, "trace": trace, "errors": errors}
