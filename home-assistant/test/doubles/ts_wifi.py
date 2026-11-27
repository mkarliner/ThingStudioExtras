# SPDX-License-Identifier: Apache-2.0
# home-assistant/test/doubles/ts_wifi.py -- a test double for ThingStudio's `ts_wifi`, written from the user guide
# only (Writing a custom node: "The flow's WiFi: ts_wifi", ThingStudio a57d686b). It has nothing the guide doesn't
# describe, plus `reset()` for a redeploy and `calls` for a test to inspect.

calls = []  # the arguments of every ensure_station call
_values = None
_station = None


class _Station:
    """Stands in for the network.WLAN the guide says ensure_station returns."""

    def __init__(self):
        self.connected = True

    def isconnected(self):
        return self.connected


def ensure_station(ssid, password, security='password', defer_to_mqtt=False):
    global _values, _station
    values = (ssid, password, security, defer_to_mqtt)
    calls.append(values)
    if security not in ('password', 'open', 'unmanaged'):
        raise ValueError('ts_wifi double: security %r is not password, open or unmanaged' % (security,))
    if _values is None:
        _values = values
        _station = _Station()
    elif values != _values:
        raise ValueError('ts_wifi: %r differs from %r' % (values, _values))
    return _station


def reset():
    """A redeploy forgets the values (the guide: "A redeploy forgets the values and leaves the board on the network")."""
    global _values
    _values = None
    del calls[:]
