# ha_button: builds the component dict (SPEC §4).


def compile(ctx, properties):
    if not [n for n in ctx['flow']['nodes'] if n['type'] == 'ha/device']:
        return {'errors': ['ha button needs an ha device node in the flow']}
    name = str(properties.get('name') or '').strip()
    if not name:
        return {'errors': ['ha button needs a name']}
    return {'properties': {'component': {'p': 'button', 'name': name}}}
