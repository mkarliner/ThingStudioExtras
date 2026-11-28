# SPDX-License-Identifier: Apache-2.0
# home-assistant/test/mqtt_test.py -- plan task 1.7, the MQTT side: ts_ha and ha device against doubles of ts_wifi and
# ts_mqtt written from the user guide (ThingStudio a57d686b, which answered core request #24).
#
# Runs under the MicroPython unix port (and CPython):
#
#   MICROPYPATH=home-assistant/test/doubles:home-assistant/home-assistant/lib:<micropython>/extmod \
#       micropython home-assistant/test/mqtt_test.py home-assistant/home-assistant
#
# What it checks is what the SPEC asks of the wire (§3-§7) and what the guide asks of a node using the client: the
# will before connecting, bytes payloads, QoS 0/1, subscribing after ensure_connected, node ids on every call.

import asyncio
import json
import sys

import runtime
import ts_mqtt
import ts_wifi
import ts_ha

CHIP = 'c0ffee'
BASE = 'thingstudio/' + CHIP
failures = []
total = [0]


def check(name, got, want):
    total[0] += 1
    if got != want:
        failures.append('%s\n    got  %r\n    want %r' % (name, got, want))


def fresh():
    """A redeploy: run the cleanups, forget the doubles' state."""
    for _name, fn in runtime.cleanups:
        fn()
    del runtime.cleanups[:]
    ts_mqtt.reset()
    ts_wifi.reset()
    runtime.settings.reset()
    ts_ha.RECORD_FILE = '/tmp/ts_ha_mqtt_test_record.json'
    try:
        import os
        os.remove(ts_ha.RECORD_FILE)
    except OSError:
        pass


def client():
    return ts_mqtt.ensure_client('broker.lan', 1883, 'home', 'pw', 'password', '', '')


def flow():
    """ha device plus a sensor, a switch and a button, set up as at flow start (entities may come first)."""
    ts_ha.register('temp', {'p': 'sensor', 'name': 'Temperature'})
    ts_ha.register('lamp', {'p': 'switch', 'name': 'Lamp'})
    ts_ha.register('bell', {'p': 'button', 'name': 'Bell'})
    c = client()
    ts_ha.configure_device(c, 'dev', 'kitchen', model='ESP32-C3', area='Kitchen', chip=CHIP)
    return c

def by_topic(c):
    return [(p[1], p[2], p[3], p[4]) for p in c.published]


async def first_connect():
    fresh()
    c = flow()
    check('will is set at setup, before connecting', c.will, (BASE + '/availability', b'offline', True, 1))
    check('nothing published before connecting', c.published, [])
    await c.ensure_connected('dev')
    topics = [p[0] for p in by_topic(c)]
    topics = topics[:2] + sorted(topics[2:])
    check('first connect: online, discovery, then None for unreported states (not the button)', topics,
          [BASE + '/availability', 'homeassistant/device/ts_' + CHIP + '/config',
           BASE + '/lamp/state', BASE + '/temp/state'])
    check('online is retained QoS 1', by_topic(c)[0], (BASE + '/availability', b'online', True, 1))
    disc = by_topic(c)[1]
    check('discovery is retained QoS 1', disc[2:], (True, 1))
    payload = json.loads(disc[1])
    check('discovery has no dev.sw while the runtime version is undocumented (#25)', 'sw' in payload['dev'], False)
    check('discovery lists the three entities', sorted(payload['cmps']), ['bell', 'lamp', 'temp'])
    check('None states are retained QoS 0', by_topic(c)[2][1:], (b'None', True, 0))
    check('device-level publishes are under the ha device node id', set(p[0] for p in c.published), {'dev'})



async def state_before_first_connect():
    """A startup node reports a state as the flow starts, before WiFi and the broker are up. The state is kept, goes
    out once connected, and the first connect sends no None over it (SPEC v1.1, §3)."""
    fresh()
    c = flow()
    await ts_ha.publish_state('lamp', False)
    topics = [p[0] for p in by_topic(c)]
    check('a state reported before the first connect: online, discovery, None only for the unreported sensor, '
          'then the state', topics,
          [BASE + '/availability', 'homeassistant/device/ts_' + CHIP + '/config', BASE + '/temp/state',
           BASE + '/lamp/state'])
    check('the early state is the value, not None', by_topic(c)[-1], (BASE + '/lamp/state', b'OFF', True, 0))

async def states_and_commands():
    fresh()
    c = flow()
    await c.ensure_connected('dev')
    del c.published[:]
    await ts_ha.publish_state('temp', 21.5)
    check('a state is published retained QoS 0, as bytes, under the entity\'s node id', c.published,
          [('temp', BASE + '/temp/state', b'21.5', True, 0)])

    del c.published[:]
    task = asyncio.create_task(ts_ha.command('lamp', True))
    await asyncio.sleep(0)
    check('a command entity subscribes to its /set topic, QoS 1, under its own node id', c.subs.get('lamp'),
          {BASE + '/lamp/set': 1})
    c.deliver(BASE + '/lamp/set', b'on')   # not valid for a switch: ignored
    c.deliver(BASE + '/lamp/set', b'ON')
    check('the first valid command is the value', await task, True)
    check('with echo, the accepted command goes back as the state', c.published,
          [('lamp', BASE + '/lamp/state', b'ON', True, 0)])

    c.deliver(BASE + '/temp/state', b'99')
    check('a node gets only its own subscriptions\' messages', c.queues.get('lamp'), [])

    del c.published[:]
    task = asyncio.create_task(ts_ha.command('bell', True))
    await asyncio.sleep(0)
    c.deliver(BASE + '/bell/set', b'PRESS')
    check('a button press is True', await task, True)
    check('a button has no state to echo', c.published, [])


async def on_start_and_restore():
    """SPEC v1.2 §3: on start. A two-faced node's start value goes out from its own start() (with echo it is also
    published as the state); a binary sensor's start value goes out on the first connect; restore reads the last
    published state back from the settings store."""
    fresh()
    # a binary sensor starting on: the first connect publishes its start value, not None
    ts_ha.register('temp', {'p': 'sensor', 'name': 'Temperature'})
    ts_ha.register('door', {'p': 'binary_sensor', 'name': 'Door'}, True)
    c = client()
    ts_ha.configure_device(c, 'dev', 'kitchen', model='ESP32-C3', area='Kitchen', chip=CHIP)
    await c.ensure_connected('dev')
    check('the door starts on, under its own node id',
          [p for p in c.published if p[1] == BASE + '/door/state'],
          [('door', BASE + '/door/state', b'ON', True, 0)])
    check('the un-started sensor still gets its None',
          [p for p in c.published if p[1] == BASE + '/temp/state'],
          [('dev', BASE + '/temp/state', b'None', True, 0)])
    check('no on start: nothing to start from', ts_ha.start_value('temp'), None)

    fresh()
    # restore: nothing stored yet behaves as unknown; the last published state is kept under the node id
    ts_ha.register('lamp', {'p': 'switch', 'name': 'Lamp'}, 'restore')
    c = client()
    ts_ha.configure_device(c, 'dev', 'kitchen', chip=CHIP)
    check('restore with nothing stored yet starts unknown', ts_ha.start_value('lamp'), None)
    runtime.settings.set('lamp', True)  # the previous flow's last published state
    check('restore reads the last published state back', ts_ha.start_value('lamp'), True)
    value = await ts_ha.start('lamp', True)
    check('the start value is emitted as if HA had sent it', value, True)
    check('with echo, the start value is published as the state',
          [p for p in c.published if p[1] == BASE + '/lamp/state'],
          [('lamp', BASE + '/lamp/state', b'ON', True, 0)])
    await c.ensure_connected('dev')
    check('the first connect sends no None over a reported start',
          [p[1] for p in c.published if p[1].endswith('/state')],
          [BASE + '/lamp/state'])
    check('publish_state keeps the value for restore',
          (runtime.settings.get('lamp'), ts_ha.start_value('lamp')), (True, True))

    fresh()
    # wired (no echo): the start value is emitted, not published; the flow will report the state
    ts_ha.register('lamp', {'p': 'switch', 'name': 'Lamp'}, False)
    c = client()
    ts_ha.configure_device(c, 'dev', 'kitchen', chip=CHIP)
    value = await ts_ha.start('lamp', False)
    check('without echo, the start value is emitted only', (value, c.published), (False, []))
    await c.ensure_connected('dev')
    check('the first connect still sends None: the flow reports the state',
          [p[1] for p in c.published if p[1].endswith('/state')], [BASE + '/lamp/state'])
    check('on start off resolves to the flow value False', ts_ha.start_value('lamp'), False)


async def settings_writes():
    """SPEC v1.2 (restore): only an entity whose on start is restore keeps its state, and only when the value
    changes -- sensors and everything else never write settings, however often they publish."""
    fresh()
    ts_ha.register('temp', {'p': 'sensor', 'name': 'Temperature'})
    ts_ha.register('door', {'p': 'binary_sensor', 'name': 'Door'})
    ts_ha.register('lamp', {'p': 'switch', 'name': 'Lamp'}, 'restore')
    c = client()
    ts_ha.configure_device(c, 'dev', 'kitchen', chip=CHIP)
    for value in (21, 21.5, 21, 'hot', 21):
        await ts_ha.publish_state('temp', value)
        await ts_ha.publish_state('door', True)
    check('a sensor publishing repeatedly causes no settings write',
          (runtime.settings.keys(), runtime.settings.writes), ([], 0))
    baseline = runtime.settings.writes
    await ts_ha.publish_state('lamp', True)
    check('a restore entity writes on its first state', runtime.settings.writes, baseline + 1)
    await ts_ha.publish_state('lamp', True)
    await ts_ha.publish_state('lamp', True)
    check('re-publishing the same value writes nothing', runtime.settings.writes, baseline + 1)
    await ts_ha.publish_state('lamp', False)
    check('a changed value writes again',
          (runtime.settings.writes, runtime.settings.get('lamp')), (baseline + 2, False))

    fresh()
    ts_ha.register('lamp', {'p': 'switch', 'name': 'Lamp'}, 'restore')
    c = client()
    ts_ha.configure_device(c, 'dev', 'kitchen', chip=CHIP)
    runtime.settings.set('lamp', True)  # the previous flow's stored state
    writes = runtime.settings.writes
    value = await ts_ha.start('lamp', True)
    check('restore starts from the stored value', value, True)
    check('publishing the start value back writes nothing new', runtime.settings.writes, writes)


async def ha_restart_and_reconnect():
    fresh()
    c = flow()
    task = asyncio.create_task(ts_ha.ha_status('dev'))
    await asyncio.sleep(0)
    check('ha device connects, then subscribes to <prefix>/status, QoS 0', c.subs.get('dev'),
          {'homeassistant/status': 0})
    c.deliver('homeassistant/status', b'online')
    check('HA\'s birth message is returned', await task, 'online')
    check('discovery goes out again later (SPEC §6)', ts_ha._device.republish is not None, True)
    ts_ha._device.stop()

    del c.published[:]
    c.reconnect()
    task = asyncio.create_task(ts_ha.ha_status('dev'))
    for _ in range(5):
        await asyncio.sleep(0)
    topics = [p[1] for p in c.published]
    check('after a reconnect: online and discovery again, no None states this time', topics,
          [BASE + '/availability', 'homeassistant/device/ts_' + CHIP + '/config'])
    c.deliver('homeassistant/status', b'offline')
    check('HA going offline is returned', await task, 'offline')


async def redeploy():
    fresh()
    flow()
    check('ts_ha registers its cleanup', [n for n, _f in runtime.cleanups][:1], ['ts_ha'])
    fresh()
    c = flow()  # would raise ValueError if the old device or components survived
    check('after a redeploy a new flow sets up cleanly', ts_ha._device.client is c, True)


class _Network:
    @staticmethod
    def hostname():
        return 'c3-kitchen'


async def ha_device_node(folder):
    """ha_device.node.py's setup, with the properties its compile hook returns."""
    fresh()
    sys.modules['network'] = _Network
    real_chip_id = ts_ha.chip_id
    ts_ha.chip_id = lambda: CHIP
    try:
        properties = {'ssid': 'home', 'wifiPassword': 'pw', 'security': 'password', 'deferToMqtt': True,
                      'broker': 'broker.lan', 'port': 1883, 'username': '', 'brokerPassword': '',
                      'nodeId': 'dev', 'deviceName': '', 'area': '', 'prefix': 'homeassistant',
                      'board': {'boardName': 'ESP32-C3 SuperMini'}}
        with open(folder + '/ha_device.node.py') as f:
            code = f.read()
        g = {'properties': properties, 'runtime': runtime, '__name__': 'ha_device'}
        exec(code, g)
        check('ha device joins WiFi with the four documented values', ts_wifi.calls,
              [('home', 'pw', 'password', True)])
        check('ha device gets the flow\'s client for its broker and port', g['_client'] is client(), True)
        check('a second node with the same WiFi values gets the same station',
              ts_wifi.ensure_station('home', 'pw', 'password', True) is not None, True)
        try:
            ts_wifi.ensure_station('home', 'pw', 'password', False)
            check('different WiFi values are refused', 'no error', 'ValueError')
        except ValueError:
            check('different WiFi values are refused', 'ValueError', 'ValueError')
        await g['_client'].ensure_connected('dev')
        payload = json.loads(g['_client'].published[1][2])
        check('ha device names the device by hostname when unnamed, model from the target field',
              (payload['dev']['name'], payload['dev'].get('mdl'), 'sw' in payload['dev']),
              ('c3-kitchen', 'ESP32-C3 SuperMini', False))
    finally:
        ts_ha.chip_id = real_chip_id
        del sys.modules['network']


async def entity_nodes_pass_start(folder):
    """SPEC v1.2: every entity node's register() hands the hook's on-start value to ts_ha. The kitchen-sink
    board pass caught this: the binary sensor's node file didn't, and its start value (which only goes out on
    the first connect, read back from what register stored) came up unknown."""
    real_chip_id = ts_ha.chip_id
    ts_ha.chip_id = lambda: CHIP
    cases = (
        ('b', 'ha_binary_sensor.node.py', False, {'p': 'binary_sensor', 'name': 'Button'}),
        ('w', 'ha_switch.node.py', True, {'p': 'switch', 'name': 'LED'}),
        ('n', 'ha_number.node.py', 32, {'p': 'number', 'name': 'Brightness', 'min': 0, 'max': 255, 'step': 1,
                                       'mode': 'slider'}),
        ('s', 'ha_select.node.py', 'on', {'p': 'select', 'name': 'Mode', 'ops': ['off', 'on']}),
        ('p', 'ha_button.node.py', None, {'p': 'button', 'name': 'Hello'}),
        ('t', 'ha_sensor.node.py', None, {'p': 'sensor', 'name': 'Knob'}),
    )
    try:
        for nid, fname, start, comp in cases:
            fresh()
            c = client()
            ts_ha.configure_device(c, 'dev', 'kitchen', chip=CHIP)
            with open(folder + '/' + fname) as f:
                code = f.read()
            g = {'properties': {'nodeId': nid, 'component': comp, 'start': start, 'echo': False, 'name': 'X'},
                 'runtime': runtime, '__name__': fname}
            exec(code, g)
            check('%s passes its on-start value to ts_ha' % fname, ts_ha.start_value(nid), start)
    finally:
        ts_ha.chip_id = real_chip_id


async def main(folder):
    await first_connect()
    await state_before_first_connect()
    await states_and_commands()
    await on_start_and_restore()
    await entity_nodes_pass_start(folder)
    await settings_writes()
    await ha_restart_and_reconnect()
    await redeploy()
    await ha_device_node(folder)
    fresh()


asyncio.run(main(sys.argv[1]))
for f in failures:
    print('FAIL ' + f)
print('mqtt: %d checks, %d failed' % (total[0], len(failures)))
sys.exit(1 if failures else 0)
