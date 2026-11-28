# ha number

A number in Home Assistant, set with a slider or a box. Sends the value when it's changed there, and shows the real
value you send it.

Needs an **ha device** node in the flow.

## Properties

- **name**: the entity's name in Home Assistant. Required.
- **min**, **max**: the range. **min** must be below **max**. Default 0 to 100.
- **step**: the slider's step. Above 0. Default 1.
- **unit**: shown after the value, such as `%`. Optional.
- **mode**: `slider` or `box`. Default `slider`.
- **on start**: a start value inside **min** to **max**, `unknown`, or `restore` (the last value it showed).
  Default `unknown`.

## Wiring

**Output**: one message each time the value is changed in Home Assistant, and once at flow start when **on start**
is a start value (as if Home Assistant had sent it):

| Field | Value |
| --- | --- |
| `payload` | the value: an int when **step** and the value are whole numbers, otherwise a float |
| `topic` | the entity's name, so one node can tell several entities apart |

**Input**: the real value, an int or a float. `None` sends nothing. The input takes any type, so a function node's
result can be wired straight in.

Wire the output to what it sets, a **pwm out** say.

## Behavior

With **on start** `unknown` (the default), the number shows as unknown until the flow (or the echo below) sends it
a value. With a start value, it goes out on the output once at flow start so the downstream flow sets the
hardware; when the input isn't wired it is also published as the state. With `restore`, the number starts from the
last value it showed, kept on the board; with nothing stored yet it behaves as `unknown`.

**Input not wired:** the node confirms each change itself: Home Assistant shows the value as set as soon as it's
changed, whether or not anything happened. That's the right choice when the value is the state, such as a screen
backlight. When the real value can differ from the command, wire the real value back to the input.

## Errors

- **Home Assistant sends a value outside min to max, or not a number.** The console shows
  `ts_ha: <node id> ignored command ...`, and nothing is sent.
- **The input's `payload` isn't a number.** The node raises `not a number: ...`. A dict raises an error saying to pick
  one field first.

These stop the compile: no **ha device** in the flow, an empty name, **min**, **max** or **step** not a number,
**min** not below **max**, **step** 0 or less.
