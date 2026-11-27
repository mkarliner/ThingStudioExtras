# Wake on LAN node — continuation briefing (2026-11-27)

**For the next session.** Read the repo's `AGENTS.md` first (Extras works as a ThingStudio user; supply-chain
caution), then this. The design below was settled on 2026-11-27 and is the record of it; it lives here because
the node itself is **on hold** until `mkarliner/ThingStudio#21` is answered (request
`2026-11-27-wifi-for-network-nodes`).

Origin: one line in `docs/mikes-notes.md` — "Wake on lan node - takes an mac address (or an IP?) and sends a
magic packet." Mike settled the contract on 2026-11-27: the MAC arrives per message, as a payload dict entry
(the payload dict may hold other stuff, which the node ignores). The "or an IP?" resolves to an optional
destination entry (below).

## Where things stand

| Task | Status |
|---|---|
| Design: descriptor, payload contract, behaviour, errors, test plan | Settled 2026-11-27 — below. |
| Node files (`wol.node.json`, `wol.node.py`) | Not started. Blocked on the WiFi part (issue #21). |
| `SPEC.md` + `vectors/` | Not started; the payload contract below is its draft. |
| Board pass (kitchen-sink C3) | Not started; includes the broadcast finding. |
| Bundle `README.md` | Not started. |
| Core request | Filed: `wifi-for-network-nodes` → mkarliner/ThingStudio#21. |

## Design (settled 2026-11-27)

Layout (one folder per node set):

```
wake-on-lan/
  wake-on-lan/            the bundle: what the user copies into ~/.thingstudio/custom-nodes/
    wol.node.json
    wol.node.py
    README.md
  docs/working-notes/     this briefing; SPEC.md + vectors/ when the set starts
  test/  tools/           development-only, never copied
```

**Kind: `sink`** — one input, **no output**. The user guide is explicit that UDP has no acknowledgement ("a
send that succeeds doesn't mean the datagram arrived", udp send page); an output "sent" confirmation would be
misleading, so there is none.

Descriptor (`wol.node.json`), settled:

```json
{
  "type": "wol/wol",
  "kind": "sink",
  "label": "wol",
  "group": "network",
  "color": "#4caf50",
  "bgcolor": "#1b3a1e",
  "icon": "⚡",
  "description": "Sends a Wake-on-LAN magic packet. Payload is a dict with the target's MAC address.",
  "requires": { "capabilities": ["wifi"] },
  "ports": { "inputs": [{ "name": "msg", "type": "any" }] },
  "properties": [
    { "name": "port", "label": "port", "kind": "number", "default": 9, "min": 1, "max": 65535,
      "help": "Destination UDP port. 9 is the Wake-on-LAN default; some machines listen on 7." },
    { "name": "repeats", "label": "repeats", "kind": "number", "default": 1, "min": 1, "max": 10,
      "help": "How many times to send the packet. Broadcasts can be dropped; 3 is a common choice." }
  ]
}
```

`requires` is a documented field: on a board without the `wifi` capability the palette grays the node out and
the compile refuses it, naming the missing capability. (`group: "network"` is to be checked against the
built-in section name on the board — the guide says any name works and a new one gets its own section.)

Payload contract (the SPEC draft):

| entry | required | meaning |
|---|---|---|
| `mac` | yes | the target's MAC, a string. Forms: `AA:BB:CC:DD:EE:FF`, also dash-, dot- or separator-less (Windows shows dashes, Cisco dots). Case-insensitive. |
| `ip` | no | destination IPv4, a string. Absent → broadcast `255.255.255.255`. Present → unicast to that address (the routed/VLAN case). |

Any other keys in the payload dict ride along and are ignored (node conventions). The magic packet is
`b'\xff' * 6 + mac * 16` — 102 bytes — sent as one UDP datagram to `(destination, port)`, `repeats` times.

Errors: runtime, reported from the board and attributed to the node, in the house style (`ValueError`,
`"wol: …"` prefix, the offending value named via `%r`, the remedy stated), e.g. `wol: payload must be a dict
with a 'mac' entry, got 42` / `wol: 'zz:bb:…' is not a MAC address -- 6 byte pairs, hex, e.g. AA:BB:CC:DD:EE:FF`
/ `wol: '300.1.1.1' is not an IPv4 address, e.g. 192.168.1.50`. A failed send names the destination, port and
the system's error.

Board behaviour (`wol.node.py`), settled sketch — **everything from the socket up is the blocked part**
(see below):

```python
import socket

_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)          # documented pattern (custom-nodes, "Cleanup")
_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)       # the broadcast finding: settle on hardware
runtime.register_cleanup('wol_socket', lambda: _sock.close())     # documented; avoids EADDRINUSE on redeploy

def _mac(text): ...      # the forms above -> 6 raw bytes; ValueError otherwise
def _dest(text): ...     # IPv4 validation -> string; '' -> '255.255.255.255'

async def run(msg, properties):
    payload = msg.get('payload')
    if not isinstance(payload, dict) or 'mac' not in payload:
        raise ValueError("wol: payload must be a dict with a 'mac' entry, got %r" % (payload,))
    packet = b'\xff' * 6 + _mac(payload['mac']) * 16              # 102 bytes
    for _ in range(properties['repeats']):
        _sock.sendto(packet, (_dest(payload.get('ip') or ''), properties['port']))
```

**The WiFi part — the blocker.** The node needs the flow's WiFi up, and the user guide documents that pattern
only for built-in nodes and for custom MQTT nodes. For a non-MQTT custom network node it says nothing about:
the WiFi config's type for a `configRef`, what the node's Python receives for it, what `ts_wifi` offers, who
brings the connection up when this node is the flow's only network node, unmanaged semantics, or the failure
path when the network is down. Per AGENTS.md (core requests, point 4): until issue #21 is answered, no node
files and no workaround leaning on undocumented behaviour — and no guessing from core or from another bundle's
implementation (Mike, 2026-11-27: hearsay from a parallel development is not acceptable; dogfood rules). On
resume, implement exactly what the docs answer says; if it differs from anything above, the docs win.

## Open questions to settle on hardware (kitchen-sink C3)

- **Broadcast.** The guide is silent on sending to `255.255.255.255` / `SO_BROADCAST`. The design defaults to
  the universal broadcast with the `setsockopt` above; if the board's stack refuses it, the fallback is a
  directed broadcast computed from `ifconfig` (ip, netmask). Decide on hardware, not from memory.
- **Test plan.**
  1. Loopback, no target machine: a flow with a `udp receive` on the node's port plus the `wol` node sending to
     the board's own IP via the `ip` entry → compare the 102 datagram bytes (6×FF + MAC×16) in the journal.
  2. Broadcast: a host-side listener (a dev tool, e.g. `tools/wol-listen.py`) on the node's port; doubles as the
     `SO_BROADCAST` check.
  3. Error vectors: non-dict payload, missing `mac`, each bad MAC form, bad `ip` → a console line naming the node.
  4. `test/setup.sh`-style pin on full commit hashes (as the HA set does); `thingstudio-compile` for
     descriptor/compile checks without a board.
- **Pin.** This set gets its own `THINGSTUDIO_VERSION` (branch + full commit hash) when its build is installed.
  The HA set's pin (`user-libraries` at 8f8d137b, 2026-11-25) records what was current then; it is a reference,
  not this set's pin.

## Findings on 2026-11-27

- **The general network-node pattern is undocumented for non-MQTT custom nodes.** What the guide documents:
  built-in nodes each carry the **WiFi** field ("the flow's WiFi network, shared by every WiFi node in the
  flow" — udp send, http request, mqtt subscribe); Editor in depth, "Config nodes": "A flow has one WiFi
  network … change it on one node and it changes on all"; custom-nodes, "Sharing a config": network configs
  "expose only the credential's name, not the secret, so a custom node can't make a WiFi connection from
  one"; custom-nodes, "Libraries you can import": `ts_wifi` listed as "the flow's WiFi … shared with the
  network nodes" with no API; the only who-manages-the-connection story is the MQTT one ("the flow's WiFi is
  left to the MQTT client"). Checked across custom-nodes, node-conventions, editor-in-depth, udp send,
  http request, mqtt subscribe and the FAQ. → Request `2026-11-27-wifi-for-network-nodes`, filed as
  mkarliner/ThingStudio#21.
- `ts_wifi` is already asked from the MQTT side in request `2026-11-26-ts-mqtt-client-for-nodes` ("what
  `ts_wifi` offers a node", still not filed); the two can be answered together.
- The repo's local `main` had diverged from `origin/main` (a local "first commit" carrying only a duplicated
  README line). Reconciled with `git pull --rebase`; the README conflict resolved to the one-line version.
  Commands that didn't work as given: bare `git pull` (no tracking information for the branch), then
  `git pull` again (divergent branches, no reconciliation strategy set).
- This session checked the **published** guide (docs.thingstudio.net, "follow the latest code") on 2026-11-27;
  no ThingStudio build is installed in this session's workspace, so nothing was checked against the copy a
  pinned build ships.

## Core requests (in `docs/core-requests/`)

| Request | Type | Status |
|---|---|---|
| `2026-11-27-wifi-for-network-nodes` | docs (or core) | Filed: mkarliner/ThingStudio#21 (2026-11-27). |

## How to resume

1. Check the state of mkarliner/ThingStudio#21. Unanswered: the set waits; nothing to build.
2. Answered: install the pinned ThingStudio build in the session's own workspace (never the shared folder),
   read the user guide that build ships (it matches the installed version), and take the answer as the design
   meets the docs — the docs win where they differ from this briefing.
3. Write `wake-on-lan/wake-on-lan/wol.node.json` and `wol.node.py` per the design above, plus the bundle
   `README.md` (install: copy the folder in; minimum build named there).
4. `SPEC.md` + `vectors/` from the payload contract; run the vectors in the same change.
5. The board pass on the kitchen-sink C3 per the test plan; settle the broadcast question there.
6. `THIRD-PARTY.md`: a line per change only when third-party code enters — expected none; the board code is
   MicroPython standard library plus what the guide documents.

## Toolchain this session used (named per AGENTS.md, briefings)

- No installs and nothing fetched: no ThingStudio or MicroPython build in the session's workspace, no Python
  or npm packages, no toolchain downloaded.
- Read: the published user guide at docs.thingstudio.net (latest code) on 2026-11-27 — pages: home,
  custom-nodes, node-conventions, udp send, mqtt subscribe, http request, editor-in-depth, FAQ.
- `git` — pull/rebase/commit; the not-working-as-given commands are under Findings.
- `gh` (GitHub CLI at `~/.local/bin/gh`) — filed mkarliner/ThingStudio#21. Not a package; no version pin
  needed by the ledger rules (nothing that runs on Mike's boards).
