# Project rules for ThingStudioExtras

ThingStudioExtras holds optional add-ons for ThingStudio: custom node bundles (the first is `home-assistant/`),
their libraries, tools and tests. Nothing here ships with ThingStudio; a user installs a bundle by copying its folder
into `~/.thingstudio/custom-nodes/`.

## We are a ThingStudio user, not a ThingStudio developer (Mike, 2026-11-25)

This repo exists partly to dogfood ThingStudio. Work here as an outside custom-node author would, with what an
outside author has:

- **Read only the user documentation.** The user guide as published at https://docs.thingstudio.net/, or the copy
  that ships with the installed ThingStudio (the editor serves it at `/docs`). Its source, `docs/user-guide/` in
  `mkarliner/ThingStudio`, counts as the same thing. Nothing else from the core repo: not the code, the tests and
  their fixtures (pymock), `interfaces/`, the design doc, `docs/working-notes/`, or core's project docs and
  briefings.
- **Use only an installed ThingStudio.** Install it the way the user guide says (a release, or a named branch
  build when a bundle needs something unreleased), in the session's own workspace. `thingstudio-compile` and the
  editor come from that install. Never a checkout of core beside this repo, and never a path into one.
- **When the docs don't say, that is a finding.** Don't guess from memory of the core code and don't go and read it.
  Write down the question as a user would ask it, then either carry on with what the docs do say or stop and raise
  a core request.
- **Core changes go through a request, never a direct edit.** See below.

`docs/working-notes/home-assistant-phase-0-briefing.md` and Phase 0 of the HA plan are the core-side record from
before this rule, and name core files. They are history, not a source on core.

The test for any doubt: could someone who has only installed ThingStudio and read its docs do this? If not, it is
either a core request or not something to do here.

## Core requests

When a bundle needs something core doesn't offer, or the docs are missing, wrong or unclear:

1. Write the request in `docs/core-requests/YYYY-MM-DD-<slug>.md`: what we were trying to do, what the user guide
   says (page and section), what happened (exact command and output), and what we need. Write it from the user's
   side: describe the behaviour wanted, not an implementation in core files you haven't seen.
2. Mark it **docs** (the guide is missing or wrong; a pull request against `docs/user-guide/` only, with the proposed
   text) or **core** (behaviour; an issue on `mkarliner/ThingStudio`).
3. Mike files it, or the session does if it has GitHub access to ThingStudio for that. Add the PR or issue link to
   the file. The work itself happens in the ThingStudio project, not here.
4. Until it lands, the bundle works within what's documented, or the task waits. No workarounds that lean on
   undocumented behaviour.

## Interface specs in this repo

Each bundle's contract with the outside world has a spec, e.g. `docs/working-notes/home-assistant/SPEC.md` with
`vectors/`. Read it before changing anything it defines, run its vectors in the same change, and change the spec
itself only with Mike's permission in the session.

## Engineering rules carried over from ThingStudio

The user guide states the ones a node author meets. These also apply here:

- **Fault handling over the happy path.** One deterministic path, each step a named state with one clear failure.
  No recovery chains. Every failure message says what happened, the figure that names it, and what the user can do.
- **No trivial implementation that won't scale.** Prefer the comprehensive design, or leave the feature out.
- **The name is ThingStudio** (capital S) in docs and UI text.
- Don't use the phrase "load bearing".

## Secrets

`env.sh` holds Mike's HA token and broker credentials for `tools/`. It is git-ignored and must stay out of commits,
docs, briefings and chat. Tools read credentials from the environment only.
