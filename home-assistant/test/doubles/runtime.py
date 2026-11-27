# SPDX-License-Identifier: Apache-2.0
# home-assistant/test/doubles/runtime.py -- a test double for ThingStudio's `runtime`, written from the user guide
# only (Writing a custom node: "Cleanup" for register_cleanup, "Event-driven sources" for runtime.asyncio). It has
# nothing the guide doesn't describe.

import asyncio

cleanups = []  # (name, callable) in registration order, for a test to inspect or run


def register_cleanup(name, fn):
    cleanups.append((name, fn))
