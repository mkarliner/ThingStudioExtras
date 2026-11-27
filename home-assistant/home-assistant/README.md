# Home Assistant nodes for ThingStudio

These nodes make a ThingStudio board a Home Assistant device. Put an **ha device** node and a few entity nodes in a
flow, deploy it, and the board appears in Home Assistant with its sensors, switches and controls, with no YAML and no
firmware to build. It works over MQTT discovery, so Home Assistant needs an MQTT broker (below).

| Node | In Home Assistant | Page |
| --- | --- | --- |
| **ha device** | the device itself; one per flow | [docs/ha-device.md](docs/ha-device.md) |
| **ha sensor** | a sensor showing a number or text | [docs/ha-sensor.md](docs/ha-sensor.md) |
| **ha binary sensor** | an on/off sensor | [docs/ha-binary-sensor.md](docs/ha-binary-sensor.md) |
| **ha switch** | a switch you can turn on and off | [docs/ha-switch.md](docs/ha-switch.md) |
| **ha number** | a number set with a slider or a box | [docs/ha-number.md](docs/ha-number.md) |
| **ha select** | a list of options | [docs/ha-select.md](docs/ha-select.md) |
| **ha button** | a button | [docs/ha-button.md](docs/ha-button.md) |

The nodes are in the palette's **home assistant** group.

## What you need

- **ThingStudio App**, built from `main` on 2026-11-27 or later (commit a57d686b). No release includes everything
  these nodes use yet (the latest, v0.13.0, is from 2026-11-18), so build from source and check out `main`: see the
  user guide, *Installation details*, "A feature that isn't released yet". A release that includes it will be named
  here. ThingStudio Web, the browser version, won't do: it has no custom nodes.
- **A board with WiFi**, set up in ThingStudio as the user guide describes. The nodes were developed on an ESP32-C3
  and an ESP32-S3.
- **Home Assistant with an MQTT broker** and its MQTT integration (below).

## New to ThingStudio?

ThingStudio's user guide (**Help → User guide** in the editor) takes a new board to a blinking LED. For these nodes,
follow it with these choices:

1. **Install ThingStudio** from source, as above (*Installation details*, "From source").
2. **Install MicroPython** with **Tools → Install firmware…** (*Step 3*). On an ESP32-C3, or a classic ESP32
   without PSRAM, pick **ThingStudio custom image**: WiFi, MQTT and these nodes need the memory it frees.
3. **Connect** the board and **install the runtime** (*Steps 4 and 5*).
4. **Name the board and give it a password**, in **Tools → Board settings…** (*Connecting over WiFi*). With a
   password you can deploy over WiFi once the board is in place, away from your computer. Home Assistant shows the
   device under the board's hostname unless you give **ha device** a name.
5. Optional: **blink an LED** (*Step 6*), to check the board works before adding Home Assistant.

Then set up MQTT, install these nodes and deploy the starter example, below.

## Install

1. Copy this whole folder, `home-assistant`, into `~/.thingstudio/custom-nodes/`, so you have
   `~/.thingstudio/custom-nodes/home-assistant/ha_device.node.json` and so on.
2. In the editor, click **Reload custom nodes** at the bottom of the palette. The console lists what loaded.

The folder loads whole or not at all: if the console says it was refused, it names the file and why. Don't move
files out of it; `lib/ts_ha.py` is shared by every node in it.

## Set up MQTT in Home Assistant

Skip this if Home Assistant already uses an MQTT broker.

1. **The broker.** In Home Assistant, go to Settings → Add-ons → Add-on Store, install **Mosquitto broker** and
   start it.
2. **A user for the board.** Settings → People → Users → Add user, for example `thingstudio`, with a password. The
   Mosquitto add-on accepts Home Assistant users.
3. **The integration.** Settings → Devices & services. Home Assistant usually offers the discovered MQTT
   integration: click **Configure**. Otherwise add the **MQTT** integration and point it at the add-on.
   Discovery is on by default, with the prefix `homeassistant`.
4. **In ThingStudio**, the flow's MQTT broker is the Home Assistant machine's address, port `1883`, and the user
   from step 2. The starter example below shows where it goes.

## Use

The quickest start is `examples/starter-ha.flow.json`. It runs on any board with WiFi and needs no wiring:

1. **File → Open…** the starter example.
2. Select **ha device**. Its **WiFi** and **MQTT Broker** fields name two credentials, `home-wifi` and
   `home-assistant-mqtt`, that aren't saved on your computer yet. Click ✎ next to each: it says so. Fill in your
   network's name and password, and for the broker the Home Assistant machine's address, port `1883` and the MQTT
   user, then **Save**. The credentials stay on your computer, in `~/.thingstudio/credentials/`, not in the flow.
3. Pick your board in the **Board** menu if the editor hasn't, and click **Compile → Deploy**.
4. In Home Assistant, the board appears under Settings → Devices & services → MQTT, with an uptime, its free memory,
   a test switch and a button.

To build your own flow:

1. Put an **ha device** node in the flow and pick the flow's **WiFi** and **MQTT Broker**.
2. Add an entity node for each thing Home Assistant should see, and wire it like any other node: a sensor's value
   into **ha sensor**, **ha switch**'s output to what it switches, and the real state back into its input.
3. Deploy. The board appears under Settings → Devices & services → MQTT as its hostname, or the **device name** you
   gave **ha device**.

Two more example flows are in `examples/`, for particular boards:

- `kitchen-sink-ha.flow.json`, for the kitchen-sink ESP32-C3 board: the knob, the button, the chip temperature, and
  the RGB LED switched and dimmed from Home Assistant. Its switch and slider are left unwired, to show the echo.
- `freenove-s3-ha.flow.json`, for the Freenove ESP32-S3 4" display board, with no extra parts: the screen backlight's
  brightness, the chip temperature and free memory, a running-hot alarm, and a switch, a select and a button. Its
  switch has its state wired back.

Open one in the editor, pick your own WiFi and MQTT broker in **ha device**, and deploy.

Each entity node's id becomes part of the entity's id in Home Assistant, so the same node keeps the same entity
across deploys, renames and restarts. Deleting a node and adding a new one makes a new entity; the old one is removed
on the next deploy.

## Removing a device

A flow without **ha device** leaves the board's device in Home Assistant. To remove it, open
the device in Home Assistant (Settings → Devices & services → MQTT → devices) and delete it.

## Limits

- One **ha device** per flow, and every entity node needs it.
- The discovery message, which describes every entity, can be at most 4 KB: about a dozen entities with long names,
  more with short ones. The compile says so when a flow goes over.
- Node ids go into MQTT topics: letters, digits, `_` and `-`, at most 32 characters.
- Home Assistant to the board only covers the board's own entities: these nodes don't read other Home Assistant
  entities.
