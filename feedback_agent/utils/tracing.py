"""Shared trace-logging helper used by every node and the tool-use loop."""

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


def log_step(trace: list[dict[str, Any]], step: str, **fields: Any) -> None:
    """Append a timestamped entry to `trace` and mirror it via `logging`.

    This is the single place trace-entry shape is defined — every node and
    `claude_client.py`'s tool-use loop call this instead of constructing
    trace dicts inline, so the shape/formatting isn't duplicated across five
    files.
    """
    entry: dict[str, Any] = {"step": step, **fields, "timestamp": datetime.now(UTC).isoformat()}
    trace.append(entry)
    logger.info("%s: %s", step, fields)
