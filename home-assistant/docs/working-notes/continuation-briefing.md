# Home Assistant bundle — continuation briefing (2026-11-27, evening)

**Start here.** Read the repo's `AGENTS.md` and `CLAUDE.md` first: we work as a ThingStudio *user* (the user guide
only, never core's code), third-party code is pinned, scriptless and gated, and git writes are handed to Mike. Then
this page. Detail lives in `phase-1-briefing.md` (status, findings, decisions), `phase-2-first-install.md`,
`implementation-plan.md` and `SPEC.md` (v1.1, frozen: changes need Mike's permission).

## Where things stand

**ThingStudio v0.14.0 is out** (2026-11-27, tag commit `416f886f632bda1cd1cfa854afe78998bceaa8a4`, which is `main`).
It contains everything the bundle needs: bundles, user libraries, the `ts_mqtt` will and `on_connect`, the
`ts_wifi`/`ts_mqtt` docs (#24, a57d686b) and runtime 15.2.0. It's 2 commits past our pin (a57d686b): the version bump
and a release-script change, with no user-guide changes. Its notes list custom firmware images with runtime 15.2.0
for the classic ESP32 (no PSRAM), the ESP32-C3 and the C5.

Phase 1, everything but the hardware, is done and committed (`ad57a4a` and before):

- Seven nodes (`ha device`, sensor, binary sensor, switch, number, select, button) and `lib/ts_ha.py`, matching the
  documented `ts_wifi`/`ts_mqtt`. Discovery leaves out `dev.sw` until #25.
- Compile hooks generated from `home-assistant/hooks/` by `tools/build-hooks.py` (1.6); `ha device`'s hook builds the
  real discovery message and errors over 4 KB.
- Three example flows: `starter-ha` (any WiFi board, no wiring), `kitchen-sink-ha` (C3), `freenove-s3-ha` (S3).
- Docs: the bundle README (what you need, a route for ThingStudio newcomers, MQTT setup in HA, use, removal,
  limits) and a page per node in `home-assistant/home-assistant/docs/`.
- Tests (2026-11-27, at a57d686b): compile 29 cases, 0 failed, no known gaps; vectors 48 checks; mqtt 28 checks;
  vectors and mqtt under MicroPython and CPython.

Phase 2 was walked on paper. Its main gap was having no release to install, which v0.14.0 now closes.

## Next, in order

1. **Move the pin to v0.14.0.** In `home-assistant/THINGSTUDIO_VERSION` set the commit to `416f886f…` and name the
   tag (`v0.14.0`; `setup.sh` checks only the full commit). Update `THIRD-PARTY.md`'s ThingStudio line. Rebuild in a
   fresh work folder and run all the tests (commands below). Expect no change: there are no guide changes since
   a57d686b.
2. **Make the README name the release.** In "What you need", replace the source-build paragraph with "ThingStudio App
   v0.14.0 or later", installed the guide's normal way (*Getting started*). Keep "ThingStudio Web won't do". In "New
   to ThingStudio?", step 1 becomes the guide's install. Step 2's custom-image advice now has released images with
   the matching runtime. Update `phase-2-first-install.md`'s walk table and the "For Mike" list to match.
3. **Mike's end-to-end run (1.9 plus the Phase 2 checks).** Mike is at the board; the session supports, reads the
   console output he pastes, and fixes. Ideally from a v0.14.0 install, not a source build, following the README as
   written:
   - Boards on runtime 15.2.0: reflash the C3 with the v0.14.0 custom image, or **Tools → Install runtime**.
   - C3 with `kitchen-sink-ha`, then the Freenove with `freenove-s3-ha`, then `starter-ha` on a board that hasn't
     run ThingStudio. Plan 1.9's checklist: entities and classes; states and commands, wired and echoed; unplug
     gives offline and plug in gives online; HA restart and broker restart; delete a node and redeploy; rename the
     board; deploy a non-HA flow; C3 heap figures (printed with each discovery); `tools/ha-cleanup.py` afterwards.
   - Phase 2 checks: does the Board settings name become the HA device name (with **device name** empty)? If not,
     raise a core request for the guide to say what the hostname is. Does ✎ on the starter's unsaved credentials
     behave as the README says? Does a WiFi deploy work with the board away from the computer?
   - Watch: no software version on the device page, entities unknown until reported, and the 4 KB check.
4. **Requests.** Mike files `docs/core-requests/2026-11-27-function-into-typed-inputs.md` (core). The session was
   refused when it tried to create the issue. After 1.9 passes, Mike decides the set's public URL, then files
   `2026-11-27-ha-bundle-pointer.md` (docs).
5. **Wrap up Phase 1 (1.11)** once 1.9 passes: update the briefing and the plan's status. Then Mike picks Phase S
   (the native-API spike) or Phase 3 (the add-on).

## Set up a session

The device shell has the repo at `$HOME/mnt/ThingStudioExtras`. Builds go in the session's own workspace, never in
the repo.

```
bash home-assistant/test/setup.sh $HOME/work
```

Run it in the foreground with `timeout_ms` 180000. A background job (`nohup … &`) is killed when the shell call
returns. It fetches ThingStudio and MicroPython (v1.29.0 at 0fd6c573) at their pinned commits and fails on anything
else, using CPython 3.12.16 from the shell's `uv`.

Tests, from the repo root:

```
python3 home-assistant/tools/build-hooks.py --check
THINGSTUDIO_COMPILE=$HOME/work/ts/editor/dist-cli/thingstudio-compile.mjs python3 -B home-assistant/test/compile_test.py
MICROPYPATH=home-assistant/test/doubles:home-assistant/home-assistant/lib:$HOME/work/mp/extmod $HOME/work/mp/ports/unix/build-standard/micropython home-assistant/test/vectors_test.py home-assistant/docs/working-notes/vectors
MICROPYPATH=home-assistant/test/doubles:home-assistant/home-assistant/lib:$HOME/work/mp/extmod $HOME/work/mp/ports/unix/build-standard/micropython home-assistant/test/mqtt_test.py home-assistant/home-assistant
```

For CPython, use `PYTHONPATH` in place of `MICROPYPATH` and `python3 -B`. After any edit to `hooks/`, or to a `ts_ha`
definition a hook includes (`BUNDLE_VERSION`, `COMMANDABLE`, `build_discovery`), run `build-hooks.py` and commit
the regenerated `.compile.py` files.

GitHub: `env.sh` holds `THINGSTUDIO_GITHUB_TOKEN` (Issues: read and write on `mkarliner/ThingStudio`). Never print it
or put it in a file. The device shell has no `gh`. A small `urllib` helper does the API calls; it lives outside the
repo, so recreate it per session. User-guide pages at a commit come from
`GET /repos/mkarliner/ThingStudio/contents/docs/user-guide/<page>?ref=<commit>`. Under the rules that counts as
reading the guide, but nothing else from the core repo may be read.

## Open core requests

| Request | Issue | State |
| --- | --- | --- |
| compile CLI for installed users | #22 | open (the docs side is done) |
| runtime version for nodes | #25 | open: `dev.sw` stays out until then |
| `--describe` ignores custom nodes | #26 | open |
| function into typed inputs | not filed | Mike to file |
| HA bundle pointer in the guide | not filed | after 1.9, with a public URL |

#21 (wake-on-lan's WiFi question), #23 and #24 are closed. The wake-on-lan set has its own session and notes: leave
`wake-on-lan/` alone.

## Gotchas from 2026-11-27

- **Automatic refusals.** The sandbox's automatic check has refused some actions with no prompt shown to Mike:
  `device_request_folder_access` and creating a GitHub issue. Don't retry; say what was refused and hand it to Mike
  (for a folder, he adds it with **Add folder** in the desktop app).
- **Git.** Even a read-only `git status` from the sandbox can leave `.git/index.lock`. Every commit command handed to
  Mike starts with `rm -f .git/index.lock`. Mike runs zsh: no comments in command blocks.
- **Wiring rules** (user guide, *Working in the editor*, "Wiring"): a function node's output is `any`, which wires
  only into `any`, `bool` and `bytes` inputs. That's why `ha number` and `ha select` inputs are `any`, and why the
  Freenove example drives the PWM straight from `ha number` as a 0-1 fraction.
- **Wiring back into a two-faced node** (wired switch state) always gives a `--layout` warning: that wire runs right
  to left. The layout check is optional and the compile tests don't use it.
- **A sink with no input wired** fails the compile (`disconnected from any source`). A test flow with entity sinks
  needs them wired.
- The C3 needs a power cycle between deploys (memory). Mike accepts this.
