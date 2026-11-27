# Third-party software

Every third-party dependency of a bundle, tool or test in this repository, with its licence. Update it in the same
change as the dependency (AGENTS.md, "Third-party code"). Versions and licences come from the package's own metadata or
licence file, not memory.

## Bundles (code that runs on a board)

| Bundle | Third-party code |
|---|---|
| `home-assistant` | None. Board code uses MicroPython and what the ThingStudio user guide documents. |
| `wake-on-lan` | None. Board code uses MicroPython and what the ThingStudio user guide documents. |

## Tools

| Package | Version | Licence | Used by | Pinned in |
|---|---|---|---|---|
| paho-mqtt | 2.2.0 (wheel, PyPI) | EPL-2.0 OR BSD-3-Clause | `home-assistant/tools/ha-probe.py`, `ha-cleanup.py` | `home-assistant/tools/requirements.txt` (sha256) |

## Test toolchains (built in a work folder outside the repository, never shipped)

| Component | Version | Licence | Source | Pinned in |
|---|---|---|---|---|
| ThingStudio (`thingstudio-compile`) | v0.14.0 (`main` @ 416f886f) | Apache-2.0 | github.com/mkarliner/ThingStudio | `home-assistant/THINGSTUDIO_VERSION` (full commit) |
| MicroPython (unix port) | v1.29.0 @ 0fd6c573 | MIT | github.com/micropython/micropython | `home-assistant/test/MICROPYTHON_VERSION` (full commit) |
| CPython (for ThingStudio's build) | 3.12.16 | PSF-2.0 | uv's managed download (checksummed by uv) | `uv python install 3.12.16` in `home-assistant/test/setup.sh` |
| ThingStudio (`thingstudio-compile`) | `main` @ a57d686b | Apache-2.0 | github.com/mkarliner/ThingStudio | `wake-on-lan/THINGSTUDIO_VERSION` (full commit) |
| MicroPython (unix port) | v1.29.0 @ 0fd6c573 | MIT | github.com/micropython/micropython | `wake-on-lan/test/MICROPYTHON_VERSION` (full commit) |

ThingStudio's own build pulls its npm and Python packages from its lockfile and hashed requirements; they're
ThingStudio's dependencies and are listed in its ledger, not here. `uv` is the device shell's own, not fetched.
