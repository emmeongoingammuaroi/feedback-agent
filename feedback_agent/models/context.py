"""Grounding context gathered by the ReAct tool-calling loop."""

from pydantic import BaseModel


class RetrievedContext(BaseModel):
    """Everything retrieved via tool calls during `gather_context`.

    `incomplete` is set True when the tool loop hits `MAX_TOOL_ITERATIONS`
    without the model signaling it has enough context to stop — the node
    returns whatever context was gathered rather than looping forever or
    crashing.
    """

    customer_found: bool
    customer_summary: str | None
    policies_used: list[dict]
    workflow_guideline: dict | None
    incomplete: bool = False
