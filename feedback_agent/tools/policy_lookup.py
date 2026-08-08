"""Local JSON-backed lookup for company policies."""

import json
from pathlib import Path

MOCK_DATA_PATH = Path(__file__).resolve().parent.parent / "mock_data" / "policies.json"


def get_policy(category: str) -> dict:
    """Look up policies whose own `category` field matches the given category.

    Policy categories are not 1:1 with the feedback classification taxonomy —
    e.g. "sla" and "escalation" are cross-cutting operational policy
    categories with no equivalent feedback category. This matches against the
    policy data's category field as-is, without assuming the caller passed a
    value from the 7-value feedback taxonomy.

    Never raises: no matching category or a mock-data read/parse failure are
    both normal, expected outcomes surfaced as {"found": False, ...} rather
    than exceptions.
    """
    try:
        policies = json.loads(MOCK_DATA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return {"found": False, "error": f"Failed to load policy data: {e}"}

    matches = [policy for policy in policies if policy.get("category") == category]
    if matches:
        return {"found": True, "policies": matches}

    return {"found": False, "message": f"No policies found for category '{category}'"}
