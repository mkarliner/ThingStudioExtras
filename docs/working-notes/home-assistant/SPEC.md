# ThingStudio ↔ Home Assistant over MQTT — SPEC v1

**Status: frozen v1, 2026-11-25 (Mike).** Checked on Mike's HA (§10). v1.1 (2026-11-25, Mike's permission): a
state is unknown until the running flow reports it (§3, §5). Phase 1 task 1.1 of
`../home-assistant-implementation-plan.md` (decision 7: the HA contract has its own spec, with vectors; Mike's
permission for this spec is in the plan). After freezing, a change needs Mike's permission, like every ThingStudio
interface spec.

Sources: HA's MQTT integration docs (device-based discovery, removal, birth and last will, abbreviations), read
2026-11-25: <https://www.home-assistant.io/integrations/mqtt/>.

Who implements it: `home-assistant/lib/ts_ha.py` (the board side) and the `ha_*` nodes' compile hooks (which build
each component dict). Conformance: `vectors/` (§9).

## 1. Ids

| Name | Value | Example |
|---|---|---|
| chip id | `machine.unique_id()` as lower-case hex, no separators | `a0b1c2d3e4f5` |
| device id | `ts_` + chip id | `ts_a0b1c2d3e4f5` |
| node id | the flow node's id. Must match `[A-Za-z0-9_-]{1,32}`: it goes into topics and HA ids (compile error otherwise) | `7` |
| entity unique id | device id + `_` + node id | `ts_a0b1c2d3e4f5_7` |

The chip id, not the hostname, keys everything (decision 8): renaming the board changes only the device name HA
shows. Deleting a node and adding a new one gives a new node id, so a new HA entity.

## 2. Topics

`<base>` is `thingstudio/<chip id>`. `<prefix>` is the discovery prefix, default `homeassistant` (`ha_device`
setting).

| Topic | Direction | Payload | Retain | QoS |
|---|---|---|---|---|
| `<prefix>/device/<device id>/config` | board → HA | discovery message (§4) | yes | 1 |
| `<base>/availability` | board → HA | `online` / `offline` (§5) | yes | 1 |
| `<base>/<node id>/state` | board → HA | state (§3) | yes | 0 |
| `<base>/<node id>/set` | HA → board | command (§3) | (HA's choice; not retained by default) | board subscribes at 1 |
| `<prefix>/status` | HA → board | `online` / `offline` (§6) | | board subscribes at 0 |

States are retained so that HA, restarting while the broker stays up, shows the last value at once.

## 3. Entity types and payloads

| Node | `p` | State payload (flow value → text) | Command payload (HA → flow value) |
|---|---|---|---|
| `ha_sensor` | `sensor` | int: decimal text; float: shortest round-trip text, no exponent for 1e-6 ≤ abs < 1e15; str: as is; bool: node error (use `ha_binary_sensor`) | none |
| `ha_binary_sensor` | `binary_sensor` | truthy → `ON`, falsy → `OFF` | none |
| `ha_switch` | `switch` | truthy → `ON`, falsy → `OFF` | `ON` → `True`, `OFF` → `False`, anything else ignored with a console line |
| `ha_number` | `number` | int or float as for `sensor`; anything else node error | text → float; an int when the step is a whole number and the value is whole; outside min..max ignored with a console line |
| `ha_select` | `select` | must be one of the options, else node error | must be one of the options, else ignored with a console line |
| `ha_button` | `button` | none | `PRESS` → `True` |

For every state: a flow value of `None` publishes nothing.

**Unknown until reported (v1.1).** When a flow starts, each entity with a state shows as unknown in HA until the
flow (or the echo) reports one. The board does this by publishing the text `None` (retained, QoS 0) on the state
topic, which HA shows as `unknown` for every type above (§10, check 7). Without it, HA and the broker keep the
previous flow's last value, e.g. a switch shown on while the new flow has just started with the LED off.

**Unwired input** on `ha_switch`, `ha_number`, `ha_select` (decision 9): the board publishes each accepted command
back as the state, as if the flow had confirmed it. The compile warns.

## 4. Discovery message

One retained message per board on `<prefix>/device/<device id>/config`, using HA's abbreviated keys. JSON compared
as parsed objects, not bytes.

```json
{
  "dev": {"ids": ["ts_a0b1c2d3e4f5"], "name": "kitchen", "mdl": "ESP32-C3 SuperMini", "mf": "ThingStudio",
          "sw": "15.1.0", "sa": "Kitchen"},
  "o": {"name": "ThingStudio", "sw": "0.1.0"},
  "avty_t": "thingstudio/a0b1c2d3e4f5/availability",
  "cmps": {
    "7": {"p": "sensor", "name": "Temperature", "uniq_id": "ts_a0b1c2d3e4f5_7",
          "stat_t": "thingstudio/a0b1c2d3e4f5/7/state", "dev_cla": "temperature", "unit_of_meas": "°C",
          "stat_cla": "measurement"},
    "9": {"p": "switch", "name": "Lamp", "uniq_id": "ts_a0b1c2d3e4f5_9",
          "stat_t": "thingstudio/a0b1c2d3e4f5/9/state", "cmd_t": "thingstudio/a0b1c2d3e4f5/9/set"}
  }
}
```

- `dev.name`: `ha_device`'s device name, default the board's hostname. `dev.mdl`: the board definition's name.
  `dev.sw`: the device runtime version. `dev.sa`: the area, omitted when empty.
- `o.name` is `ThingStudio`; `o.sw` is the HA bundle's version. `o` is required: HA creates nothing without it
  (§10).
- `avty_t` at the root applies to every component (`online`/`offline` are HA's defaults, so no `pl_avail`).
- `cmps` is keyed by node id. Each component has `p`, `name`, `uniq_id`, and `stat_t` (all but `button`) and
  `cmd_t` (`switch`, `number`, `select`, `button`). Per type, when set:
  - `sensor`: `dev_cla`, `unit_of_meas`, `stat_cla`, `ic`
  - `binary_sensor`: `dev_cla`
  - `switch`: `dev_cla` (`outlet` or `switch`)
  - `number`: `min`, `max`, `step`, `unit_of_meas`, `mode` (`slider` or `box`)
  - `select`: `ops` (non-empty list of unique strings)
  - `button`: nothing more
- The compile hooks build each component dict (validated); `ts_ha` only adds the ids and topics and serialises.

**When it is sent:** after every connect (§5), and again after HA's `online` on `<prefix>/status` (§6).

## 5. Availability

- Will (set before the first connect): `offline`, retained, QoS 1, on `<base>/availability`.
- On every connect, in order: `online` (retained, QoS 1) on `<base>/availability`, then the discovery message.
- On the first connect after the flow starts (not on later reconnects, which keep this flow's states): `None` on the
  state topic of every entity with a state that the flow hasn't reported yet (§3).
- The board is subscribed to its command topics and `<prefix>/status`. On a reconnect `ts_mqtt` restores those
  subscriptions before the two publishes; nothing depends on the order, since command topics are not retained.

## 6. HA restarts

HA publishes `online` on `<prefix>/status` when it starts. On `online` the board waits a random 1–5 s (HA's advice,
to spread the load) and republishes the discovery message. `offline` changes nothing on the board except the
`ha_device` node's output.

## 7. Removed entities (decision 10)

The board keeps a record file `/ha_entities.json`: `{"device": "<device id>", "cmps": {"<node id>": "<p>", ...}}`,
the components it last announced. On connect, each node id in the record but not in the flow is added to that
discovery message's `cmps` as `{"p": "<p>"}` (HA's documented way to remove one component). Once that message is
published, the record is rewritten with the current set, so the next discovery message omits them. The file is
written only when the set changes.

A flow with no HA nodes does nothing: the device stays in HA until deleted there (documented). An empty retained
payload on the discovery topic removes the whole device (`tools/ha-cleanup.py` uses that).

Checked (§10): omitting a component does **not** remove it; the `{"p": …}` stub does. So the record stays.

## 8. Limits

- Discovery message: at most 4 KB serialised (the C3 has to build and send it). The compile errors above that.
- One `ha_device` per flow; every `ha_*` node needs it.

## 9. Conformance vectors

`vectors/discovery.json`: a device and a set of components (plus a record) → the expected topic and parsed payload.
`vectors/values.json`: entity type and flow value → payload or "nothing" or "error"; command payload → flow value
or "ignored". `ts_ha`'s tests in Extras run both under MicroPython.

## 10. Checked on Mike's HA (1.2, 2026-11-25)

`tools/ha-probe.py` against Mike's HA and broker, as a fake board `ts-test-probe`:

1. The abbreviated device-discovery message (§4) created one device with all six entity types, with the right
   names, device classes, units and options. Entity ids came out as `<platform>.ts_test_probe_<name>`.
2. `o` is enforced: the same message without it created nothing.
3. Removal: omitting a component left it in HA; the `{"p": …}` stub removed it (§7 stands).
4. An empty retained payload on the discovery topic removed the device and its entities.
5. `offline` on the availability topic made every entity `unavailable`; `online` restored the states.
6. Commands from HA (`switch.turn_on`/`turn_off`, `number.set_value`, `select.select_option`, `button.press`)
   arrived on `<base>/<node id>/set` as `ON`, `OFF`, `42`, `on`, `PRESS`, as §3 says.

7. A state of `None` made HA show `unknown` for sensor, binary_sensor, switch, number and select. An empty retained
   message on the state topic changed nothing in HA (it only clears the broker's copy), so it can't be used for this.

Not covered by the probe, left for the hardware pass (plan 1.9): retained states after an HA restart with the
board off, and the `<prefix>/status` republish.
