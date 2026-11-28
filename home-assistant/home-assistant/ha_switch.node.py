import ts_ha

ts_ha.register(properties['nodeId'], properties['component'], properties.get('start'))
_last = {'value': None, 'started': False}


async def run(msg, properties):
    await ts_ha.publish_state(properties['nodeId'], msg.get('payload'))


async def wait(properties):
    if not _last['started']:
        _last['started'] = True
        value = await ts_ha.start(properties['nodeId'], properties['echo'])
        if value is not None:
            _last['value'] = value
            return
    _last['value'] = await ts_ha.command(properties['nodeId'], properties['echo'])


async def emit(properties):
    return {'payload': _last['value'], 'topic': properties['name']}
