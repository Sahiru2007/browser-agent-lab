"""Offline metrics. Unknown usage is never silently converted into zero."""

import math
from collections import defaultdict
from statistics import mean, median

METRICS = (
    "wall_seconds", "driver_seconds", "model_calls", "input_tokens", "output_tokens",
    "total_tokens", "cached_input_tokens", "estimated_cost_usd", "reserved_cost_usd",
    "billed_cost_usd",
)


def metric(value=None, status="unknown", unit=None, reason=None, **extra):
    return {"value": value, "status": status, "unit": unit, "reason": reason, **extra}


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def wilson(successes, n):
    if not n:
        return None
    z = 1.959963984540054
    p = successes / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, center - margin), min(1.0, center + margin)]


def rate(successes, n):
    return metric(successes / n if n else None, "measured" if n else "unavailable",
                  "fraction", numerator=successes, denominator=n, wilson95=wilson(successes, n))


def trial_metrics(raw, duration, kind, limits=None):
    result = {name: metric(unit="USD" if "cost" in name else
                           "seconds" if "seconds" in name else "count") for name in METRICS}
    result["wall_seconds"] = metric(duration, "measured", "seconds")
    driver = raw.get("driver_duration_seconds")
    result["driver_seconds"] = metric(
        driver, "measured" if number(driver) else "unavailable", "seconds",
        None if number(driver) else "Runner did not record driver duration")
    result["billed_cost_usd"] = metric(status="unavailable", unit="USD",
                                        reason="Provider billing was not reconciled")
    if kind.startswith("scripted_"):
        for name in METRICS[2:]:
            result[name] = metric(status="unavailable", unit=result[name]["unit"],
                                  reason="Scripted control; model metric is not applicable")
        return result
    usage = (raw.get("agent") or {}).get("usage") or {}
    calls = usage.get("model_calls")
    entries = usage.get("provider_usage") or []
    valid_calls = isinstance(calls, int) and not isinstance(calls, bool) and calls >= 0
    if valid_calls:
        result["model_calls"] = metric(calls, "measured", "count")
    complete = valid_calls and len(entries) == calls
    for name, field in (("input_tokens", "prompt_tokens"),
                        ("output_tokens", "completion_tokens"),
                        ("cached_input_tokens", "prompt_cached_tokens")):
        values = [entry.get(field) for entry in entries]
        known = [value for value in values if number(value) and value >= 0]
        full = complete and len(known) == len(entries)
        result[name] = metric(sum(known) if full else None,
                              "measured" if full else "unknown", "count",
                              known_subtotal=sum(known) if known or full else None,
                              reported_calls=len(known))
    inp, out = result["input_tokens"], result["output_tokens"]
    if inp["status"] == out["status"] == "measured":
        result["total_tokens"] = metric(inp["value"] + out["value"], "measured", "count")
    if limits and (inp.get("known_subtotal") is not None
                   or out.get("known_subtotal") is not None):
        estimate = ((inp.get("known_subtotal") or 0) * limits["input_usd_per_million"]
                    + (out.get("known_subtotal") or 0)
                    * limits["output_usd_per_million"]) / 1_000_000
        full = inp["status"] == out["status"] == "measured"
        result["estimated_cost_usd"] = metric(
            estimate if full else None, "estimated" if full else "unknown", "USD",
            "Operator price ceilings; not an invoice", known_subtotal=estimate)
    reserved = usage.get("reserved_cost_usd")
    if number(reserved):
        result["reserved_cost_usd"] = metric(reserved, "estimated", "USD",
                                             "Conservative call reservations, not actual cost")
    return result


def valid_evaluation(trial):
    value = trial.get("evaluation")
    return (isinstance(value, dict) and isinstance(value.get("passed"), bool)
            and isinstance(value.get("issues"), list)
            and all(isinstance(issue, str) for issue in value["issues"])
            and value["passed"] == (not value["issues"]))


def aggregate(trials):
    groups = defaultdict(list)
    for trial in trials:
        key = tuple(trial.get(field) for field in (
            "kind", "strategy", "scenario", "transport", "task_version", "policy_version",
            "provider", "model"))
        groups[key].append(trial)
    output = []
    for key, rows in sorted(groups.items(), key=lambda item: str(item[0])):
        group = dict(zip(("kind", "strategy", "scenario", "transport", "task_version",
                          "policy_version", "provider", "model"), key, strict=True))
        started = [row for row in rows if row["state"] not in {"scheduled", "not_run_budget"}]
        evaluated = [row for row in started if valid_evaluation(row)]
        successes = sum(row["evaluation"]["passed"] and not row.get("execution_error")
                        and row["state"] == "completed" for row in started
                        if valid_evaluation(row))
        group.update(
            planned=len(rows), started=len(started), evaluated=len(evaluated),
            unfinished=sum(row["state"] in {"running", "interrupted"} for row in started),
            execution_errors=sum(bool(row.get("execution_error")) for row in started),
            operational_success=rate(successes, len(started)),
            business_success=rate(sum(row["evaluation"]["passed"] for row in evaluated),
                                  len(evaluated)),
            duplicate_action_rate=rate(sum("duplicate_customer" in row["evaluation"]["issues"]
                                          for row in evaluated), len(evaluated)),
            missing_evaluations=len(started) - len(evaluated),
        )
        group["metrics"] = {}
        for name in METRICS:
            values = [row.get("metrics", {}).get(name, metric()) for row in started]
            known = [m["value"] for m in values if m["status"] in {"measured", "estimated"}
                     and number(m.get("value"))]
            unknown = sum(m["status"] == "unknown" for m in values)
            unavailable = len(values) - len(known) - unknown
            observed = [m.get("known_subtotal") for m in values
                        if m["status"] == "unknown" and number(m.get("known_subtotal"))]
            status = ("unknown" if unknown else "unavailable" if not known else
                      "estimated" if any(m["status"] == "estimated" for m in values)
                      else "measured")
            group["metrics"][name] = {
                "status": status, "known_count": len(known), "unknown_count": unknown,
                "unavailable_count": unavailable, "coverage": len(known) / len(values)
                if values else None,
                "total": sum(known) if known else None,
                "observed_subtotal": sum(known + observed) if known or observed else None,
                "mean": mean(known) if known else None,
                "median": median(known) if known else None,
                "p95": sorted(known)[math.ceil(len(known) * 0.95) - 1] if known else None,
                "totals_are_partial": len(known) != len(values),
            }
        output.append(group)
    return output
