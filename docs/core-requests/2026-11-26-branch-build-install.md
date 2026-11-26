# Installing a named branch build

**Type: docs.** Status: not filed.

## What we were trying to do

Install ThingStudio from the `user-libraries` branch (not yet released), because the Home Assistant bundle needs
bundles, user libraries and the `ts_mqtt` will and connect hook.

## What the user guide says

- Getting started (Option A installer, Option B package): releases only. Branch builds aren't mentioned.
- Installation details, "From source": "For working on ThingStudio itself." It says to run `make` "in the repository
  folder", but not how to get the repository (`git clone` of `mkarliner/ThingStudio`) or how to pick a branch.

## What happened

We could only get the branch by knowing, from outside the guide, to clone the repository and check out
`user-libraries`. After that, `make` worked as described (with the Python version caveat in
`2026-11-26-python-3-10-source-build.md`).

## What we need

A short section, probably under "From source", for people who need an unreleased feature: clone the repository,
check out the branch, then `make`, with a note that branch builds are unsupported and change without notice. If
pre-release packages are ever published from branches, say where.
