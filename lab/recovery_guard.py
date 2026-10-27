"""CRM-scoped browser-observation guard. No database/operator task access."""

import asyncio
import json
import time
from urllib.parse import urlsplit


class RecoveryGuard:
    def __init__(self, origin, context, log):
        self.origin = origin.rstrip("/")
        self.context = context
        self.log = log
        self.state = "idle"
        self.submitted = None
        self.generation = 0
        self.reads = {}
        self.writes = {}
        self.fresh_read = False
        self.blocked = 0
        self.events = []
        self.tasks = set()
        self.error = None
        self.unresolved = False

    def event(self, decision, **details):
        item = {"sequence": len(self.events) + 1, "monotonic": time.monotonic(),
                "decision": decision, "state": self.state, **details}
        self.events.append(item)
        with self.log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(item) + "\n")

    def spawn(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.tasks.add(task)
        def completed(finished):
            self.tasks.discard(finished)
            if not finished.cancelled() and finished.exception() is not None:
                self.error = "BrowserObservationError"
                self.event("observation_error")
        task.add_done_callback(completed)

    async def install(self):
        if self.context.service_workers:
            raise RuntimeError("Guard cannot enforce service-worker traffic")
        self.context.on("serviceworker", self.worker_seen)
        self.context.on("response", lambda response: self.spawn(self.response(response)))
        self.context.on("requestfailed", self.failed)
        await self.context.route("**/*", self.route)
        self.event("guard_installed")

    def worker_seen(self, worker):
        self.error = "ServiceWorkerUnsupported"
        self.event("unsupported_service_worker")

    async def route(self, route):
        request = route.request
        method = request.method.upper()
        parsed = urlsplit(request.url)
        same = f"{parsed.scheme}://{parsed.netloc}" == self.origin
        if method in {"GET", "HEAD", "OPTIONS"}:
            if same and method == "GET" and parsed.path == "/api/customers":
                self.reads[request] = self.generation
            await route.continue_()
            return
        if self.error or not same or parsed.path != "/api/customers" or method != "POST":
            self.blocked += 1
            self.event("write_blocked_unsupported", method=method)
            await route.abort("blockedbyclient")
            return
        if self.state in {"unknown", "confirmed_visible"}:
            self.blocked += 1
            self.event("repeat_write_blocked")
            await route.abort("blockedbyclient")
            return
        try:
            payload = request.post_data_json
            if (not isinstance(payload, dict) or set(payload) != {"name", "email", "company"}
                    or not all(isinstance(v, str) for v in payload.values())):
                raise ValueError()
        except (ValueError, TypeError):
            self.blocked += 1
            self.event("write_blocked_unrecognized_payload")
            await route.abort("blockedbyclient")
            return
        # No await between checking state and closing the gate: concurrent repeats
        # cannot pass while the first POST is paused at this routing boundary.
        self.generation += 1
        self.submitted = {k: v.strip() for k, v in payload.items()}
        self.state = "unknown"
        self.fresh_read = False
        self.writes[request] = self.generation
        self.event("write_dispatched_outcome_unknown", submitted=self.submitted)
        await route.continue_()

    async def response(self, response):
        request = response.request
        try:
            if request in self.writes:
                if self.writes[request] != self.generation:
                    return
                self.event("write_response_observed", status=response.status)
                if response.status == 422:
                    body = await response.json()
                    if isinstance(body.get("detail"), list) and body["detail"]:
                        self.state = "rejected"
                        self.event("validation_rejection_observed")
            elif self.reads.get(request) == self.generation and self.generation:
                if response.status == 200 and await response.finished() is None:
                    self.fresh_read = True
                    self.event("post_write_read_observed")
        except Exception:
            # An aborted body/read does not establish a rejected or successful write.
            self.event("response_incomplete_outcome_unchanged")

    def failed(self, request):
        if request in self.writes:
            self.event("write_network_failure_outcome_unknown")

    async def observe(self):
        if self.error:
            raise RuntimeError(self.error)
        if self.state != "unknown" or not self.fresh_read:
            return
        matches = []
        for page in self.context.pages:
            if not page.url.startswith(self.origin + "/") and page.url != self.origin:
                continue
            for row in await page.locator("tbody tr").all():
                if not await row.is_visible():
                    continue
                if (await row.locator("strong").count() != 1
                        or await row.locator(".email").count() != 1
                        or await row.locator("td").count() != 2):
                    continue
                details = {"name": (await row.locator("strong").inner_text()).strip(),
                           "email": (await row.locator(".email").inner_text()).strip(),
                           "company": (await row.locator("td").nth(1).inner_text()).strip()}
                if details == self.submitted:
                    matches.append(details)
        if len(matches) == 1:
            self.state = "confirmed_visible"
            self.event("visible_record_reconciled", visible_record=matches[0])
        elif len(matches) > 1:
            self.event("multiple_visible_matches_unresolved", count=len(matches))

    async def after_action(self):
        # Bounded observation, never a fetch/search/click. Included in existing time limit.
        if self.state == "unknown":
            for _ in range(5):
                await asyncio.sleep(.2)
                await self.observe()
                if self.state != "unknown":
                    break

    def message(self):
        if self.state == "unknown":
            return ("Recovery guard: business outcome UNKNOWN. Further writes are BLOCKED. "
                    "Use read-only browser interaction to inspect visible state. A search alone "
                    "is insufficient: a fresh visible row must match the submitted name, email "
                    "and company together. Finish unsuccessfully if this cannot be established.")
        if self.state == "confirmed_visible":
            return ("Recovery guard: one visible row matches the submitted name, email and "
                    "company after a fresh read. Further writes are blocked. You may explicitly "
                    "finish based on this visible evidence; this is not a database grade.")
        return f"Recovery guard state: {self.state}."

    def finish(self):
        self.unresolved = self.state == "unknown"
        self.event("guard_finished", unresolved=self.unresolved)
        return self.summary()

    def summary(self):
        return {"state": self.state, "unresolved": self.unresolved,
                "blocked_writes": self.blocked, "submitted": self.submitted,
                "fresh_read": self.fresh_read, "event_count": len(self.events),
                "infrastructure_error": self.error}


def guarded_tools(guard):
    from browser_use import Tools
    from browser_use.agent.views import ActionResult

    class GuardedTools(Tools):
        async def act(self, action, browser_session, **kwargs):
            await guard.observe()
            fields = action.model_dump(exclude_unset=True)
            guard.event("agent_action", action=fields)
            if fields.get("done") is not None and guard.state in {"unknown", "rejected"}:
                guard.unresolved = guard.state == "unknown"
                guard.event("agent_done_blocked", proposed_success=fields["done"].get("success"))
                text = ("UNRESOLVED: uncertain write could not be reconciled from visible "
                        "record details; further writes remain prohibited." if guard.unresolved else
                        "FAILED: submission was rejected and no completed write was observed.")
                return ActionResult(is_done=True, success=False, extracted_content=text)
            result = await super().act(action, browser_session, **kwargs)
            await guard.after_action()
            result.extracted_content = (result.extracted_content or "") + "\n" + guard.message()
            return result

    return GuardedTools()
