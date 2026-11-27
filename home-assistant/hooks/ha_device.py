# ha_device: resolves the WiFi and broker credentials (a node's Python sees only a config's name; the hook gets the
# secrets in referencedConfigs), checks the flow's HA nodes as a set (one ha device, node ids usable in topics) and
# the discovery message's size (SPEC §8). The WiFi and broker derivation follows the user guide's custom-nodes.md
# (ts_wifi and ts_mqtt sections, ThingStudio a57d686b).
#@include common.py
#@include-lib ts_ha.py BUNDLE_VERSION COMMANDABLE build_discovery

DISCOVERY_LIMIT = 4096   # SPEC §8
WORST_CHIP_ID = 'f' * 16  # machine.unique_id() as hex: 6 bytes on the ESP32s, up to 8 on other boards
WORST_HOSTNAME = 'x' * 32  # MicroPython's longest hostname, for a device left unnamed (the board names it)


def _discovery_size(ctx, properties, prefix):
    """The discovery message's size as ts_ha.build_discovery makes it on the board, for this flow's valid entities
    (an entity with an error reports it itself). Worst case for what only the board knows (chip id, hostname). Not
    counted: the short stubs for entities a previous flow announced and this one dropped (SPEC §7)."""
    components = {}
    for n in ctx['flow']['nodes']:
        if n['type'].startswith('ha/') and n['type'] != 'ha/device':
            comp, err = component(n['type'], n.get('properties') or {})
            if comp is not None:
                components[str(n['id'])] = comp
    target = ctx.get('target') or {}
    info = {'name': str(properties.get('deviceName') or '') or WORST_HOSTNAME,
            'model': target.get('boardName') or target.get('label') or '',
            'runtime': '', 'area': properties.get('area') or '', 'bundle': BUNDLE_VERSION}
    topic, payload, after = build_discovery(WORST_CHIP_ID, prefix, info, components, None)
    return json_size(payload), len(components)


def _resolved(ctx, config_type, what):
    configs = [c for c in ctx['flow']['configs'] if c['type'] == config_type]
    if len(configs) != 1:
        return None, 'ha device needs exactly one %s config in the flow (it has %d)' % (what, len(configs))
    cfg = (ctx.get('referencedConfigs') or {}).get(configs[0]['id'])
    if cfg is None:
        return None, 'ha device: pick the %s in its properties' % what
    return cfg, None


def compile(ctx, properties):
    errors = []
    warnings = []
    nodes = ctx['flow']['nodes']
    devices = ha_devices(ctx)
    if len(devices) > 1:
        errors.append('a flow can have only one ha device node (this one has %d)' % len(devices))
    ha_nodes = [n for n in nodes if n['type'].startswith('ha/')]
    for n in ha_nodes:
        nid = str(n['id'])
        if not nid or len(nid) > 32 or any(ch not in ID_CHARS for ch in nid):
            errors.append('node id %r can\'t be used in MQTT topics -- use letters, digits, _ and - (at most 32)' % nid)
    if len(ha_nodes) == len(devices):
        warnings.append('ha device has no entities -- add ha sensor, ha switch and so on')

    wifi, err = _resolved(ctx, 'thingstudio/config/wifi', 'WiFi')
    if err:
        errors.append(err)
    broker, err = _resolved(ctx, 'thingstudio/config/mqtt-broker', 'MQTT broker')
    if err:
        errors.append(err)
    if errors:
        return {'errors': errors}
    security = wifi.get('security')
    if security == 'unmanaged':
        return {'errors': ['ha device: MQTT manages the WiFi connection, so the WiFi config cannot be "unmanaged"']}
    if security != 'open':
        security = 'password'
    host = str(broker.get('broker') or '').strip()
    if not host:
        return {'errors': ['ha device: the broker config has no broker hostname']}
    # As the guide's hook: any node holding the flow's broker config is an MQTT node (this one does, so it's True).
    broker_ids = [c['id'] for c in ctx['flow']['configs'] if c['type'] == 'thingstudio/config/mqtt-broker']
    defer = any(isinstance(v, str) and v in broker_ids
                for n in nodes for v in (n.get('properties') or {}).values())
    prefix = str(properties.get('prefix') or 'homeassistant').strip().strip('/') or 'homeassistant'
    size, count = _discovery_size(ctx, properties, prefix)
    if size > DISCOVERY_LIMIT:
        return {'errors': ['ha device: the discovery message would be up to %d bytes for %d entities, over the 4 KB '
                           '(%d bytes) the board can build and send (SPEC §8) -- remove entities or shorten their '
                           'names, or split them across two boards' % (size, count, DISCOVERY_LIMIT)]}
    return {'warnings': warnings, 'properties': {
        'prefix': prefix,
        'ssid': str(wifi.get('ssid') or '').strip(),
        'wifiPassword': str(wifi.get('password') or ''),
        'security': security,
        'deferToMqtt': defer,
        'broker': host,
        'port': int(broker.get('port') or 1883),
        'username': str(broker.get('username') or ''),
        'brokerPassword': str(broker.get('password') or ''),
    }}
