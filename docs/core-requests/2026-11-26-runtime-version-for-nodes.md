# Reading the device runtime version from a custom node

**Type: core.** Status: not filed.

## What we were trying to do

The Home Assistant bundle's `ha device` node reports the device's software version to HA (`sw` in HA's device
registry, shown on the device page), so a user can see which ThingStudio runtime a board runs.

## What the user guide says

Nothing. `custom-nodes.md` documents `runtime.register_cleanup`, `runtime.settings`, `runtime.shared`,
`runtime.report_status` and `runtime.asyncio`, and the `target` property kind (board and processor, not the
runtime). The runtime version appears only as something the editor or the command line shows: Flow lifecycle
("Tools → Check status"), Custom firmware (the console's version line), Command line (`device_cli.py hello`).

## What happened

The bundle reads a module-level value from one of the runtime's own modules
(`sys.modules['listener']._RUNTIME_VERSION`), found outside the guide. It works today and can break with any runtime
change.

## What we need

A documented, stable way for a node's Python to read the runtime version, e.g. `runtime.version` as a string such
as `15.1.0` (or a tuple). Until then the bundle should leave `sw` out of the discovery message rather than reach into
the runtime.
