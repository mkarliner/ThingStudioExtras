# ThingStudioExtras

Optional custom nodes for [ThingStudio](https://thingstudio.net), the flow-based editor for MicroPython boards.
Nothing here ships with ThingStudio. Each set below is a self-contained folder: to use one, copy its bundle folder
into `~/.thingstudio/custom-nodes/` and click **Reload custom nodes** in the editor. The set's own README says what
it needs.

## Sets

| Set | Nodes | Status | ThingStudio |
|---|---|---|---|
| [Home Assistant](home-assistant/) | `ha device`, `ha sensor`, `ha binary sensor`, `ha switch`, `ha number`, `ha select`, `ha button` | work in progress | v0.14.0 or later |
| [Wake on LAN](wake-on-lan/) | `wol` | work in progress | v0.14.0 or newer |

Custom nodes need the ThingStudio App; ThingStudio Web has none.

## Writing your own nodes

Start with the user guide's [Writing custom nodes](https://docs.thingstudio.net/custom-nodes/) and
[Node conventions](https://docs.thingstudio.net/node-conventions/). Each set here is meant as a worked example, with
a `docs/how-it-works.md` that explains it against the guide. [Wake on LAN](wake-on-lan/docs/how-it-works.md) is one
node and the place to begin; Home Assistant is the larger example.

Every set is laid out the same way:

```
<set>/
  README.md              the set at a glance
  <set>/                 the bundle: what you copy into custom-nodes/ (its README is the user docs)
  docs/                  how-it-works.md, and the set's SPEC.md and vectors/ if it has an external contract
  test/  tools/          development only
```

## Working on this repo

`AGENTS.md` has the rules: the layout, documentation (`docs/templates/`, checked by `python3 docs/check-docs.py`),
requests to ThingStudio core (`docs/core-requests/`), and third-party code (`THIRD-PARTY.md`).
