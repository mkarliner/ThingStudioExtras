# WiFi for a custom network node that isn't an MQTT node

**Type: docs** (or **core**, if a custom node that isn't an MQTT node isn't meant to get the flow's WiFi at
all; then a custom UDP node needs some documented way to be on the flow's network).
Filed: mkarliner/ThingStudio#21 (2026-11-27).
Answered in the user guide on 2026-11-27: commit a57d686b85dc74ae7e3f7240536ad3c40d406fe9 (main)
added "The flow's WiFi: ts_wifi" and "The flow's MQTT client: ts_mqtt" to custom-nodes — the
configRef field, the compile hook, `ensure_station`'s arguments and semantics, `unmanaged`, and the
network-down failure. This set is developed against that build (see ../THINGSTUDIO_VERSION). The
issue was closed 2026-11-27.

## What we were trying to do

Write a Wake on LAN node for the `wake-on-lan` set: a `sink` that sends a magic packet as a UDP datagram
(`socket.sendto` — the documented pattern under *Writing a custom node, "Cleanup"*). It needs the flow's
WiFi up to send anything. It is the simplest possible network node: no broker, no HTTP server, one UDP
socket, nothing shared with other nodes but the network.

## What the user guide says

The published guide (docs.thingstudio.net, checked 2026-11-27) says, from the user's side:

- *udp send* / *http request* / *mqtt subscribe* — "**WiFi** — the flow's WiFi network, shared by every
  WiFi node in the flow." (`mqtt subscribe` adds that **unmanaged** "isn't accepted in a flow with MQTT
  nodes, because they manage the connection themselves".)
- *Editor in depth, "Config nodes"* — "A flow has one WiFi network and one MQTT broker. Every node that
  uses WiFi has a **WiFi** field, and every MQTT node an **MQTT Broker** field. They all show the
  flow's one setting: change it on one node and it changes on all."
- *Writing a custom node, "Sharing a config"* — a `configRef` property "lets your node pick one of the
  flow's config nodes", and its value in Python is "that config's own properties as a dict (or `None` if
  none is picked)"; "(Network configs — WiFi, MQTT — expose only the credential's name, not the secret,
  so a custom node can't make a WiFi connection from one.)"
- *Writing a custom node, "Libraries you can import"* — "`ts_wifi`, `ts_mqtt`, `ts_http_server` — the
  flow's WiFi, MQTT client and HTTP server, shared with the network nodes." Nothing else anywhere about
  `ts_wifi`: no calls, arguments, behaviour or failures.
- The only documented story of who manages the connection for a custom node is the MQTT one (*Writing a
  custom node, "Libraries you can import"*): "Any node holding the flow's broker counts as an MQTT node,
  so the flow's WiFi is left to the MQTT client, as it is for the mqtt nodes", with the WiFi and broker
  passwords readable "only a compile hook … can read, from `ctx[\"referencedConfigs\"]`".

What the guide does **not** say, anywhere we looked:

- the WiFi config's type for a custom node's `configRef` — the guide names `thingstudio/config/i2c-bus`
  and `thingstudio/config/mqtt-broker`; the WiFi type's string is never written;
- what the node's Python receives for a picked WiFi config, beyond "the credential's name";
- what `ts_wifi` offers a node that isn't an MQTT node;
- who brings the flow's WiFi up when the flow's only network node is a custom node that isn't an MQTT
  node — the "Cleanup" socket example shows `sendto` without a word about the network being up;
- whether **unmanaged** WiFi is usable by such a node;
- what a node's send does (error, message) when the network isn't up.

## What happened

We can't write the node from the guide. Every part of it except the packet itself is on the WiFi: without
a documented way to be on the flow's network, the node can't be written, and per AGENTS.md ("Core
requests", point 4) the task waits rather than lean on undocumented behaviour. No board test has been run
for this set: there is nothing to test until the node exists.

## What we need

The general pattern the built-in nodes already have, documented for custom nodes — any networking node
can pick the flow's WiFi config (or share the existing one):

1. A custom node that uses the network declares a WiFi `configRef`, the same as a built-in node's **WiFi**
   field. State the config's type, and what the node's Python receives for it.
2. How such a node uses the flow's connection at runtime: the `ts_wifi` calls a node may use, with their
   arguments, behaviour and failures — or a statement of which nodes bring the flow's WiFi up and what a
   node that isn't one of them relies on.
3. The failure path: what a send does when the WiFi is down (the error, its message), so the node's fault
   handling is deterministic.
4. Whether **unmanaged** WiFi is usable by a non-MQTT custom node.

Related: `2026-11-26-ts-mqtt-client-for-nodes.md` asks "what `ts_wifi` offers a node" from the MQTT side;
this is the same surface from the non-MQTT side. The two can be answered together.

Until this lands, the `wake-on-lan` node waits (AGENTS.md, "Core requests" point 4).
