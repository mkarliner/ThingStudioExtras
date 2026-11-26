# SPDX-License-Identifier: Apache-2.0
# home-assistant/home-assistant/lib/ts_ha.py
#
# The board side of home-assistant/docs/working-notes/SPEC.md (v1): Home Assistant MQTT discovery for ThingStudio's
# ha_* nodes. One module, so its state is shared by every HA node in the flow (plan task 1.3).
#
#   ha_device:  configure_device(...) at setup; await ha_status(node_id) in its wait() for HA's online/offline
#   entities:   register(node_id, component) at setup (the component dict comes from the node's compile hook);
#               await publish_state(node_id, value); await command(node_id, echo) for HA's commands
#
# Entity nodes may be set up before ha_device (graph order), so register() works without a device. The will goes on
# the shared ts_mqtt client in configure_device(), before anything connects (all node setup runs at flow start).
# On every connect (ts_mqtt's on_connect): `online`, then the discovery message, with a {"p": ...} stub for each
# component the board announced last time and no longer has (SPEC §7, the record in ha_entities.json). On the
# first connect of a flow, `None` for every state the flow hasn't reported yet, so HA shows unknown rather than the
# previous flow's value (SPEC v1.1, §3/§5).
#
# build_discovery(), state_payload() and command_value() are pure, and are what the SPEC's vectors test.

import json
import runtime

try:
    import asyncio
except ImportError:  # pragma: no cover -- the board's runtime always has it
    asyncio = runtime.asyncio

BUNDLE_VERSION = "0.1.0"
RECORD_FILE = "ha_entities.json"
COMMANDABLE = ("switch", "number", "select", "button")
IGNORED = object()  # command_value(): the command is not valid for this entity

_components = {}  # node id -> component dict, as the hook built it (without ids or topics)
_device = None


# -- pure: SPEC §3 and §4 ------------------------------------------------------------------------------------------

def _number_text(value):
    if isinstance(value, dict):
        raise ValueError("got a dict %r -- an HA entity shows one value: pick a field first (a function or change "
                         "node, e.g. msg['payload'] = msg['payload']['percent'])" % (value,))
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("not a number: %r" % (value,))
    if isinstance(value, int):
        return str(value)
    text = repr(value)
    if ("e" in text or "E" in text) and 1e-6 <= abs(value) < 1e15:
        text = ("%.12f" % value).rstrip("0").rstrip(".")
    return text


def state_payload(platform, value, options=None):
    """The state text for a flow value, or None for "publish nothing". Raises ValueError for a value this entity
    type can't show (a node error)."""
    if value is None:
        return None
    if platform == "sensor":
        if isinstance(value, bool):
            raise ValueError("a sensor shows numbers or text -- use ha binary sensor for true/false")
        if isinstance(value, str):
            return value
        return _number_text(value)
    if platform in ("binary_sensor", "switch"):
        return "ON" if value else "OFF"
    if platform == "number":
        return _number_text(value)
    if platform == "select":
        if value not in (options or ()):
            raise ValueError("%r is not one of the options %r" % (value, list(options or ())))
        return value
    raise ValueError("%s has no state" % platform)


def command_value(platform, payload, component=None):
    """The flow value for a command payload from HA, or IGNORED."""
    component = component or {}
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode()
    if platform == "switch":
        return True if payload == "ON" else False if payload == "OFF" else IGNORED
    if platform == "button":
        return True if payload == "PRESS" else IGNORED
    if platform == "select":
        return payload if payload in component.get("ops", ()) else IGNORED
    if platform == "number":
        try:
            value = float(payload)
        except ValueError:
            return IGNORED
        lo, hi = component.get("min"), component.get("max")
        if (lo is not None and value < lo) or (hi is not None and value > hi):
            return IGNORED
        step = component.get("step", 1)
        if step == int(step) and value == int(value):
            return int(value)
        return value
    return IGNORED


def build_discovery(chip_id, prefix, device, components, record=None):
    """(topic, payload dict, record after) for SPEC §4/§7. `device` has name, model, runtime, area, bundle."""
    device_id = "ts_" + chip_id
    base = "thingstudio/" + chip_id
    dev = {"ids": [device_id], "name": device["name"], "mf": "ThingStudio"}
    if device.get("model"):
        dev["mdl"] = device["model"]
    if device.get("runtime"):
        dev["sw"] = device["runtime"]
    if device.get("area"):
        dev["sa"] = device["area"]
    cmps = {}
    for node_id, comp in components.items():
        out = dict(comp)
        out["uniq_id"] = device_id + "_" + node_id
        if comp["p"] != "button":
            out["stat_t"] = base + "/" + node_id + "/state"
        if comp["p"] in COMMANDABLE:
            out["cmd_t"] = base + "/" + node_id + "/set"
        cmps[node_id] = out
    if record and record.get("device") == device_id:
        for node_id, platform in record.get("cmps", {}).items():
            if node_id not in cmps:
                cmps[node_id] = {"p": platform}
    payload = {
        "dev": dev,
        "o": {"name": "ThingStudio", "sw": device.get("bundle") or BUNDLE_VERSION},
        "avty_t": base + "/availability",
        "cmps": cmps,
    }
    after = {"device": device_id, "cmps": {k: v["p"] for k, v in components.items()}}
    return "%s/device/%s/config" % (prefix, device_id), payload, after


def _dumps(obj):
    try:
        return json.dumps(obj, separators=(",", ":"))
    except TypeError:  # an older MicroPython json without separators
        return json.dumps(obj)


# -- the record (SPEC §7) ------------------------------------------------------------------------------------------

def _read_record():
    try:
        with open(RECORD_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write_record(record):
    try:
        with open(RECORD_FILE, "w") as f:
            f.write(_dumps(record))
    except OSError as e:
        print("ts_ha: couldn't save %s (%r) -- a removed entity may stay in HA" % (RECORD_FILE, e))


def _memory():
    """Free memory for the discovery console line (plan 1.9: C3 heap before and after discovery)."""
    text = ""
    try:
        import gc
        gc.collect()
        text += ", MicroPython %d KB free" % (gc.mem_free() // 1024)
    except Exception:
        pass
    try:
        import esp32
        info = esp32.idf_heap_info(esp32.HEAP_DATA)
        text += ", ESP-IDF heap %d KB free, largest block %d KB" % (
            sum(h[1] for h in info) // 1024, max(h[2] for h in info) // 1024)
    except Exception:
        pass
    return text


def chip_id():
    import machine
    return "".join("%02x" % b for b in machine.unique_id())


# -- the device ----------------------------------------------------------------------------------------------------

class _Device:
    def __init__(self, client, node_id, name, model, runtime_version, area, prefix, chip):
        self.client = client
        self.node_id = node_id
        self.chip = chip
        self.prefix = prefix
        self.info = {"name": name, "model": model, "runtime": runtime_version, "area": area, "bundle": BUNDLE_VERSION}
        self.base = "thingstudio/" + chip
        self.availability = self.base + "/availability"
        self.record = _read_record()
        self.status_subscribed = False
        self.republish = None
        self.commands_subscribed = set()
        self.reported = set()   # node ids whose state this flow has published
        self.started = False    # the first connect of this flow has happened
        client.set_will(self.availability, b"offline", True, 1)
        client.on_connect(self._on_connect)

    async def announce(self):
        topic, payload, after = build_discovery(self.chip, self.prefix, self.info, _components, self.record)
        data = _dumps(payload).encode()
        await self.client.publish(self.node_id, topic, data, True, 1)
        print("ts_ha: discovery sent, %d entities, %d bytes%s" % (len(_components), len(data), _memory()))
        if after != self.record:
            _write_record(after)
            self.record = after

    async def _on_connect(self):
        await self.client.publish(self.node_id, self.availability, b"online", True, 1)
        await self.announce()
        if not self.started:
            self.started = True
            for node_id, comp in list(_components.items()):
                if comp["p"] != "button" and node_id not in self.reported:
                    await self.client.publish(self.node_id, self.base + "/" + node_id + "/state", b"None", True, 0)

    async def _announce_later(self):
        try:
            import random
            delay = random.randint(1000, 5000)
        except ImportError:
            delay = 3000
        await asyncio.sleep(delay / 1000)
        self.republish = None
        await self.announce()

    def stop(self):
        if self.republish is not None:
            self.republish.cancel()
            self.republish = None


def configure_device(client, node_id, name, model="", runtime_version="", area="", prefix="homeassistant",
                     chip=None):
    """ha_device's setup. One device per flow: a second call is a loud error."""
    global _device
    if _device is not None:
        raise ValueError("ts_ha: a flow can have only one ha device node")
    _device = _Device(client, node_id, name, model, runtime_version, area, prefix or "homeassistant",
                      chip or chip_id())
    runtime.register_cleanup("ts_ha", _reset)
    return _device


def register(node_id, component):
    """An entity node's setup. `component` is its hook-built dict: p, name and the type's options."""
    if node_id in _components:
        raise ValueError("ts_ha: two HA nodes share the node id %r" % (node_id,))
    _components[node_id] = dict(component)
    runtime.register_cleanup("ts_ha", _reset)


def _need_device():
    if _device is None:
        raise ValueError("ts_ha: this flow has HA nodes but no ha device node")
    return _device


async def publish_state(node_id, value):
    dev = _need_device()
    comp = _components[node_id]
    text = state_payload(comp["p"], value, comp.get("ops"))
    if text is None:
        return
    dev.reported.add(node_id)
    await dev.client.publish(node_id, dev.base + "/" + node_id + "/state", text.encode(), True, 0)


async def command(node_id, echo=False):
    """Wait for HA's next valid command for this entity and return its flow value. With `echo` (an unwired input,
    SPEC §3) the accepted command is published back as the state."""
    dev = _need_device()
    comp = _components[node_id]
    topic = dev.base + "/" + node_id + "/set"
    if node_id not in dev.commands_subscribed:
        await dev.client.ensure_connected(node_id)
        await dev.client.subscribe(node_id, topic, 1)
        dev.commands_subscribed.add(node_id)
    while True:
        _topic, payload, _retained = await dev.client.wait_message(node_id)
        value = command_value(comp["p"], payload, comp)
        if value is IGNORED:
            print("ts_ha: %s ignored command %r -- not valid for this %s" % (node_id, payload, comp["p"]))
            continue
        if echo and comp["p"] != "button":
            await publish_state(node_id, value)
        return value


async def ha_status(node_id):
    """ha_device's wait: HA's next `online`/`offline` on <prefix>/status. On `online`, discovery goes out again
    after a random 1-5 s (SPEC §6)."""
    dev = _need_device()
    if not dev.status_subscribed:
        await dev.client.ensure_connected(node_id)
        await dev.client.subscribe(node_id, dev.prefix + "/status", 0)
        dev.status_subscribed = True
    while True:
        _topic, payload, _retained = await dev.client.wait_message(node_id)
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode()
        if payload in ("online", "offline"):
            if payload == "online" and dev.republish is None:
                dev.republish = asyncio.create_task(dev._announce_later())
            return payload


def _reset():
    """Redeploy cleanup: the next flow starts with no device and no components."""
    global _device
    if _device is not None:
        _device.stop()
    _device = None
    _components.clear()
