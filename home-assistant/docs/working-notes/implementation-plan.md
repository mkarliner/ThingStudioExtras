# Home Assistant integration — implementation plan

**Status: agreed shape, 2026-11-24.** Written with Mike after a question-by-question pass over
`scoping.md` (the brief). This plan supersedes the brief's open questions; the brief stays
as the background and the reasoning. Phase 0 and Phase 1 are planned task by task; later phases are milestones,
planned in detail when they start.

**Progress, 2026-11-27:** Phase 1 tasks 1.1 to 1.8, 1.10 and 1.11 done, except the ThingStudio pointer in 1.10
(a docs request, not filed until 1.9 passes). 1.9, the hardware pass, is partly done; Mike runs the rest end to end.
Status and findings: `phase-1-briefing.md`.

## Decisions (Mike, 2026-11-24)

| # | Decision |
|---|---|
| 1 | **Route:** MQTT discovery first. A time-boxed spike on ESPHome's native API runs alongside (Phase S). |
| 2 | **CYD wall panel** is a separate, later project. Phase 1 has no GUI work and no CYD. |
| 3 | **Dedicated nodes**, one per HA entity type: `ha_sensor`, `ha_binary_sensor`, `ha_switch`, `ha_number`, `ha_select`, `ha_button`, plus an `ha_device` node for device-level settings. |
| 4 | **The HA nodes are custom nodes in the Extras repo**, shipped as one bundle folder. Only on the palette for people who install them. |
| 5 | **User libraries (part A of `user-libraries-and-frozen-builds-scoping.md`) are built in core first**, so the shared HA code is a real library (`ts_ha`), not copied into every node. |
| 6 | **A custom node package can carry its own library:** a bundle is a subfolder of `custom-nodes/` with its nodes and a `lib/`. Mike approved the spec changes: node-descriptor SPEC §3 (bundle layout) and a new library-format spec. |
| 7 | **The HA contract gets its own spec, in Extras:** `home-assistant/docs/working-notes/SPEC.md`, with conformance vectors. |
| 8 | **Topics use the chip ID:** `thingstudio/<chip id>/...`. HA unique ids also use the chip ID. The hostname is the device name HA shows. |
| 9 | **Unwired input on a commandable entity** (switch, number, select): the node echoes the command back as confirmed state, and the compile gives a warning. |
| 10 | **Removed entities:** the board keeps a small record of the entities it last announced and tells HA to remove any that have gone. Dropped if testing shows HA removes missing entities by itself. |
| 11 | **Testing on Mike's own HA**, no Docker. Test boards are named `ts-test-…`; a cleanup script clears their retained messages. |
| 12 | **Hardware pass:** ESP32-C3 first (tightest memory), then the Freenove ESP32-S3 4" (octal PSRAM). Pico W and the no-PSRAM S3s later. |
| 13 | **Inbound service calls in v1**, limited to the node's own bound entity and that entity type's obvious actions; HA-side "allow ThingStudio boards to control entities" switch, as ESPHome has. |
| 14 | **HA offline:** widgets blank to `--` (send `None`). No GUI change. |
| 15 | **First-install route:** already built. ThingStudio Web's Set up a board page (web.thingstudio.net/setup) is the hosted installer; Board settings sets hostname and password. |
| 16 | **Inbound work** goes on a new branch from main and is rebased; only the entity picker overlaps `remote-display-spike`. |

## Shape of the work

```
Phase 0  core prerequisites (ThingStudio)  ──►  Phase 1  outbound discovery (Extras)  ──►  Phase 3  add-on  ──►  Phase 4  inbound + picker
                                                Phase S  native-API spike (parallel) ───────────────┘ (may replace the relay)
Phase 2  first-install path (small, any time)                                                         Phase 5  wall panel (separate project)
```

## How sessions work on this

**Update 2026-11-25 (Mike): Extras is its own project and works as a ThingStudio user.** An Extras session reads only
the user documentation and uses only an installed ThingStudio; anything it needs from core goes through a core request
(`AGENTS.md` in this repo). Phase 0 below was core work, done in the ThingStudio project; it stays here as the record.
Where Phase 1 text below names core files or fixtures, the `AGENTS.md` rule wins.

- **Git writes:** the session hands Mike the exact commands; Mike runs them in Terminal, starting with
  `rm -f .git/index.lock`. Commands are zsh with no comments.
- **Interface specs:** this repo's HA spec: read before implementing, run the vectors in the same change, change only
  with Mike's permission.

## Phase 0 — core prerequisites (ThingStudio repo, branch from main)

Everything here helps any custom-node author, not just HA. It lands as a ThingStudio release that the HA bundle
names as its minimum version.

**0.1 Specs first.**
- New `interfaces/library-format/SPEC.md`: the user libraries folder (`~/.thingstudio/libraries/`) and a bundle's
  `lib/`: one module (`<name>.py`) or package (`<name>/__init__.py` …) per entry; the name is the module name;
  `requires` worked out by scanning imports; refusal rules (shadows a built-in, runtime or firmware module; doesn't
  compile; over the 64 KB file limit); clash rule (same name from two sources: both refused, named in the console).
  Conformance vectors: good module, good package, each refusal, a clash.
- `interfaces/node-descriptor/SPEC.md` §3: the bundle layout. A subfolder of `custom-nodes/` is a bundle, one level
  deep; its node files load as top-level ones do; its `lib/` joins the library list under the library-format rules;
  a bad bundle is skipped whole with a reason; a node `type` clash keeps today's rule (first by name loads, the other
  is reported). Conformance: a bundle loads, a broken bundle is skipped, a library clash between bundles.

**0.2 User libraries (scoping doc part A).**
- Backend: library source list (the user folder, then each bundle's `lib/`), merged after the built-ins in
  `/api/dependencies`, entries marked `"source": "user"`; the sources endpoint the editor precompiles from serves them
  (confirm which: `/api/runtime-sources` today).
- CLI: `thingstudio-compile --libraries <dir>`, and bundles found through `--custom-nodes`.
- Confirm the "nothing changes" claims: the editor resolves/hashes/sends a user entry unchanged; `deps.py` installs a
  user-named module and package (test on the unix port); `DEP_PUT` carries any name (`interfaces/protocol/SPEC.md`).
- Tests: backend (load, refusals, clash, package); editor (a flow whose custom node imports a user library resolves
  and sends it); device runtime on the unix port.
- Docs: `custom-nodes.md` "Libraries you can import" gains "Your own libraries" and "Bundles", and the "can't be sent
  yet" line goes; `thingstudio-folder.md` the new folder; `function.md` one line.

**0.3 Bundles in the loader.** `persisted_store.py` globs `*.node.json` in each folder of `custom_node_dirs` today;
add one level of subfolders, report per bundle, and feed `lib/` into 0.2's source list. Same for the CLI. Tests as
0.1's vectors.

**0.4 `ts_mqtt`: Last Will and a reconnect hook.**
- `set_will(topic, msg, retain, qos)` on the shared client: only before the first connect (an error after); a second,
  different will is a loud error, matching `ensure_client`'s settings rule. mqtt_as already supports a will
  (`config['will']`).
- `on_connect(callback)`: called after the first connect and on every reconnect that `ensure_connected()` detects
  (where it already resubscribes). `ts_ha` uses it to publish `online` and the discovery message again.
- Update `editor/test/fixtures/pymock/mqtt_as.py` and `ts_mqtt.py`; tests in `ts-mqtt.test.ts`. Mention both in
  `custom-nodes.md`. `ts_mqtt` is a flow dependency, not runtime core, so no runtime major bump (check against the
  AGENTS.md bump rules).

**0.5 One "uses MQTT" rule.** Five places list only `mqtt_publish`/`mqtt_subscribe`: `compile-hooks.ts:30`,
`wifi-status.ts` (237, 339), `resource-check.ts:70`, `verify-flow-file.ts:76`, `palette.ts`. Custom HA nodes would
be missed and WiFi managed twice. Replace them with one rule that works inside the sandboxed hooks too: a node
uses MQTT if any of its properties holds the id of a `thingstudio/config/mqtt-broker` config in `flow.configs`.
Tests: a custom node with a broker configRef sets `deferToMqtt`.

**0.6 Release.** Version, changelog, a short briefing. Mike runs the build and tests.

## Phase 1 — outbound discovery (Extras repo)

Repo layout:

```
ThingStudioExtras/
  AGENTS.md, CLAUDE.md               repo-wide rules
  docs/core-requests/                requests to core, from any bundle
  home-assistant/                    everything for this node set; a session normally works inside one such folder
    home-assistant/                  the bundle: this folder is copied into ~/.thingstudio/custom-nodes/
      README.md                      install, minimum ThingStudio version, broker setup
      ha_device.node.json / .node.py / .compile.py
      ha_sensor.…  ha_binary_sensor.…  ha_switch.…  ha_number.…  ha_select.…  ha_button.…
      lib/ts_ha.py
      examples/                      example flows
    hooks/                           shared compile-hook source (see 1.6)
    tools/                           build-hooks, ha-probe, ha-cleanup, test runner
    test/
    docs/working-notes/              scoping.md, implementation-plan.md, briefings, SPEC.md (+ vectors/)
```
(Layout updated 2026-11-26, Mike: one folder per node set, holding the bundle, its tools and its working notes.)

**1.1 The HA spec** (`home-assistant/docs/working-notes/SPEC.md`):
- **Ids.** Device id `ts_<chip id hex>` (`machine.unique_id()`); entity unique id `<device id>_<nodeId>`.
- **Topics.** `thingstudio/<chip id>/availability`; `thingstudio/<chip id>/<nodeId>/state`; `…/<nodeId>/set` for
  commandable entities. Discovery on `<prefix>/device/<device id>/config` (prefix default `homeassistant`).
- **Payloads per type.** sensor: the value as text; binary_sensor and switch: `ON`/`OFF`; number: the number as text;
  select: the option; button: `PRESS`. How flow values convert (truthiness for booleans, numbers to text, `None` →
  not published).
- **Discovery message.** Device-based, abbreviated keys, `dev` (ids, name, model = board name, manufacturer
  ThingStudio, sw = runtime version), `o` (origin), `cmps` keyed by node id. Retained.
- **Availability.** Will: `offline`, retained, on the availability topic; `online`, retained, after every connect.
- **HA restarts.** Subscribe to `<prefix>/status`; on `online`, republish discovery.
- **Removal.** The record of last-announced entities, and the removal entry sent for each one gone (form to confirm
  in 1.2). Deploying a flow with no HA nodes does not clean up; the docs say to delete the device in HA.
- **QoS and retain** per message.
- Vectors: example node sets → the exact discovery JSON; example values → topic and payload; a removal case.

**1.2 Check HA's behaviour on Mike's HA before freezing the spec.** A small CPython script (`home-assistant/tools/ha-probe.py`,
paho-mqtt plus HA's REST API) that publishes the spec's messages and reads back `/api/states` and the device
registry. It answers: the device-discovery key names and whether `o` is required; the exact form of a removal entry;
whether a component missing from a republished `cmps` is removed (this decides whether decision 10's record is
needed); empty payload deleting the device; availability behaviour. Mike runs it: it needs `HA_URL`, `HA_TOKEN` (a
long-lived token from his HA profile) and the broker details in environment variables, never in the repo.

**1.3 `ts_ha` library** (`home-assistant/home-assistant/lib/ts_ha.py`). One module, so its state is shared by every HA node.
- `configure_device(...)` from `ha_device`: names, prefix, broker client; sets the will before the first connect (all
  node setup runs at flow start, before any task connects).
- `register(node_id, component)` from each entity node at setup; `publish_state(node_id, value)`; `commands(node_id)`
  as an async wait for HA commands (per-node routing through `ts_mqtt`'s existing subscription registry).
- On connect (0.4's hook): `online`, then the discovery message, then removals. On `<prefix>/status` = `online`:
  discovery again.
- The removal record: a small JSON file on the board, written only when the entity set changes.
- Cleanup on redeploy through `runtime.register_cleanup`.
- Tests: real MicroPython (unix port) against a broker double written in this repo, checked against the spec
  vectors. Not core's pymock fixtures.

**1.4 `ha_device` node.** A source (`eventSource`) whose output reports HA's own status (`online`/`offline` from
`<prefix>/status`), so a flow can show it or act on it. Settings: device name (default: the board's hostname), area,
discovery prefix, broker and WiFi configRefs. Compile hook: the MQTT/WiFi derivation (as the core MQTT nodes do,
from `referencedConfigs`); exactly one `ha_device` when any `ha_*` node is present (an error), a warning for an
`ha_device` with no entities; unique node ids across all `ha_*` nodes (from `flow.nodes`); board name for `model`.

**1.5 Entity nodes.**

| Node | Kind | Ports | Settings and checks |
|---|---|---|---|
| `ha_sensor` | sink | in: number or text | name, device class, unit (checked against the class), state class, icon |
| `ha_binary_sensor` | sink | in: boolean | name, device class |
| `ha_switch` | sink + eventSource (two-faced) | in: actual state; out: command | name, device class (outlet/switch); unwired input → echo + warning |
| `ha_number` | two-faced | in: actual value; out: value set in HA | name, min, max, step, unit, mode (slider/box); min < max, step > 0; unwired → echo + warning |
| `ha_select` | two-faced | in: current option; out: option chosen | name, options (non-empty, unique); unwired → echo + warning |
| `ha_button` | source (eventSource) | out: pressed | name |

Each hook builds its own abbreviated component dict, validated, so the board only serialises it. The device-class
and unit table is copied from HA's docs and dated.

**1.6 Shared hook code.** Compile hooks can import only the sandbox's built-in modules, so code shared by the seven
hooks (derivation, id checks, the component builder) can't be a library. Keep it once in `home-assistant/hooks/`, generate each
`.compile.py` with `home-assistant/tools/build-hooks.py`, commit the generated files, and have a test fail if they're out of date.

**1.7 Tests in Extras.** Compile tests run the example flows through the installed `thingstudio-compile
--custom-nodes home-assistant/home-assistant` (expected errors and warnings, including the unwired echo warning and a duplicate id),
as the user guide describes. `ts_ha` tests run under the MicroPython unix port with doubles for `ts_mqtt`, `runtime`
and `machine` written here from what `custom-nodes.md` documents; anything the docs don't pin down becomes a core
request. No ThingStudio checkout beside Extras. Mike runs anything that touches the shared folders' `node_modules`.

**1.8 Example flows** (`home-assistant/home-assistant/examples/`): one flow per board using every entity type: a counter or chip
reading into `ha_sensor`, a button into `ha_binary_sensor`, `ha_switch` driving the onboard LED with its state wired
back, `ha_number` driving PWM brightness, `ha_select` and `ha_button` into debug, and one unwired switch to show the
echo.

**1.9 Hardware pass on Mike's HA.** C3 first, then the Freenove S3. Checklist:
- entities appear under one device with the right names, classes and units
- states update; commands round-trip, wired (confirmed) and unwired (echo)
- unplug → `offline` within the keepalive window; plug in → `online`
- restart HA → entities come back with no action on the board; restart the broker → same
- delete a node and redeploy → the entity goes
- rename the board → entities and topics unchanged, device name updated
- deploy a non-HA flow → device stays in HA (as documented)
- C3: log `freeIdfHeapBytes` / `largestIdfHeapBlockBytes` before and after discovery
- `home-assistant/tools/ha-cleanup.py` removes the `ts-test-…` devices afterwards

**1.10 Docs.** In Extras: the bundle README (install by copying the folder; minimum ThingStudio version; setting up
the Mosquitto add-on and MQTT integration; removing a device), and a page per node in the house layout. In
ThingStudio: a short pointer from `custom-nodes.md` and the nodes catalog. Optional: a `coming-from/esphome.md`
page making the drag-and-drop case.

**1.11 Wrap-up.** Briefing in `home-assistant/docs/working-notes/`; update this plan's status.

## Phase S — native API spike (parallel; ThingStudio branch `esphome-native-api-spike`)

Time-boxed: stop when the measurements are in. No production code.

- On the C3 and the Freenove: a plaintext native-API server in MicroPython (hand-written protobuf for the few
  messages needed): hello/connect, device info, list entities, one sensor state, subscribe to one HA entity's state,
  and one action call. Add the board to HA by IP.
- Measure IDF heap and `gc.mem_free()` with WiFi up, serving HA.
- Time the encryption in pure MicroPython (Noise: X25519, ChaCha20-Poly1305, SHA-256): one handshake and per-message
  cost. MicroPython has SHA-256 built in, but not the other two.
- Discovery: stock MicroPython advertises a hostname over mDNS but, as far as known, not a service record, which HA's
  automatic ESPHome discovery needs. Check; adding by IP works regardless.
- Output: a go/no-go note with the numbers. **Go** means the native API replaces the add-on's entity relay in
  Phases 3 and 4 (inbound states and actions with no broker and no relay); **no-go** leaves them as below.

## Phase 2 — first-install path (small)

Walk the Set up a board → Board settings → deploy steps as an HA user would, fix gaps, and link it from the bundle
README and later the add-on. The add-on doesn't do Web Serial itself (it needs HTTPS; HA is usually plain HTTP).

## Phase 3 — HA add-on (milestone)

Package the backend and editor as an HA add-on (from the existing packaging work), with host networking for the UDP
board probe and HA ingress for the editor. Unless Phase S says go: the entity relay (HA API → MQTT topics for the
entities a deployed flow names), with its topic layout added to the HA spec, and the "allow ThingStudio boards to
control entities" setting. Links to Set up a board for the cable step.

## Phase 4 — inbound and the entity picker (new branch from main)

`ha_entity_in`: bound to one entity; state out (HA `unavailable`/`unknown` and relay loss → `None`, shown as `--`);
in: that entity type's own actions only (decision 13). The entity picker in the screen builder, rebased onto the
`remote-display-spike` merge.

## Phase 5 — wall panel (separate project)

Start on the Freenove S3 (PSRAM, 4" touch). The CYD follows its memory measurement (GUI + framebuffer + WiFi +
MQTT). This is the integration test for everything and the media demo.

## Still open

- `mqtt_statestream`: supported path or documented workaround for HA installs that can't run add-ons (matters in
  Phase 4, and only if Phase S is no-go).
- The HA facts in 1.2.
- Which ThingStudio release Phase 0 ships in.
- The brief's "Device-based discovery PR description" source link points at an unrelated forum post; replace it.
