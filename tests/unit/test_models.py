"""Unit tests for Pydantic models — pure validation logic, no AWS/network."""

import json

import pytest
from pydantic import ValidationError

from feedback_agent.models.classification import Classification
from feedback_agent.models.feedback import FeedbackSubmission
from feedback_agent.models.report import CustomerContextSummary, FeedbackReport


class TestFeedbackSubmission:
    def test_valid_submission_validates(self):
        submission = FeedbackSubmission(channel="email", text="I have an issue with my order.")
        assert submission.text == "I have an issue with my order."
        assert submission.channel == "email"
        assert submission.feedback_id  # auto-assigned by default_factory

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError):
            FeedbackSubmission(channel="email", text="")


class TestClassification:
    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError):
            Classification(category="praise", urgency="low", confidence=1.5, rationale="x")

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError):
            Classification(category="praise", urgency="low", confidence=-0.1, rationale="x")

    def test_confidence_valid_value_ok(self):
        classification = Classification(category="praise", urgency="low", confidence=0.5, rationale="x")
        assert classification.confidence == 0.5

    def test_invalid_category_raises(self):
        with pytest.raises(ValidationError):
            Classification(category="not_a_real_category", urgency="low", confidence=0.5, rationale="x")

    def test_invalid_urgency_raises(self):
        with pytest.raises(ValidationError):
            Classification(category="praise", urgency="not_a_real_urgency", confidence=0.5, rationale="x")


class TestFeedbackReport:
    def test_to_json_serialises_valid_json(self):
        report = FeedbackReport(
            feedback_id="fb-123",
            generated_at="2026-08-08T10:00:00Z",
            summary="Test summary.",
            category="billing_complaint",
            urgency="high",
            classification_confidence=0.9,
            customer_context=CustomerContextSummary(found=True, summary="Pro tier"),
            policy_references=[],
            suggested_actions=["Do something"],
            requires_human_review=False,
            review_reason=None,
            trace_ref="fb-123.trace.json",
        )

        parsed = json.loads(report.to_json())

        assert parsed["feedback_id"] == "fb-123"
        assert parsed["category"] == "billing_complaint"
        assert parsed["customer_context"] == {"found": True, "summary": "Pro tier"}
