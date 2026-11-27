# Home Assistant bundle — Phase 1 briefing (updated 2026-11-27, evening)

**For the next session.** Read the repo's `AGENTS.md` first (Extras works as a ThingStudio user; supply chain
caution), then this. Plan: `implementation-plan.md`. Contract: `SPEC.md` (v1.1) with `vectors/`. Layout: this node
set lives in `home-assistant/`: the bundle in `home-assistant/home-assistant/`, notes here, tools in
`home-assistant/tools/`, tests in `home-assistant/test/`.

## Set up the session (the build doesn't survive between sessions)

```
bash home-assistant/test/setup.sh $HOME/work
```

It fetches ThingStudio (`../../THINGSTUDIO_VERSION`: `main` at a57d686b, since 2026-11-27) and MicroPython
(`home-assistant/test/MICROPYTHON_VERSION`: v1.29.0 at 0fd6c573) by full commit, fails if a checkout isn't at its pin,
and builds both in the work folder, never in the shared folder (it refuses a folder inside the repository).
ThingStudio is built by the user guide's "From source" route, with CPython 3.12.16 from the device shell's own `uv`:
the device shell has 3.10 and ThingStudio needs 3.11+.

- Each device-shell call runs in its own sandbox: a `nohup ... &` job is killed when the call returns (a background
  `setup.sh` on 2026-11-27 left nothing useful; rerun in the foreground). Run
  `setup.sh` in the foreground with `timeout_ms` 180000 (about 35 s with warm caches on 2026-11-27).
- The GitHub API (token in `env.sh`) reads user-guide pages at a commit without a clone:
  `GET /repos/mkarliner/ThingStudio/contents/docs/user-guide/<page>?ref=<commit>`. Creating issues from the session
  may be refused by the sandbox (2026-11-27); hand them to Mike.
- Read only `docs/user-guide/` in the ThingStudio clone. Nothing else from it. (Exception on 2026-11-27, at Mike's
  request: its `AGENTS.md` and `CLAUDE.md`, for the supply-chain rules now in ours.)
- The HA tools' one package: `pip install --require-hashes --only-binary :all: --no-deps -r
  home-assistant/tools/requirements.txt`. Every third-party dependency is in `THIRD-PARTY.md`.

What `setup.sh` fetches: ThingStudio and MicroPython from GitHub at the pinned commits; CPython 3.12.16 (uv's
checksummed download); ThingStudio's own npm packages (its lockfile, `npm ci --ignore-scripts`) and Python packages
(`--require-hashes`), both run by its `make`.

## Tests (1.7)

```
THINGSTUDIO_COMPILE=$HOME/work/ts/editor/dist-cli/thingstudio-compile.mjs python3 -B home-assistant/test/compile_test.py
MICROPYPATH=home-assistant/test/doubles:home-assistant/home-assistant/lib:$HOME/work/mp/extmod $HOME/work/mp/ports/unix/build-standard/micropython home-assistant/test/vectors_test.py home-assistant/docs/working-notes/vectors
MICROPYPATH=home-assistant/test/doubles:home-assistant/home-assistant/lib:$HOME/work/mp/extmod $HOME/work/mp/ports/unix/build-standard/micropython home-assistant/test/mqtt_test.py home-assistant/home-assistant
```

From the repository root. On 2026-11-27 (evening) at a57d686b: compile 27 cases, 0 failed, no known gaps (the first
case is `build-hooks.py --check`); vectors 48 checks, 0 failed (includes the hook's JSON sizing against the board's
`json.dumps`); mqtt 28 checks, 0 failed. Vectors and mqtt pass under MicroPython and CPython.

After editing anything in `hooks/` or the `ts_ha` definitions a hook includes, run
`python3 home-assistant/tools/build-hooks.py` and commit the regenerated `.compile.py` files. Run them after any change to the bundle or the vectors.

## Where things stand

| Task | Status |
|---|---|
| 1.1 HA spec | Frozen v1, then v1.1 (Mike). |
| 1.2 Probe on Mike's HA | Done. `home-assistant/tools/ha-probe.py`. Results in SPEC §10. |
| 1.3 `ts_ha` library | Done. Pure functions pass the vectors; the MQTT side passes `mqtt_test.py` against doubles of the documented `ts_mqtt`/`ts_wifi` (2026-11-27). |
| 1.4 `ha device` | Done. No runtime version in discovery until #25 (below). |
| 1.5 Entity nodes | All six done. `emit` includes the required `topic` key. `ha number` and `ha select` inputs are `any` (2026-11-27, Mike), so a function node's value can be wired back. |
| 1.6 Shared hook generator | Done (2026-11-27). Shared code in `hooks/`, `tools/build-hooks.py` writes the seven `.compile.py`; the compile test fails if they're stale. `ha device`'s hook builds the real discovery message (with `ts_ha.build_discovery`'s own source) and errors over 4 KB. |
| 1.7 Tests | Done: compile tests, SPEC vectors, MQTT side (`home-assistant/test/`). |
| 1.8 Example flows | Done: `kitchen-sink-ha` (C3) and `freenove-s3-ha` (2026-11-27, every entity type, no extra parts). Both compile with their 2 echo warnings. |
| 1.9 Hardware pass | Partly, on the kitchen-sink C3, all good so far. Not yet: HA restart, broker restart, rename board, C3 heap logging, `ha-cleanup.py` check, then the Freenove S3. |
| 1.10 Docs | Done (2026-11-27): bundle README (install, MQTT setup in HA, use, removing a device, limits) and a page per node in `home-assistant/home-assistant/docs/`, in the user guide's node-page layout. The ThingStudio pointer is request `ha-bundle-pointer`, not filed until 1.9 passes and the set has a public URL. |

## Findings on 2026-11-26 (afternoon)

- **The bundle relies on calls the user guide doesn't document.** The morning's check covered `set_will`,
  `on_connect`, bundles, `lib/`, `referencedConfigs` and `register_cleanup`, and those are documented. But nothing in
  the guide covers publishing, subscribing or receiving: `client.publish/subscribe/wait_message/ensure_connected`,
  `ts_wifi.ensure_station`, and `ensure_client`'s arguments (shown as `...`). `ha device` also reads
  `sys.modules['listener']._RUNTIME_VERSION`. Requests `ts-mqtt-client-for-nodes` (docs) and
  `runtime-version-for-nodes` (core). **Resolved 2026-11-27:** ThingStudio a57d686b documents `ts_wifi` and
  `ts_mqtt` (#24 closed). Checked against it: every call, argument order, bytes payloads, QoS, `set_will` before
  connecting and a library's `import runtime` already matched. Two changes: `ha device` takes `deferToMqtt` from its
  hook as the guide's hook works it out (it was a literal `True`, the same value), and it no longer reads the runtime
  version, so discovery has no `dev.sw` until #25 gives a documented way. a57d686b also makes core count any
  broker-holding node as MQTT, so a built-in network node in the same flow now passes the same `defer_to_mqtt` as
  `ha device` (before, it could pass `False` and `ensure_station` would raise).
- **SPEC §8, closed 2026-11-27:** `ha device`'s hook sizes the discovery message and errors over 4096 bytes, naming
  the size and the entity count. It counts worst cases for what only the board knows (16 hex digits of chip id, a
  32-character hostname for an unnamed device) and leaves out the stubs for entities a previous flow announced. About
  13 long-named sensors fit. The guide doesn't say which modules a hook may import, so the hooks import nothing:
  `json_size` counts bytes itself, and `vectors_test.py` checks it against MicroPython's `json.dumps` exactly.
- **A computed value can't reach a `number` input** (2026-11-27). A function node's outputs are `any`, and `any` wires
  only into `any`, `bool` and `bytes`, so the pwm out page's "convert it first, in a function node" can't be
  followed. Found writing the Freenove example: its slider drives the backlight PWM directly as a 0-1 fraction
  instead of a percentage. Request `function-into-typed-inputs` (core), **not filed**: the session wasn't allowed to
  create the issue.
- **Wiring, fixed 2026-11-27:** `ha number` and `ha select` had inputs typed `number` and `string`, which a function
  node's `any` output can't wire into, so the unwired-input warning's advice couldn't be followed. Both are `any` now;
  `ts_ha` still errors on a value the entity can't show. Compile test `function-feedback` passes.
- `--describe` ignores custom nodes: request `describe-custom-nodes`.

## Core requests (in `docs/core-requests/`)

Filed 2026-11-27 with a token Mike put in `env.sh` (`THINGSTUDIO_GITHUB_TOKEN`). It can create, comment on and close issues
(Issues: read and write).

| Request | Type | Where |
|---|---|---|
| `2026-11-26-branch-build-install` | docs | Already done on `main` (b5b83cdb). No PR. |
| `2026-11-26-python-3-10-source-build` | core | #23, closed: already fixed on `main` (b5b83cdb). |
| `2026-11-26-compile-cli-for-installed-users` | core | #22. Docs side done on `main` (00b98637), noted on the issue; the core ask stays open. |
| `2026-11-26-ts-mqtt-client-for-nodes` | docs | #24, closed by a57d686b (related: #21, from the wake-on-lan set) |
| `2026-11-26-runtime-version-for-nodes` | core | #25 |
| `2026-11-26-describe-custom-nodes` | core | #26 |
| `2026-11-27-function-into-typed-inputs` | core | Not filed: Mike to file. |
| `2026-11-27-ha-bundle-pointer` | docs | Not filed: after 1.9, once the set has a public URL. |

Lesson: check `main`'s user guide before filing: a gap at the pin may already be fixed. The pin moved to `main`
(67e9fc26, then a57d686b for #24) on 2026-11-27. `main` raised the device runtime to 15.2.0 (HELLO carries `chipId`, protocol SPEC 5): the
boards may need the matching runtime before the hardware pass.

## Decisions (Mike)

- No `ha light` now: the comprehensive version (with a board-side LED effects engine) is a later feature.
- The C3 needs a power cycle between deploys (memory); acceptable.
- Bluetooth scan left out of the C3 example for memory.
- Pin file (`home-assistant/THINGSTUDIO_VERSION`) over a git submodule of core.
- Third-party code: pinned, scriptless, gated (AGENTS.md), aligned with ThingStudio's rules on 2026-11-27.
- Pin ThingStudio to `main` (2026-11-27).
- `ha number` and `ha select` inputs are `any` (2026-11-27).
- Finish everything but the hardware, then test end to end (2026-11-27).
- 1.9 waits for #24 rather than going on under an exception (2026-11-27).
- #24 is about documenting core's own APIs (`ts_mqtt`, `ts_wifi`): what the built-in mqtt nodes use, and so any
  other node can (Mike, 2026-11-27). Not a separate API for custom nodes. Documented in ThingStudio, not here.

## Gotchas a user would meet

- An `adc` node sends a dict (`percent`, `raw`, `volts`), not a number: pick a field before an HA sensor. `ts_ha`'s
  error says so.
- Custom-node select options can't have an empty value: the HA nodes use `none` for "no device class".

## Next

1. **1.9 end to end** (Mike at the board): the C3 with `kitchen-sink-ha`, then the Freenove with `freenove-s3-ha`.
   First put both boards on the pinned build's runtime (15.2.0). The checklist is in the plan, task 1.9; still to do
   from the first pass: HA restart, broker restart, rename the board, the C3 heap figures (printed with each
   discovery), `ha-cleanup.py`, and the S3. New since the first pass, worth watching: `dev.sw` is gone from the device
   page, and the 4 KB check.
2. File `function-into-typed-inputs`. After 1.9: decide the set's public URL and file `ha-bundle-pointer`.
3. Then Phase 2 (first-install path), or Phase S.
