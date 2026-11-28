# SPDX-License-Identifier: Apache-2.0
# home-assistant/test/doubles/runtime.py -- a test double for ThingStudio's `runtime`, written from the user guide
# only (Writing a custom node: "Cleanup" for register_cleanup, "Persisting values" for settings: get(key, default),
# set(key, value) raising SettingsError when the store can't save, delete(key), keys()). It has nothing the guide
# doesn't describe.

import asyncio

cleanups = []  # (name, callable) in registration order, for a test to inspect or run


def register_cleanup(name, fn):
    cleanups.append((name, fn))


class SettingsError(Exception):
    pass


class _Settings:
    """The board's settings store, per the user guide; one store for the test's duration, namespaced by nothing
    here (the real one namespaces by flow name)."""

    def __init__(self):
        self.store = {}
        self.break_next = False

    def get(self, key, default=None):
        return self.store.get(key, default)

    def set(self, key, value):
        if self.break_next:
            self.break_next = False
            raise SettingsError('double: no room left on the board')
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)

    def keys(self):
        return list(self.store)

    def reset(self):
        self.store = {}
        self.break_next = False


settings = _Settings()
