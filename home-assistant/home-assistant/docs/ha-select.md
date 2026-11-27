# ha select

A list of options in Home Assistant. Sends the option chosen there, and shows the current option you send it.

Needs an **ha device** node in the flow.

## Properties

- **name**: the entity's name in Home Assistant. Required.
- **options**: one option per line, each different. Blank lines and spaces around an option are ignored.

## Wiring

**Output**: one message each time an option is chosen in Home Assistant:

| Field | Value |
| --- | --- |
| `payload` | the option, as text |
| `topic` | `''` |

**Input**: the current option. It must be one of **options**. `None` sends nothing. The input takes any type, so a
function node's result can be wired straight in.

## Behavior

The select shows as unknown until the flow sends it an option.

**Input not wired:** the node confirms each choice itself, and the compile warns about it, as for
[ha switch](ha-switch.md#behavior).

## Errors

- **Home Assistant sends something that isn't one of the options.** The console shows
  `ts_ha: <node id> ignored command ...`, and nothing is sent.
- **The input's `payload` isn't one of the options.** The node raises an error naming the value and the options.

These stop the compile: no **ha device** in the flow, an empty name, no options, an option listed twice.
