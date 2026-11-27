#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# home-assistant/test/compile_test.py -- plan task 1.7, compile tests.
#
# Runs flows through an installed ThingStudio's thingstudio-compile (user guide: "Check a flow without the editor"),
# with the bundle copied into a scratch custom-nodes folder the way a user installs it, and checks each result's
# errors and warnings. Stdlib only.
#
#   THINGSTUDIO_COMPILE=/path/to/editor/dist-cli/thingstudio-compile.mjs python3 home-assistant/test/compile_test.py
#
# Exit 0 when every case passes. A KNOWN GAP case is one the bundle doesn't meet yet: it is reported, doesn't fail
# the run, and fails it once it starts passing, so the case gets promoted.

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.join(os.path.dirname(HERE), 'home-assistant')
EXAMPLE = os.path.join(BUNDLE, 'examples', 'kitchen-sink-ha.flow.json')
BOARD = 'board:kitchen-sink-c3'

WIFI = {'id': 'wifi1', 'type': 'thingstudio/config/wifi', 'properties': {'credentialName': 'test', 'security': 'password'}}
BROKER = {'id': 'broker1', 'type': 'thingstudio/config/mqtt-broker', 'properties': {'credentialName': 'test'}}


def node(nid, ntype, **props):
    return {'id': nid, 'type': ntype, 'properties': props}


def device(nid='dev'):
    return node(nid, 'ha/device', area='', prefix='homeassistant', deviceName='',
                brokerConfigId=BROKER['id'], wifiConfigId=WIFI['id'])


def flow(name, nodes, edges=()):
    layout = {n['id']: {'pos': [200 * i, 0]} for i, n in enumerate(nodes)}
    return {'formatVersion': 1, 'flowName': name, 'nodes': nodes, 'edges': [list(e) for e in edges],
            'layout': layout, 'configs': [WIFI, BROKER]}


def tick(nid='tick'):
    return node(nid, 'thingstudio/timer', intervalMs=10000)


def fn(nid, code="return msg"):
    return node(nid, 'thingstudio/function', code=code, outputCount=1, label=nid)


def button_input(nid='btn'):
    # a built-in whose output is typed string, to wire into ha select
    return node(nid, 'thingstudio/ebutton', pin=3, suppress=False, senseMode='auto', debounceMs=50,
                longPressMs=1000, doubleClickMs=400, pull='up')


def sensor(nid='temp', **kw):
    props = dict(name='Temperature', deviceClass='none', unit='', stateClass='none', icon='')
    props.update(kw)
    return node(nid, 'ha/sensor', **props)


def entity_types():
    return [
        sensor('s1'),
        node('b1', 'ha/binary_sensor', name='Door', deviceClass='none'),
        node('w1', 'ha/switch', name='Lamp', deviceClass='none'),
        node('n1', 'ha/number', name='Level', min=0, max=100, step=1, unit='', mode='slider'),
        node('l1', 'ha/select', name='Mode', options='off\non'),
        node('p1', 'ha/button', name='Go'),
    ]


def many_entities(count):
    long_name = 'A sensor with a deliberately long name to fill the discovery message'
    return [sensor('s%02d' % i, name='%s %d' % (long_name, i), unit='°C', deviceClass='temperature',
                   stateClass='measurement', icon='mdi:thermometer') for i in range(count)]


# (name, flow or path, expect) -- expect: ok (bool), errors / warnings (substrings, each must match one line),
# warning_count (exact, optional), gap (a reason: KNOWN GAP)
CASES = [
    ('the kitchen-sink example', EXAMPLE,
     {'ok': True, 'warnings': ["node haled): ha switch 'LED': input not wired",
                               "node habright): ha number 'LED brightness': input not wired"], 'warning_count': 2}),
    ('every entity type, inputs wired',
     flow('all-wired', [device(), tick(), fn('f'), button_input()] + entity_types(),
          [('tick', 0, 'f', 0), ('f', 0, 's1', 0), ('f', 0, 'b1', 0), ('f', 0, 'w1', 0), ('tick', 0, 'n1', 0),
           ('btn', 0, 'l1', 0)]),
     {'ok': True, 'warning_count': 0}),
    ('unwired inputs warn (switch, number, select)',
     flow('unwired', [device()] + [n for n in entity_types() if n['type'] in ('ha/switch', 'ha/number',
                                                                              'ha/select', 'ha/button')]),
     {'ok': True, 'warnings': ["ha switch 'Lamp': input not wired", "ha number 'Level': input not wired",
                               "ha select 'Mode': input not wired"], 'warning_count': 3}),
    ('a function node\'s value wired back into ha number and ha select',
     flow('function-feedback', [device(), tick(), fn('f')] + [n for n in entity_types()
                                                              if n['type'] in ('ha/number', 'ha/select')],
          [('tick', 0, 'f', 0), ('f', 0, 'n1', 0), ('f', 0, 'l1', 0)]),
     {'ok': True, 'warning_count': 0}),
    ('a device with no entities warns',
     flow('no-entities', [device()]),
     {'ok': True, 'warnings': ['ha device has no entities'], 'warning_count': 1}),
    ('two ha device nodes',
     flow('two-devices', [device('dev'), device('dev2'), sensor()]),
     {'ok': False, 'errors': ['only one ha device node (this one has 2)']}),
    ('a node id that can\'t go in a topic',
     flow('bad-id', [device(), sensor('temp sensor')]),
     {'ok': False, 'errors': ["node id 'temp sensor' can't be used in MQTT topics"]}),
    ('a node id over 32 characters',
     flow('long-id', [device(), sensor('t' * 33)]),
     {'ok': False, 'errors': ["can't be used in MQTT topics"]}),
    ('two nodes with the same id',
     flow('duplicate-id', [device(), sensor('temp'), sensor('temp', name='Other')]),
     {'ok': False, 'errors': ['duplicate node id temp']}),
    ('a sensor with no name',
     flow('no-name', [device(), sensor(name='  ')]),
     {'ok': False, 'errors': ['ha sensor needs a name']}),
    ('a temperature sensor in %',
     flow('bad-unit', [device(), sensor(deviceClass='temperature', unit='%')]),
     {'ok': False, 'errors': ["a temperature sensor's unit must be one of °C, °F, K"]}),
    ('a number with min not below max',
     flow('number-range', [device(), node('n1', 'ha/number', name='Level', min=5, max=5, step=1, unit='',
                                          mode='slider')]),
     {'ok': False, 'errors': ["ha number 'Level': min must be below max"]}),
    ('a number with step 0',
     flow('number-step', [device(), node('n1', 'ha/number', name='Level', min=0, max=10, step=0, unit='',
                                         mode='slider')]),
     {'ok': False, 'errors': ["ha number 'Level': step must be above 0"]}),
    ('a select with no options',
     flow('select-empty', [device(), node('l1', 'ha/select', name='Mode', options='\n \n')]),
     {'ok': False, 'errors': ["ha select 'Mode' needs at least one option"]}),
    ('a select listing an option twice',
     flow('select-twice', [device(), node('l1', 'ha/select', name='Mode', options='on\noff\non')]),
     {'ok': False, 'errors': ["ha select 'Mode' lists 'on' twice"]}),
] + [
    ('%s without an ha device' % e['type'], flow('no-device-' + e['id'], [e]),
     {'ok': False, 'errors': ['%s needs an ha device node in the flow' % e['type'][3:].replace('_', ' ')]})
    for e in entity_types()
] + [
    ('a discovery message over 4 KB (SPEC §8)',
     flow('too-big', [device()] + many_entities(40)),
     {'ok': False, 'errors': ['4 KB'],
      'gap': 'SPEC §8 says the compile errors above 4 KB; no hook checks it yet (needs the shared generator, 1.6)'}),
]


def compile_flow(cli, custom_nodes, path):
    cmd = ['node', cli, '--json', '--custom-nodes', custom_nodes, '--board', BOARD, path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    try:
        results = json.loads(proc.stdout)
    except ValueError:
        raise RuntimeError('thingstudio-compile gave no JSON (exit %d): %s' % (proc.returncode,
                                                                            (proc.stderr or proc.stdout)[:500]))
    if len(results) != 1:
        raise RuntimeError('expected one result, got %d' % len(results))
    return results[0]


def _lines(items):
    # --json gives warnings as strings and errors as {"message", "node"}
    return [i['message'] if isinstance(i, dict) else i for i in items]


def check(result, expect):
    problems = []
    result = dict(result, errors=_lines(result['errors']), warnings=_lines(result['warnings']))
    if result['ok'] != expect['ok']:
        problems.append('ok is %s, expected %s' % (result['ok'], expect['ok']))
    for key in ('errors', 'warnings'):
        for want in expect.get(key, ()):
            if not any(want in line for line in result[key]):
                problems.append('no %s line contains %r' % (key[:-1], want))
    if 'warning_count' in expect and len(result['warnings']) != expect['warning_count']:
        problems.append('%d warnings, expected %d' % (len(result['warnings']), expect['warning_count']))
    if problems:
        problems.append('errors: %r' % result['errors'])
        problems.append('warnings: %r' % result['warnings'])
    return problems


def main():
    cli = os.environ.get('THINGSTUDIO_COMPILE')
    if not cli or not os.path.isfile(cli):
        print('compile_test: set THINGSTUDIO_COMPILE to thingstudio-compile.mjs from an installed ThingStudio '
              '(got %r) -- see the user guide, "Check a flow without the editor"' % cli)
        return 2
    scratch = tempfile.mkdtemp(prefix='ha-compile-test-')
    try:
        custom_nodes = os.path.join(scratch, 'custom-nodes')
        shutil.copytree(BUNDLE, os.path.join(custom_nodes, 'home-assistant'))
        failed = gaps = 0
        for name, spec, expect in CASES:
            if isinstance(spec, dict):
                path = os.path.join(scratch, spec['flowName'] + '.flow.json')
                with open(path, 'w') as f:
                    json.dump(spec, f, indent=1)
            else:
                path = spec
            problems = check(compile_flow(cli, custom_nodes, path), expect)
            if expect.get('gap'):
                if problems:
                    gaps += 1
                    print('KNOWN GAP  %s -- %s' % (name, expect['gap']))
                else:
                    failed += 1
                    print('FAIL  %s -- passes now: drop its gap note' % name)
            elif problems:
                failed += 1
                print('FAIL  %s' % name)
                for p in problems:
                    print('      ' + p)
            else:
                print('ok    %s' % name)
        print('%d cases, %d failed, %d known gaps' % (len(CASES), failed, gaps))
        return 1 if failed else 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
