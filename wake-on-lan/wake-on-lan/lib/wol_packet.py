# wol_packet: the pure functions behind the wol node -- MAC parsing, the destination, the magic
# packet. No imports and no runtime calls, so the SPEC vectors run them under MicroPython and
# CPython alike (test/vectors_test.py).


def parse_mac(text):
    # The target's MAC address as six byte pairs, hex, case-insensitive. The separators are
    # colons, dashes or dots (each is what its own world shows), or none at all.
    if not isinstance(text, str):
        raise ValueError("wol: the payload's 'mac' must be a string, got %r" % (text,))
    t = text.upper()
    for sep in (':', '-', '.'):
        t = t.replace(sep, '')
    if len(t) != 12:
        raise ValueError("wol: %r is not a MAC address -- 6 byte pairs, hex, e.g. AA:BB:CC:DD:EE:FF" % (text,))
    for c in t:
        if c not in '0123456789ABCDEF':
            raise ValueError("wol: %r is not a MAC address -- 6 byte pairs, hex, e.g. AA:BB:CC:DD:EE:FF" % (text,))
    return bytes.fromhex(t)


def dest(value):
    # The destination from the payload's 'ip' entry: an IPv4 address, or the broadcast when absent.
    if value is None or value == '':
        return '255.255.255.255'
    if not isinstance(value, str):
        raise ValueError("wol: the payload's 'ip' must be a string, got %r" % (value,))
    ip = value.strip()
    parts = ip.split('.')
    if len(parts) != 4:
        raise ValueError("wol: %r is not an IPv4 address, e.g. 192.168.1.50" % (value,))
    for p in parts:
        if not p.isdigit() or len(p) > 3 or int(p) > 255 or (len(p) > 1 and p[0] == '0'):
            raise ValueError("wol: %r is not an IPv4 address, e.g. 192.168.1.50" % (value,))
    return ip


def magic_packet(mac):
    # The Wake-on-LAN magic packet: six 0xFF bytes, then the MAC address sixteen times. 102 bytes.
    return b'\xff' * 6 + mac * 16
