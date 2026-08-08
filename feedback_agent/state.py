"""AgentState — the typed, shared state threaded through the LangGraph pipeline."""

from typing import TypedDict

from feedback_agent.models.classification import Classification
from feedback_agent.models.context import RetrievedContext
from feedback_agent.models.feedback import FeedbackSubmission
from feedback_agent.models.report import FeedbackReport


class AgentState(TypedDict):
    """Shared pipeline state. Each node returns a partial update to this."""

    # Set by intake
    feedback: FeedbackSubmission
    trace: list[dict]  # append-only observability log across all nodes
    errors: list[str]  # non-fatal errors accumulated across nodes

    # Set by classify
    classification: Classification | None

    # Set by gather_context
    context: RetrievedContext | None
    tool_call_log: list[dict]  # every tool call made: name, args, result, timestamp

    # Set by generate_report
    report: FeedbackReport | None
