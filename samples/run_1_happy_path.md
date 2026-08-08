# Sample 1: happy_path

Happy path — clear billing complaint, known customer, policy found.

## Input

- **channel**: email
- **customer_id**: CUST-1001
- **text**: I was charged twice for my last order — please refund the duplicate charge as soon as possible.

## Trace

- `2026-08-08T15:38:31.827676+00:00` **node_end** — node='intake'; feedback_id='6d41c28e-61cb-459d-aec9-858392b43f49'
- `2026-08-08T15:38:35.461620+00:00` **node_end** — node='classify'; category='billing_complaint'; urgency='high'; confidence=0.95
- `2026-08-08T15:38:39.083568+00:00` **tool_call** — tool='get_workflow_guideline'; args={'category': 'billing_complaint'}; result_summary='{"found": true, "guideline": {"category": "billing_complaint", "standard_process": ["Verify the customer\'s identity and pull recent billing history", "Identify the specific charge(s) in dispute", "Check refund eligibility against REFUND-01", "Issue a refund or credit if eligible, or clearly explain …'
- `2026-08-08T15:38:39.084325+00:00` **tool_call** — tool='get_customer_context'; args={'customer_id': 'CUST-1001'}; result_summary='{"found": true, "customer": {"customer_id": "CUST-1001", "email": "j.tan@example.com", "name": "Jasmine Tan", "tier": "pro", "tenure_months": 14, "order_count": 23, "lifetime_value_usd": 4200, "past_tickets": [{"ticket_id": "TCK-881", "date": "2026-05-02", "category": "billing_complaint", "resolutio…'
- `2026-08-08T15:38:41.160522+00:00` **tool_call** — tool='get_policy'; args={'category': 'billing_complaint'}; result_summary='{"found": true, "policies": [{"policy_id": "REFUND-01", "category": "billing_complaint", "title": "Duplicate Charge & Billing Error Refund Policy", "summary": "Full refund for verified duplicate charges or billing system errors, issued within 5 business days.", "full_text": "If a customer is charged…'
- `2026-08-08T15:38:47.450564+00:00` **node_end** — node='gather_context'; customer_found=True; incomplete=False
- `2026-08-08T15:38:54.265915+00:00` **node_end** — node='generate_report'; requires_human_review=False

## Final Report

```json
{
  "feedback_id": "6d41c28e-61cb-459d-aec9-858392b43f49",
  "generated_at": "2026-08-08T15:38:47.461883Z",
  "summary": "Customer reports being charged twice for their last order and is requesting a prompt refund of the duplicate charge.",
  "category": "billing_complaint",
  "urgency": "high",
  "classification_confidence": 0.95,
  "customer_context": {
    "found": true,
    "summary": "Jasmine Tan (CUST-1001), Pro-tier customer with 14 months tenure, 23 orders, $4,200 lifetime value, and one prior billing complaint (TCK-881) resolved via refund for a duplicate charge."
  },
  "policy_references": [
    {
      "policy_id": "REFUND-01",
      "title": "Duplicate Charge & Billing Error Refund Policy",
      "relevance": "Directly applies since the customer reports a duplicate charge for the same order, which qualifies for a full refund once verified against billing system logs."
    }
  ],
  "suggested_actions": [
    "Verify the duplicate charge against billing system logs per REFUND-01",
    "Issue a full refund of the duplicate charge to the original payment method within 5 business days once verified, consistent with the resolution of the customer's prior similar case (TCK-881)",
    "Document the resolution on the customer's account record",
    "Follow up within 48 hours to confirm the refund resolved the issue to the customer's satisfaction"
  ],
  "requires_human_review": false,
  "review_reason": null,
  "trace_ref": "6d41c28e-61cb-459d-aec9-858392b43f49.trace.json"
}
```
