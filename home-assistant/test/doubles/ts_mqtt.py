# SPDX-License-Identifier: Apache-2.0
# home-assistant/test/doubles/ts_mqtt.py -- a test double for ThingStudio's `ts_mqtt`, written from the user guide
# only (Writing a custom node: "The flow's MQTT client: ts_mqtt", ThingStudio a57d686b). It keeps what the guide
# says: one client per broker and port, node ids on every call but set_will and on_connect, bytes payloads, QoS 0 or
# 1, per-node subscriptions and queues of 20, re-subscribe then on_connect after a reconnect, set_will only before
# connecting. It is strict where the guide is: a str payload or QoS 2 is an error, so a misuse fails the test.
#
# Test-only additions: `deliver()` (a message from the broker), `reconnect()`, `published`, `statuses`, `reset()`.
# Unlike the real client, the double doesn't time out or retry; `fail_connect` makes the first connect raise as the
# guide describes.

import asyncio

_clients = {}  # (broker, port) -> Client


def _matches(pattern, topic):
    p, t = pattern.split('/'), topic.split('/')
    for i, part in enumerate(p):
        if part == '#':
            return True
        if i >= len(t) or (part != '+' and part != t[i]):
            return False
    return len(p) == len(t)


def _check_qos(qos):
    if qos not in (0, 1):
        raise ValueError('ts_mqtt: QoS is 0 or 1, not %r' % (qos,))


class Client:
    def __init__(self, settings):
        self.settings = settings
        self.will = None
        self.callbacks = []
        self.connected = False
        self.fail_connect = False
        self.subs = {}     # node id -> {topic: qos}
        self.queues = {}   # node id -> [(topic, payload, retained)]
        self.events = {}   # node id -> asyncio.Event
        self.published = []  # (node id, topic, payload, retain, qos)
        self.statuses = []   # (node id, status), as the client would report them
        self._pending_reconnect = False

    def _report(self, node_id, status):
        if not self.statuses or self.statuses[-1] != (node_id, status):
            self.statuses.append((node_id, status))

    async def _run_callbacks(self):
        for cb in list(self.callbacks):
            r = cb()
            if r is not None and hasattr(r, 'send'):
                await r

    async def ensure_connected(self, node_id):
        if not self.connected:
            if self.fail_connect:
                self._report(node_id, 'error')
                raise OSError('mqtt connect to %s:%s failed after 3 attempts (double)' % self.settings[:2])
            self.connected = True
            self._report(node_id, 'connected')
            await self._run_callbacks()
        elif self._pending_reconnect:
            self._pending_reconnect = False
            self._report(node_id, 'connected')
            await self._run_callbacks()  # the client has already subscribed every node's topics again

    async def publish(self, node_id, topic, payload, retain=False, qos=0):
        _check_qos(qos)
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError('ts_mqtt double: publish payload must be bytes, got %r' % (payload,))
        await self.ensure_connected(node_id)
        self.published.append((node_id, topic, bytes(payload), retain, qos))

    async def subscribe(self, node_id, topic, qos=0):
        _check_qos(qos)
        if not self.connected:
            raise AssertionError('ts_mqtt double: subscribe before ensure_connected would wait forever')
        self.subs.setdefault(node_id, {})[topic] = qos
        self.queues.setdefault(node_id, [])
        self.events.setdefault(node_id, asyncio.Event())

    async def unsubscribe(self, node_id, topic):
        self.subs.get(node_id, {}).pop(topic, None)

    async def wait_message(self, node_id):
        ev = self.events.setdefault(node_id, asyncio.Event())
        q = self.queues.setdefault(node_id, [])
        while True:
            await self.ensure_connected(node_id)  # the guide: wait_message notices a reconnect (about once a second)
            if q:
                return q.pop(0)
            ev.clear()
            await ev.wait()

    def set_will(self, topic, msg, retain=False, qos=0):
        _check_qos(qos)
        will = (topic, msg, retain, qos)
        if self.connected:
            raise ValueError('ts_mqtt: set_will after the client connected')
        if self.will is not None and self.will != will:
            raise ValueError('ts_mqtt: a different will on the same broker')
        self.will = will

    def on_connect(self, callback):
        self.callbacks.append(callback)

    # -- test-only ---------------------------------------------------------------------------------------------

    def deliver(self, topic, payload, retained=False):
        """A message from the broker: queued for every node with a matching subscription, at most 20 each."""
        for node_id, topics in self.subs.items():
            if any(_matches(t, topic) for t in topics):
                q = self.queues[node_id]
                q.append((topic.encode(), bytes(payload), retained))
                if len(q) > 20:
                    q.pop(0)
                self.events[node_id].set()

    def reconnect(self):
        """The connection dropped and came back: noticed at the next ensure_connected (wait_message, publish)."""
        self._pending_reconnect = True
        for ev in self.events.values():
            ev.set()


def ensure_client(broker, port, ssid, wifi_password, security='password', username='', password=''):
    settings = (broker, port, ssid, wifi_password, security, username, password)
    c = _clients.get((broker, port))
    if c is None:
        c = _clients[(broker, port)] = Client(settings)
    elif c.settings != settings:
        raise ValueError('ts_mqtt: different settings for %s:%s' % (broker, port))
    return c


def reset():
    """A redeploy stops the client."""
    _clients.clear()
