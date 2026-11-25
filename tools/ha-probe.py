#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# tools/ha-probe.py -- Phase 1 task 1.2 of docs/working-notes/home-assistant-implementation-plan.md.
#
# Publishes docs/working-notes/home-assistant/SPEC.md's messages for a fake board ("ts-test-probe") and reads back
# what Home Assistant made of them through its REST API, to settle SPEC §10 before the spec is frozen:
#   1. the abbreviated device-discovery message creates one device with every entity type
#   2. whether the origin ("o") is enforced
#   3. removing one component: does omitting it work, or is the {"p": ...} stub needed
#   4. an empty retained payload removes the device
#   5. availability offline/online
#   6. commands from HA arrive on the set topics with the spec's payloads
#   7. whether a "None" state (or clearing the retained state) makes HA show an entity as unknown
# It leaves nothing behind: every retained message it set is cleared at the end, also on Ctrl-C.
#
# Needs: pip install paho-mqtt (2.x). Settings come from the environment, never the repo:
#   HA_URL (e.g. http://homeassistant.local:8123), HA_TOKEN (a long-lived token from your HA profile),
#   MQTT_HOST, MQTT_PORT (default 1883), MQTT_USER, MQTT_PASSWORD (both optional).

import json
import os
import sys
import time
import urllib.error
import urllib.request

try:
    import paho.mqtt.client as mqtt
except ImportError:
    sys.exit("ha-probe: needs paho-mqtt 2.x -- pip install paho-mqtt")

PREFIX = "homeassistant"
CHIP = "testprobe"
DEV_ID = "ts_" + CHIP
DEV_NAME = "ts-test-probe"
BASE = "thingstudio/" + CHIP
DISC = "%s/device/%s/config" % (PREFIX, DEV_ID)
AVTY = BASE + "/availability"
CHIP2 = "testprobe2"
DISC2 = "%s/device/ts_%s/config" % (PREFIX, CHIP2)
SETTLE = float(os.environ.get("PROBE_SETTLE_S", "3"))

COMPONENTS = {
    "t": {"p": "sensor", "name": "Temperature", "dev_cla": "temperature", "unit_of_meas": "°C", "stat_cla": "measurement"},
    "b": {"p": "binary_sensor", "name": "Door", "dev_cla": "door"},
    "w": {"p": "switch", "name": "Lamp"},
    "n": {"p": "number", "name": "Brightness", "min": 0, "max": 100, "step": 1, "unit_of_meas": "%", "mode": "slider"},
    "s": {"p": "select", "name": "Mode", "ops": ["off", "auto", "on"]},
    "k": {"p": "button", "name": "Restart"},
}
STATES = {"t": "21.5", "b": "ON", "w": "OFF", "n": "40", "s": "auto"}
COMMANDABLE = ("switch", "number", "select", "button")


def env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        sys.exit("ha-probe: set %s in the environment" % name)
    return value


HA_URL = env("HA_URL").rstrip("/")
HA_TOKEN = env("HA_TOKEN")


def ha(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(HA_URL + path, data=data, method=method, headers={
        "Authorization": "Bearer " + HA_TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        text = r.read().decode()
    return json.loads(text) if text else None


def component(node_id, comp, chip=CHIP):
    out = dict(comp)
    out["uniq_id"] = "ts_%s_%s" % (chip, node_id)
    if comp["p"] != "button":
        out["stat_t"] = "thingstudio/%s/%s/state" % (chip, node_id)
    if comp["p"] in COMMANDABLE:
        out["cmd_t"] = "thingstudio/%s/%s/set" % (chip, node_id)
    return out


def discovery(cmps, chip=CHIP, name=DEV_NAME, origin=True):
    msg = {
        "dev": {"ids": ["ts_" + chip], "name": name, "mdl": "probe", "mf": "ThingStudio", "sw": "0.0.0"},
        "avty_t": "thingstudio/%s/availability" % chip,
        "cmps": cmps,
    }
    if origin:
        msg["o"] = {"name": "ThingStudio", "sw": "0.0.0-probe"}
    return msg


class Broker:
    def __init__(self):
        self.c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ts-ha-probe")
        user = os.environ.get("MQTT_USER")
        if user:
            self.c.username_pw_set(user, os.environ.get("MQTT_PASSWORD", ""))
        self.received = []
        self.retained_topics = set()
        self.c.on_message = lambda _c, _u, m: self.received.append((m.topic, m.payload.decode(errors="replace")))
        self.c.connect(env("MQTT_HOST"), int(os.environ.get("MQTT_PORT", "1883")))
        self.c.loop_start()

    def pub(self, topic, payload, retain=True):
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        self.c.publish(topic, payload, qos=1, retain=retain).wait_for_publish(5)
        if retain:
            self.retained_topics.add(topic)

    def clear_all(self):
        for topic in sorted(self.retained_topics):
            self.c.publish(topic, "", qos=1, retain=True).wait_for_publish(5)
        self.retained_topics.clear()


def probe_states(name=DEV_NAME):
    """This device's entities, by entity name (friendly name minus the device name)."""
    out = {}
    for s in ha("GET", "/api/states"):
        friendly = s.get("attributes", {}).get("friendly_name", "")
        if friendly == name or friendly.startswith(name + " "):
            out[friendly[len(name):].strip() or "(device)"] = s
    return out


def settle():
    time.sleep(SETTLE)


results = []


def report(n, question, answer):
    results.append((n, question, answer))
    print("\n[%s] %s\n    %s" % (n, question, answer))


def main():
    print("ha-probe: HA %s, device %s, discovery %s" % (HA_URL, DEV_NAME, DISC))
    try:
        ha("GET", "/api/")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            sys.exit("ha-probe: HA refused the token (401). Check HA_TOKEN: a long-lived access token from your HA "
                     "profile page (Security tab), copied whole, with no quotes or spaces inside. "
                     "Token length here: %d characters (a real one is about 180)." % len(HA_TOKEN))
        sys.exit("ha-probe: HA answered %s %s for %s/api/" % (e.code, e.reason, HA_URL))
    except OSError as e:
        sys.exit("ha-probe: can't reach HA at %s: %s" % (HA_URL, e))
    b = Broker()
    try:
        # Start clean, in case an earlier run was interrupted.
        b.pub(DISC, "")
        b.pub(DISC2, "")
        settle()

        # 1. Full discovery.
        b.pub(AVTY, "online")
        b.pub(DISC, discovery({k: component(k, v) for k, v in COMPONENTS.items()}))
        settle()
        for k, v in STATES.items():
            b.pub("%s/%s/state" % (BASE, k), v)
        settle()
        found = probe_states()
        lines = []
        for k, comp in COMPONENTS.items():
            s = found.get(comp["name"])
            if s is None:
                lines.append("%s (%s): MISSING" % (comp["name"], comp["p"]))
                continue
            a = s["attributes"]
            lines.append("%s: %s state=%r device_class=%r unit=%r options=%r" % (
                comp["name"], s["entity_id"], s["state"], a.get("device_class"), a.get("unit_of_measurement"),
                a.get("options")))
        report(1, "Abbreviated device discovery creates every entity type?",
               ("yes" if len(lines) == len(COMPONENTS) and "MISSING" not in " ".join(lines) else "NO") + "\n    " +
               "\n    ".join(lines))
        ids = {k: found[c["name"]]["entity_id"] for k, c in COMPONENTS.items() if c["name"] in found}

        # 6. Commands from HA.
        b.c.subscribe(BASE + "/+/set", qos=1)
        time.sleep(0.5)
        calls = [
            ("w", "switch", "turn_on", {}, "ON"),
            ("w", "switch", "turn_off", {}, "OFF"),
            ("n", "number", "set_value", {"value": 42}, "42"),
            ("s", "select", "select_option", {"option": "on"}, "on"),
            ("k", "button", "press", {}, "PRESS"),
        ]
        cmd_lines = []
        for node, domain, service, extra, expect in calls:
            if node not in ids:
                cmd_lines.append("%s.%s: entity missing, skipped" % (domain, service))
                continue
            b.received.clear()
            body = dict(extra)
            body["entity_id"] = ids[node]
            ha("POST", "/api/services/%s/%s" % (domain, service), body)
            time.sleep(1.5)
            got = [p for t, p in b.received if t == "%s/%s/set" % (BASE, node)]
            cmd_lines.append("%s.%s -> %r (spec says %r)%s" % (
                domain, service, got, expect, "" if got == [expect] else "  <-- DIFFERS"))
        report(6, "Commands arrive on <base>/<node>/set with the spec's payloads?", "\n    ".join(cmd_lines))

        # 7. Unknown after a restart: "None" as the state, and clearing the retained state.
        none_lines = []
        for k, comp in COMPONENTS.items():
            if comp["p"] == "button":
                continue
            b.pub("%s/%s/state" % (BASE, k), "None")
        settle()
        after_none = {n: s["state"] for n, s in probe_states().items()}
        for k, comp in COMPONENTS.items():
            if comp["p"] != "button":
                none_lines.append("%s (%s): %r" % (comp["name"], comp["p"], after_none.get(comp["name"])))
        for k, v in STATES.items():
            b.pub("%s/%s/state" % (BASE, k), v)
        settle()
        for k in STATES:
            b.pub("%s/%s/state" % (BASE, k), "")
        settle()
        after_clear = {n: s["state"] for n, s in probe_states().items()}
        report(7, "Does a \"None\" state make HA show unknown? (and does clearing the retained state?)",
               "after \"None\":\n      " + "\n      ".join(none_lines) +
               "\n    after an empty retained message (states were set again first): %s" % after_clear)
        for k, v in STATES.items():
            b.pub("%s/%s/state" % (BASE, k), v)
        settle()

        # 5. Availability.
        b.pub(AVTY, "offline")
        settle()
        off = {n: s["state"] for n, s in probe_states().items()}
        b.pub(AVTY, "online")
        settle()
        on = {n: s["state"] for n, s in probe_states().items()}
        report(5, "offline makes every entity unavailable, online restores?",
               "offline: %s\n    online: %s" % (off, on))

        # 3. Removal: omission first, then the stub.
        without = {k: component(k, v) for k, v in COMPONENTS.items() if k != "w"}
        b.pub(DISC, discovery(without))
        settle()
        gone_by_omission = "Lamp" not in probe_states()
        how = "omitting it removes it"
        if not gone_by_omission:
            stub = dict(without)
            stub["w"] = {"p": "switch"}
            b.pub(DISC, discovery(stub))
            settle()
            b.pub(DISC, discovery(without))
            settle()
            how = "stub needed: " + ("the stub removed it" if "Lamp" not in probe_states() else "STILL THERE after the stub")
        report(3, "Removing one component: omission or {\"p\": ...} stub?", how)

        # 2. Origin enforced?
        b.pub(DISC2, discovery({"t": component("t", COMPONENTS["t"], CHIP2)}, chip=CHIP2, name="ts-test-probe2",
                               origin=False))
        settle()
        no_origin = probe_states("ts-test-probe2")
        report(2, "Discovery without \"o\" accepted?",
               "yes, entities created: %s" % sorted(no_origin) if no_origin else
               "no, nothing created (check HA's log for an MQTT discovery error)")

        # 4. Empty payload removes the device.
        b.pub(DISC, "")
        b.pub(DISC2, "")
        settle()
        left = probe_states()
        report(4, "Empty retained payload removes the device and its entities?",
               "yes" if not left else "NO, still there: %s" % sorted(left))
    finally:
        b.clear_all()
        time.sleep(0.5)
        b.c.loop_stop()
        b.c.disconnect()
        print("\nha-probe: retained messages cleared.")

    print("\n=== Summary ===")
    for n, q, a in sorted(results):
        print("[%s] %s\n    %s" % (n, q, a))


if __name__ == "__main__":
    main()
