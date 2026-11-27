import network
import ts_ha
import ts_mqtt
import ts_wifi

ts_wifi.ensure_station(properties['ssid'], properties['wifiPassword'], properties['security'], properties['deferToMqtt'])
_client = ts_mqtt.ensure_client(
    properties['broker'], properties['port'], properties['ssid'], properties['wifiPassword'],
    properties['security'], properties['username'], properties['brokerPassword'])


def _hostname():
    try:
        return network.hostname()
    except Exception:
        return 'thingstudio'


_board = properties.get('board') or {}
# No runtime version (HA's dev.sw): there's no documented way for a node to read it yet (ThingStudio #25).
ts_ha.configure_device(
    _client, properties['nodeId'], properties['deviceName'] or _hostname(),
    model=_board.get('boardName') or _board.get('label') or '',
    area=properties['area'], prefix=properties['prefix'])
_last = {'status': None}


async def wait(properties):
    _last['status'] = await ts_ha.ha_status(properties['nodeId'])


async def emit(properties):
    return {'payload': _last['status'], 'topic': properties['prefix'] + '/status'}
