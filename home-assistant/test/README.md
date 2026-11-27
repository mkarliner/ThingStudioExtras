# Home Assistant bundle tests (plan task 1.7)

Development only: never copied into `custom-nodes/`. Both need only what a ThingStudio user has.

## Set up

`setup.sh` fetches and builds both toolchains at the full commits pinned in `../THINGSTUDIO_VERSION` and
`MICROPYTHON_VERSION`, in a work folder outside the repository, and fails if a checkout isn't at its pin:

```
bash home-assistant/test/setup.sh $HOME/work
```

About 35 s with warm caches. Safe to re-run. Each device-shell call is its own sandbox, so run it in the foreground
with a long timeout, not in the background.

## Compile tests: `compile_test.py`

Runs flows (the kitchen-sink example plus small flows built in the script) through an installed ThingStudio's
`thingstudio-compile`, with the bundle copied into a scratch `custom-nodes` folder, and checks the errors and
warnings. Stdlib Python 3. Point `THINGSTUDIO_COMPILE` at the `thingstudio-compile.mjs` that `setup.sh` built (user guide, "Check a flow
without the editor"):

```
THINGSTUDIO_COMPILE=$HOME/work/ts/editor/dist-cli/thingstudio-compile.mjs python3 -B home-assistant/test/compile_test.py
```

A KNOWN GAP case is one the bundle doesn't meet yet. It's reported without failing the run, and fails the run once
it passes, so the case gets promoted.

## SPEC vectors: `vectors_test.py`

`ts_ha`'s pure functions against `../docs/working-notes/vectors/` (SPEC §9), under the MicroPython unix port
(`setup.sh` builds it without frozen modules, so `extmod` on the path supplies `asyncio`), with `doubles/runtime.py`
written from the user guide:

```
MICROPYPATH=home-assistant/test/doubles:home-assistant/home-assistant/lib:$HOME/work/mp/extmod $HOME/work/mp/ports/unix/build-standard/micropython home-assistant/test/vectors_test.py home-assistant/docs/working-notes/vectors
```

Run from the repository root. The same script runs under CPython with `PYTHONPATH` in place of `MICROPYPATH`.

Not tested yet: `ts_ha`'s MQTT side (announce, availability, commands, the record file). The user guide doesn't
document the client calls it uses (core request `2026-11-26-ts-mqtt-client-for-nodes`), so there is nothing to
write a double from.
