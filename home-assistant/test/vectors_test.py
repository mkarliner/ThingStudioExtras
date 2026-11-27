# SPDX-License-Identifier: Apache-2.0
# home-assistant/test/vectors_test.py -- plan task 1.7: ts_ha against the SPEC's vectors (SPEC §9).
#
# Runs under the MicroPython unix port (and CPython). Tests ts_ha's pure functions only: build_discovery,
# state_payload, command_value, and that ha device's hook sizes discovery exactly. The MQTT side is mqtt_test.py.
#
#   MICROPYPATH=home-assistant/test/doubles:home-assistant/home-assistant/lib:<micropython>/extmod \
#       micropython home-assistant/test/vectors_test.py home-assistant/docs/vectors
#
# The unix port's floats are double precision; the ESP32 boards' are single. Float payloads are checked on the board
# in the hardware pass (plan 1.9).

import json
import sys

import ts_ha


def load(folder, name):
    with open(folder + '/' + name) as f:
        return json.load(f)


def show(v):
    return 'IGNORED' if v is ts_ha.IGNORED else repr(v)


def run(folder):
    failures = []
    total = 0

    for case in load(folder, 'discovery.json')['cases']:
        total += 1
        topic, payload, after = ts_ha.build_discovery(case['chipId'], case['prefix'], case['device'],
                                                      case['components'], case.get('record'))
        for what, got, want in (('topic', topic, case['topic']), ('payload', payload, case['payload']),
                                ('record after', after, case['recordAfter'])):
            if got != want:
                failures.append('discovery %r: %s\n    got  %r\n    want %r' % (case['name'], what, got, want))

    values = load(folder, 'values.json')
    for case in values['state']:
        total += 1
        try:
            got = ts_ha.state_payload(case['p'], case['value'], case.get('options'))
        except ValueError:
            got = 'ERROR'
        if got != case['payload']:
            failures.append('state %s %r: got %r, want %r' % (case['p'], case['value'], got, case['payload']))

    for case in values['command']:
        total += 1
        component = {'p': case['p']}
        for key in ('min', 'max', 'step'):
            if key in case:
                component[key] = case[key]
        if 'options' in case:
            component['ops'] = case['options']
        got = ts_ha.command_value(case['p'], case['payload'], component)
        want = ts_ha.IGNORED if case['value'] == 'IGNORED' else case['value']
        same = got is want if want is ts_ha.IGNORED else (got is not ts_ha.IGNORED and got == want
                                                          and type(got) is type(want))
        if not same:
            failures.append('command %s %r: got %s, want %s' % (case['p'], case['payload'], show(got), show(want)))
        if case['payload'] is not None and isinstance(case['payload'], str):
            total += 1
            again = ts_ha.command_value(case['p'], case['payload'].encode(), component)
            if (again is ts_ha.IGNORED) != (got is ts_ha.IGNORED) or (got is not ts_ha.IGNORED and again != got):
                failures.append('command %s %r as bytes: got %s, as text %s' % (case['p'], case['payload'],
                                                                                 show(again), show(got)))

    # ha device's compile hook sizes the discovery message (SPEC §8) without json; its count must be the board's
    # json.dumps byte count exactly. The hook file has no imports, so it runs here as it is.
    hook = {}
    with open(folder + '/../../home-assistant/ha_device.compile.py') as f:
        exec(f.read(), hook)
    sized = [case['payload'] for case in load(folder, 'discovery.json')['cases']]
    sized.append({'name': 'Température « salon » \u2014 \U0001F321', 'esc': 'a"b\\c\n\t\x01', 'n': [0, -3, 2.5, 1e-07],
                  'flags': [True, False, None], 'nested': {'empty': {}, 'list': []}})
    for i, payload in enumerate(sized):
        total += 1
        if sys.implementation.name == 'micropython':
            want = len(ts_ha._dumps(payload).encode())
        else:  # CPython escapes non-ASCII by default; the board's MicroPython json doesn't
            want = len(json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode())
        got = hook['json_size'](payload)
        if got != want:
            failures.append('json_size case %d: hook counts %d bytes, the board\'s json.dumps writes %d' % (i, got, want))

    for line in failures:
        print('FAIL  ' + line)
    print('%s: %d checks, %d failed' % (sys.implementation.name, total, len(failures)))
    return 1 if failures else 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: vectors_test.py <vectors folder>')
        sys.exit(2)
    sys.exit(run(sys.argv[1]))
