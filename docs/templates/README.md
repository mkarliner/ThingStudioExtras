# Templates for a set's docs

Skeletons for the docs every set has (AGENTS.md, "Documentation"). Copy one, keep its headings and their order, and
replace the guidance comments. A heading that doesn't apply stays, with one line saying why ("None: the node has no
output."), so sets stay comparable.

| Template | Becomes | Reader |
|---|---|---|
| `set-README.md` | `<set>/README.md` | someone browsing the repo |
| `bundle-README.md` | `<set>/<set>/README.md` | the user |
| `node-page.md` | `<set>/<set>/docs/<node>.md`, one per node, when the bundle README would get too long | the user |
| `how-it-works.md` | `<set>/docs/how-it-works.md` | a node author |

Worked examples: `wake-on-lan/` (one node, everything in the bundle README) and `home-assistant/` (seven nodes, a
page each).
