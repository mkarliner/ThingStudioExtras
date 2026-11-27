#!/usr/bin/env python3
# wake-on-lan/test/compile_test.py -- compile tests.
#
# Runs flows through an installed ThingStudio's thingstudio-compile (user guide: "Check a flow
# without the editor"), with the bundle loaded the way a user installs it, and checks each
# result's errors and warnings. Stdlib only.
#
#   THINGSTUDIO_COMPILE=/path/to/editor/dist-cli/thingstudio-compile.mjs python3 wake-on-lan/test/compile_test.py
#
# Exit 0 when every case passes.

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SET_DIR = os.path.dirname(HERE)
CLI = os.environ.get('THINGSTUDIO_COMPILE')
if not CLI:
    print('set THINGSTUDIO_COMPILE to editor/dist-cli/thingstudio-compile.mjs')
    sys.exit(2)

WIFI = {'id': 'wifi1', 'type': 'thingstudio/config/wifi',
        'properties': {'credentialName': 'test', 'security': 'password'}}


def flow(name, nodes, edges, configs=(WIFI,)):
    layout = {n['id']: {'pos': [200 * i, 0]} for i, n in enumerate(nodes)}
    return {'formatVersion': 1, 'flowName': name, 'nodes': nodes, 'edges': [list(e) for e in edges],
            'layout': layout, 'configs': list(configs)}


def wake(nid='wake', wifi='wifi1', port=9, repeats=1):
    return {'id': nid, 'type': 'wol/wol', 'properties': {'port': port, 'repeats': repeats, 'wifi': wifi}}


def fn(nid='payload', code="msg['payload'] = {'mac': 'AA:BB:CC:DD:EE:FF'}\nreturn msg"):
    return {'id': nid, 'type': 'thingstudio/function', 'properties': {'code': code, 'outputCount': 1}}


def tick(nid='tick'):
    return {'id': nid, 'type': 'thingstudio/timer', 'properties': {'intervalMs': 10000}}


def run(name, flow_json, board):
    path = os.path.join(HERE, '.%s.flow.json' % name)
    with open(path, 'w') as f:
        json.dump(flow_json, f, indent=2)
    try:
        r = subprocess.run(['node', CLI, '--board', board, '--custom-nodes', SET_DIR, path],
                           capture_output=True, text=True)
        return r
    finally:
        os.remove(path)


def check(name, board, flow_json, want_ok, want_error=None, want_no_error=None):
    r = run(name, flow_json, board)
    out = r.stdout + r.stderr
    ok = (r.returncode == 0) == want_ok
    if ok and want_error and want_error not in out:
        ok = False
        print('FAIL %s: wanted error %r in output:\n%s' % (name, want_error, out))
    if ok and want_no_error and want_no_error in out:
        ok = False
        print('FAIL %s: did not want %r in output:\n%s' % (name, want_no_error, out))
    if not ok:
        print('FAIL %s (rc=%d, wanted ok=%s):\n%s' % (name, r.returncode, want_ok, out))
    return ok


C3 = 'board:kitchen-sink-c3'
PICO = 'board:pico'

base = flow('wol', [tick(), fn(), wake()], [('tick', 0, 'payload', 0), ('payload', 0, 'wake', 0)])

all_ok = True
# the example shape: a timer, a function that builds the payload dict, and the node.
all_ok &= check('ok', C3, base, True, want_no_error='error:')
# no WiFi config in the flow: the hook's named compile error
nowifi = json.loads(json.dumps(base))
nowifi['configs'] = []
nowifi['nodes'][2]['properties']['wifi'] = ''
all_ok &= check('no-wifi', C3, nowifi, False,
                want_error='needs the flow\'s WiFi -- set "WiFi" in its properties')
# the node refuses a board without the wifi capability, naming the node and the capability
all_ok &= check('no-capability', PICO, base, False,
                want_error='needs "wifi", which Raspberry Pi Pico (RP2040) doesn\'t provide')

print('wake-on-lan compile: %d cases, %s' % (3, 'all pass' if all_ok else 'FAILURES'))
sys.exit(0 if all_ok else 1)
