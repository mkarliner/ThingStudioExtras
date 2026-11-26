# ha_select: builds the component dict (SPEC §4); an unwired input means the node echoes choices (SPEC §3).


def compile(ctx, properties):
    if not [n for n in ctx['flow']['nodes'] if n['type'] == 'ha/device']:
        return {'errors': ['ha select needs an ha device node in the flow']}
    name = str(properties.get('name') or '').strip()
    if not name:
        return {'errors': ['ha select needs a name']}
    ops = [line.strip() for line in str(properties.get('options') or '').split('\n') if line.strip()]
    if not ops:
        return {'errors': ['ha select %r needs at least one option, one per line' % name]}
    seen = []
    for op in ops:
        if op in seen:
            return {'errors': ['ha select %r lists %r twice' % (name, op)]}
        seen.append(op)
    wired = ((ctx.get('node') or {}).get('wired') or {}).get('inputs') or [False]
    echo = not wired[0]
    warnings = []
    if echo:
        warnings.append('ha select %r: input not wired, so HA shows each choice as done -- wire the current option '
                        'back to the input to show what actually happened' % name)
    return {'properties': {'component': {'p': 'select', 'name': name, 'ops': ops}, 'echo': echo},
            'warnings': warnings}
