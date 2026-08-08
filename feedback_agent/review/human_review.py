"""Human-in-the-loop review stub — not a graph node.

Approval is a human action outside the agent's control flow, not something
the agent decides to do, so this lives outside the LangGraph pipeline
entirely and is called directly by main.py after generate_report.
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from feedback_agent.models.report import FeedbackReport

REVIEW_LOG_PATH = Path("review_log.jsonl")

_DECISION_LABELS = {"a": "approved", "e": "edited", "r": "rejected"}


def present_for_review(report: FeedbackReport, interactive: bool) -> None:
    """Print the report and, if interactive, prompt for approve/edit/reject.

    Non-interactive (default for batch/sample runs): prints the report and,
    if requires_human_review, a clear warning banner. No blocking.

    Interactive (--interactive flag): prompts [a]pprove / [e]dit / [r]eject,
    appends the decision to review_log.jsonl (officer_id is a placeholder
    env var — no real auth, explicitly out of scope). Only an "approved"
    report would, in a real system, trigger downstream action; there is no
    real downstream system here, so that's stubbed with a log line.
    """
    print(report.to_json())

    if report.requires_human_review:
        print("\n⚠ REQUIRES HUMAN REVIEW")
        if report.review_reason:
            print(f"  Reason: {report.review_reason}")

    if not interactive:
        return

    officer_id = os.environ.get("CS_OFFICER_ID", "unknown-officer")
    choice = ""
    while choice not in _DECISION_LABELS:
        choice = input("\n[a]pprove / [e]dit / [r]eject: ").strip().lower()
    decision = _DECISION_LABELS[choice]

    log_entry = {
        "feedback_id": report.feedback_id,
        "officer_id": officer_id,
        "decision": decision,
        "reviewed_at": datetime.now(UTC).isoformat(),
    }
    with REVIEW_LOG_PATH.open("a") as f:
        f.write(json.dumps(log_entry) + "\n")

    if decision == "approved":
        print(f"Approved by {officer_id} — would trigger downstream action here (stubbed).")
    else:
        print(f"{decision.capitalize()} by {officer_id} — logged to {REVIEW_LOG_PATH}.")
