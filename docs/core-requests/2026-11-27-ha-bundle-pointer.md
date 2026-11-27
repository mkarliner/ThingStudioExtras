# Point users at the Home Assistant node set

**Type: docs.** Status: not filed. Waits for Mike: the HA set's end-to-end test (plan 1.9), and a public URL for it.

## What we were trying to do

Finish plan task 1.10 for the `home-assistant` set: "In ThingStudio: a short pointer from `custom-nodes.md` and the
nodes catalog." A user who wants their board in Home Assistant has no way to find out the set exists.

## What the user guide says

- *Writing a custom node, "Bundles"* shows a `home-assistant/` bundle as the example layout, but doesn't say one
  exists.
- *Node catalog* (`nodes-catalog.md`) is generated from the compiler (`--describe-all --markdown`), with a test that
  fails on hand edits, so a pointer can't go there. The node reference (`nodes/index.md`) is hand-written.

## What we need

Two short additions, proposed text below. `<URL>` is where the set is published (to decide: ThingStudioExtras is
the source today).

In `custom-nodes.md`, at the end of "Bundles":

> The Home Assistant node set is a bundle: an `ha device` node and entity nodes (sensor, binary sensor, switch,
> number, select, button) that make a board a Home Assistant device over MQTT discovery. Get it from `<URL>`; its
> README covers installing it and setting up MQTT in Home Assistant.

In `nodes/index.md`, after the built-in nodes:

> **More nodes.** Node sets that don't ship with ThingStudio install as [custom nodes](../custom-nodes.md#bundles).
> The [Home Assistant set](<URL>) makes a board a Home Assistant device: its sensors, switches and controls appear
> there with no YAML.
