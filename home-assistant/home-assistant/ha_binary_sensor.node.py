import ts_ha

ts_ha.register(properties['nodeId'], properties['component'], properties.get('start'))


async def run(msg, properties):
    await ts_ha.publish_state(properties['nodeId'], msg.get('payload'))
