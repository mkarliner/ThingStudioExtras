# wol: the documented WiFi hook (user guide, custom-nodes, "The flow's WiFi: ts_wifi"). The node's
# Python sees only the credential's name, so the hook resolves the flow's one WiFi config and
# returns its values, with deferToMqtt worked out as the guide's example does.


def compile(ctx, properties):
    configs = ctx['flow']['configs']
    wifi_ids = [c['id'] for c in configs if c['type'] == 'thingstudio/config/wifi']
    broker_ids = [c['id'] for c in configs if c['type'] == 'thingstudio/config/mqtt-broker']
    wifi = (ctx.get('referencedConfigs') or {}).get(wifi_ids[0]) if len(wifi_ids) == 1 else None
    if wifi is None:
        return {'errors': ['needs the flow\'s WiFi -- set "WiFi" in its properties']}
    security = wifi.get('security')
    if security not in ('open', 'unmanaged'):
        security = 'password'
    mqtt = any(isinstance(v, str) and v in broker_ids
               for n in ctx['flow']['nodes'] for v in (n.get('properties') or {}).values())
    return {'properties': {
        'ssid': str(wifi.get('ssid') or '').strip(),
        'password': str(wifi.get('password') or ''),
        'security': security,
        'deferToMqtt': mqtt,
    }}
