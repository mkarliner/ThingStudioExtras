#!/usr/bin/env python3
# wake-on-lan/tools/wol-listen.py -- host-side Wake-on-LAN listener for the board pass.
#
# Listens on a UDP port and prints each datagram's size and bytes, so a magic packet can be
# verified by eye (or by its "magic packet ok" line). Standard library only; nothing here is
# copied to the board.
#
#   python3 wake-on-lan/tools/wol-listen.py [port]        (default port 9)
#
# Port 9 is privileged: run it with sudo, or set the wol node's port to an unprivileged value
# (say 9090) and pass that here.

import socket
import sys

port = int(sys.argv[1]) if len(sys.argv) > 1 else 9
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', port))
print('listening on 0.0.0.0:%d -- waiting for datagrams' % port)

while True:
    data, addr = sock.recvfrom(2048)
    print('from %s:%d -- %d bytes: %s%s' % (
        addr[0], addr[1], len(data), data[:24].hex(), '...' if len(data) > 24 else ''))
    if len(data) == 102 and data[:6] == b'\xff' * 6:
        print('  magic packet ok (6 x 0xFF + MAC x 16); MAC = %s' %
              ':'.join('%02x' % b for b in data[6:12]))
