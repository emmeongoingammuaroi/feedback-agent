"""Local JSON-backed lookup for customer account records."""

import json
from pathlib import Path

MOCK_DATA_PATH = Path(__file__).resolve().parent.parent / "mock_data" / "customers.json"


def get_customer_context(customer_id: str) -> dict:
    """Look up a customer's account context by customer_id.

    Never raises: a missing record or a mock-data read/parse failure are both
    normal, expected outcomes surfaced as {"found": False, ...} rather than
    exceptions, so the caller (the tool-use loop) can feed the result straight
    back to the model without a try/except of its own.
    """
    try:
        customers = json.loads(MOCK_DATA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return {"found": False, "error": f"Failed to load customer data: {e}"}

    for customer in customers:
        if customer.get("customer_id") == customer_id:
            return {"found": True, "customer": customer}

    return {"found": False, "message": f"No customer record found for {customer_id}"}
