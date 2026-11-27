# ha switch

A switch in Home Assistant. Sends `True` or `False` when it's switched there, and shows the real state you send it.

Needs an **ha device** node in the flow.

## Properties

- **name**: the entity's name in Home Assistant. Required.
- **device class**: `switch` or `outlet`, for the icon Home Assistant shows. Default `none`.

## Wiring

**Output**: one message each time the switch is turned on or off in Home Assistant:

| Field | Value |
| --- | --- |
| `payload` | `True` for on, `False` for off |
| `topic` | `''` |

**Input**: the real state, on when `payload` is true in Python and off when it's false. `None` sends nothing.

Wire the output to what it switches, a **gpio out** say, and the real state back into the input. Then Home Assistant
shows what actually happened, not just what was asked for.

## Behavior

The switch shows as unknown until the flow sends it a state.

**Input not wired:** the node confirms each command itself: Home Assistant shows the switch on as soon as it's turned
on, whether or not anything happened. The compile warns about it. Fine for a quick test; wire the real state back
for anything you rely on.

## Errors

- **Home Assistant sends something other than on or off.** The console shows `ts_ha: <node id> ignored command ...`,
  and nothing is sent.

These stop the compile: no **ha device** in the flow, an empty name.
