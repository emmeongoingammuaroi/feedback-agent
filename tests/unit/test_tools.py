"""Unit tests for tool lookup functions — against the real mock_data files, no LLM."""

from typing import get_args

import pytest

from feedback_agent.models.classification import Category
from feedback_agent.tools.customer_lookup import get_customer_context
from feedback_agent.tools.policy_lookup import get_policy
from feedback_agent.tools.workflow_lookup import get_workflow_guideline


class TestGetCustomerContext:
    def test_known_customer_id_found(self):
        result = get_customer_context("CUST-1001")

        assert result["found"] is True
        customer = result["customer"]
        assert customer["customer_id"] == "CUST-1001"
        assert "tier" in customer
        assert "tenure_months" in customer

    def test_unknown_customer_id_not_found_without_raising(self):
        result = get_customer_context("CUST-9999")

        assert result == {"found": False, "message": "No customer record found for CUST-9999"}


class TestGetPolicy:
    def test_known_category_found(self):
        result = get_policy("billing_complaint")

        assert result["found"] is True
        assert len(result["policies"]) > 0
        assert all("policy_id" in policy for policy in result["policies"])


class TestGetWorkflowGuideline:
    @pytest.mark.parametrize("category", get_args(Category))
    def test_every_taxonomy_category_found(self, category):
        """Every one of the 7 fixed taxonomy categories must have a guideline —
        this also validates workflow_guidelines.json has full coverage.
        """
        result = get_workflow_guideline(category)

        assert result["found"] is True, f"Missing workflow guideline for {category}"
        assert result["guideline"]["category"] == category
