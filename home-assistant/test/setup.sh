#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# home-assistant/test/setup.sh -- fetch and build the two toolchains the tests use, at the pinned commits, in a work
# folder outside this repository (default $HOME/work). Fails on a commit mismatch rather than warning.
#
#   bash home-assistant/test/setup.sh [work folder]
#
# ThingStudio: ../THINGSTUDIO_VERSION, built by the user guide's "From source" route (make: npm ci --ignore-scripts,
# pip --require-hashes), then the check command. MicroPython: MICROPYTHON_VERSION, the unix port without frozen
# modules. Python 3.12.16 comes from the uv already installed (the branch needs 3.11+). Safe to re-run: each step
# skips what's already built, and the commit check runs every time.

set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo=$(realpath "$here/../..")
work=$(realpath -m "${1:-$HOME/work}")
case "$work/" in
  "$repo"/*) echo "setup: $work is inside the repository -- build outside it (CLAUDE.md)"; exit 2 ;;
esac
mkdir -p "$work"

pin() { sed -n "s/^commit: \([0-9a-f]\{40\}\).*/\1/p" "$1"; }

fetch() {
  local url=$1 commit=$2 dir=$3
  if [ ! -d "$dir/.git" ]; then
    git init -q "$dir"
    git -C "$dir" fetch -q --depth 1 "$url" "$commit"
    git -C "$dir" -c advice.detachedHead=false checkout -q FETCH_HEAD
  fi
  local got
  got=$(git -C "$dir" rev-parse HEAD)
  if [ "$got" != "$commit" ]; then
    echo "setup: $dir is at $got, the pin is $commit -- delete $dir and run again"
    exit 1
  fi
  echo "setup: $dir at $commit"
}

ts_commit=$(pin "$repo/home-assistant/THINGSTUDIO_VERSION")
mp_commit=$(pin "$here/MICROPYTHON_VERSION")
[ -n "$ts_commit" ] || { echo "setup: no full commit hash in THINGSTUDIO_VERSION"; exit 1; }
[ -n "$mp_commit" ] || { echo "setup: no full commit hash in MICROPYTHON_VERSION"; exit 1; }

command -v uv >/dev/null || { echo "setup: needs uv (the device shell has it); not fetching it"; exit 1; }

fetch https://github.com/mkarliner/ThingStudio "$ts_commit" "$work/ts"
uv python install 3.12.16 >/dev/null 2>&1
py=$(uv python find 3.12.16)
if [ ! -f "$work/ts/editor/dist-cli/thingstudio-compile.mjs" ]; then
  make -C "$work/ts" PYTHON="$py"
  (cd "$work/ts/editor" && npm run build:cli)
fi
echo "setup: THINGSTUDIO_COMPILE=$work/ts/editor/dist-cli/thingstudio-compile.mjs"

fetch https://github.com/micropython/micropython "$mp_commit" "$work/mp"
if [ ! -x "$work/mp/ports/unix/build-standard/micropython" ]; then
  make -C "$work/mp/ports/unix" -j4 MICROPY_PY_BTREE=0 MICROPY_PY_SSL=0 MICROPY_SSL_MBEDTLS=0 FROZEN_MANIFEST=
fi
echo "setup: micropython $work/mp/ports/unix/build-standard/micropython (asyncio from $work/mp/extmod)"
