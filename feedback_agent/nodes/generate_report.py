"""Node 4: combine classification + context into the final FeedbackReport."""

import logging
from datetime import UTC, datetime

from anthropic import AnthropicBedrock

from feedback_agent.clients.claude_client import AgentError, call_json
from feedback_agent.config import Settings
from feedback_agent.models.report import CustomerContextSummary, FeedbackReport
from feedback_agent.prompts.report import build_report_prompt
from feedback_agent.state import AgentState
from feedback_agent.utils.tracing import log_step

logger = logging.getLogger(__name__)


def _fallback_report(state: AgentState, reason: str) -> FeedbackReport:
    """A minimal report built with no LLM call, used when the report call
    itself fails. Every field here comes directly from already-validated
    state — nothing is fabricated.
    """
    feedback = state["feedback"]
    classification = state["classification"]
    context = state["context"]
    return FeedbackReport(
        feedback_id=feedback.feedback_id,
        generated_at=datetime.now(UTC),
        summary=feedback.text[:200],
        category=classification.category,
        urgency=classification.urgency,
        classification_confidence=classification.confidence,
        customer_context=CustomerContextSummary(
            found=context.customer_found,
            summary=context.customer_summary or "No customer record found.",
        ),
        policy_references=[],
        suggested_actions=["Manual triage required — automated report generation failed."],
        requires_human_review=True,
        review_reason=reason,
        trace_ref=f"{feedback.feedback_id}.trace.json",
    )


def _apply_review_guarantee(
    report: FeedbackReport, state: AgentState, settings: Settings
) -> FeedbackReport:
    """Force requires_human_review=True on any of three conditions, as a
    code-level guarantee rather than trusting the prompt to set it correctly
    — same pattern as the KWH project's theme sorting: the contract must be
    a code guarantee, not a hope that the LLM followed instructions.
    """
    classification = state["classification"]
    context = state["context"]
    feedback = state["feedback"]

    reasons: list[str] = []
    if classification.confidence < settings.classification_confidence_threshold:
        reasons.append(f"low classification confidence ({classification.confidence:.2f})")
    if context.incomplete:
        reasons.append("context gathering was incomplete")
    if feedback.customer_id and not context.customer_found:
        reasons.append(f"customer_id {feedback.customer_id} was provided but no record was found")

    if not reasons:
        return report

    return report.model_copy(
        update={"requires_human_review": True, "review_reason": "; ".join(reasons)}
    )


def generate_report(state: AgentState) -> dict:
    """Produce the final FeedbackReport from classification + context.

    After the LLM call, requires_human_review is forced True whenever
    confidence is below threshold, context gathering was incomplete, or a
    given customer_id wasn't found — a code-level guarantee, not something
    left to the prompt alone to get right.
    """
    logger.info("Starting node: generate_report")
    trace = list(state.get("trace", []))
    errors = list(state.get("errors", []))

    settings = Settings()
    client = AnthropicBedrock(aws_region=settings.aws_region)
    system, user = build_report_prompt(state["feedback"], state["classification"], state["context"])

    try:
        report = call_json(client, settings.anthropic_model, system, user, FeedbackReport)
    except AgentError as e:
        logger.warning("generate_report: falling back after AgentError: %s", e)
        errors.append(f"generate_report: {e}")
        report = _fallback_report(state, "automated triage incomplete — generate_report failed")
        log_step(trace, "node_end", node="generate_report", ok=False)
        return {"report": report, "trace": trace, "errors": errors}

    report = _apply_review_guarantee(report, state, settings)

    log_step(
        trace,
        "node_end",
        node="generate_report",
        requires_human_review=report.requires_human_review,
    )
    return {"report": report, "trace": trace, "errors": errors}
