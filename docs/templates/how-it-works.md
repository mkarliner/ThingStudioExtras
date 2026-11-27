# How <set> works

<!-- For someone writing their own custom nodes, who wants a real example to copy from. It assumes the user guide's
"Writing custom nodes" page and explains this set against it: which sections each file relies on, and why it's built
this way. Explain only what an author with the user guide could do; anything that needed more is a core request. -->

## What it does

<!-- Two sentences, and a link to the bundle README for the user's view. -->

## The files

<!-- A table: each file in the bundle, its job, and the user-guide section it follows. Then the development-only
files (test/, tools/, THINGSTUDIO_VERSION). -->

## Walkthrough

<!-- The descriptor, the compile hook, the node's Python, the library: each with the lines that matter quoted and
explained. Follow a message through. -->

## Design decisions

<!-- Choices an author would want to know about, and the alternatives turned down: what goes in properties vs the
payload, where validation happens, how failures are named, what runs at compile time vs on the board. -->

## Testing

<!-- What's tested, how, and against what (SPEC vectors, thingstudio-compile, a board pass). What isn't tested yet. -->

## Making your own from this

<!-- What to copy, what to rename, what to change, for a node of a similar kind. -->
