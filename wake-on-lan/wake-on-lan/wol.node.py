import socket
import ts_wifi

from wol_packet import parse_mac, dest, magic_packet

_sta = ts_wifi.ensure_station(properties['ssid'], properties['password'], properties['security'],
                              properties['deferToMqtt'])

_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
runtime.register_cleanup('wol_socket', lambda: _sock.close())


async def run(msg, properties):
    payload = msg.get('payload')
    if not isinstance(payload, dict) or 'mac' not in payload:
        raise ValueError("wol: payload must be a dict with a 'mac' entry, got %r" % (payload,))
    target = dest(payload.get('ip'))
    packet = magic_packet(parse_mac(payload['mac']))
    if not _sta.isconnected():
        raise OSError("wol: the flow's WiFi is not connected -- check the flow's WiFi config, or send again once it is up")
    try:
        for _ in range(properties['repeats']):
            _sock.sendto(packet, (target, properties['port']))
    except OSError as e:
        raise OSError("wol: send to %s:%d failed: %s" % (target, properties['port'], e))
