# ha_binary_sensor: builds the component dict (SPEC §4) so the board only adds ids and topics.
#@include common.py


def compile(ctx, properties):
    return entity_compile(ctx, 'ha/binary_sensor', properties)
