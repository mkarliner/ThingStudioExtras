import network
import sys
import ts_ha
import ts_mqtt
import ts_wifi

ts_wifi.ensure_station(properties['ssid'], properties['wifiPassword'], properties['security'], True)
_client = ts_mqtt.ensure_client(
    properties['broker'], properties['port'], properties['ssid'], properties['wifiPassword'],
    properties['security'], properties['username'], properties['brokerPassword'])


def _runtime_version():
    v = getattr(sys.modules.get('listener'), '_RUNTIME_VERSION', None)
    if isinstance(v, dict):
        return '%s.%s.%s' % (v.get('major'), v.get('minor'), v.get('patch'))
    return ''


def _hostname():
    try:
        return network.hostname()
    except Exception:
        return 'thingstudio'


_board = properties.get('board') or {}
ts_ha.configure_device(
    _client, properties['nodeId'], properties['deviceName'] or _hostname(),
    model=_board.get('boardName') or _board.get('label') or '', runtime_version=_runtime_version(),
    area=properties['area'], prefix=properties['prefix'])
_last = {'status': None}


async def wait(properties):
    _last['status'] = await ts_ha.ha_status(properties['nodeId'])


async def emit(properties):
    return {'payload': _last['status'], 'topic': properties['prefix'] + '/status'}
