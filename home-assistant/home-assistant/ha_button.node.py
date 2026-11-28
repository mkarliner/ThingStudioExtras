import ts_ha

ts_ha.register(properties['nodeId'], properties['component'], properties.get('start'))


async def wait(properties):
    await ts_ha.command(properties['nodeId'])


async def emit(properties):
    return {'payload': True, 'topic': properties['name']}
