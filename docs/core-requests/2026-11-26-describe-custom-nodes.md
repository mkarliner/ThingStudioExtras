# thingstudio-compile --describe doesn't see custom nodes

**Type: core** (or **docs**, if built-ins only is intended). Status: filed as [#26](https://github.com/mkarliner/ThingStudio/issues/26), 2026-11-27.

## What we were trying to do

Print the Home Assistant bundle's node types, ports and property defaults, to write test flows for them.

## What the user guide says

Check a flow without the editor, "Options": "`--describe timer` prints a node's type, ports and properties with their
defaults. `--describe-all` prints every node and config node". "`--custom-nodes ~/my-nodes` loads custom node
packages from that folder." Nothing says `--describe` leaves custom nodes out.

## What happened

```
node dist-cli/thingstudio-compile.mjs --custom-nodes cn --describe ha/select
thingstudio-compile: no node "ha/select". Try --describe-all.
```

`--describe-all` with the same `--custom-nodes` lists no `ha/` nodes either, while a flow check in the same call
reports "7 custom node packages loaded from cn".

## What we need

`--describe` and `--describe-all` to include the custom nodes `--custom-nodes` (or the default folder) loads, marked
as custom, so an author or an AI assistant can look them up the same way as built-ins. If built-ins only is
intended, the guide should say so.
