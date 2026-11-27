# thingstudio-compile for users who installed a release

**Type: core** (could be answered by docs if source-only is intended). Status: filed as [#22](https://github.com/mkarliner/ThingStudio/issues/22), 2026-11-27. The docs side is done on `main` by 00b98637 (Check a flow says it needs a source build "yet"); the core ask is open.

## What we were trying to do

Check the Home Assistant bundle's example flows from the command line, as a custom-node author with an installed
ThingStudio.

## What the user guide says

"Check a flow without the editor", "Build it": from the `editor/` folder, `npm ci --ignore-scripts` then
`npm run build:cli`, which writes `dist-cli/thingstudio-compile.mjs`. Getting started and Installation details
(package, installer script) don't mention `thingstudio-compile`, and a package "doesn't add a `thingstudio`
command" beyond the editor.

## What happened

Only a source checkout can produce the command. Someone who installed a release package or used the installer script
has no `editor/` folder and no `thingstudio-compile`. The page's own audience ("in a script, in CI, or to let an AI
assistant check a flow") is mostly those users.

## What we need

`thingstudio-compile` available from a normal install: shipped in the release packages and linked by the installer
script next to `thingstudio`, or a published package (`npx thingstudio-compile`). If source-only is intended, the page
should say so at the top.
