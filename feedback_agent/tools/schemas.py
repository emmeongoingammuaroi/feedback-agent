"""Anthropic tool schemas and dispatch table for the gather_context ReAct loop.

Descriptions are written as carefully as prompts — they're what the model uses
to decide which tool to call, with what arguments, and when.
"""

from collections.abc import Callable
from typing import Any, get_args

from feedback_agent.models.classification import Category
from feedback_agent.tools.customer_lookup import get_customer_context
from feedback_agent.tools.policy_lookup import get_policy
from feedback_agent.tools.workflow_lookup import get_workflow_guideline

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "get_customer_context",
        "description": (
            "Look up a customer's account context: subscription tier, tenure in "
            "months, order count, lifetime value, and their past support ticket "
            "history (category and resolution of each). Call this whenever the "
            "feedback is tied to a specific customer_id and their account history "
            "would materially change the triage decision — e.g. a billing dispute "
            "where prior refunds matter, or a churn signal where tier and lifetime "
            "value determine what retention offer applies. Do not call this if the "
            "feedback has no customer_id (anonymous submissions) — there is nothing "
            "to look up. Returns found=false if the customer_id does not exist in "
            "records; treat that as a normal 'no record found' result, not an error."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The customer_id from the feedback submission, e.g. 'CUST-1001'.",
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_policy",
        "description": (
            "Look up the company's written policy text for a category, so any "
            "recommended action (refund, escalation, retention offer, suspension) "
            "can cite a real policy_id instead of an invented one. Policy "
            "categories are NOT the same set as the feedback classification "
            "taxonomy: some policy categories are cross-cutting operational ones, "
            "e.g. 'sla' and 'escalation', that exist alongside taxonomy-aligned "
            "categories like 'billing_complaint', 'churn_risk', "
            "'abuse_or_policy_violation', and 'bug_report'. Call this before "
            "suggesting any action that should be policy-grounded. If the "
            "feedback's own category returns no policy, consider whether 'sla' "
            "or 'escalation' applies instead. Returns found=false if no policy "
            "matches the given category."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": (
                        "The policy category to look up, e.g. 'billing_complaint', "
                        "'sla', 'escalation', 'abuse_or_policy_violation', "
                        "'churn_risk', or 'bug_report'."
                    ),
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "get_workflow_guideline",
        "description": (
            "Look up the standard CS operating procedure for a feedback taxonomy "
            "category: the ordered steps a human CS officer follows, the default "
            "SLA in hours, what triggers escalation, and the owning team. This is "
            "usually the first tool to call once the feedback's category is known "
            "— it tells you what else the standard process expects you to check "
            "(e.g. it may point at a specific policy to verify with get_policy). "
            "The category must be exactly the feedback's own classified category."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": list(get_args(Category)),
                    "description": "The feedback taxonomy category to look up the standard workflow for.",
                },
            },
            "required": ["category"],
        },
    },
]

TOOL_DISPATCH: dict[str, Callable[..., dict]] = {
    "get_customer_context": get_customer_context,
    "get_policy": get_policy,
    "get_workflow_guideline": get_workflow_guideline,
}
