# ha_number: builds the component dict (SPEC §4); an unwired input means the node echoes changes (SPEC §3).


def _num(value, what, name):
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, 'ha number %r: %s must be a number' % (name, what)


def compile(ctx, properties):
    if not [n for n in ctx['flow']['nodes'] if n['type'] == 'ha/device']:
        return {'errors': ['ha number needs an ha device node in the flow']}
    name = str(properties.get('name') or '').strip()
    if not name:
        return {'errors': ['ha number needs a name']}
    values = {}
    for key in ('min', 'max', 'step'):
        v, err = _num(properties.get(key), key, name)
        if err:
            return {'errors': [err]}
        values[key] = int(v) if v == int(v) else v
    if values['min'] >= values['max']:
        return {'errors': ['ha number %r: min must be below max' % name]}
    if values['step'] <= 0:
        return {'errors': ['ha number %r: step must be above 0' % name]}
    comp = {'p': 'number', 'name': name, 'min': values['min'], 'max': values['max'], 'step': values['step'],
            'mode': properties.get('mode') or 'slider'}
    unit = str(properties.get('unit') or '').strip()
    if unit:
        comp['unit_of_meas'] = unit
    wired = ((ctx.get('node') or {}).get('wired') or {}).get('inputs') or [False]
    echo = not wired[0]
    warnings = []
    if echo:
        warnings.append('ha number %r: input not wired, so HA shows each change as done -- wire the real value back '
                        'to the input to show what actually happened' % name)
    return {'properties': {'component': comp, 'echo': echo}, 'warnings': warnings}
