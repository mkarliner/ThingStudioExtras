# ha select

A list of options in Home Assistant. Sends the option chosen there, and shows the current option you send it.

Needs an **ha device** node in the flow.

## Properties

- **name**: the entity's name in Home Assistant. Required.
- **options**: one option per line, each different. Blank lines and spaces around an option are ignored.
- **on start**: a start value, one of the **options**, `unknown`, or `restore` (the last value it showed).
  Default `unknown`.

## Wiring

**Output**: one message each time an option is chosen in Home Assistant, and once at flow start when **on start**
is a start value (as if Home Assistant had sent it):

| Field | Value |
| --- | --- |
| `payload` | the option, as text |
| `topic` | the entity's name, so one node can tell several entities apart |

**Input**: the current option. It must be one of **options**. `None` sends nothing. The input takes any type, so a
function node's result can be wired straight in.

## Behavior

With **on start** `unknown` (the default), the select shows as unknown until the flow (or the echo below) sends it
an option. With a start value, it goes out on the output once at flow start so the downstream flow can act on it;
when the input isn't wired it is also published as the state. With `restore`, the select starts from the last
option it showed, kept on the board; with nothing stored yet it behaves as `unknown`.

**Input not wired:** the node confirms each choice itself: Home Assistant shows the option as chosen as soon as
it's picked, whether or not anything happened. That's the right choice when the choice is the state. When the
real option can differ from the command, wire the current option back to the input.

## Errors

- **Home Assistant sends something that isn't one of the options.** The console shows
  `ts_ha: <node id> ignored command ...`, and nothing is sent.
- **The input's `payload` isn't one of the options.** The node raises an error naming the value and the options.

These stop the compile: no **ha device** in the flow, an empty name, no options, an option listed twice.
