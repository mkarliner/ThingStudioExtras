# wake on lan (`wol`)

A Wake-on-LAN node for ThingStudio: it sends a magic packet to the MAC address that arrives in each
message's payload, so the target to wake is per-message and nothing else on the board has to know it.

## Install

Copy this folder into `~/.thingstudio/custom-nodes/`. The node appears in the palette under
**network**; it needs a board with the `wifi` capability (on other boards the palette grays it out
and the compile refuses it).

ThingStudio App v0.14.0 or newer — the release in which the user guide documents a custom node's use of the
flow's WiFi (custom-nodes, "The flow's WiFi: ts_wifi").

## Use

Wire anything that produces a dict payload into the node's input (a `function` node is the usual
producer):

| payload entry | required | meaning |
|---|---|---|
| `mac` | yes | the target's MAC address, e.g. `AA:BB:CC:DD:EE:FF`. Dash-, dot- or separator-less forms work too; case-insensitive. |
| `ip` | no | the destination IPv4 address. Absent (or empty), the packet goes to the broadcast `255.255.255.255`. |

Any other keys in the payload dict ride along and are ignored.

The packet — six `0xFF` bytes, then the MAC sixteen times, 102 bytes — is sent as one UDP datagram to
the destination on the node's **port** (default 9; some machines listen on 7), **repeats** times
(default 1; broadcasts can be dropped, 3 is a common choice).

## Behaviour and failures

The node joins the flow's one WiFi network like every network node (its **WiFi** field). It checks
the connection before sending:

- **The payload is not a dict with `mac`** — the node fails, naming what it got.
- **The MAC or the destination is not in a usable form** — the node fails, naming the value and the
  form wanted.
- **The flow's WiFi is not connected** — the node fails, saying so.
- **The board's network stack refuses the send** — the node fails as `wol: send to <ip>:<port> failed: …`,
  as the built-in `udp send` reports its failures.

UDP has no acknowledgement: a send that succeeds means the board handed the datagram to the network
stack, not that the target woke.

## Example flows

- `examples/wol-wake.flow.json` — a timer builds the payload dict and wakes one machine (unicast to its
  IP; drop the `ip` entry to wake on the whole network).
- `examples/wol-loopback.flow.json` — a self-test: the node wakes the board itself, and a `udp receive`
  on the same port feeds the received datagram, as hex, to a debug node. Every 10 s the console should
  show 204 hex characters: `ffffffffffff` + the MAC 16 times. Open it, pick your WiFi config, deploy.
