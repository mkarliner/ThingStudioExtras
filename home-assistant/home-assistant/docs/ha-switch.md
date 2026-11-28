# ha switch

A switch in Home Assistant. Sends `True` or `False` when it's switched there, and shows the real state you send it.

Needs an **ha device** node in the flow.

## Properties

- **name**: the entity's name in Home Assistant. Required.
- **device class**: `switch` or `outlet`, for the icon Home Assistant shows. Default `none`.
- **on start**: what the switch starts from: `unknown` (default), `off`, `on`, or `restore` (the last value it
  showed).

## Wiring

**Output**: one message each time the switch is turned on or off in Home Assistant, and once at flow start when
**on start** is `off` or `on` (as if Home Assistant had sent it):

| Field | Value |
| --- | --- |
| `payload` | `True` for on, `False` for off |
| `topic` | the entity's name, so one node can tell several entities apart |

**Input**: the real state, on when `payload` is true in Python and off when it's false. `None` sends nothing.

Wire the output to what it switches, a **gpio out** say.

## Behavior

With **on start** `unknown` (the default), the switch shows as unknown until the flow (or the echo below) reports
a value. With `off` or `on`, the value goes out on the output once at flow start so the downstream flow sets the
hardware; when the input isn't wired it is also published as the state. With `restore`, the switch starts from the
last value it showed, kept on the board; with nothing stored yet it behaves as `unknown`.

**Input not wired:** the node confirms each command itself: Home Assistant shows the switch on as soon as it's
turned on, whether or not anything happened. That's the right choice when the command is the state, such as an
LED. When the real state can differ from the command, such as a relay with a feedback contact or a thermostat,
wire the real state back to the input.

## Errors

- **Home Assistant sends something other than on or off.** The console shows `ts_ha: <node id> ignored command ...`,
  and nothing is sent.

These stop the compile: no **ha device** in the flow, an empty name.
