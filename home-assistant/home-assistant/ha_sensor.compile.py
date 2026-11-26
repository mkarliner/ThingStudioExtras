# ha_sensor: builds the component dict (SPEC §4) so the board only adds ids and topics.

_UNITS = {
    'temperature': ('°C', '°F', 'K'),
    'humidity': ('%',),
    'battery': ('%',),
    'pressure': ('Pa', 'hPa', 'kPa', 'bar', 'mbar', 'mmHg', 'inHg', 'psi'),
    'illuminance': ('lx',),
    'voltage': ('V', 'mV'),
    'current': ('A', 'mA'),
    'power': ('W', 'kW'),
    'energy': ('Wh', 'kWh', 'MWh'),
    'signal_strength': ('dB', 'dBm'),
    'duration': ('d', 'h', 'min', 's', 'ms'),
}


def _devices(ctx):
    return len([n for n in ctx['flow']['nodes'] if n['type'] == 'ha/device'])


def compile(ctx, properties):
    if _devices(ctx) == 0:
        return {'errors': ['ha sensor needs an ha device node in the flow']}
    name = str(properties.get('name') or '').strip()
    if not name:
        return {'errors': ['ha sensor needs a name']}
    comp = {'p': 'sensor', 'name': name}
    dev_cla = properties.get('deviceClass') or ''
    if dev_cla == 'none':
        dev_cla = ''
    unit = str(properties.get('unit') or '').strip()
    if dev_cla:
        allowed = _UNITS.get(dev_cla)
        if allowed and unit not in allowed:
            return {'errors': ['ha sensor %r: a %s sensor\'s unit must be one of %s' % (name, dev_cla, ', '.join(allowed))]}
        comp['dev_cla'] = dev_cla
    if unit:
        comp['unit_of_meas'] = unit
    if properties.get('stateClass') not in (None, '', 'none'):
        comp['stat_cla'] = properties['stateClass']
    icon = str(properties.get('icon') or '').strip()
    if icon:
        comp['ic'] = icon
    return {'properties': {'component': comp}}
