# Home Assistant bundle — Phase 1 briefing (2026-11-25)

**For the first session in the ThingStudioExtras project.** From today Extras works as a ThingStudio user: read
`AGENTS.md` first. Plan: `home-assistant-implementation-plan.md`. Contract: `home-assistant/SPEC.md` (v1.1) with
`vectors/`.

## ThingStudio version needed

The bundle needs ThingStudio from the `user-libraries` branch (2026-11-25 or later), not yet merged or released:
bundles, user libraries, the `ts_mqtt` will and connect hook, and `referencedConfigs` in custom-node compile hooks.
Install that branch build the way the user guide's install pages allow, in the session's own workspace. When it is
released, change the bundle README to name the minimum version.

## Where things stand

| Task | Status |
|---|---|
| 1.1 HA spec | Frozen v1, then v1.1 (Mike). |
| 1.2 Probe on Mike's HA | Done. `tools/ha-probe.py` (stdlib + paho-mqtt; credentials from `env.sh`'s variables). Results in SPEC §10. |
| 1.3 `ts_ha` library | Done, `home-assistant/lib/ts_ha.py`. Passes the vectors under CPython. No MicroPython unit tests yet (Mike: test on the board, backfill later). |
| 1.4 `ha device` | Done. |
| 1.5 Entity nodes | All six done (types `ha/...`). Select's options are a textarea, one per line (custom nodes have no list field; Mike: fine). |
| 1.6 Shared hook generator | Not started. Each `.compile.py` is self-contained for now. |
| 1.7 Tests | Not started. Now planned without core's fixtures (plan 1.7). |
| 1.8 Example flow | Done: `home-assistant/examples/kitchen-sink-ha.flow.json` (kitchen-sink ESP32-C3). |
| 1.9 Hardware pass | Partly, on the kitchen-sink C3, all good: entities appear and work, states unknown after redeploy, deleting a node removes its entity. Not yet: HA restart, broker restart, rename board, C3 heap logging, `tools/ha-cleanup.py` check, then the Freenove S3. |
| 1.10 Docs | Bundle README only. Per-node pages not started. |

## Decisions (Mike)

- No `ha light` now: the comprehensive version (with a board-side LED effects engine) is a later feature.
- The C3 needs a power cycle between deploys (memory); acceptable.
- Bluetooth scan left out of the C3 example for memory.

## Gotchas a user would meet

- An `adc` node sends a dict (`percent`, `raw`, `volts`), not a number: pick a field before an HA sensor. `ts_ha`'s
  error says so.
- Custom-node select options can't have an empty value: the HA nodes use `none` for "no device class".

## First jobs under the new rule

1. Install the branch build from the docs alone, in the session workspace. Anything the install pages don't cover is
   the first core request.
2. Check each thing the bundle relies on against `custom-nodes.md`: `set_will`/`on_connect`, bundles and `lib/`,
   `referencedConfigs`, `register_cleanup`. The board's chip id (`machine.unique_id()`) is used by `ts_ha` but not
   mentioned in the guide: decide whether that's plain MicroPython (fine) or needs a docs request.
3. Then the plan's Next: rest of 1.9, 1.6, 1.7, 1.10.
