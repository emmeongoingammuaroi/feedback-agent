# Sample 2: missing_customer

Missing customer data — valid-looking but unknown customer_id.

## Input

- **channel**: email
- **customer_id**: CUST-1099
- **text**: I noticed I was billed twice for my last order this month, can someone look into refunding the duplicate charge?

## Trace

- `2026-08-08T15:38:54.269371+00:00` **node_end** — node='intake'; feedback_id='f1e8222b-7f6b-45fd-8164-676225f70154'
- `2026-08-08T15:38:56.741948+00:00` **node_end** — node='classify'; category='billing_complaint'; urgency='high'; confidence=0.95
- `2026-08-08T15:38:59.210912+00:00` **tool_call** — tool='get_workflow_guideline'; args={'category': 'billing_complaint'}; result_summary='{"found": true, "guideline": {"category": "billing_complaint", "standard_process": ["Verify the customer\'s identity and pull recent billing history", "Identify the specific charge(s) in dispute", "Check refund eligibility against REFUND-01", "Issue a refund or credit if eligible, or clearly explain …'
- `2026-08-08T15:38:59.211579+00:00` **tool_call** — tool='get_customer_context'; args={'customer_id': 'CUST-1099'}; result_summary='{"found": false, "message": "No customer record found for CUST-1099"}'
- `2026-08-08T15:39:00.839241+00:00` **tool_call** — tool='get_policy'; args={'category': 'billing_complaint'}; result_summary='{"found": true, "policies": [{"policy_id": "REFUND-01", "category": "billing_complaint", "title": "Duplicate Charge & Billing Error Refund Policy", "summary": "Full refund for verified duplicate charges or billing system errors, issued within 5 business days.", "full_text": "If a customer is charged…'
- `2026-08-08T15:39:06.544130+00:00` **node_end** — node='gather_context'; customer_found=False; incomplete=False
- `2026-08-08T15:39:13.142640+00:00` **node_end** — node='generate_report'; requires_human_review=True

## Final Report

```json
{
  "feedback_id": "f1e8222b-7f6b-45fd-8164-676225f70154",
  "generated_at": "2026-08-08T15:39:06.548577Z",
  "summary": "Customer reports being billed twice for their last order and is requesting a refund of the duplicate charge.",
  "category": "billing_complaint",
  "urgency": "high",
  "classification_confidence": 0.95,
  "customer_context": {
    "found": false,
    "summary": "Customer record was not found in the retrieved context."
  },
  "policy_references": [
    {
      "policy_id": "REFUND-01",
      "title": "Duplicate Charge & Billing Error Refund Policy",
      "relevance": "This policy directly covers full refunds for verified duplicate charges, which matches the customer's report of being billed twice for the same order."
    }
  ],
  "suggested_actions": [
    "Verify the customer's identity and pull recent billing history to confirm the duplicate charge, per standard billing_complaint workflow",
    "Check the disputed charge against billing system logs to confirm it qualifies as a duplicate under REFUND-01",
    "If verified, issue a full refund of the duplicate charge to the original payment method within 5 business days per REFUND-01",
    "Document the resolution on the customer's account record and follow up within 48 hours to confirm satisfaction"
  ],
  "requires_human_review": true,
  "review_reason": "customer_id CUST-1099 was provided but no record was found",
  "trace_ref": "f1e8222b-7f6b-45fd-8164-676225f70154.trace.json"
}
```
