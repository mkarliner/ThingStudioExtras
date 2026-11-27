# Wake on LAN node — SPEC (v1)

The contract of the `wol` node with the outside world. Read this before changing anything it defines;
run the vectors in the same change; change the spec only with Mike's permission in the session.

The node is a `sink`: one input, no output. UDP has no acknowledgement (user guide, udp send), so the
node reports nothing on success; every failure is a named node error.

## 1. Message contract

Input: any message whose `payload` is a dict.

| entry | required | meaning |
|---|---|---|
| `mac` | yes | the target's MAC address, a string. Six byte pairs, hex, case-insensitive; the separator is a colon, a dash, a dot, or none: `AA:BB:CC:DD:EE:FF`, `aa-bb-cc-dd-ee-ff`, `aa.bb.cc.dd.ee.ff`, `AABBCCDDEEFF`. |
| `ip` | no | the destination IPv4 address, a string (`192.168.1.50`). Absent, empty or whitespace: the packet goes to the broadcast `255.255.255.255`. Present: unicast to that address. |

Any other keys in the payload dict ride along and are ignored (node conventions). `topic` and the
node's own state are not put in the message; the node produces none.

## 2. The magic packet

Six `0xFF` bytes, then the MAC address sixteen times — 102 bytes, built by `magic_packet` in
`lib/wol_packet.py`. Sent as one UDP datagram per send.

## 3. Destination and port

- Destination: §1.
- Port: the node's **port** property, an integer 1–65535, default 9. 9 is the Wake-on-LAN default;
  some machines listen on 7 (help text says so).
- Repetition: the node's **repeats** property, an integer 1–10, default 1. The same datagram is sent
  that many times; broadcasts can be dropped (help text says 3 is a common choice).

## 4. Node properties

| name | kind | default | notes |
|---|---|---|---|
| `port` | number | 9 | min 1, max 65535 |
| `repeats` | number | 1 | min 1, max 10 |
| `wifi` | configRef | — | `thingstudio/config/wifi`, `singleton: true`; the flow's one WiFi network, as every network node's **WiFi** field |

`requires: {"capabilities": ["wifi"]}`: on a board without the `wifi` capability the palette grays the
node out and the compile refuses it, naming the missing capability.

## 5. WiFi

Per the user guide (custom-nodes, "The flow's WiFi: ts_wifi"): the `wifi` field holds only the
credential's name in the node's Python. `wol.compile.py` resolves the flow's one WiFi config from
`ctx["referencedConfigs"]` and returns `ssid`, `password`, `security` (`password`, `open` or
`unmanaged`) and `deferToMqtt` (`True` when any node in the flow holds the flow's MQTT broker config,
worked out as the guide's example does).

Setup: `ts_wifi.ensure_station(ssid, password, security, deferToMqtt)` — joins the flow's WiFi (or
leaves it to the MQTT client when `deferToMqtt`). Before every send the node checks
`isconnected()`; a send that the board's stack refuses is caught and reported (§6).

## 6. Errors

Every message names the node (`wol:` prefix), the figure that names the failure (`%r`/`%s`), and what
the user can do. Wording is pinned: a change is a SPEC change.

| Failure | Where | Message |
|---|---|---|
| payload not a dict, or no `mac` entry | runtime, `run` | `wol: payload must be a dict with a 'mac' entry, got %r` |
| `mac` not a string | runtime, `parse_mac` | `wol: the payload's 'mac' must be a string, got %r` |
| `mac` not six hex byte pairs | runtime, `parse_mac` | `wol: %r is not a MAC address -- 6 byte pairs, hex, e.g. AA:BB:CC:DD:EE:FF` |
| `ip` not a string | runtime, `dest` | `wol: the payload's 'ip' must be a string, got %r` |
| `ip` not an IPv4 address (incl. octets > 255, wrong part count, leading zeros) | runtime, `dest` | `wol: %r is not an IPv4 address, e.g. 192.168.1.50` |
| the flow's WiFi not connected | runtime, `run` | `wol: the flow's WiFi is not connected -- check the flow's WiFi config, or send again once it is up` |
| the stack refuses the send | runtime, `run` | `wol: send to %s:%d failed: %s` (destination, port, the system's error — as `udp send` reports its failures) |
| no WiFi config in the flow | compile, hook | `needs the flow's WiFi -- set "WiFi" in its properties` |

## 7. Vectors

`vectors/values.json`: `mac` (parse → hex bytes, or the exact error), `dest` (value → destination
string, or the exact error), `packet` (MAC → the full 102-byte packet in hex). Run in the same change
as any move of §1–§6:

```
python3 wake-on-lan/test/vectors_test.py
MICROPYPATH=wake-on-lan/wake-on-lan/lib micropython wake-on-lan/test/vectors_test.py
```

from the repository root (CPython 3, and the pinned MicroPython's unix port — the board code is
MicroPython, so the CPython pass alone is not the check). The compile hook and the descriptor are
checked by `thingstudio-compile` against `examples/` flows (see the continuation briefing).
