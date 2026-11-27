# How wake-on-lan works

For someone writing their own custom nodes. This set is one node, `wol`, small enough to read start to finish, and
built only from what the ThingStudio user guide documents. Read it beside the guide's
[Writing custom nodes](https://docs.thingstudio.net/custom-nodes/) page: each part below names the section it
follows.

## What it does

`wol` is a sink. Each message's payload names a computer by its MAC address, and the node sends that computer a
Wake-on-LAN magic packet over the flow's WiFi. The user's view (install, payload, failures, example flows) is the
bundle's [README](../wake-on-lan/README.md). The contract, with every error message word for word, is
[SPEC.md](SPEC.md).

## The files

The bundle, `wake-on-lan/wake-on-lan/`, is what a user copies into `~/.thingstudio/custom-nodes/`. Because it's a
folder, it's a bundle: it loads whole or not at all, and its `lib/` travels with it (*Bundles*).

| File | Job | User guide |
|---|---|---|
| `wol.node.json` | the descriptor: palette entry, ports, properties, the board capability it needs | *The descriptor: `<name>.node.json`* |
| `wol.compile.py` | runs in the editor at compile time: turns the flow's WiFi config into values the board can use | *Compile time: `<name>.compile.py`*, and *The flow's WiFi: `ts_wifi`* |
| `wol.node.py` | runs on the board: joins the WiFi once, then sends a packet per message | *The behavior: `<name>.node.py`*, *Cleanup* |
| `lib/wol_packet.py` | the pure functions: MAC parsing, the destination, the packet | *Your own libraries*, *Bundles* |
| `examples/*.flow.json` | a flow that wakes a machine, and a loopback self-test | |
| `README.md` | the user docs | |

Development only, never copied: `THINGSTUDIO_VERSION` (the build the set is tested against, by full commit), `test/`
(builds the pinned ThingStudio and MicroPython, then runs the compile and vector tests), `tools/wol-listen.py` (a
listener on a computer, for checking packets during a board pass), and `docs/`.

## Walkthrough

### The descriptor

```json
"type": "wol/wol",
"kind": "sink",
"requires": { "capabilities": ["wifi"] },
"ports": { "inputs": [ { "name": "msg", "type": "any" } ] },
```

A `sink` takes a message and sends none. `requires` keeps the node off boards that can't run it: the palette grays it
out and the compile refuses it, naming the capability, so the node's own code never has to check. The input is `any`
because the payload is a dict, built by whatever is upstream (usually a `function` node).

The properties are what stays the same for every message: the UDP **port** and how many **repeats**, each with a
`default`, a range and a `help` line that the property panel shows. The third is the WiFi:

```json
{ "name": "wifi", "label": "WiFi", "kind": "configRef",
  "configType": "thingstudio/config/wifi", "singleton": true, "default": "" }
```

With `singleton`, the field refers to the flow's one WiFi config rather than an id the user picks, so `wol` shares
the network every other network node uses. The descriptor's `description` line sits at the top of the property panel.

### The compile hook

The node's Python only sees the WiFi credential's *name*. The SSID and password are resolved in the editor, at
compile time, by `wol.compile.py`, which is the guide's own example (*The flow's WiFi: `ts_wifi`*) with a named
error added:

```python
wifi = (ctx.get('referencedConfigs') or {}).get(wifi_ids[0]) if len(wifi_ids) == 1 else None
if wifi is None:
    return {'errors': ['needs the flow\'s WiFi -- set "WiFi" in its properties']}
...
return {'properties': {'ssid': ..., 'password': ..., 'security': security, 'deferToMqtt': mqtt}}
```

A hook returns data only. `errors` stops the compile with a message the user can act on; `properties` is merged into
what the node's Python receives. `deferToMqtt` is true when another node in the flow uses the flow's MQTT broker, in
which case the MQTT client owns the WiFi connection and `wol` shouldn't start its own.

### The node's Python

Top-level code runs once, when the flow starts, and already has `properties`:

```python
_sta = ts_wifi.ensure_station(properties['ssid'], properties['password'], properties['security'],
                              properties['deferToMqtt'])

_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
runtime.register_cleanup('wol_socket', lambda: _sock.close())
```

The socket is opened once and closed on redeploy by the cleanup (*Cleanup*). Without that, the next deploy can fail
because the old socket still holds the port.

`run` is called for each message. It checks everything before it touches the network, then sends:

```python
async def run(msg, properties):
    payload = msg.get('payload')
    if not isinstance(payload, dict) or 'mac' not in payload:
        raise ValueError("wol: payload must be a dict with a 'mac' entry, got %r" % (payload,))
    target = dest(payload.get('ip'))
    packet = magic_packet(parse_mac(payload['mac']))
    if not _sta.isconnected():
        raise OSError("wol: the flow's WiFi is not connected -- ...")
    ...
            _sock.sendto(packet, (target, properties['port']))
```

A sink's return value is ignored, and an uncaught exception from `run` is reported against the node (*Errors*). So
each failure is just a `raise` with a good message.

### The library

`lib/wol_packet.py` has no imports and no runtime calls: `parse_mac`, `dest` and `magic_packet` take values and
return values or raise. When `wol.node.py` imports it, ThingStudio sends it to the board with the node (*Your own
libraries*). Keeping it pure means the same file runs under CPython and MicroPython's unix port on a computer, with
no board and no doubles of the runtime, which is what the vector tests do.

## Design decisions

- **What varies per message goes in the payload; what doesn't goes in properties.** The MAC is per message, so one
  node can wake any machine and nothing else on the board has to know the target. The port and the repeat count are
  properties.
- **Extra payload keys are ignored**, as the user guide's
  [Node conventions](https://docs.thingstudio.net/node-conventions/) ask, so the node fits into existing flows.
- **No output.** UDP has no acknowledgement (user guide, *udp send*), so a "sent" message would claim more than the
  node knows. Success is silence; every failure is a named node error.
- **Validate first, then use the network.** Bad input fails the same way whether or not the WiFi is up.
- **Every failure message says what happened, names the value, and says what to do**, with a `wol:` prefix. The
  exact wording is in SPEC §6 and checked by the vectors, so a change to a message is a deliberate change.
- **Broadcast by default.** With no `ip`, the packet goes to `255.255.255.255`, which wakes a machine whose address
  you don't know. Whether every board's network stack accepts that is the open question for the board pass.
- **Accept the MAC in the forms people copy it in**: colons, dashes, dots or none, any case.

## Testing

From the repository root, after `bash wake-on-lan/test/setup.sh <work folder>` has built the pinned toolchains (see
the header of each script for the exact command):

- **Vectors** (`test/vectors_test.py`): the library against `docs/vectors/values.json`, which covers MAC forms, bad
  MACs, destinations and the full packet, with the exact error messages. It runs under CPython and the pinned
  MicroPython. MicroPython is the one that counts, because it's what the board runs.
- **Compile** (`test/compile_test.py`): flows through an installed ThingStudio's `thingstudio-compile` (user guide,
  [Check a flow without the editor](https://docs.thingstudio.net/check-a-flow/)), with the bundle loaded as a user
  installs it. It checks a good flow, the hook's error when there's no WiFi, the refusal on a board without WiFi, and
  that both example flows compile cleanly.
- **Board pass:** not yet done. The loopback example (the board wakes itself and prints what it received) and
  `tools/wol-listen.py` are what it uses. The runbook is in `docs/working-notes/continuation-briefing.md`.

## Making your own from this

For a node that sends something over the network on each message:

1. Copy the bundle folder, rename it and the `wol.*` files, and give the descriptor a new `type` in your own
   namespace (`yourset/yournode`).
2. Keep the `wifi` property and `wol.compile.py` as they are: they're how any node joins the flow's WiFi.
3. Put the logic you can test without a board in `lib/`, pure, and write vectors for it.
4. In `run`, check the payload, then the connection, then act; raise one named error per failure.
5. Close anything you open at top level with `runtime.register_cleanup`.
6. Copy `test/compile_test.py` and change its cases to your node's errors and examples.

If you need something the user guide doesn't document, that's a gap in ThingStudio, not something to work around:
ask for it.
