"""LangGraph pipeline: intake -> classify -> gather_context -> generate_report.

Four linear nodes. `AgentState` makes every inter-node dependency explicit
and typed; each node's return value is a partial state update that's trivial
to unit test in isolation without mocking the whole pipeline. `human_review`
is deliberately NOT a graph node — it's a post-processing step in main.py,
since approval is a human action outside the agent's control flow, not
something the agent decides to do.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from feedback_agent.nodes.classify import classify
from feedback_agent.nodes.gather_context import gather_context
from feedback_agent.nodes.generate_report import generate_report
from feedback_agent.nodes.intake import intake
from feedback_agent.state import AgentState


def build_graph() -> CompiledStateGraph:
    """Build and compile the 4-node feedback triage pipeline."""
    graph = StateGraph(AgentState)

    graph.add_node("intake", intake)
    graph.add_node("classify", classify)
    graph.add_node("gather_context", gather_context)
    graph.add_node("generate_report", generate_report)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "classify")
    graph.add_edge("classify", "gather_context")
    graph.add_edge("gather_context", "generate_report")
    graph.add_edge("generate_report", END)

    return graph.compile()
