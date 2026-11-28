# How home-assistant works

For someone writing their own custom nodes, who wants a real multi-node example to copy from. This set is seven
nodes that make a board a Home Assistant device over MQTT, and it's built only from what the ThingStudio user
guide documents. Read it beside the guide's [Writing custom nodes](https://docs.thingstudio.net/custom-nodes/)
page: each part below names the section it follows.

## What it does

One `ha device` node announces the board to Home Assistant (device discovery, availability, offline will), and
each entity node (`ha sensor`, `ha binary sensor`, `ha switch`, `ha number`, `ha select`, `ha button`) is one
Home Assistant entity: it shows a state Home Assistant sends, and (except sensors) it acts on commands Home
Assistant sends. The user's view (install, setup, use, failures, examples) is the bundle's
[README](../home-assistant/README.md); the wire contract, with every message and error pinned, is
[SPEC.md](SPEC.md).

## The files

The bundle, `home-assistant/home-assistant/`, is what a user copies into `~/.thingstudio/custom-nodes/`. Because
it's a folder, it's a **bundle**: it loads whole or not at all, and its `lib/` travels with it (*Bundles*).

| File | Job | User guide |
|---|---|---|
| `ha_device.node.json` / `.node.py` / `.compile.py` | the device: joins the flow's WiFi and MQTT broker, sends the discovery message and the availability, waits for HA's own status | *The descriptor* (`configRef`, `singleton`, `target`), *Compile time* (`referencedConfigs`), *The flow's WiFi: `ts_wifi`*, *The flow's MQTT client: `ts_mqtt`*, *Event-driven sources* |
| `ha_sensor.node.json` / `.node.py` / `.compile.py` | an input-only entity: publishes each message's payload as the state | *The behavior*, *Compile time* |
| `ha_binary_sensor.…` | as `ha sensor`, but on/off; its on-start value goes out at the first connect | as above |
| `ha_switch.…`, `ha_number.…`, `ha_select.…` | two-faced entities: the input publishes the state, the output carries HA's commands (and the on-start value once) | *Two-faced nodes* |
| `ha_button.node.json` / `.node.py` / `.compile.py` | an output-only entity: one message per press in Home Assistant | *Event-driven sources* |
| `lib/ts_ha.py` | the board side of the SPEC, shared by every node: discovery, states, commands, the record of removed entities | *Your own libraries*, *Bundles* |
| `examples/*.flow.json` | three flows: any WiFi board, the kitchen-sink C3, the Freenove S3 display board | |
| `docs/*.md` | one page per node | |
| `README.md` | the user docs | |

`ha_*.compile.py` files say at the top that they are **generated**: `tools/build-hooks.py` writes each one
from `hooks/<name>.py`, expanding `#@include common.py` (the shared hook code, once) and, for `ha device`,
`#@include-lib ts_ha.py BUNDLE_VERSION COMMANDABLE build_discovery` (the board-side discovery functions,
verbatim, so the hook and the board run the same code for the 4 KB check). A hook is one sandboxed file and the
guide doesn't say it may import (*Compile time*), so code seven hooks share can't be a library they all import —
it is inlined instead, and the generator keeps the one copy honest.

Development only, never copied: `THINGSTUDIO_VERSION` and `test/MICROPYTHON_VERSION` (the pinned builds, by full
commit), `test/` (`setup.sh` builds both pins; `compile_test.py`, `vectors_test.py`, `mqtt_test.py`, and
`doubles/`), `tools/` (`build-hooks.py`, `ha-probe.py`, `ha-cleanup.py`), `hooks/` (the hook sources), and `docs/`
(SPEC, vectors, this page, the working notes).

## Walkthrough

### The descriptor

`ha switch` is the richest: a two-faced node (*Two-faced nodes*), one input, one output, three functions in the
Python.

```json
"kind": "sink",
"eventSource": true,
"ports": { "inputs": [{ "name": "msg", "type": "any" }], "outputs": [{ "name": "msg", "type": "bool" }] },
```

The output's type is what a command becomes in the flow (`bool` for a switch, `number` for a number, `string`
for a select); the input is `any` because whatever upstream is wired in is valid by the time it arrives, and
`ts_ha` errors on a value the entity can't show.

Most properties are plain — `name` (the entity's name in Home Assistant), `deviceClass`, `min`/`max`/`step`
(number), `options` (select, one per line) — each with a `default` and a `help` line the property panel shows.
Two are worth knowing:

```json
{ "name": "nodeId", "label": "node id", "kind": "nodeId", "default": "" }
```

gives the node's Python its own flow id, which is the key for everything (*The descriptor*, `nodeId`): topics,
the entity's unique id, the settings store. The compile hook checks it against
`[A-Za-z0-9_-]{1,32}` because it goes into MQTT topics.

Only `ha device` holds config nodes: its **WiFi** and **MQTT Broker** fields are `configRef` with
`singleton: true` (*Sharing a config*), so every entity in the flow shares the board's one network and one
broker without asking again. The `target` property is how `ha device` names the board in Home Assistant
(*The descriptor*, `target`).

### The compile hook

What the hook does, per entity (*Compile time*):

1. Refuses a flow with no `ha device` (`'ha switch needs an ha device node in the flow'`).
2. Builds the component dict of SPEC §4 — `p`, `name`, and the type's options — validating as it goes (a
   temperature sensor's unit against the allowed set, a number's min/max/step, a select's options).
3. Resolves **on start** (SPEC v1.2): `off`/`on` to `False`/`True`, a number's start text to a value inside
   min..max, a select's to one of the options, `restore` to the word itself, else a named compile error.
4. For the two-faced nodes, works out `echo` from `ctx['node']['wired']`: input unwired means the node
   confirms each command itself (SPEC §3). No warning either way, as of v1.2.

`ha device`'s hook goes further, because it's the only node that may touch credentials (*The flow's WiFi:
`ts_wifi`*): it reads the WiFi and broker configs from `ctx['referencedConfigs']` and returns `ssid`,
`wifiPassword`, `security`, `deferToMqtt` for the WiFi and `broker`, `port`, `username`, `brokerPassword` for
the broker. It refuses an `unmanaged` WiFi (the MQTT client manages the connection), checks every `ha/` node's
id against the topic charset, and — building the discovery message for the whole flow with the board's own
`build_discovery` (inlined by the generator) — refuses a flow whose message would be over the 4 KB the board
can send (SPEC §8).

### The node's Python

`ha switch`, all of it:

```python
import ts_ha

ts_ha.register(properties['nodeId'], properties['component'], properties.get('start'))
_last = {'value': None, 'started': False}


async def run(msg, properties):
    await ts_ha.publish_state(properties['nodeId'], msg.get('payload'))


async def wait(properties):
    if not _last['started']:
        _last['started'] = True
        value = await ts_ha.start(properties['nodeId'], properties['echo'])
        if value is not None:
            _last['value'] = value
            return
    _last['value'] = await ts_ha.command(properties['nodeId'], properties['echo'])


async def emit(properties):
    return {'payload': _last['value'], 'topic': properties['name']}
```

Follow a message both ways:

- **HA → board.** `wait` is awaited until an event fires (*Two-faced nodes*). `ts_ha.command` waits on the
  flow's one MQTT client (*The flow's MQTT client: `ts_mqtt`*): `client.wait_message` returns the next message
  for this node id, `command_value` turns `ON` into `True` (ignoring anything else, with a console line), and —
  with `echo` — the accepted command is published back as the state. `emit` then puts the value on the output,
  with `topic` set to the entity's name so one downstream node can tell several entities apart (SPEC v1.2 §3).
  The first call instead runs `ts_ha.start`: the on-start value, once, as if HA had sent it (SPEC v1.2).
- **Board → HA.** Anything wired into the input arrives at `run`; `publish_state` turns it into text
  (`state_payload`, SPEC §3) and publishes it retained at QoS 0 on the entity's state topic. For an entity whose
  on start is `restore` it also keeps the value under the node's id in `runtime.settings` (*Persisting values*) —
  one write per changed value, compared against the RAM mirror — which is what `restore` reads back; no other
  entity writes the store.

`ha device`'s Python does the one-time setup: `ts_wifi.ensure_station(...)` with the four values its hook
returned, `ts_mqtt.ensure_client(...)` for the flow's broker, `client.set_will(availability, b"offline", ...)`
before anything connects, `client.on_connect(...)` for the per-connect work, and
`ts_ha.configure_device(...)` (*The flow's MQTT client: `ts_mqtt`*). The model name Home Assistant shows comes
from the descriptor's `target`-kind property (*The descriptor*, `target`): the board dict at runtime. Its
`wait`/`emit` then report HA's own `online`/`offline` on the status topic.

### The library

`lib/ts_ha.py` holds what every node shares, so no state is per-node-file (*Your own libraries*; the guide's
per-instance wrapper would give two instances of the same node two libraries, not one):

- **One device per flow.** `configure_device` raises on a second; entities register themselves, in any order
  (a node may set up before `ha device`).
- **Availability.** The will is set at setup; on every connect, `online` (retained, QoS 1), then the discovery
  message; on the *first* connect of the flow, `None` on the state topic of every entity the flow hasn't
  reported yet, so Home Assistant shows unknown rather than the previous flow's value (SPEC v1.1 §3/§5) — except
  a binary sensor's on-start value, which the connect publishes instead (SPEC v1.2: a binary sensor has no
  output of its own to start from).
- **Removed entities (SPEC §7).** A record file, `ha_entities.json`, keeps the components last announced; on
  connect, each one no longer in the flow goes out as a `{"p": …}` stub, Home Assistant's documented way to
  remove one component. Omitting a component does **not** remove it (checked on Mike's HA, SPEC §10).
- **HA restarts (SPEC §6).** HA publishes `online` on its status topic; the board waits a random 1–5 s (HA's
  advice) and republishes discovery.

The pure functions — `build_discovery`, `state_payload`, `command_value`, `start_value` — take values and
return values or raise; everything with a socket or the settings store is async and thin around them. That split
is what the tests run.

## Design decisions

- **One device node, many entity nodes.** Home Assistant's device-based discovery groups entities under one
  device with one availability topic; so does the flow. The device holds the credentials and the will; the
  entities hold the protocol values.
- **The chip id, not the hostname, keys everything** (SPEC §1, decision 8). Renaming the board changes only the
  device name Home Assistant shows; the entity ids survive.
- **The hook builds the component dict; `ts_ha` adds the ids and topics and serialises.** The split keeps the
  per-type validation next to the properties it validates, and lets `ha device`'s hook run the board's own
  `build_discovery` for the 4 KB check at compile time.
- **Echo without a warning.** An unwired two-faced input means "the command is the state" (an LED). v1.1
  warned; v1.2 doesn't — the README and node pages say when to wire the real state back instead (a relay with a
  feedback contact, a thermostat).
- **On start is a property, not a startup node wired into the flow.** The start value travels with the entity
  (SPEC v1.2): it goes out on the two-faced output once at flow start, is published as the state when the input
  is unwired, and `restore` reads it back from `runtime.settings` — which a wired startup node couldn't do.
- **Unknown until reported.** A retained `None` at the first connect clears the last flow's value; it's skipped
  for anything the flow already reported, including a start value.
- **Every failure is named.** `ValueError` out of the pure functions becomes a node error attributed to the
  node; console lines (`ts_ha: <node id> ignored command …`) name the id and the value. The wording is pinned
  in the SPEC and checked by the tests, so a change is deliberate.
- **No state is read from Home Assistant.** The nodes cover the board's own entities only (SPEC, limits);
  reading other entities is not this bundle's job.

## Testing

From the repository root, after `bash home-assistant/test/setup.sh <work folder>` has built the pinned builds
(v0.14.0 and MicroPython v1.29.0, both by full commit; see each script's header for the exact command):

- **Compile** (`test/compile_test.py`, 33 cases): flows through an installed ThingStudio's `thingstudio-compile`
  (user guide, [Check a flow without the editor](https://docs.thingstudio.net/check-a-flow/)), with the bundle
  in a scratch custom-nodes folder the way a user installs it. It first runs `build-hooks.py --check`, so the
  generated hooks are part of the test. The cases cover the three example flows, every entity type wired and
  unwired, the hook's errors (no device, bad ids, bad units, an on start that doesn't fit, over 4 KB), and the
  boards each example needs.
- **Vectors** (`test/vectors_test.py`, 48 checks): `ts_ha`'s pure functions against `docs/vectors/`
  (`discovery.json`: device and components → topic and parsed payload; `values.json`: flow value → state text,
  command payload → flow value), run under CPython and the pinned MicroPython. MicroPython is the one that
  counts: it's what the board runs.
- **MQTT side** (`test/mqtt_test.py`, 42 checks): `ts_ha` and `ha device` against doubles of `ts_mqtt`,
  `ts_wifi` and `runtime` (`test/doubles/`), written from the user guide only — *The flow's WiFi: `ts_wifi`*,
  *The flow's MQTT client: `ts_mqtt`*, *Persisting values* — with `reset()` for a redeploy and hooks to inspect
  what went out. The checks are the wire contract: the will set before connecting, bytes payloads, QoS 0 and 1
  where the SPEC says, subscribing after `ensure_connected`, every call under the right node id, the on-start
  and restore paths.
- **On Mike's Home Assistant** (`tools/ha-probe.py`, SPEC §10): discovery, removal, availability, commands and
  the `None`-as-unknown check against the real integration, as a fake board. `tools/ha-cleanup.py` removes the
  probe's device afterwards.
- **The board pass** (kitchen-sink C3, and the Freenove S3): the 1.9 checklist in the working notes, plus the
  SPEC v1.2 checks — after a redeploy and a reboot, Home Assistant shows the start values, and `restore` comes
  back with the last value, without anyone pressing anything.

## Making your own from this

For a set that speaks a protocol to a server over MQTT — Home Assistant, but it could be anything with
discovery-like JSON:

1. Copy the bundle folder; rename it and the node files; give the descriptors new `type`s in your own namespace
   (`yourset/yournode` — `ha/` is this set's).
2. Keep the shape: one config node that holds the server's credentials (its `configRef`s are `singleton`, its
   hook resolves them from `referencedConfigs`), entity nodes that register with a shared `lib/`, and the
   two-faced pattern for anything both settable and reporting.
3. If more than one node shares hook code, don't paste: keep one copy in `hooks/` and a generator, the way
   `tools/build-hooks.py` does it (and keep the board-side functions the hook needs inlined with
   `#@include-lib`, so compile time and the board run the same code).
4. Write the SPEC first: the wire messages, the failure wording, the limits — and vectors for every pure
   function in the day.
5. Double the client you can't run in a test (from the user guide only), and test the wire contract against the
   double; test against the real server with a probe tool that leaves no trace.
6. Give every property a `help` line and every node a `docs/` page; the editor shows the first two, the docs
   carry the rest.

If you need something the user guide doesn't document, that's a gap in ThingStudio, not something to work
around: file it as a core request instead.
