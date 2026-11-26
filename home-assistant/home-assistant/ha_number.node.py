import ts_ha

ts_ha.register(properties['nodeId'], properties['component'])
_last = {'value': None}


async def run(msg, properties):
    await ts_ha.publish_state(properties['nodeId'], msg.get('payload'))


async def wait(properties):
    _last['value'] = await ts_ha.command(properties['nodeId'], properties['echo'])


async def emit(properties):
    return {'payload': _last['value']}
