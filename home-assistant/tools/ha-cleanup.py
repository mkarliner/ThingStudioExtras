#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# home-assistant/tools/ha-cleanup.py -- removes ThingStudio test devices from Home Assistant by clearing their retained MQTT
# messages (plan decision 11 and task 1.9). For each matching device: an empty retained message on its discovery
# topic (HA then deletes the device and its entities, SPEC §7) and on every retained thingstudio/<chip id>/... topic
# (availability and states), so nothing comes back.
#
# Which devices: by default those whose HA name starts with "ts-test" (how test boards are named). --name PREFIX
# picks another prefix, --device ts_<chip id> one device. Lists what it found and stops unless --yes is given.
#
# Needs: pip install paho-mqtt (2.x). Broker settings from the environment: MQTT_HOST, MQTT_PORT (default 1883),
# MQTT_USER, MQTT_PASSWORD. --prefix if your discovery prefix isn't homeassistant.

import argparse
import json
import os
import sys
import time

try:
    import paho.mqtt.client as mqtt
except ImportError:
    sys.exit("ha-cleanup: needs paho-mqtt 2.x -- pip install paho-mqtt")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[2] if __doc__ else None)
    ap.add_argument("--name", default="ts-test", help="HA device name prefix to match (default ts-test)")
    ap.add_argument("--device", help="one device id, e.g. ts_a0b1c2d3e4f5 (overrides --name)")
    ap.add_argument("--prefix", default="homeassistant", help="discovery prefix (default homeassistant)")
    ap.add_argument("--yes", action="store_true", help="actually clear the messages (default: only list)")
    ap.add_argument("--wait", type=float, default=3.0, help="seconds to collect retained messages (default 3)")
    args = ap.parse_args()

    host = os.environ.get("MQTT_HOST") or sys.exit("ha-cleanup: set MQTT_HOST in the environment")
    retained = {}
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ts-ha-cleanup")
    if os.environ.get("MQTT_USER"):
        client.username_pw_set(os.environ["MQTT_USER"], os.environ.get("MQTT_PASSWORD", ""))

    def on_message(_c, _u, m):
        if m.retain and m.payload:
            retained[m.topic] = m.payload

    client.on_message = on_message
    client.connect(host, int(os.environ.get("MQTT_PORT", "1883")))
    client.loop_start()
    client.subscribe("%s/device/+/config" % args.prefix)
    client.subscribe("thingstudio/#")
    time.sleep(args.wait)

    devices = {}
    for topic, payload in retained.items():
        parts = topic.split("/")
        if len(parts) != 4 or parts[0] != args.prefix or parts[1] != "device" or not parts[2].startswith("ts_"):
            continue
        try:
            name = json.loads(payload).get("dev", {}).get("name", "")
        except ValueError:
            name = ""
        device_id = parts[2]
        if args.device:
            if device_id != args.device:
                continue
        elif not name.startswith(args.name):
            continue
        devices[device_id] = name

    if not devices:
        print("ha-cleanup: no matching ThingStudio devices (%s)." % (
            "device " + args.device if args.device else "names starting %r" % args.name))
        client.loop_stop()
        client.disconnect()
        return

    to_clear = []
    for device_id, name in sorted(devices.items()):
        chip = device_id[len("ts_"):]
        topics = ["%s/device/%s/config" % (args.prefix, device_id)]
        topics += sorted(t for t in retained if t.startswith("thingstudio/%s/" % chip))
        print("%s (%s): %d retained message(s)" % (name or "?", device_id, len(topics)))
        for t in topics:
            print("    " + t)
        to_clear += topics

    if not args.yes:
        print("\nha-cleanup: nothing cleared. Run again with --yes to remove these devices from HA.")
    else:
        for t in to_clear:
            client.publish(t, b"", qos=1, retain=True).wait_for_publish(5)
        print("\nha-cleanup: cleared %d retained message(s); HA removes the device(s)." % len(to_clear))
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
