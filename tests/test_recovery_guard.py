"""Guard policy and actual browser enforcement tests; no real model calls."""

import asyncio
import json
import os
from types import SimpleNamespace

import pytest

from lab.adapters import GuardConfig, OllamaConfig
from lab.agent_run import run_trial
from lab.recovery_guard import RecoveryGuard
from lab.tasks import benchmark_task


class Request:
    method = "POST"
    url = "http://127.0.0.1:1234/api/customers"
    post_data_json = {"name": "Example", "email": "e@example.test", "company": "Grove"}


class Route:
    def __init__(self, request=None):
        self.request = request or Request()
        self.continued = self.aborted = False

    async def continue_(self):
        self.continued = True

    async def abort(self, reason):
        self.aborted = True


def test_pre_dispatch_unknown_blocks_repeats_and_payload_changes(tmp_path):
    guard = RecoveryGuard("http://127.0.0.1:1234", SimpleNamespace(pages=[]), tmp_path / "log")

    async def check():
        first, repeat = Route(), Route()
        await guard.route(first)
        await guard.route(repeat)
        assert first.continued and repeat.aborted
        assert guard.state == "unknown"
        changed = Route()
        changed.request.post_data_json = {
            "name": "Other", "email": "o@example.test", "company": "X"}
        await guard.route(changed)
        assert changed.aborted
        assert guard.blocked == 2
        await guard.observe()
        assert guard.state == "unknown"  # No read/record evidence, not success.

    asyncio.run(check())
    assert guard.finish()["unresolved"]


def test_known_validation_rejection_allows_another_attempt(tmp_path):
    guard = RecoveryGuard("http://127.0.0.1:1234", SimpleNamespace(pages=[]), tmp_path / "log")

    async def check():
        first = Route()
        await guard.route(first)

        async def body():
            return {"detail": [{"type": "value_error", "loc": ["body", "email"]}]}

        await guard.response(SimpleNamespace(request=first.request, status=422, json=body))
        assert guard.state == "rejected"
        corrected = Route()
        await guard.route(corrected)
        assert corrected.continued
        assert guard.state == "unknown"

    asyncio.run(check())


def test_config_does_not_change_old_limits():
    from dataclasses import asdict

    guarded = asdict(GuardConfig())
    assert guarded.pop("recovery_guard") == "visible-write-v1"
    assert guarded == asdict(OllamaConfig())


@pytest.mark.skipif(os.environ.get("LAB_TEST_BROWSER_USE") != "1", reason="Opt-in Chromium")
@pytest.mark.parametrize("case", ["normal", "lost-reconcile", "lost-unresolved", "wrong-unresolved",
                                  "rejected-then-corrected"])
def test_real_browser_guard_enforcement_and_independent_grade(tmp_path, case):
    from playwright.async_api import async_playwright

    class BrowserFixture:
        kind = "mocked_adapter_test"

        def execute(self, request, config, output):
            return asyncio.run(self.drive(request, output))

        async def drive(self, request, output):
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                try:
                    context = await browser.new_context(service_workers="block")
                    page = await context.new_page()
                    guard = RecoveryGuard(request.url, context, output / "guard-events.jsonl")
                    await guard.install()
                    await page.goto(request.url)
                    await page.locator("tbody tr").nth(1).wait_for()
                    if case == "rejected-then-corrected":
                        # Trusted test code only; the tested agent gets no evaluate tool.
                        await page.evaluate("""async () => fetch('/api/customers', {
                            method:'POST',headers:{'Content-Type':'application/json'},
                            body:JSON.stringify({name:'X',email:'bad',company:'Y'})})""")
                        await asyncio.sleep(.2)
                        assert guard.state == "rejected"
                    name = "Wrong Person" if case == "wrong-unresolved" else "Nimal Silva"
                    await page.locator('#name').fill(name)
                    await page.locator('#email').fill('nimal@example.test')
                    await page.locator('#company').fill('Evergreen Farms')
                    # Independent CDP connection dispatches the same native click protocol
                    # used by Browser Use, not a Playwright click wrapper.
                    box = await page.locator('button[type=submit]').bounding_box()
                    cdp = await context.new_cdp_session(page)
                    point = {"x": box['x'] + box['width']/2, "y": box['y'] + box['height']/2,
                             "button": "left", "clickCount": 1}
                    await cdp.send("Input.dispatchMouseEvent", {"type": "mousePressed", **point})
                    await cdp.send("Input.dispatchMouseEvent", {"type": "mouseReleased", **point})
                    await asyncio.sleep(1)
                    await guard.observe()
                    if case in {"normal", "rejected-then-corrected"}:
                        assert guard.state == "confirmed_visible"
                        # Refill cleared form and submit with Enter: route must still block.
                        await page.locator('#name').fill(name)
                        await page.locator('#email').fill('nimal@example.test')
                        await page.locator('#company').fill('Evergreen Farms')
                    else:
                        assert guard.state == "unknown"
                    await page.locator('#company').press('Enter')
                    await asyncio.sleep(.3)
                    assert guard.blocked == 1
                    if case == "lost-reconcile":
                        await page.locator('#search').fill('nimal@example.test')
                        assert guard.state == "unknown"  # Search initiation is insufficient.
                        await page.locator('tbody tr').filter(has_text='Nimal Silva').wait_for()
                        await guard.observe()
                        assert guard.state == "confirmed_visible"
                    summary = guard.finish()
                    return {"recovery_guard": summary,
                            "agent_claimed_success": not summary['unresolved'],
                            "execution_error": None}
                finally:
                    await browser.close()

    scenario = "normal" if case in {"normal", "rejected-then-corrected"} else "lost-confirmation"
    result = run_trial(benchmark_task(scenario, "basic-browser-use"), BrowserFixture(),
                       GuardConfig(), tmp_path / case)
    assert result['execution_error'] is None, result
    assert result['evaluation']['passed'] == (case != 'wrong-unresolved')
    assert 'duplicate_customer' not in result['evaluation']['issues']
    assert result['agent']['recovery_guard']['unresolved'] == (
        case in {'lost-unresolved', 'wrong-unresolved'})
    # Guard prevention alone cannot pass an incorrect task.
    if case == 'wrong-unresolved':
        assert result['evaluation']['passed'] is False
    events = [json.loads(line) for line in
              (tmp_path / case / 'guard-events.jsonl').read_text().splitlines()]
    assert any(e['decision']=='repeat_write_blocked' for e in events)


def test_unresolved_done_cannot_be_claimed_success(tmp_path):
    pytest.importorskip("browser_use")
    from lab.agent_worker import browser_tools

    guard = RecoveryGuard("http://127.0.0.1:1234", SimpleNamespace(pages=[]), tmp_path / "log")
    guard.state = "unknown"
    action = SimpleNamespace(model_dump=lambda **kwargs: {
        "done": {"text": "Claimed success", "success": True}})
    result = asyncio.run(browser_tools(guard).act(action, None))
    assert result.is_done and result.success is False
    assert 'UNRESOLVED' in result.extracted_content
    assert 'remain prohibited' in result.extracted_content
    assert 'were blocked' not in result.extracted_content
    assert guard.blocked == 0
    assert guard.events[-1]['proposed_success'] is True


@pytest.mark.parametrize('change,count', [({'company': 'Different'}, 1),
                                         ({'email': 'other@example.test'}, 1),
                                         ({'name': 'Other'}, 1), ({}, 2), ({}, 1)])
def test_only_complete_unique_visible_details_reconcile(tmp_path, change, count):
    submitted = {'name': 'Example', 'email': 'e@example.test', 'company': 'Grove'}
    details = {**submitted, **change}

    class Locator:
        def __init__(self, value, n=1):
            self.value, self.n = value, n

        async def count(self):
            return self.n

        async def inner_text(self):
            return self.value

        def nth(self, index):
            return self

    class Row:
        async def is_visible(self):
            return True

        def locator(self, selector):
            return {'strong': Locator(details['name']), '.email': Locator(details['email']),
                    'td': Locator(details['company'], 2)}[selector]

    async def rows():
        return [Row() for _ in range(count)]

    page = SimpleNamespace(url='http://127.0.0.1:1234/',
                           locator=lambda selector: SimpleNamespace(all=rows))
    guard = RecoveryGuard('http://127.0.0.1:1234', SimpleNamespace(pages=[page]), tmp_path / 'log')
    guard.state, guard.submitted = 'unknown', submitted
    asyncio.run(guard.observe())
    assert guard.state == 'unknown'  # Matching but stale rows are insufficient too.
    guard.fresh_read = True
    asyncio.run(guard.observe())
    assert (guard.state == 'confirmed_visible') == (not change and count == 1)


def test_5xx_is_not_proof_of_failed_write(tmp_path):
    guard = RecoveryGuard('http://127.0.0.1:1234', SimpleNamespace(pages=[]), tmp_path / 'log')

    async def check():
        first = Route()
        await guard.route(first)
        await guard.response(SimpleNamespace(request=first.request, status=500))
        assert guard.state == 'unknown'
        repeat = Route()
        await guard.route(repeat)
        assert repeat.aborted

    asyncio.run(check())


def test_guard_report_separates_grade_from_unresolved(tmp_path):
    from lab.benchmark import atomic_json
    from lab.guard_run import analyze

    specs = [{'trial_id': f'trial-{i:04d}', 'scenario': 'normal', 'seed': i}
             for i in range(1, 5)]
    atomic_json(tmp_path / 'manifest.json', {'kind': 'mocked_adapter_test', 'schedule': specs})
    atomic_json(tmp_path / 'state.json', {'state': 'stopped'})
    for i, spec in enumerate(specs):
        folder = tmp_path / spec['trial_id']
        folder.mkdir()
        value = {**spec, 'state': 'not_started'}
        if i == 0:
            value.update(state='completed', evaluation={'passed': True, 'issues': []},
                         guard={'state': 'unknown', 'unresolved': True, 'blocked_writes': 2})
        atomic_json(folder / 'guard-result.json', value)
    log = tmp_path / specs[0]['trial_id'] / 'evidence/browser-evidence/guard-events.jsonl'
    log.parent.mkdir(parents=True)
    events = [{'decision': 'repeat_write_blocked'}, {'decision': 'repeat_write_blocked'},
              {'decision': 'agent_done_blocked', 'proposed_success': False},
              {'decision': 'agent_done_blocked', 'proposed_success': True}]
    log.write_text('\n'.join(json.dumps(event) for event in events))
    result = analyze(tmp_path)
    assert result['counts']['unresolved_done_interceptions'] == 2
    assert result['counts']['positive_success_claims_overridden'] == 1
    assert result['counts']['business_pass'] == 1
    assert result['counts']['unresolved'] == 1
    assert result['counts']['guard_blocked_writes'] == 2
    assert 'mocked_adapter_test' in (tmp_path / 'report.html').read_text()


def test_existing_service_worker_is_explicitly_unsupported(tmp_path):
    guard = RecoveryGuard('http://127.0.0.1:1234',
                          SimpleNamespace(service_workers=[object()]), tmp_path / 'log')
    with pytest.raises(RuntimeError, match='service-worker'):
        asyncio.run(guard.install())


def test_concurrent_repeats_cannot_pass_the_gate(tmp_path):
    guard = RecoveryGuard('http://127.0.0.1:1234', SimpleNamespace(pages=[]), tmp_path / 'log')
    routes = [Route(), Route()]

    async def check():
        await asyncio.gather(*(guard.route(route) for route in routes))

    asyncio.run(check())
    assert sum(route.continued for route in routes) == 1
    assert sum(route.aborted for route in routes) == 1



@pytest.mark.parametrize('method,url,payload', [
    ('PUT', 'http://127.0.0.1:1234/api/customers', None),
    ('PATCH', 'http://127.0.0.1:1234/api/customers', None),
    ('DELETE', 'http://127.0.0.1:1234/api/customers', None),
    ('POST', 'http://127.0.0.1:1234/other', None),
    ('POST', 'http://example.test/api/customers', None),
    ('POST', 'http://127.0.0.1:1234/api/customers', ['name', 'email', 'company']),
])
def test_routed_unsupported_writes_are_blocked(tmp_path, method, url, payload):
    guard = RecoveryGuard('http://127.0.0.1:1234', SimpleNamespace(pages=[]), tmp_path / 'log')
    request = Request()
    request.method, request.url = method, url
    if payload is not None:
        request.post_data_json = payload
    route = Route(request)
    asyncio.run(guard.route(route))
    assert route.aborted and not route.continued
    assert guard.blocked == 1
    assert guard.state == 'idle'


def test_detected_service_worker_flags_error_and_blocks_only_routed_writes(tmp_path):
    guard = RecoveryGuard('http://127.0.0.1:1234', SimpleNamespace(pages=[]), tmp_path / 'log')
    guard.worker_seen(object())
    assert guard.error == 'ServiceWorkerUnsupported'
    route = Route()
    asyncio.run(guard.route(route))
    assert route.aborted
    with pytest.raises(RuntimeError, match='ServiceWorkerUnsupported'):
        asyncio.run(guard.observe())
    # This does not assert interception of service-worker-owned bypass traffic.


@pytest.mark.skipif(os.environ.get('LAB_TEST_BROWSER_USE') != '1', reason='Opt-in Chromium')
def test_other_browser_context_is_not_guarded(tmp_path):
    """Negative boundary test with scripted browser actions; no model invocation."""
    from playwright.async_api import async_playwright, expect

    class BoundaryFixture:
        kind = 'mocked_adapter_test'

        def execute(self, request, config, output):
            return asyncio.run(self.drive(request.url, output))

        async def drive(self, url, output):
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                try:
                    context = await browser.new_context(service_workers='block')
                    guard = RecoveryGuard(url, context, output / 'guard.jsonl')
                    await guard.install()
                    page = await context.new_page()
                    await page.goto(url)
                    for key, value in [('name', 'Nimal Silva'), ('email', 'nimal@example.test'),
                                       ('company', 'Evergreen Farms')]:
                        await page.locator('#' + key).fill(value)
                    await page.get_by_role('button', name='Save customer').click()
                    await expect(page.get_by_role('status')).to_contain_text('Could not confirm')
                    assert guard.state == 'unknown'
                    other = await browser.new_context(service_workers='block')
                    second = await other.new_page()
                    await second.goto(url)
                    for key, value in [('name', 'Nimal Silva'), ('email', 'nimal@example.test'),
                                       ('company', 'Evergreen Farms')]:
                        await second.locator('#' + key).fill(value)
                    await second.get_by_role('button', name='Save customer').click()
                    await expect(second.get_by_role('status')).to_have_text('Customer saved.')
                    assert guard.blocked == 0
                    assert len(guard.writes) == 1  # Other context's POST was not intercepted.
                    assert guard.state == 'unknown'
                    return {'execution_error': None, 'recovery_guard': guard.finish()}
                finally:
                    await browser.close()

    report = run_trial(benchmark_task('lost-confirmation', 'basic-browser-use'),
                       BoundaryFixture(), GuardConfig(), tmp_path / 'boundary')
    assert report['execution_error'] is None, report
    assert report['evaluation']['passed'] is False
    assert 'duplicate_customer' in report['evaluation']['issues']
