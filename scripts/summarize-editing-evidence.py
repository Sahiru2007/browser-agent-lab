"""Read retained editing evidence only; never import or dispatch an agent/model."""
import argparse
import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path


def supplied_values_match(native, recorded):
    # SDK history includes default arguments absent from the native response.
    if isinstance(native, dict):
        return isinstance(recorded, dict) and all(
            k in recorded and supplied_values_match(v, recorded[k]) for k, v in native.items())
    if isinstance(native, list):
        return isinstance(recorded, list) and len(native) == len(recorded) and all(
            supplied_values_match(a, b) for a, b in zip(native, recorded, strict=True))
    return native == recorded


def summarize(root):
    manifest = json.loads((root / 'manifest.json').read_text())
    rows = []
    for spec in manifest['schedule']:
        folder = root / spec['trial_id']
        raw = json.loads((folder / 'result.json').read_text())
        history_file = folder / 'browser-evidence/browser-history.json'
        history = json.loads(history_file.read_text())['history']
        steps = [s for s in history if s['metadata']['step_number'] > 0]
        calls = raw['agent']['usage']['model_calls']
        if [s['metadata']['step_number'] for s in steps] != list(range(1, calls + 1)):
            raise ValueError('Call/history mapping unavailable')
        for step in steps:
            n = step['metadata']['step_number']
            response = folder / f'browser-evidence/model-response-{n:02d}.json'
            native = json.loads(json.loads(response.read_text())['message']['content'])
            if not supplied_values_match(native['action'], step['model_output']['action']):
                raise ValueError('Native response/history mismatch')
        trace_file = folder / 'browser-evidence/trace.zip'
        writes = []
        with zipfile.ZipFile(trace_file) as archive:
            for name in archive.namelist():
                if not name.endswith('.network'):
                    continue
                for line in archive.read(name).decode().splitlines():
                    snap = json.loads(line).get('snapshot', {})
                    req = snap.get('request', {})
                    if req.get('method') != 'PATCH':
                        continue
                    body = json.loads(archive.read(req['postData']['_file']))
                    response_body = json.loads(archive.read(snap['response']['content']['_file']))
                    start = datetime.fromisoformat(
                        snap['startedDateTime'].replace('Z', '+00:00')).timestamp()
                    writes.append({'body': body, 'changed': response_body['changed'],
                                   'start': start, 'response_end': start + snap['time'] / 1000,
                                   'status': snap['response']['status']})
        real = [w for w in writes if w['changed']]
        if len(real) != 1 or real[0]['body'] != raw['task']['changes']:
            raise ValueError('Expected one truthful successful edit response')
        boundary = real[0]['response_end']
        write_steps = [s['metadata']['step_number'] for s in steps
                       if s['metadata']['step_start_time'] <= real[0]['start']
                       <= s['metadata']['step_end_time']]
        later = [s['metadata']['step_number'] for s in steps
                 if s['metadata']['step_start_time'] > boundary]
        rows.append({'trial_id': spec['trial_id'], 'calls': calls,
                     'write_call': write_steps, 'calls_after_successful_response': later,
                     'post_ack_calls': len(later),
                     'noop_saves': sum(not w['changed'] for w in writes),
                     'duration_seconds': raw['duration_seconds'],
                     'agent_claimed_success': raw['agent']['agent_claimed_success'],
                     'final_message': raw['agent']['final_agent_message'],
                     'saved_feedback_calls': [s['metadata']['step_number'] for s in steps
                                             if 'Changes saved.' in s.get('state_message', '')],
                     'noop_feedback_calls': [s['metadata']['step_number'] for s in steps
                                            if 'No changes to save.' in s.get('state_message', '')],
                     'source_sha256': {str(p.relative_to(root)): hashlib.sha256(
                         p.read_bytes()).hexdigest() for p in
                         (folder / 'result.json', history_file, trace_file)}})
    return {'method': 'Conservative post-commit lower bound: model steps starting after the '
            'first successful changed=true PATCH response completed. The application commits '
            'before replying. Exact DB commit timestamps and precise invocation start times '
            'are unavailable. Native action arguments match numbered history steps, allowing '
            'SDK-added defaults. State-message feedback is observable, not proof of comprehension.',
            'trials': rows, 'post_ack_calls_total': sum(r['post_ack_calls'] for r in rows),
            'noop_saves_total': sum(r['noop_saves'] for r in rows)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    print(json.dumps(summarize(parser.parse_args().evidence), indent=2))
