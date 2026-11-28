# ha button

A button in Home Assistant. Sends `True` each time it's pressed there.

Needs an **ha device** node in the flow.

## Properties

- **name**: the entity's name in Home Assistant. Required.

## Wiring

**Output**: one message per press:

| Field | Value |
| --- | --- |
| `payload` | `True` |
| `topic` | the entity's name, so one node can tell several entities apart |

## Behavior

A button has no state: Home Assistant shows when it was last pressed.

## Errors

- **Home Assistant sends something other than a press.** The console shows `ts_ha: <node id> ignored command ...`.

These stop the compile: no **ha device** in the flow, an empty name.
