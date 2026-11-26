# Home Assistant bundle — Phase 1 briefing (updated 2026-11-26)

**For the next session.** Read the repo's `AGENTS.md` first (Extras works as a ThingStudio user), then this. Plan:
`implementation-plan.md`. Contract: `SPEC.md` (v1.1) with `vectors/`. Layout (2026-11-26): this node set lives in
`home-assistant/`: the bundle in `home-assistant/home-assistant/`, notes here, tools in `home-assistant/tools/`.

## Set up the session (the build doesn't survive between sessions)

`../../THINGSTUDIO_VERSION` names the build: `user-libraries` at `8f8d137b`. Build it in the session's own workspace
(device shell, outside `mnt/`), never in the shared folder. The repository is public; this is the user guide's "From
source" route plus the clone it doesn't mention (core request `2026-11-26-branch-build-install`):

```
mkdir -p $HOME/work && cd $HOME/work
git clone -q --branch user-libraries --single-branch https://github.com/mkarliner/ThingStudio ts
python3 -m pip install --quiet --user uv && $HOME/.local/bin/uv python install 3.12
cd ts && make PYTHON=$($HOME/.local/bin/uv python find 3.12)
cd editor && npm ci --ignore-scripts && npm run build:cli
```

- Python 3.12 because the device shell has 3.10 and the branch's requirements need 3.11+ (core request
  `2026-11-26-python-3-10-source-build`). `make` takes about 2.5 minutes: run it with `nohup ... &` and poll.
- Read only `docs/user-guide/` in that clone. Nothing else from it.
- Check the example as a user would: copy the bundle into a scratch `custom-nodes` folder, then

```
cd $HOME/work && mkdir -p cn && cp -R $HOME/mnt/ThingStudioExtras/home-assistant/home-assistant cn/
node ts/editor/dist-cli/thingstudio-compile.mjs --custom-nodes cn --board board:kitchen-sink-c3 cn/home-assistant/examples/kitchen-sink-ha.flow.json
```

  Expected on 2026-11-26: `OK`, 7 custom node packages, 2 warnings (the unwired `ha switch` and `ha number` echo).

## Where things stand

| Task | Status |
|---|---|
| 1.1 HA spec | Frozen v1, then v1.1 (Mike). |
| 1.2 Probe on Mike's HA | Done. `home-assistant/tools/ha-probe.py` (stdlib + paho-mqtt; credentials from `env.sh`'s variables). Results in SPEC §10. |
| 1.3 `ts_ha` library | Done, `home-assistant/home-assistant/lib/ts_ha.py`. Passes the vectors under CPython. No MicroPython unit tests yet (Mike: test on the board, backfill later). |
| 1.4 `ha device` | Done. |
| 1.5 Entity nodes | All six done (types `ha/...`). Select's options are a textarea, one per line (custom nodes have no list field; Mike: fine). |
| 1.6 Shared hook generator | Not started. Each `.compile.py` is self-contained for now. |
| 1.7 Tests | Not started. `thingstudio-compile` now available from the branch build (above). |
| 1.8 Example flow | Done: `home-assistant/home-assistant/examples/kitchen-sink-ha.flow.json` (kitchen-sink ESP32-C3). Compiles clean on the branch build. |
| 1.9 Hardware pass | Partly, on the kitchen-sink C3, all good: entities appear and work, states unknown after redeploy, deleting a node removes its entity. Not yet: HA restart, broker restart, rename board, C3 heap logging, `home-assistant/tools/ha-cleanup.py` check, then the Freenove S3. |
| 1.10 Docs | Bundle README only. Per-node pages not started. |

## Done on 2026-11-26

- Repo reorganised to one folder per node set (`AGENTS.md` "Layout"). Committed.
- Branch build installed from the guide; everything the bundle relies on checked against the branch's
  `custom-nodes.md`: `set_will`/`on_connect`, your own libraries, bundles and `lib/` (other folders in a bundle are
  ignored), `referencedConfigs`, `register_cleanup`. All documented. `machine.unique_id()` is plain MicroPython: no
  request needed.
- Three core requests written in `docs/core-requests/`, **not yet filed**: branch-build install (docs),
  `thingstudio-compile` for installed users (core), Python 3.10 source build (core).
- Mike chose a pin file (`home-assistant/THINGSTUDIO_VERSION`) over a git submodule of core.
- `~/Src/ThingStudio` was attached for one step (the clone) and isn't needed: clone from GitHub as above.

## Decisions (Mike)

- No `ha light` now: the comprehensive version (with a board-side LED effects engine) is a later feature.
- The C3 needs a power cycle between deploys (memory); acceptable.
- Bluetooth scan left out of the C3 example for memory.

## Gotchas a user would meet

- An `adc` node sends a dict (`percent`, `raw`, `volts`), not a number: pick a field before an HA sensor. `ts_ha`'s
  error says so.
- Custom-node select options can't have an empty value: the HA nodes use `none` for "no device class".

## Next

1. Mike files the three core requests (or says to); add the links to each file.
2. Rest of 1.9 on the C3 (Mike at the board), then the Freenove S3.
3. 1.7 tests: compile tests through the branch `thingstudio-compile`; `ts_ha` under the MicroPython unix port with
   doubles written from `custom-nodes.md`.
4. 1.6, then 1.10.
