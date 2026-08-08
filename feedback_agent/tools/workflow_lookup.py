"""Local JSON-backed lookup for CS workflow guidelines."""

import json
from pathlib import Path

MOCK_DATA_PATH = Path(__file__).resolve().parent.parent / "mock_data" / "workflow_guidelines.json"


def get_workflow_guideline(category: str) -> dict:
    """Look up the standard CS workflow guideline for a feedback taxonomy category.

    Never raises: an unrecognized category or a mock-data read/parse failure
    are both normal, expected outcomes surfaced as {"found": False, ...}
    rather than exceptions.
    """
    try:
        guidelines = json.loads(MOCK_DATA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return {"found": False, "error": f"Failed to load workflow guideline data: {e}"}

    for guideline in guidelines:
        if guideline.get("category") == category:
            return {"found": True, "guideline": guideline}

    return {"found": False, "message": f"No workflow guideline found for category '{category}'"}
