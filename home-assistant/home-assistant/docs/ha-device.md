# ha device

Makes the board a Home Assistant device, and sends Home Assistant's own status when it changes.

Every flow with Home Assistant nodes has exactly one **ha device**. The entity nodes (**ha sensor**, **ha switch**
and the rest) appear in Home Assistant as that device's entities.

## Properties

- **device name**: the name Home Assistant shows. Empty: the board's hostname.
- **area**: the area Home Assistant suggests for the device, such as `Kitchen`. Optional.
- **discovery prefix**: the MQTT discovery prefix set in Home Assistant's MQTT integration. Default `homeassistant`;
  change it only if you changed it there.
- **MQTT Broker**: the flow's MQTT broker, shared by every MQTT node in the flow. Required.
- **WiFi**: the flow's WiFi network, shared by every WiFi node in the flow. **unmanaged** isn't accepted, because
  MQTT manages the connection.

The device's model in Home Assistant is the board you compile for.

## Wiring

**Output**: one message each time Home Assistant starts or stops:

| Field | Value |
| --- | --- |
| `payload` | `online` or `offline` |
| `topic` | `<discovery prefix>/status`, such as `homeassistant/status` |

Leave it unwired if you don't need it. Wire it to a **debug** node to see Home Assistant restart, or to anything
that should react when it goes away.

## Behavior

Each time the board connects to the broker, **ha device** tells Home Assistant the board is online and describes
every entity in the flow (the discovery message). If the board drops off without saying goodbye, the broker tells
Home Assistant it's offline, and every entity shows as unavailable until it's back.

When a flow starts, each entity shows as unknown until the flow sends it a value. Home Assistant doesn't keep showing
the last flow's value as if it were current.

When Home Assistant restarts, the board describes its entities again after a random 1 to 5 seconds, so they come
back with nothing to do on the board.

The board's chip id, not its name, identifies the device. Renaming the board, or changing **device name**, changes
only the name Home Assistant shows: entities, their history and automations stay.

The board remembers which entities it last described, in a small file `ha_entities.json`. When a deploy drops an
entity node, the next connect tells Home Assistant to remove that entity.

A flow without **ha device** leaves the device in Home Assistant: delete it there.

## Errors

- **The board can't reach the broker.** The console shows `mqtt connect to HOST:PORT failed after 3 attempts`. Check
  the broker config's address, port and user, and that the broker is running.
- **The board can't save its list of entities.** The console shows `ts_ha: couldn't save ha_entities.json`, and an entity
  removed later may stay in Home Assistant: delete it there.

These stop the compile:

- a second **ha device** in the flow;
- no WiFi or no MQTT broker config in the flow, or none picked in **ha device**'s properties;
- an **unmanaged** WiFi network;
- a broker config with no address;
- a node id that can't go in an MQTT topic: use letters, digits, `_` and `-`, at most 32;
- a discovery message over 4 KB, with its size: remove entities or shorten their names, or split them across two
  boards.

A flow with **ha device** and no entities compiles with a warning.
