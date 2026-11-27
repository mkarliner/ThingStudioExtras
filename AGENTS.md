# Project rules for ThingStudioExtras

ThingStudioExtras holds optional add-ons for ThingStudio: custom node bundles (the first is `home-assistant/`),
their libraries, tools and tests. Nothing here ships with ThingStudio; a user installs a bundle by copying its folder
into `~/.thingstudio/custom-nodes/`.

## Layout: one folder per node set

Each set of related nodes has its own top-level folder, and a session normally works inside one of them. Read the
working notes of the set you're working on, not the others.

```
<set>/
  <set>/                 the bundle: exactly what the user copies into ~/.thingstudio/custom-nodes/
  docs/working-notes/    scoping, plan, briefings, the set's interface SPEC.md and vectors/
  tools/  hooks/  test/  development-only, never copied
```

Repo-wide: `AGENTS.md`, `CLAUDE.md`, `THIRD-PARTY.md` (the third-party ledger), and `docs/core-requests/`
(requests from any set).

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

`home-assistant/docs/working-notes/phase-0-briefing.md` and Phase 0 of the HA plan are the core-side record from
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

Each bundle's contract with the outside world has a spec, e.g. `home-assistant/docs/working-notes/SPEC.md` with
`vectors/`. Read it before changing anything it defines, run its vectors in the same change, and change the spec
itself only with Mike's permission in the session.

## Engineering rules carried over from ThingStudio

The user guide states the ones a node author meets. These also apply here:

- **Fault handling over the happy path.** One deterministic path, each step a named state with one clear failure.
  No recovery chains. Every failure message says what happened, the figure that names it, and what the user can do.
- **No trivial implementation that won't scale.** Prefer the comprehensive design, or leave the feature out.
- **The name is ThingStudio** (capital S) in docs and UI text.
- Don't use the phrase "load bearing".

## Third-party code: pinned, scriptless, gated (Mike, 2026-11-26; aligned with ThingStudio's rules 2026-11-27)

Anything fetched from outside this repository (Python and npm packages, the ThingStudio and MicroPython builds the
tests use, toolchains) is code that runs on Mike's machine or his boards. It is untrusted until it is all three:

- **Pinned** to an immutable identifier: a full commit hash, an exact version with its hash, a lockfile. A tag or a
  branch name can move, so it isn't a pin on its own.
- **Installed without its own code running:** `npm ci --ignore-scripts`; pip with `--only-binary :all:` (wheels,
  no build scripts).
- **Checked by something that fails, not warns, when it changes:** pip `--require-hashes`, `npm ci` against the
  committed lockfile, a commit check like `home-assistant/test/setup.sh`'s.

And:

- **Warn Mike before adding or installing a package:** name it and say why. Prefer fewer dependencies and
  sanity-check a new one (maintenance, install scripts). A bundle's board code uses MicroPython and what the user
  guide documents, nothing else.
- **npm:** `npm ci`, never a bare `npm install` once a lockfile exists, and commit the lockfile. No git-URL
  dependencies. No bulk upgrades (`npm update`, `ncu -u`): review each. Never an arbitrary `npx <package>`; `npx --no`
  for one that isn't already a dependency.
- **Prefer a tool that's already installed** (the device shell has `uv`) to fetching one.
- **Install instructions never give `curl | sh` alone:** a plain download (a releases page) alongside, as an equal
  choice, and how to read the script first.
- **Ledger:** every third-party dependency of a bundle, tool or test gets a line in `THIRD-PARTY.md` in the same
  change, with version and licence from the package's own metadata.
- **Briefings** name every toolchain the session used and what was fetched, from where, at which version, including
  commands that didn't work.
- **Never install or build against the shared folder** (CLAUDE.md): work in the session's own workspace.

## Secrets

`env.sh` holds Mike's HA token and broker credentials for `home-assistant/tools/`. It is git-ignored and must stay out of commits,
docs, briefings and chat. Tools read credentials from the environment only.
