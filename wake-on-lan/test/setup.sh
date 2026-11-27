#!/usr/bin/env bash
# wake-on-lan test setup: build the pinned ThingStudio and MicroPython builds in a work folder.
#
# Usage: bash wake-on-lan/test/setup.sh [workdir]      (default: $HOME/work)
#
# It fetches mkarliner/ThingStudio (the user guide's "From source" route: git, Python 3.11+,
# Node.js 22, make) and micropython/micropython (its unix port, for the SPEC vectors' second
# interpreter) at the full commits in ../THINGSTUDIO_VERSION and MICROPYTHON_VERSION. A checkout
# anywhere else is a failure, not a silent rebuild. MicroPython's submodules are the exact commits
# recorded in that pinned tree. It refuses to build in the shared ~/.thingstudio folder or inside
# this repository, per AGENTS.md.
set -euo pipefail

SET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$SET_DIR/.." && pwd)"
WORK="${1:-$HOME/work}"

case "$WORK" in
    "$HOME/.thingstudio"*)
        echo "refusing work folder '$WORK': never the shared ~/.thingstudio folder" >&2
        exit 1
        ;;
    "$REPO_ROOT"*)
        echo "refusing work folder '$WORK': never inside this repository" >&2
        exit 1
        ;;
esac

pin() { sed -n "s/^$1: \([0-9a-f]\{40\}\).*/\1/p" "$2"; }

TS_PIN="$(pin commit "$SET_DIR/THINGSTUDIO_VERSION")"
MP_PIN="$(pin commit "$SET_DIR/test/MICROPYTHON_VERSION")"
if [ -z "$TS_PIN" ] || [ -z "$MP_PIN" ]; then
    echo "missing full commit in $SET_DIR/THINGSTUDIO_VERSION or $SET_DIR/test/MICROPYTHON_VERSION" >&2
    exit 1
fi

TS_REPO="$WORK/ThingStudio"
if [ ! -d "$TS_REPO/.git" ]; then
    git clone https://github.com/mkarliner/ThingStudio.git "$TS_REPO"
fi
HEAD="$(git -C "$TS_REPO" rev-parse HEAD)"
if [ "$HEAD" != "$TS_PIN" ]; then
    echo "refusing to build: $TS_REPO is at $HEAD, the set pins $TS_PIN" >&2
    echo "check it out (git -C \"$TS_REPO\" fetch origin && git -C \"$TS_REPO\" checkout $TS_PIN), then re-run" >&2
    exit 1
fi

MP_REPO="$WORK/micropython"
if [ ! -d "$MP_REPO/.git" ]; then
    git clone https://github.com/micropython/micropython.git "$MP_REPO"
fi
HEAD="$(git -C "$MP_REPO" rev-parse HEAD)"
if [ "$HEAD" != "$MP_PIN" ]; then
    echo "refusing to build: $MP_REPO is at $HEAD, the set pins $MP_PIN" >&2
    echo "check it out (git -C \"$MP_REPO\" fetch origin && git -C \"$MP_REPO\" checkout $MP_PIN), then re-run" >&2
    exit 1
fi
git -C "$MP_REPO" submodule update --init --recursive   # the submodules at the commits the pin records

make -C "$TS_REPO"
echo "built: $TS_REPO (ThingStudio at $TS_PIN)"

make -C "$MP_REPO" ports/unix
echo "built: $MP_REPO (MicroPython at $MP_PIN; binary: $MP_REPO/ports/unix/build-standard/micropython)"
