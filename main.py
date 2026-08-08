"""CLI entrypoint for the feedback triage pipeline."""

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from feedback_agent.config import Settings
from feedback_agent.graph import build_graph
from feedback_agent.models.feedback import FeedbackSubmission
from feedback_agent.review.human_review import present_for_review

SAMPLES_DIR = Path("samples")

logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triage a piece of customer feedback.")
    parser.add_argument("--text", required=True, help="The feedback text.")
    parser.add_argument("--customer-id", default=None, help="Optional customer_id.")
    parser.add_argument(
        "--channel",
        default="web_form",
        choices=["email", "web_form", "chat", "survey"],
        help="Submission channel (default: web_form).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for human review (approve/edit/reject) after the report is produced.",
    )
    return parser.parse_args()


def main() -> None:
    # pydantic-settings reads .env for its own fields without exporting them,
    # but AWS_PROFILE isn't a Settings field — boto3 (inside AnthropicBedrock)
    # reads it straight from the process environment, so it must actually be
    # exported there via load_dotenv(), not just parsed internally.
    load_dotenv()

    args = _parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    settings = Settings()
    logger.info("Using model %s in region %s", settings.anthropic_model, settings.aws_region)

    feedback = FeedbackSubmission(
        channel=args.channel, text=args.text, customer_id=args.customer_id
    )

    graph = build_graph()
    result = graph.invoke(
        {
            "feedback": feedback,
            "trace": [],
            "errors": [],
            "classification": None,
            "context": None,
            "tool_call_log": [],
            "report": None,
        }
    )

    trace = result.get("trace", [])
    errors = result.get("errors", [])
    report = result.get("report")

    print("\n=== Trace ===")
    for entry in trace:
        print(json.dumps(entry, default=str))

    if report is not None:
        print("\n=== Report ===")
        present_for_review(report, interactive=args.interactive)

    SAMPLES_DIR.mkdir(exist_ok=True)
    trace_path = SAMPLES_DIR / f"{feedback.feedback_id}.trace.json"
    trace_path.write_text(json.dumps(trace, indent=2, default=str))
    print(f"\nTrace saved to {trace_path}")

    if errors:
        print("\n=== Errors ===")
        for err in errors:
            print(f"  - {err}")

    sys.exit(1 if errors and report is None else 0)


if __name__ == "__main__":
    main()
