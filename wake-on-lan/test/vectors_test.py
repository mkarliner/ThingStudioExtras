# wake-on-lan vectors: run lib/wol_packet.py against docs/working-notes/vectors/values.json.
# From the repository root, under CPython and the pinned MicroPython's unix port:
#   python3 wake-on-lan/test/vectors_test.py
#   MICROPYPATH=wake-on-lan/wake-on-lan/lib micropython wake-on-lan/test/vectors_test.py
# Exit 0 when every case passes; a failure names the case and the mismatch.

import json
import sys

sys.path.insert(0, 'wake-on-lan/wake-on-lan/lib')
import wol_packet

_failed = 0


def check(name, got, want):
    global _failed
    if got != want:
        _failed += 1
        print('FAIL %s: got %r, want %r' % (name, got, want))


def expect_error(name, fn, value, want):
    global _failed
    try:
        got = fn(value)
    except ValueError as e:
        check(name + ' (error)', str(e), want)
        return
    _failed += 1
    print('FAIL %s (error): no error, got %r' % (name, got))


with open(sys.argv[1] if len(sys.argv) > 1 else
          'wake-on-lan/docs/working-notes/vectors/values.json') as f:
    vectors = json.load(f)

total = 0
for case in vectors['mac']:
    total += 1
    if 'expect' in case:
        check('mac %r' % (case['input'],), wol_packet.parse_mac(case['input']).hex(), case['expect'])
    else:
        expect_error('mac %r' % (case['input'],), wol_packet.parse_mac, case['input'], case['error'])

for case in vectors['dest']:
    total += 1
    if 'expect' in case:
        check('dest %r' % (case['input'],), wol_packet.dest(case['input']), case['expect'])
    else:
        expect_error('dest %r' % (case['input'],), wol_packet.dest, case['input'], case['error'])

for case in vectors['packet']:
    total += 1
    check('packet %s' % case['mac'],
          wol_packet.magic_packet(bytes.fromhex(case['mac'])).hex(), case['expect'])

print('wake-on-lan vectors: %d checks, %d failed' % (total, _failed))
sys.exit(1 if _failed else 0)
