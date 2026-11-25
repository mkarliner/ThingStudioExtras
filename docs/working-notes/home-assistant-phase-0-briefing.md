# Home Assistant work — Phase 0 briefing (2026-11-25)

**For the next session.** Read this, then `home-assistant-implementation-plan.md` (the plan and its 16 decisions),
then start Phase 0.4. The background reasoning is in `home-assistant-integration-scoping.md`. All three are in the
ThingStudio project and in ThingStudioExtras `docs/working-notes/`.

## Where things stand

| Phase | Status |
|---|---|
| 0.1 Specs | **Done.** `interfaces/library-format/` (new) and `interfaces/node-descriptor/SPEC.md` §3.1 Bundles, with test cases. Mike approved both spec changes. |
| 0.2 User libraries | **Done** (backend + editor). |
| 0.3 Bundles | **Done** (backend + editor + CLI packages). |
| 0.4 `ts_mqtt` will + reconnect hook | **Next.** |
| 0.5 One "uses MQTT" rule | Next after 0.4. |
| 0.6 Release | After 0.5. |
| Phase 1 onwards | Not started. |

Mike's full test suite passed on his Mac on 2026-11-24 ("green"), after an `npm ci` in `editor/` (his `node_modules`
predated the `esptool-js` dependency added on 18 November; nothing to do with this work).

**Git state is unconfirmed.** Mike was given commit commands for the `user-libraries` branch (ThingStudio) and for
the brief and plan (Extras). Ask him whether they ran before changing anything.

## What 0.1–0.3 built (ThingStudio, branch `user-libraries`)

- **Backend:** `user_libraries.py` (new: scan, refusal rules, requires by import scan, reserved names);
  `library_catalog.py` (new: built-ins + user libraries; drops libraries of skipped bundles);
  `dependencies.py` (`Dependency.source`/`origin`, `runtime_module_names()`); `persisted_store.py` (bundles one level
  deep, all or nothing, `libraries_dir`, `library_sources()`, editor writes and deletes refused for bundle packages);
  `admin_api.py` (`/api/custom-nodes` adds `bundle`, `skippedBundles`, `libraryRefusals`); `app.py`
  (`/api/dependencies` serves the merged catalog plus `refused`).
- **Editor:** `custom-node-loader.ts` (bundles all or nothing, two-pass type claiming, ready-made console lines);
  `admin-api-client.ts` (its own copy of the listing type: `flow-file/` may not import `app/`,
  `module-boundaries.test.ts`); `main.ts` (prints `p.line`; compile failure names the library's origin);
  `flow-dependencies.ts` (`source`/`origin` on `DependencyInfo`); `thingstudio-compile.ts` (CLI loads bundle packages).
- **Tests:** `backend/test/test_user_libraries.py` (all 19 spec cases, reserved-names check, routes);
  `test_dependencies.py` and `test_admin_api.py` updated for the new fields; 5 new cases in
  `editor/test/custom-node-loader.test.ts`.
- **Docs:** `custom-nodes.md` ("Your own libraries", "Bundles"), `thingstudio-folder.md`, `nodes/function.md`.
  `tools/docs_lint.py` passes.

**Known gaps, recorded in the library-format spec:** the CLI doesn't read libraries yet (`--libraries` planned); no
editor test yet for a deploy that sends a user library, nor a unix-port test of a user-named package installing.
`thingstudio-folder.md` still says ThingStudio adds "two examples" (it's six); not from this work.

## Next: 0.4 — `ts_mqtt` Last Will and reconnect hook

File: `device-runtime/src/vendor/thingstudio_mqtt/ts_mqtt.py` (the shared client, one per broker, `_Client`).

- **`set_will(topic, msg, retain=False, qos=0)`.** mqtt_as takes the will in its config as
  `config['will'] = (topic, msg, retain, qos)` and applies it in `MQTTClient.__init__` (it calls `_set_last_will`),
  so `_Client` builds `mqtt_as.MQTTClient(cfg)` too early to pass it. Either rebuild the client, or call
  `self.client._set_last_will(...)` before the first connect (check mqtt_as's code for which is safe). Refuse after
  the first connect, and refuse a second, different will loudly, matching `ensure_client`'s settings rule.
- **`on_connect(callback)`.** Call it after the first connect and on each reconnect that `ensure_connected()`
  detects: the branch where `now and not self.link_up` (it resubscribes there). `ts_ha` will publish `online` and its
  discovery message from it. A reconnect is only noticed when something calls `ensure_connected()`; `wait_message()`
  polls about once a second, so a subscriber (`ts_ha` subscribes to the HA status topic) covers it.
- Update `editor/test/fixtures/pymock/mqtt_as.py` and `pymock/ts_mqtt.py`; tests in `editor/test/ts-mqtt.test.ts`;
  mention both in `docs/user-guide/custom-nodes.md`. `ts_mqtt` is a flow dependency, not runtime core: check
  AGENTS.md's runtime version-bump rules, but no major bump is expected.

## Then: 0.5 — one "uses MQTT" rule

These list only `thingstudio/mqtt_publish` and `thingstudio/mqtt_subscribe`, so custom HA nodes would be missed and
WiFi managed twice:

- `editor/src/node-library/core-packages/compile-hooks.ts:30` (Python, inside the sandboxed hook)
- `editor/src/node-library/wifi-status.ts:237` and `:339`
- `editor/src/node-library/resource-check.ts:70`
- `editor/src/dev-tools/verify-flow-file.ts:76`
- `editor/src/app/rete/palette.ts` (a type union, line ~108; may only need a comment)

The rule, which works inside the hook sandbox too: a node uses MQTT if any of its properties holds the id of a
`thingstudio/config/mqtt-broker` config in `flow.configs`. Test: a custom node with a broker configRef sets
`deferToMqtt`.

## How sessions work here (from CLAUDE.md, plus what worked)

- **Writes:** stage a file, edit the staged copy, commit it back with its `expectedMtimeMs`. New files: write and
  commit.
- **Git:** never from the sandbox. Hand Mike zsh commands with no comments, starting `rm -f .git/index.lock`.
- **Tests:** never run npm, vite, vitest, make or pytest against the shared repo. What worked: copy the repo
  (excluding `node_modules`, `.venv`, `.git`, `firmware/out`, `dist`, `site`) to `$HOME/work/ts` in the device
  shell, then:
  - backend: `python3 -m venv .venv`, `.venv/bin/pip install -e "backend[test]"`, run pytest from `backend/` with
    `-p no:cacheprovider --basetemp=/tmp/pt` (a temp folder under `$HOME` breaks one existing `display_path` test)
  - editor: `npm ci` in the copy, then `npx tsc --noEmit -p tsconfig.json` and `npx vitest run`. Include
    `micropython-wasi/` and `mpy-cross-wasm/`, or about 20 test files fail to load.
  - Mike runs the suite on his Mac as the final check.
- **The device connection can drop** (it did on 2026-11-25). Reading via staging may still work when the shell and
  commit tools are gone; if so, work on a clone and hand over a patch.

## Still open

- `mqtt_statestream` status (only matters if the native-API spike is no-go).
- The HA facts in plan task 1.2, checked on Mike's HA before the HA spec is frozen.
- Which release Phase 0 ships in.
- The brief's "Device-based discovery PR description" source link points at an unrelated forum post.
