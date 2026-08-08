"""Anthropic Bedrock client wrapper: retry logic and the ReAct tool-use loop.

Client instantiation is the caller's responsibility (`AnthropicBedrock(aws_region=...)`)
so every function here stays testable with a mock/fake client and no AWS credentials.
"""

import json
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from anthropic import AnthropicBedrock, APIStatusError, RateLimitError
from anthropic.types import Message
from pydantic import BaseModel, ValidationError

from feedback_agent.utils.tracing import log_step

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_RETRY_BACKOFF_SECONDS = 1.0
_MAX_TOKENS = 2048
_RESULT_SUMMARY_MAX_CHARS = 300


class AgentError(Exception):
    """Raised when a Claude API call fails after its retry has also failed."""


def _is_transient(error: Exception) -> bool:
    """Transient errors are worth retrying once; everything else is not."""
    if isinstance(error, RateLimitError):
        return True
    if isinstance(error, APIStatusError):
        return error.status_code >= 500
    return False


def call_with_retry(client: AnthropicBedrock, **kwargs: Any) -> Message:
    """Call `client.messages.create(**kwargs)`, retrying once on a transient error.

    Retries on `RateLimitError` or an `APIStatusError` with a 5xx status,
    after a ~1s backoff. Any failure that isn't recovered — the retry itself
    failing, or a non-transient error on the first attempt — raises
    `AgentError` with the original exception attached, so callers only ever
    need to handle one exception type at this boundary.
    """
    try:
        return client.messages.create(**kwargs)
    except Exception as e:
        if not _is_transient(e):
            logger.error("Non-transient error calling messages.create: %s", e)
            raise AgentError("messages.create failed") from e

        logger.warning("Transient error calling messages.create, retrying once: %s", e)
        time.sleep(_RETRY_BACKOFF_SECONDS)
        try:
            return client.messages.create(**kwargs)
        except Exception as retry_error:
            logger.error("messages.create failed again after retry: %s", retry_error)
            raise AgentError("messages.create failed after retry") from retry_error


def _truncate_result(result: dict) -> str:
    """Render a tool result as a string, truncated for trace readability."""
    rendered = json.dumps(result, default=str)
    if len(rendered) > _RESULT_SUMMARY_MAX_CHARS:
        return rendered[:_RESULT_SUMMARY_MAX_CHARS] + "…"
    return rendered


def run_tool_loop(
    client: AnthropicBedrock,
    model: str,
    system: str,
    user_prompt: str,
    tools: list[dict[str, Any]],
    tool_dispatch: dict[str, Callable[..., dict]],
    max_iterations: int,
    trace: list[dict],
    tool_call_log: list[dict] | None = None,
) -> tuple[str, bool]:
    """Run the ReAct tool-calling loop until Claude stops calling tools.

    The model decides which tools to call, with what arguments, and when it
    has enough context to stop — this is not three hardcoded calls in a fixed
    order. Returns (final_text, incomplete); `incomplete` is True only when
    `max_iterations` is exhausted without the model reaching a stop_reason
    other than "tool_use", in which case the loop degrades gracefully rather
    than raising or looping forever.

    `trace` gets a truncated `result_summary` per call, for human-readable
    observability. If `tool_call_log` is also given, it gets the full,
    untruncated result for each call instead — this is the data
    `generate_report` grounds its claims against (CLAUDE.md: "every field
    that references customer data or policy must be traceable to an actual
    tool result in state['tool_call_log']"), so it must not be truncated the
    way the trace summary is. Optional and additive — omitting it changes
    nothing about the loop's existing behavior.
    """
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]
    last_text = ""

    for _ in range(max_iterations):
        response = call_with_retry(
            client,
            model=model,
            system=system,
            tools=tools,
            messages=messages,
            max_tokens=_MAX_TOKENS,
            thinking={"type": "disabled"},
        )

        text_blocks = [block.text for block in response.content if block.type == "text"]
        if text_blocks:
            last_text = "\n".join(text_blocks)

        if response.stop_reason != "tool_use":
            return last_text, False

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_fn = tool_dispatch.get(block.name)
            if tool_fn is None:
                result = {"found": False, "error": f"Unknown tool: {block.name}"}
            else:
                try:
                    result = tool_fn(**block.input)
                except Exception as e:  # noqa: BLE001 — must never raise; see CLAUDE.md tool design
                    logger.warning("Tool %s raised %s: %s", block.name, type(e).__name__, e)
                    result = {"found": False, "error": str(e)}

            log_step(
                trace,
                "tool_call",
                tool=block.name,
                args=block.input,
                result_summary=_truncate_result(result),
            )
            if tool_call_log is not None:
                tool_call_log.append(
                    {
                        "name": block.name,
                        "args": block.input,
                        "result": result,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})

    # max_iterations exhausted without stop_reason != "tool_use" — degrade, don't crash
    return last_text or "Tool loop reached max_iterations without a final answer.", True


def call_json(
    client: AnthropicBedrock,
    model: str,
    system: str,
    user: str,
    response_model: type[T],
    max_retries: int = 1,
) -> T:
    """Call Claude expecting a single JSON object matching `response_model`.

    Used for the non-tool-loop calls (classify, generate_report) — no tools,
    no loop, one call that must produce valid JSON. On a JSON parse failure
    or a Pydantic validation failure, retries with the same prompt plus an
    appended note describing what went wrong, so the model can self-correct.
    Exhausting `max_retries` raises `AgentError`.
    """
    current_user = user
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        response = call_with_retry(
            client,
            model=model,
            system=system,
            messages=[{"role": "user", "content": current_user}],
            max_tokens=_MAX_TOKENS,
            thinking={"type": "disabled"},
        )

        text = "\n".join(block.text for block in response.content if block.type == "text")

        try:
            parsed = json.loads(text)
            return response_model.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            logger.warning("call_json parse/validation failure on attempt %d: %s", attempt + 1, e)
            current_user = (
                f"{user}\n\n"
                f"Your previous response could not be parsed: {e}. "
                "Respond with ONLY a single valid JSON object matching the required "
                "schema — no prose, no markdown code fences."
            )

    raise AgentError(f"call_json failed after {max_retries + 1} attempts") from last_error
