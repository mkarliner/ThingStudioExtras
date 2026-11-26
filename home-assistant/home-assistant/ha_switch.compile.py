# ha_switch: builds the component dict (SPEC §4); an unwired input means the node echoes commands (SPEC §3).


def compile(ctx, properties):
    if not [n for n in ctx['flow']['nodes'] if n['type'] == 'ha/device']:
        return {'errors': ['ha switch needs an ha device node in the flow']}
    name = str(properties.get('name') or '').strip()
    if not name:
        return {'errors': ['ha switch needs a name']}
    comp = {'p': 'switch', 'name': name}
    if properties.get('deviceClass') not in (None, '', 'none'):
        comp['dev_cla'] = properties['deviceClass']
    wired = ((ctx.get('node') or {}).get('wired') or {}).get('inputs') or [False]
    echo = not wired[0]
    warnings = []
    if echo:
        warnings.append('ha switch %r: input not wired, so HA shows each command as done -- wire the real state back '
                        'to the input to show what actually happened' % name)
    return {'properties': {'component': comp, 'echo': echo}, 'warnings': warnings}
