"""Node 3: the ReAct tool-calling loop — gathers grounding context."""

import json
import logging

from anthropic import AnthropicBedrock
from pydantic import ValidationError

from feedback_agent.clients.claude_client import AgentError, run_tool_loop
from feedback_agent.config import Settings
from feedback_agent.models.context import RetrievedContext
from feedback_agent.prompts.gather_context import build_gather_context_prompt
from feedback_agent.state import AgentState
from feedback_agent.tools.schemas import TOOL_DISPATCH, TOOL_SCHEMAS
from feedback_agent.utils.tracing import log_step

logger = logging.getLogger(__name__)


def _context_from_tool_call_log(tool_call_log: list[dict]) -> RetrievedContext:
    """Best-effort fallback: derive context directly from the tool call
    records (full fidelity, never truncated) when the model's final text
    isn't valid structured JSON. Always flags incomplete=True — reaching
    this path means something didn't go cleanly.
    """
    customer_found = False
    customer_summary = None
    policies_used: list[dict] = []
    workflow_guideline = None

    for entry in tool_call_log:
        result = entry.get("result", {})
        if entry.get("name") == "get_customer_context" and result.get("found"):
            customer_found = True
            customer = result.get("customer", {})
            customer_summary = (
                f"{customer.get('tier', '?')} tier, "
                f"{customer.get('tenure_months', '?')}mo tenure, "
                f"{customer.get('order_count', '?')} orders"
            )
        elif entry.get("name") == "get_policy" and result.get("found"):
            policies_used.extend(result.get("policies", []))
        elif entry.get("name") == "get_workflow_guideline" and result.get("found"):
            workflow_guideline = result.get("guideline")

    return RetrievedContext(
        customer_found=customer_found,
        customer_summary=customer_summary,
        policies_used=policies_used,
        workflow_guideline=workflow_guideline,
        incomplete=True,
    )


def gather_context(state: AgentState) -> dict:
    """Run the ReAct tool-calling loop and parse its output into RetrievedContext.

    The model decides which tools to call, in what order, and when to stop —
    see CLAUDE.md's "Non-negotiable grading requirement: real tool use". Its
    final answer is a JSON summary (see prompts/gather_context.py) that this
    node parses; if parsing fails (malformed JSON, unexpected shape), context
    is instead derived directly from the tool call log rather than raising,
    and flagged incomplete=True — the report is still produced, just flagged
    for review.
    """
    logger.info("Starting node: gather_context")
    trace = list(state.get("trace", []))
    errors = list(state.get("errors", []))
    tool_call_log = list(state.get("tool_call_log", []))

    settings = Settings()
    client = AnthropicBedrock(aws_region=settings.aws_region)
    system, user = build_gather_context_prompt(state["feedback"], state["classification"])

    try:
        final_text, loop_incomplete = run_tool_loop(
            client,
            settings.anthropic_model,
            system,
            user,
            TOOL_SCHEMAS,
            TOOL_DISPATCH,
            settings.max_tool_iterations,
            trace,
            tool_call_log,
        )
    except AgentError as e:
        logger.warning("gather_context: falling back after AgentError: %s", e)
        errors.append(f"gather_context: {e}")
        context = RetrievedContext(
            customer_found=False,
            customer_summary=None,
            policies_used=[],
            workflow_guideline=None,
            incomplete=True,
        )
        log_step(trace, "node_end", node="gather_context", ok=False)
        return {
            "context": context,
            "trace": trace,
            "errors": errors,
            "tool_call_log": tool_call_log,
        }

    try:
        parsed = json.loads(final_text)
        context = RetrievedContext(
            customer_found=bool(parsed.get("customer_found", False)),
            customer_summary=parsed.get("customer_summary"),
            policies_used=parsed.get("policies_used") or [],
            workflow_guideline=parsed.get("workflow_guideline"),
            incomplete=loop_incomplete,
        )
    except (json.JSONDecodeError, TypeError, ValueError, ValidationError) as e:
        logger.warning(
            "gather_context: final text wasn't valid structured JSON (%s); "
            "falling back to tool_call_log",
            e,
        )
        context = _context_from_tool_call_log(tool_call_log)

    log_step(
        trace,
        "node_end",
        node="gather_context",
        customer_found=context.customer_found,
        incomplete=context.incomplete,
    )
    return {
        "context": context,
        "trace": trace,
        "errors": errors,
        "tool_call_log": tool_call_log,
    }
