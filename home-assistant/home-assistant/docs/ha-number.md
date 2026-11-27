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

## Wiring

**Output**: one message each time the value is changed in Home Assistant:

| Field | Value |
| --- | --- |
| `payload` | the value: an int when **step** and the value are whole numbers, otherwise a float |
| `topic` | `''` |

**Input**: the real value, an int or a float. `None` sends nothing. The input takes any type, so a function node's
result can be wired straight in.

Wire the output to what it sets, a **pwm out** say, and the real value back into the input.

## Behavior

The number shows as unknown until the flow sends it a value. To show a value from the moment the flow starts, see "Showing a value from the start" in the bundle README.

**Input not wired:** the node confirms each change itself, and the compile warns about it, as for
[ha switch](ha-switch.md#behavior).

## Errors

- **Home Assistant sends a value outside min to max, or not a number.** The console shows
  `ts_ha: <node id> ignored command ...`, and nothing is sent.
- **The input's `payload` isn't a number.** The node raises `not a number: ...`. A dict raises an error saying to pick
  one field first.

These stop the compile: no **ha device** in the flow, an empty name, **min**, **max** or **step** not a number,
**min** not below **max**, **step** 0 or less.
