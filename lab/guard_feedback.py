"""Feedback-only presentation wrapper; no guard decision or operator-state access."""

import json

CLARIFICATION = (
    "Finding text or scrolling only examines the currently loaded page.\n"
    "To verify an uncertain submission, use the application's search or\n"
    "refresh mechanism to retrieve current records, then inspect the\n"
    "matching record's visible details. Do not resubmit while uncertain."
)


def feedback_tools(tools, guard, variant, log):
    if variant not in {"A", "B"}:
        raise ValueError("Feedback variant must be A or B")
    original = tools.act

    async def act(action, browser_session, **kwargs):
        result = await original(action, browser_session, **kwargs)
        # Only the guard's existing browser-observable UNKNOWN feedback triggers
        # the clarification. No task/scenario/seed/assertion is consulted here.
        if guard.state == "unknown" and guard.message() in (result.extracted_content or ""):
            added = variant == "B"
            if added:
                result.extracted_content += "\n" + CLARIFICATION
            with log.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"variant": variant, "uncertainty_observed": True,
                    "clarification_added": added, "feedback": guard.message() + (
                        "\n" + CLARIFICATION if added else "")}) + "\n")
        return result

    tools.act = act
    return tools
