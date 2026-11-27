# Wake on LAN

One node, `wol`, that sends a Wake-on-LAN magic packet from a ThingStudio board to the MAC address in each message, so
a board can wake a computer on its network. Small enough to read start to finish: the place to start if you're
writing your first custom node.

**Status:** work in progress: compile-checked and vector-tested; the board pass is still to do · **ThingStudio:**
v0.14.0 or newer · **Nodes:** `wol`

| Doc | For |
|---|---|
| [`wake-on-lan/README.md`](wake-on-lan/README.md) | using the node: install, payload, failures, example flows |
| [`docs/how-it-works.md`](docs/how-it-works.md) | writing your own nodes, with this one as the example |
| [`docs/SPEC.md`](docs/SPEC.md) | the contract: payload, packet, properties, every error message; `docs/vectors/` checks it |
| `test/` | `setup.sh` builds the pinned ThingStudio and MicroPython; `compile_test.py` and `vectors_test.py` say how to run them in their headers |

`tools/wol-listen.py` is a host-side listener for checking packets during the board pass. `docs/working-notes/` holds
the set's briefing: history, not documentation.
