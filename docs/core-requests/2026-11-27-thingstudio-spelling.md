# "Thingstudio" in the About box and the custom images' chip type

**Type: core.** Status: answered by the core session, 2026-11-27; nothing to file. The About box is fixed on `main`
(0ce2f4ac) and ships in the next release. The custom images' `chipType` is built into each firmware image, so it
changes at the next runtime bump, when every image is rebuilt. Check both then, and close this.

Found during the Home Assistant bundle's hardware pass, ThingStudio App 0.14.0 (commit 416f886f), macOS, ESP32-C3 on
the ThingStudio custom image (runtime 15.2.0).

## What we were trying to do

Check the editor's version in **Help → About** before an end-to-end test, and read the board's HELLO in the console.

## What the user guide says

The name is ThingStudio, with a capital S, throughout the guide.

## What happened

The About box's title and first line read "Thingstudio 0.14.0". The board's HELLO from the custom image reports
`"chipType":"Thingstudio ESP32-C3 (generic) with ESP32-C3"`, which the console repeats in its `[board]` line.

## What we need

"ThingStudio" in the About box and in the custom images' chip type.

## Withdrawn

The first version of this request also reported the console's version check saying `targets 15.1.0` on v0.14.0.
That came from an older editor tab still open: after closing every tab and restarting the backend, v0.14.0 prints
`targets 15.2.0`, matching the About box. Not a core bug. (A user upgrading with the editor open in a tab could meet
the same thing.)
