# Document ts_mqtt and ts_wifi, the core APIs the mqtt nodes use

**Type: docs** (or **core**, if these calls aren't meant for custom nodes; then a node needs some documented way to
publish, subscribe and receive on the shared client). Status: filed as [#24](https://github.com/mkarliner/ThingStudio/issues/24), 2026-11-27. Related: [#21](https://github.com/mkarliner/ThingStudio/issues/21) (the same `ts_wifi` question from a non-MQTT node).

**Framing (Mike, 2026-11-27):** this is documenting core's own APIs, `ts_mqtt` and `ts_wifi`, which the built-in
mqtt nodes use and so other nodes can too. Not a separate API for custom nodes.

## What we were trying to do

Write test doubles for `ts_mqtt` and `ts_wifi` from the user guide (Home Assistant bundle, plan task 1.7), so the
bundle's `ts_ha` library can be tested under the MicroPython unix port. The bundle's nodes publish retained
discovery and state messages, subscribe to command topics and wait for HA's messages, all on the flow's shared
client.

## What the user guide says

Writing a custom node, "Libraries you can import" (`custom-nodes.md`, `user-libraries` at 8f8d137b):

- `ts_wifi`, `ts_mqtt` are listed as "the flow's WiFi, MQTT client and HTTP server, shared with the network nodes".
- "`ts_mqtt.ensure_client(...)` returns the flow's one client for a broker". The arguments are shown as `...`.
- Two client methods are documented: `client.set_will(topic, msg, retain=False, qos=0)` and
  `client.on_connect(callback)`.

Nothing else about the client or `ts_wifi`. No page in the guide mentions publishing, subscribing or receiving from a
custom node.

## What happened

The bundle (written before Extras worked only from the user guide) calls these, none of which the guide documents:

| Call | What the bundle needs from it |
|---|---|
| `ts_wifi.ensure_station(ssid, password, security, ...)` | bring up the flow's WiFi before the MQTT client |
| `ts_mqtt.ensure_client(broker, port, ssid, wifi_password, security, username, broker_password)` | the arguments, in order |
| `client.ensure_connected(node_id)` | wait until the client is connected |
| `client.publish(node_id, topic, payload, retain, qos)` | publish; what `node_id` is for |
| `client.subscribe(node_id, topic, qos)` | subscribe; is it restored after a reconnect (the bundle's SPEC assumes so) |
| `client.wait_message(node_id)` | the next message for this node, as `(topic, payload, retained)`; only for topics this node subscribed to? |

Without these, a test double can't be written from the guide, and an author outside the project couldn't write
the bundle at all.

## What we need

In `custom-nodes.md`, under the existing MQTT paragraph, the client calls a node may use, with their arguments and
behaviour: connecting, publishing (retain, QoS), subscribing (and whether subscriptions survive a reconnect),
receiving (which messages a node gets, the shape of each, what happens to messages nobody waits for), and failures
(what each raises when the broker is down). Also `ensure_client`'s arguments, whether a library (not only a node) may `import runtime` (the guide says nodes
have `runtime` without importing it, and calls it a module of ThingStudio's runtime), and what `ts_wifi` offers a node, or a
statement that a node holding the broker config never touches WiFi itself.

Until this lands, the bundle's MQTT side has no tests here, and it stays on calls the guide doesn't cover (AGENTS.md,
"Core requests" point 4): Mike to decide whether the hardware pass goes on meanwhile.

**Done, 2026-11-27:** #24 closed by ThingStudio a57d686b (user guide, custom-nodes.md: `ts_wifi` and `ts_mqtt`).
The HA bundle was checked against it and the pin moved there.
