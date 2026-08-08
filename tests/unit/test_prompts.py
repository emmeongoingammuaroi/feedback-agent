"""Unit tests for prompt-building functions — pure string logic, no LLM."""

from typing import get_args

from feedback_agent.models.classification import Category, Classification
from feedback_agent.models.context import RetrievedContext
from feedback_agent.models.feedback import FeedbackSubmission
from feedback_agent.prompts.classify import build_classify_prompt
from feedback_agent.prompts.gather_context import build_gather_context_prompt
from feedback_agent.prompts.report import build_report_prompt

# Distinctive substring used consistently by every prompt's injection guardrail
# sentence — see the "# Prompt-injection guardrail" comment in each prompts/*.py.
GUARDRAIL_SUBSTRING = "untrusted"

FEEDBACK = FeedbackSubmission(channel="email", text="Test feedback text.", customer_id="CUST-1001")
CLASSIFICATION = Classification(
    category="billing_complaint", urgency="high", confidence=0.9, rationale="Clear billing issue"
)
CONTEXT = RetrievedContext(
    customer_found=True,
    customer_summary="Pro tier, 14mo tenure",
    policies_used=[],
    workflow_guideline=None,
    incomplete=False,
)


class TestBuildClassifyPrompt:
    def test_returns_non_empty_tuple(self):
        system, user = build_classify_prompt(FEEDBACK)

        assert isinstance(system, str) and isinstance(user, str)
        assert system.strip() and user.strip()

    def test_mentions_all_taxonomy_categories(self):
        system, _ = build_classify_prompt(FEEDBACK)

        for category in get_args(Category):
            assert category in system, f"classify prompt missing category {category!r}"

    def test_contains_injection_guardrail(self):
        system, _ = build_classify_prompt(FEEDBACK)

        assert GUARDRAIL_SUBSTRING in system


class TestBuildGatherContextPrompt:
    def test_returns_non_empty_tuple(self):
        system, user = build_gather_context_prompt(FEEDBACK, CLASSIFICATION)

        assert system.strip() and user.strip()

    def test_mentions_all_three_tool_names(self):
        system, _ = build_gather_context_prompt(FEEDBACK, CLASSIFICATION)

        for tool_name in ("get_customer_context", "get_policy", "get_workflow_guideline"):
            assert tool_name in system, f"gather_context prompt missing tool {tool_name!r}"

    def test_contains_injection_guardrail(self):
        system, _ = build_gather_context_prompt(FEEDBACK, CLASSIFICATION)

        assert GUARDRAIL_SUBSTRING in system


class TestBuildReportPrompt:
    def test_returns_non_empty_tuple(self):
        system, user = build_report_prompt(FEEDBACK, CLASSIFICATION, CONTEXT)

        assert system.strip() and user.strip()

    def test_contains_injection_guardrail(self):
        system, _ = build_report_prompt(FEEDBACK, CLASSIFICATION, CONTEXT)

        assert GUARDRAIL_SUBSTRING in system
