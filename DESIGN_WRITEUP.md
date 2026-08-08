# Design Write-up

## 1. Agent structure: single agent, fixed pipeline + one real tool loop

Three of the four nodes — intake, classify, generate_report — have a fixed shape: one clear input, one clear output, nothing for the model to decide about control flow. Only gather_context is genuinely open-ended: which of three tools to call, in what order, and when enough context has been gathered. So this is a single agent with a mostly-fixed pipeline plus exactly one real ReAct-style loop at the one point that needs it.

I rejected both extremes. A fully fixed pipeline — calling all three tools in a hardcoded order — would fail the brief's core requirement outright: it says explicitly that the LLM must decide to call a retrieval function, and a hardcoded sequence decides nothing. A multi-agent system, with separate agents negotiating or handing off between classification, context-gathering, and report-writing, would add coordination overhead without adding capability — nothing here needs parallel exploration or specialized roles, and splitting the pipeline into multiple agents wouldn't make the one genuinely uncertain decision (what to look up, and when to stop) any better made. The tool loop already gives the model all the autonomy this task has a use for.

## 2. Toward production

**Reliability.** `feedback_id` as an idempotency key, so a retried request can't reprocess and produce a duplicate report. LangGraph checkpointing, so a crashed run resumes from its last completed node instead of restarting from intake. Per-node exponential backoff with more than the current single fixed-backoff retry, which was sized for a CLI tool, not a long-running service.

**Cost.** `get_policy` and `get_workflow_guideline` results are keyed only by category, not by the specific feedback, so caching them removes two of three tool round-trips' cost on every run. Track token usage per run in the trace. Move `classify` to a cheaper, faster model — picking one of seven categories is a simpler task than the open-ended reasoning the other two LLM calls need.

**Latency.** Three sequential LLM calls — classify, the tool loop, the report — add up. Any grounding lookup that doesn't depend on the classification result, the customer lookup specifically, could run in parallel with classify instead of waiting on it.

**Evaluation.** The labeled eval harness left as a bonus item: a small fixed set of feedback paired with an expected category and urgency, to catch classification drift across model or prompt changes, plus a report-quality rubric — grounding, actionability — scored by a second LLM call or a periodic human spot-check.

## 3. Deliberately left out

Real CRM/ticketing integration, auth, a UI, multi-language support, and fine-tuning are all explicitly out of scope per the brief. I also skipped two bonus items: multi-turn clarification with the customer for ambiguous feedback, which needs a stateful conversation rather than the single-shot pipeline this is built as; and batch processing with a rollup summary. Both were reasonable cuts against a 1-2 day time-box — the four graded core requirements were the priority, and neither bonus item would have improved them.
