# Wake on LAN node — continuation briefing (updated 2026-11-27, after the docs landed)

**For the next session.** Read the repo's `AGENTS.md` first (Extras works as a ThingStudio user; supply-chain
caution), then this. The node is written and compile-checked; what is left is the board pass (kitchen-sink C3),
which needs the board plugged in.

Origin: one line in `docs/mikes-notes.md` — "Wake on lan node - takes an mac address (or an IP?) and sends a
magic packet." Mike settled the contract on 2026-11-27: the MAC arrives per message, as a payload dict entry
(the payload dict may hold other stuff, which the node ignores). The "or an IP?" resolves to an optional
destination entry (§1 of the SPEC).

## Where things stand

| Task | Status |
|---|---|
| Design: descriptor, payload contract, behaviour, errors, test plan | Settled 2026-11-27 — below. |
| Node files | Done: `wake-on-lan/wake-on-lan/` (`wol.node.json`, `wol.node.py`, `wol.compile.py`, `lib/wol_packet.py`, `README.md`, `examples/wol-wake.flow.json`, `examples/wol-loopback.flow.json`). |
| `SPEC.md` + `vectors/` | Done; vectors pass under CPython and the pinned MicroPython v1.29.0 unix port (28 checks each). |
| Compile checks | Done: `thingstudio-compile` on both example flows is clean; `wake-on-lan/test/compile_test.py` — 5 cases (ok, no-WiFi, no-capability, both example flows), all pass. |
| Board pass (kitchen-sink C3) | Not started: the C3 was not connected on 2026-11-27 (no serial device). Includes the broadcast finding. |

## Design (settled 2026-11-27)

Layout (one folder per node set):

```
wake-on-lan/
  wake-on-lan/            the bundle: what the user copies into ~/.thingstudio/custom-nodes/
    wol.node.json
    wol.node.py
    wol.compile.py
    lib/wol_packet.py     the pure functions, testable under MicroPython and CPython alike
    examples/wol-wake.flow.json
    README.md
  docs/                   SPEC.md, vectors/, how-it-works.md
  docs/working-notes/     this briefing
  test/                   setup.sh, compile_test.py, vectors_test.py; THINGSTUDIO_VERSION in the set root
  tools/                  wol-listen.py (host-side board-pass listener, never copied)
```

**Kind: `sink`** — one input, **no output**. The user guide is explicit that UDP has no acknowledgement ("a
send that succeeds doesn't mean the datagram arrived", udp send page); an output "sent" confirmation would be
misleading, so there is none.

The descriptor is in `wake-on-lan/wake-on-lan/wol.node.json`; the payload contract, the packet, the
destination/port rules, the properties and every error message are in `SPEC.md` (v1). The one decision to
remember: `mac` is required in the payload dict, `ip` is optional (absent → the broadcast
`255.255.255.255`), and every other key rides along ignored. The magic packet is six `0xFF` bytes + the MAC
sixteen times — 102 bytes.

### The WiFi part (settled once the docs landed)

The node joins the flow's one WiFi network exactly as the user guide now documents it (custom-nodes,
"The flow's WiFi: ts_wifi" — added by commit `a57d686b85dc74ae7e3f7240536ad3c40d406fe9`, main, 2026-11-27,
which is this set's pin):

- the descriptor carries a `wifi` field (`configRef`, `thingstudio/config/wifi`, `singleton: true`);
- `wol.compile.py` is the guide's example hook: it resolves the config from `ctx["referencedConfigs"]` and
  returns `ssid`, `password`, `security` and `deferToMqtt` (worked out as the guide's example does — `True`
  when any node holds the flow's MQTT broker config);
- setup calls `ts_wifi.ensure_station(ssid, password, security, deferToMqtt)`;
- `run` checks `isconnected()` before sending (named error), and a refused send is caught and reported as
  `wol: send to <ip>:<port> failed: …`, as `udp send` reports its failures.

The node's own failure style is pinned in SPEC §6: `ValueError`/`OSError` raised in `run`, `"wol: …"`
prefix, the offending value named, the remedy stated.

## Board pass (runbook, kitchen-sink C3)

The only open design question is on this pass: does the board's stack honour
`SO_BROADCAST`/`255.255.255.255`, or does it want a directed broadcast computed from `ifconfig`? The
design uses the universal broadcast (`_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)`); if the stack
refuses it, the console says `wol: send to 255.255.255.255:9 failed: …` and that is the finding —
fall back to a directed broadcast only then (a SPEC change, Mike's permission).

On the machine with the board:

```
# 0. build the pinned tools in a work folder
bash wake-on-lan/test/setup.sh $HOME/work

# 1. install the bundle the way a user does
cp -r wake-on-lan/wake-on-lan ~/.thingstudio/custom-nodes/

# 2. start the pinned build's editor, pick the kitchen-sink C3, install the runtime from this build
#    if the board doesn't have it

# 3. loopback (the byte check; no target machine needed):
#    File -> Open: wake-on-lan/wake-on-lan/examples/wol-loopback.flow.json
#    pick your WiFi config, deploy. Every ~10 s the debug node should show 204 hex
#    characters: ffffffffffff + aabbccddeeff x 16 (SPEC §2).

# 4. broadcast (the SO_BROADCAST check, with a real receiver):
#    on a host on the same network:  sudo python3 wake-on-lan/tools/wol-listen.py 9
#    (or set the wol node's port to an unprivileged one, say 9090, and pass that to the listener)
#    open wol-wake.flow.json, drop the 'ip' entry from the payload, deploy.
#    the listener should print "magic packet ok (6 x 0xFF + MAC x 16); MAC = aa:bb:cc:dd:ee:ff".

# 5. the error vectors on the console (SPEC §6):
#    - wire the timer straight into the wol input (a count, not a dict)
#      -> "wol: payload must be a dict with a 'mac' entry, got 1"
#    - payload {'mac': 'GG:BB:CC:DD:EE:FF'} -> the not-a-MAC-address line, naming the value
#    - payload {'mac': '…', 'ip': '300.1.1.1'} -> the not-an-IPv4 line, naming the value
#    - WiFi down (wrong credential, or the AP off) -> "wol: the flow's WiFi is not connected …"

# 6. the redeploy check: deploy the same flow twice; the second deploy must not fail with
#    EADDRINUSE (register_cleanup closes the socket).
```

Record the results in the working notes when the pass is done, and move the SPEC (with Mike's
permission) if the board says otherwise.

## Set up the session (the build doesn't survive between sessions)

```
bash wake-on-lan/test/setup.sh $HOME/work
```

It builds ThingStudio (`wake-on-lan/THINGSTUDIO_VERSION`: v0.14.0 at 416f886f, which postdates the ts_wifi
docs on main) and MicroPython
(`wake-on-lan/test/MICROPYTHON_VERSION`: v1.29.0 at 0fd6c573) by full commit into the work folder, never in
the shared folder (it refuses a folder inside the repository), and fails on a checkout that is anywhere else.
It needs git, Python 3.11+, Node.js 22 and `make` (the device shell has 3.13.5, Node 22.23.4 and make; no
uv-managed CPython was needed, unlike the HA set). MicroPython's standard variant needs its submodules at
the commits the pin records (`git submodule update --init --recursive`; on 2026-11-27 the plain `make`
failed without them: `mbedtls/platform.h: No such file or directory`). On 2026-11-27 the ThingStudio build
took a few minutes warm (npm from its lockfile, `pip --require-hashes`, the editor's `npm run build:cli` for
`dist-cli/thingstudio-compile.mjs`).

## Tests

From the repository root:

```
python3 wake-on-lan/test/vectors_test.py
MICROPYPATH=wake-on-lan/wake-on-lan/lib $HOME/work/micropython/ports/unix/build-standard/micropython wake-on-lan/test/vectors_test.py
THINGSTUDIO_COMPILE=$HOME/work/ThingStudio/editor/dist-cli/thingstudio-compile.mjs python3 wake-on-lan/test/compile_test.py
```

On 2026-11-27: vectors 28 checks, 0 failed under CPython (3.13.5) and MicroPython v1.29.0; compile 5
cases, all pass. Run them after any change to the bundle or the vectors.

## Findings on 2026-11-27

- **The general network-node pattern was undocumented until this afternoon.** Request
  `2026-11-27-wifi-for-network-nodes` was filed as mkarliner/ThingStudio#21 (morning) and answered in the
  user guide the same day (commit a57d686b): "The flow's WiFi: ts_wifi" and "The flow's MQTT client: ts_mqtt"
  under custom-nodes. This set is pinned to that commit; the issue was closed 2026-11-27.
- **Flow files namespace their built-in types:** `thingstudio/timer`, `thingstudio/function`, … The
  `--describe` output shows the short name (`Type: timer`), which is not the string a flow file holds;
  writing the short name fails the check with "no custom node package defines type". The strings the flow
  file wants are the ones the node catalog and an existing flow use.
- **`thingstudio-compile` uses stand-in credentials** and says so in a note ("WiFi credentials were not
  resolved (they live in the backend): stand-in values were used"); it checks a custom node's descriptor and
  compile hook for real, but only the syntax of `.node.py`.
- **The MicroPython unix standard variant needs its submodules** (mbedtls, berkeley-db, …): `make -C
  ports/unix` fails on a fresh clone until `git submodule update --init --recursive`.
- **The session's first git pull needed a rebase** (local `main` had diverged from `origin/main` with a
  duplicated README line): `git branch --set-upstream-to=origin/main main`, then `git pull --rebase`,
  README conflict resolved to the one-line version.

## Core requests (in `docs/core-requests/`)

| Request | Type | Status |
|---|---|---|
| `2026-11-27-wifi-for-network-nodes` | docs (or core) | Filed: mkarliner/ThingStudio#21; answered in the user guide 2026-11-27 (commit a57d686b); closed 2026-11-27. |

## How to resume

1. Plug in the kitchen-sink C3 (it was not connected on 2026-11-27), set up the session (above), install the
   runtime from the pinned build's editor.
2. The board pass per the runbook above: loopback byte check, broadcast + `SO_BROADCAST` finding, error
   vectors on the console, the redeploy socket check. Settle the broadcast question there; record the
   results in the working notes.
3. If the board pass moves the design, move the SPEC with it (Mike's permission for the spec) and run the
   vectors in the same change.
4. Close out: if the board pass earns a note, put it in the bundle `README.md`; `tools/wol-listen.py`
   stays a dev tool (never copied, standard library only, no ledger line).

## Toolchain this session used (named per AGENTS.md, briefings)

- Built in `$HOME/work` (outside the repository and the shared folder): ThingStudio v0.14.0 at
  416f886f632bda1cd1cfa854afe78998bceaa8a4 (git clone + `make`: npm from its committed lockfile,
  `pip --require-hashes` into its own `.venv`, `npm run build:cli`) and MicroPython v1.29.0 at
  0fd6c573ea815774668bbb16b8e197c8822368b2 (git clone + submodules at the pin's recorded commits,
  `make -C ports/unix`). Nothing was installed into `~/.thingstudio`; `make` linked
  `~/.local/bin/thingstudio-backend` to the work-folder build, as its documented From-source route does.
- Read: the published user guide on 2026-11-27 (home, getting-started, installation-details, custom-nodes —
  twice, node-conventions, udp send, mqtt subscribe, http request, editor-in-depth, check-a-flow, FAQ).
- The device shell's own `git`, `python3` (3.13.5), `node` (v22.23.4) and `make` (4.4.1); `gh` filed the
  issue. No other packages fetched.
