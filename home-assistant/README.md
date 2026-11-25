# Home Assistant nodes for ThingStudio (work in progress)

Makes a ThingStudio board a Home Assistant device over MQTT discovery. The contract is
`docs/working-notes/home-assistant/SPEC.md` (v1, frozen 2026-11-25).

Nodes: `ha device`, `ha sensor`, `ha binary sensor`, `ha switch`, `ha number`, `ha select`, `ha button`. The example uses all but `ha select`.

## Install

Needs ThingStudio from the `user-libraries` branch (2026-11-25 or later): bundles, user libraries, the `ts_mqtt` will
and connect hook, and custom-node compile hooks that receive `referencedConfigs`.

1. Copy this whole folder into `~/.thingstudio/custom-nodes/` and click **Reload custom nodes**. The nodes appear in
   the palette's **home assistant** group.
2. In HA: the MQTT integration, pointed at your broker (the Mosquitto add-on is the usual one).

## Use

Put one `ha device` in the flow (pick the WiFi and the MQTT broker), then an `ha …` node per entity. The board shows
up in HA under Settings → Devices as its hostname (or the device name you set). `examples/kitchen-sink-ha.flow.json`
runs on the kitchen-sink ESP32-C3 board.

Deploying a flow without HA nodes leaves the device in HA: delete it there.
