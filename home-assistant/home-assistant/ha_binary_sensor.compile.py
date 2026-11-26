# ha_binary_sensor: builds the component dict (SPEC §4).


def compile(ctx, properties):
    if not [n for n in ctx['flow']['nodes'] if n['type'] == 'ha/device']:
        return {'errors': ['ha binary sensor needs an ha device node in the flow']}
    name = str(properties.get('name') or '').strip()
    if not name:
        return {'errors': ['ha binary sensor needs a name']}
    comp = {'p': 'binary_sensor', 'name': name}
    if properties.get('deviceClass') not in (None, '', 'none'):
        comp['dev_cla'] = properties['deviceClass']
    return {'properties': {'component': comp}}
