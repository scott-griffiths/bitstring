#!/usr/bin/env python

import collections
import copy
import os
import sys

import pytest

import bitstring
from bitstring import BitArray, Bits, Dtype, Reader, pack


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ('uint:8=12', BitArray(uint=12, length=8)),
        (' uint : 8 =  12', BitArray(uint=12, length=8)),
        ('     int:2=  -1', BitArray(int=-1, length=2)),
        ('int :2   = -1', BitArray(int=-1, length=2)),
        (' int:  2  =-1  ', BitArray(int=-1, length=2)),
        ('hex=12', '0x12'),
        ('oct=33', '0o33'),
        ('bin=10', '0b10'),
        ('se=-1', 'se=-1'),
        (' se = -1 ', 'se=-1'),
        ('ue=23', 'ue=23'),
        ('ue = 23', 'ue=23'),
    ],
)
def test_flexible_initialisation(source, expected):
    assert BitArray(source) == expected


def test_multiple_string_initialisation_with_reader():
    a = BitArray('0b1 , 0x1')
    assert a == '0b10001'
    r = Reader(BitArray('ue=5, ue=1, se=-2'))
    assert r.read('ue') == 5
    assert r.read('ue') == 1
    assert r.read('se') == -2
    r = Reader(BitArray('uint:32 = 12, 0b11') + 'int:100=-100, 0o44')
    assert r.read(32).uint == 12
    assert r.read(2).bin == '11'
    assert r.read(100).int == -100


def test_reader_reads_bits_and_bytes():
    s = Reader(BitArray.from_bytes(b'\x4d\x55'))
    assert s.read(4).hex == '4'
    assert s.read(8).hex == 'd5'
    assert s.read(1) == [0]
    assert s.read(3).bin == '101'
    assert not s.read(0)

    s = Reader(BitArray(hex='4d55'))
    assert s.read(8).hex == '4d'
    assert s.read(8).hex == '55'

    s = Reader(BitArray(hex='0x112233448811'))
    assert s.read(3 * 8).hex == '112233'
    with pytest.raises(ValueError):
        s.read(-16)
    s.bitpos += 1
    assert s.read(2 * 8).bin == '1000100100010000'


def test_reader_reads_exp_golomb_codes():
    with pytest.raises(bitstring.InterpretError):
        _ = Bits('').ue
    s = Reader(BitArray(bin='1 010 011 00100 00101 00110 00111 0001000 0001001'))
    assert s.pos == 0
    for i in range(9):
        assert s.read('ue') == i
    with pytest.raises(bitstring.ReadError):
        s.read('ue')

    s = Reader(BitArray(bin='010 00110 0001010 0001000 00111'))
    assert s.read('se') == 1
    assert s.read('se') == 3
    assert s.readlist(3 * ['se']) == [5, 4, -3]


def test_reader_find_variants():
    s = Reader(Bits(bin='0b0000110110000'))
    assert s.find(BitArray(bin='11011')) == 4
    assert s.bitpos == 4
    assert s.read(5).bin == '11011'
    s.bitpos = 0
    assert s.find('0b11001', bytealigned=False) is None

    s = Reader(BitArray(bin='0'))
    assert s.find(s.bits, bytealigned=False) == 0
    assert s.pos == 0
    assert s.find('0b00', bytealigned=False) is None
    with pytest.raises(ValueError):
        s.find(BitArray())

    s = Reader(BitArray(hex='0x112233')[4:])
    assert s.find('0x23', bytealigned=False) == 8
    assert s.pos == 8


def test_reader_find_corner_cases():
    s = Reader(BitArray(bin='000111000111'))
    assert s.find('0b000') == 0
    assert s.pos == 0
    assert s.find('0b000') == 0
    assert s.pos == 0
    assert s.find('0b0111000111') == 2
    assert s.pos == 2
    assert s.find('0b000', start=2) == 6
    assert s.pos == 6
    assert s.find('0b111', start=6) == 9
    assert s.pos == 9
    s.pos += 2
    assert s.find('0b1', start=s.pos) == 11


def test_reader_find_byte_aligned():
    s = Reader(BitArray.from_string('0x010203040102ff'))
    assert s.find('0x05', bytealigned=True) is None
    assert s.find('0x02', bytealigned=True) == 8
    assert s.read(16).hex == '0203'
    assert s.find('0x02', start=s.bitpos, bytealigned=True) == 40
    s.read(1)
    assert s.find('0x02', start=s.bitpos, bytealigned=True) is None

    s = Reader(BitArray(hex='0x12345678'))
    assert s.find(BitArray(hex='0x56'), bytealigned=True) == 16
    assert s.bytepos == 2
    s.pos = 0
    assert s.find(BitArray(hex='0x45'), bytealigned=True) is None


def test_reader_rfind_variants():
    a = Reader(BitArray('0b001001001'))
    b = a.rfind('0b001')
    assert b == 6
    assert a.pos == 6
    big = BitArray(length=100000) + '0x12' + BitArray(length=10000)
    r = Reader(big)
    found = r.rfind('0x12', bytealigned=True)
    assert found == 100000
    assert r.pos == 100000

    a = Reader(BitArray('0x8888'))
    b = a.rfind('0b1', bytealigned=True)
    assert b == 8
    assert a.pos == 8

    a = Reader(BitArray('0x0000ffffff'))
    b = a.rfind('0x0000', start=1, bytealigned=True)
    assert b is None
    assert a.pos == 0
    b = a.rfind('0x00', start=1, bytealigned=True)
    assert b == 8
    assert a.pos == 8


def test_reader_find_and_rfind_errors():
    s = Reader(BitArray(hex='0xffff'))
    with pytest.raises(ValueError):
        s.find('')
    with pytest.raises(ValueError):
        s.find(BitArray())
    a = Reader(BitArray('0x43234234'))
    with pytest.raises(ValueError):
        a.rfind('', bytealigned=True)
    with pytest.raises(ValueError):
        a.rfind('0b1', start=-99, bytealigned=True)
    with pytest.raises(ValueError):
        a.rfind('0b1', end=33, bytealigned=True)
    with pytest.raises(ValueError):
        a.rfind('0b1', start=10, end=9, bytealigned=True)


def test_shift_left_and_right():
    s = BitArray.from_string('0b1010')
    t = s << 1
    assert s.bin == '1010'
    assert t.bin == '0100'
    s = t << 0
    assert s == '0b0100'
    t = s << 100
    assert t.bin == '0000'

    s = BitArray('0b1010')
    t = s >> 1
    assert s.bin == '1010'
    assert t.bin == '0101'
    q = s >> 0
    assert q == '0b1010'
    q.replace('0b1010', '')
    t = s >> 100
    assert t.bin == '0000'


def test_shift_errors():
    s = BitArray()
    with pytest.raises(ValueError):
        s << 1
    with pytest.raises(ValueError):
        s >> 1
    s = BitArray('0xf')
    with pytest.raises(ValueError):
        s << -1
    with pytest.raises(ValueError):
        s >> -1


def test_shift_in_place():
    s = BitArray.from_string('0xffff')[4:12]
    s >>= 1
    assert s == '0b01111111'
    s = BitArray('0b11011')
    s >>= 2
    assert s.bin == '00110'
    s >>= 100000000000000
    assert s.bin == '00000'
    s = BitArray('0xff')
    s >>= 1
    assert s == '0x7f'
    s >>= 0
    assert s == '0x7f'

    s = BitArray('0xffff')[4:12]
    s <<= 2
    assert s == '0b11111100'
    s = BitArray('0b11011')
    s <<= 2
    assert s.bin == '01100'
    s <<= 100000000000000000000
    assert s.bin == '00000'


def test_replace_variants():
    a = BitArray('0b1')
    n = a.replace('0b1', '0b0', bytealigned=True)
    assert a.bin == '0'
    assert n == 1
    assert a.replace('0b1', '0b0', bytealigned=True) == 0

    a = BitArray('0b00001111111')
    n = a.replace('0b1', '0b0', bytealigned=True)
    assert a.bin == '00001111011'
    assert n == 1
    n = a.replace('0b1', '0b0', bytealigned=False)
    assert a.bin == '00000000000'
    assert n == 6

    a = BitArray('0b0')
    n = a.replace('0b0', '0b110011111', bytealigned=True)
    assert n == 1
    assert a.bin == '110011111'
    n = a.replace('0b11', '', bytealigned=False)
    assert n == 3
    assert a.bin == '001'


def test_replace_count_and_self():
    a = BitArray('0b11')
    a.replace('0b1', a)
    assert a == '0xf'
    a.replace(a, a)
    assert a == '0xf'

    a = BitArray('0x223344223344223344')
    n = a.replace('0x2', '0x0', count=0, bytealigned=True)
    assert n == 0
    assert a.hex == '223344223344223344'
    n = a.replace('0x2', '0x0', count=1, bytealigned=True)
    assert n == 1
    assert a.hex == '023344223344223344'
    n = a.replace('0x33', '', count=2, bytealigned=True)
    assert n == 2
    assert a.hex == '02442244223344'
    n = a.replace('0x44', '0x4444', count=1435, bytealigned=True)
    assert n == 3
    assert a.hex == '02444422444422334444'


def test_replace_does_not_adjust_reader_position():
    a = BitArray('0xff')
    r = Reader(a, pos=8)
    a.replace('0xff', '', bytealigned=True)
    assert a == ''
    assert r.pos == 8


def test_replace_errors():
    a = BitArray('0o123415')
    with pytest.raises(ValueError):
        a.replace('', Bits.from_zeros(0o7), bytealigned=True)
    with pytest.raises(ValueError):
        a.replace('0b1', '0b1', start=-100, bytealigned=True)
    with pytest.raises(ValueError):
        a.replace('0b1', '0b1', end=19, bytealigned=True)


def test_slice_assignment():
    a = BitArray()
    a[0:0] = '0xabcdef'
    a[4:16] = ''
    assert a == '0xaef'
    a[8:] = '0x00'
    assert a == '0xae00'
    a += '0xf'
    a[8:] = '0xe'
    assert a == '0xaee'
    b = BitArray("0x0000")
    b[0:16] = '0xffee'
    assert b == '0xffee'
    b[4:16] = '0xeed123'
    assert b == '0xfeed123'
    b[0:8] = '0x0000'
    assert b == '0x0000ed123'


def test_inserting_using_set_item():
    a = BitArray()
    a[0:0] = '0xdeadbeef'
    assert a == '0xdeadbeef'
    a[16:16] = '0xfeed'
    assert a == '0xdeadfeedbeef'
    a[0:0] = '0xa'
    assert a == '0xadeadfeedbeef'
    a[0:8] = '0xff'
    a[8:0] = '0x000'
    assert a.startswith('0xff000ead')


def test_pack_legacy_cases():
    s = bitstring.pack('uint:6, bin, hex, int:6, se, ue, oct', 10, '0b110', 'ff', -1, -6, 6, '54')
    t = BitArray('uint:6=10, 0b110, 0xff, int:6=-1, se=-6, ue=6, oct=54')
    assert s == t
    assert type(s) is Bits
    with pytest.raises(ValueError):
        pack('tomato', '0')
    with pytest.raises(ValueError):
        pack('uint', 12)
    with pytest.raises(ValueError):
        pack('int', 12)
    with pytest.raises(ValueError):
        pack('hex', 'penguin')
    with pytest.raises(ValueError):
        pack('hex12', '0x12')


@pytest.mark.parametrize(
    ("fmt", "expected"),
    [
        ('0xf', '0xf'),
        ('0b1', '0b1'),
        ('0o7', '0o7'),
        ('int:10=-1', '0b1111111111'),
        ('uint:10=1', '0b0000000001'),
        ('bin=01', '0b01'),
        ('hex=01', '0x01'),
        ('oct=01', '0o01'),
    ],
)
def test_pack_literals(fmt, expected):
    assert pack(fmt) == expected


def test_pack_with_dicts_and_lists():
    a = pack('uint:6=width, se=height', height=100, width=12)
    w, h = a.unpack('uint:6, se')
    assert w == 12
    assert h == 100
    d = {'w': '0xf', '300': 423, 'e': '0b1101'}
    a = pack('int:100=300, bin=e, uint:12=300', **d)
    x, y, z = a.unpack('int:100, bin, uint:12')
    assert x == 423
    assert y == '1101'
    assert z == 423

    a = pack('int:5, bin:3=b, 0x3, bin=c, se=12', 10, b='0b111', c='0b1')
    b = BitArray('int:5=10, 0b111, 0x3, 0b1, se=12')
    assert a == b
    assert pack('bits:3=b', b=BitArray('0b101')) == '0b101'
    assert pack('bits:24=b', b=BitArray('0x001122')) == '0x001122'

    f = ['bin', 'hex', 'uint:10']
    a = pack(','.join(f), '00', '234', 100)
    b = pack(f, '00', '234', 100)
    assert a == b


def test_pack_length_restrictions_and_null_formats():
    _ = pack('bin:3', '0b000')
    with pytest.raises(bitstring.CreationError):
        _ = pack('bin:3', '0b0011')
    with pytest.raises(bitstring.CreationError):
        _ = pack('bin:3', '0b11')
    _ = pack('hex:4', '0xf')
    with pytest.raises(bitstring.CreationError):
        _ = pack('hex:4', '0b111')
    _ = pack('oct:6', '0o77')
    with pytest.raises(bitstring.CreationError):
        _ = pack('oct:6', '0o1')
    _ = pack('bits:3', BitArray('0b111'))
    with pytest.raises(bitstring.CreationError):
        _ = pack('bits:3', BitArray('0b11'))

    assert not pack('')
    assert not pack(',')
    assert pack(',,,,,0b1,,,,,,,,,,,,,0b1,,,,,,,,,,') == '0b11'
    s = pack(',,uint:12,,bin:3,', 100, '100')
    a, b = s.unpack('uint:12,bin:3')
    assert a == 100
    assert b == '100'


def test_unpack_does_not_depend_on_reader_position():
    bits = BitArray('uint:13=23, hex=e, bin=010, int:41=-554, 0o44332, se=-12, ue=4')
    r = Reader(bits, pos=11)
    a, b, c, d, e, f, g = bits.unpack('uint:13, hex:4, bin:3, int:41, oct:15, se, ue')
    assert (a, b, c, d, e, f, g) == (23, 'e', '010', -554, '44332', -12, 4)
    assert r.pos == 11


def test_unpack_stretchy_tokens():
    s = BitArray('0xff, 0b000, uint:12=100')
    a, b, c = s.unpack('bits:8, bits, uint:12')
    assert a == '0xff'
    assert b == '0b000'
    assert c == 100
    a, b = s.unpack(['bits:11', 'uint'])
    assert a == '0xff, 0b000'
    assert b == 100


def test_file_creation_and_mutation_operations():
    filename = os.path.join(THIS_DIR, 'smalltestfile')
    s = BitArray.from_file(filename)
    s.append('0xff')
    assert s.hex == '0123456789abcdefff'

    s = Bits.from_file(filename)
    t = BitArray('0xff') + s
    assert t.hex == 'ff0123456789abcdef'

    s = BitArray.from_file(filename)
    del s[:1]
    assert (BitArray('0b0') + s).hex == '0123456789abcdef'

    s = BitArray.from_file(filename)
    del s[:7 * 8]
    assert s.hex == 'ef'

    s = BitArray.from_file(filename)
    s.insert('0xc', 4)
    assert s.hex == '0c123456789abcdef'

    s = BitArray.from_file(filename)
    s.prepend('0xf')
    assert s.hex == 'f0123456789abcdef'

    s = BitArray.from_file(filename)
    s.overwrite('0xaaa', 12)
    assert s.hex == '012aaa6789abcdef'

    s = BitArray.from_file(filename)
    s.reverse()
    assert s.hex == 'f7b3d591e6a2c480'


def test_file_properties_and_reader():
    s = Bits.from_file(os.path.join(THIS_DIR, 'smalltestfile'))
    assert s.hex == '0123456789abcdef'
    assert s.uint == 81985529216486895
    assert s.int == 81985529216486895
    assert s.bin == '0000000100100011010001010110011110001001101010111100110111101111'
    assert s[:-1].oct == '002215053170465363367'
    r = Reader(s)
    assert r.read('se') == -72
    r.pos = 0
    assert r.read('ue') == 144
    assert s.bytes == b'\x01\x23\x45\x67\x89\xab\xcd\xef'
    assert s.tobytes() == b'\x01\x23\x45\x67\x89\xab\xcd\xef'


def test_file_creation_with_length_and_offset():
    test_filename = os.path.join(THIS_DIR, 'test.m1v')
    s = Bits.from_file(test_filename, length=32)
    assert len(s) == 32
    assert s.hex == '000001b3'
    assert s.bytes == b'\x00\x00\x01\xb3'
    assert s.uint == 0x1b3
    assert s.int == 0x1b3
    assert s.bin == '00000000000000000000000110110011'
    assert not Bits.from_file(test_filename, length=0)

    small_test_filename = os.path.join(THIS_DIR, 'smalltestfile')
    with pytest.raises(bitstring.CreationError):
        _ = BitArray.from_file(small_test_filename, length=65)
    with pytest.raises(bitstring.CreationError):
        _ = Bits.from_file(small_test_filename, length=64, offset=1)
    with pytest.raises(bitstring.CreationError):
        _ = Bits.from_file(small_test_filename, offset=65)

    a = BitArray.from_file(test_filename, offset=4)
    assert Reader(a).peek(4 * 8).hex == '00001b31'
    b = BitArray.from_file(test_filename, offset=28)
    assert Reader(b).peek(8).hex == '31'


def test_find_in_file_with_reader():
    r = Reader(BitArray.from_file(os.path.join(THIS_DIR, 'test.m1v')))
    assert r.find('0x160120') == 32
    assert r.bytepos == 4
    s3 = r.read(24)
    assert s3.hex == '160120'
    r.bytepos = 0
    assert r.pos == 0
    assert r.find('0x0001b2') == 104
    assert r.bytepos == 13


def test_file_bit_getting():
    s = Bits.from_file(os.path.join(THIS_DIR, 'smalltestfile'), offset=16, length=8)
    assert s[1]
    assert s.any(0, [-1, -2, -3])
    assert not s.all(0, [0, 1, 2])


def test_creation_errors_and_basic_conversions():
    s = BitArray()
    with pytest.raises(bitstring.CreationError):
        s._setbin('0010020')
    with pytest.raises(bitstring.CreationError):
        s.hex = '0xabcdefg'
    assert len(BitArray('')) == 0
    assert len(BitArray('0x80')) == 8
    with pytest.raises(bitstring.CreationError):
        BitArray(hex='0xffff', offset=-1)
    assert BitArray('0x10').uint == 16
    assert BitArray('0b000111').uint == 7
    assert BitArray('0x10').int == 16
    assert BitArray('0b11110').int == -2
    assert BitArray.from_bytes(b'\x00\x12\x23\xff').hex == '001223ff'
    with pytest.raises(bitstring.InterpretError):
        _ = BitArray('0b11111').hex


def test_empty_bits_and_reader_position():
    s = Reader(BitArray())
    with pytest.raises(bitstring.ReadError):
        s.read(1)
    assert s.bits.bin == ''
    assert s.bits.hex == ''
    with pytest.raises(bitstring.InterpretError):
        _ = s.bits.int
    with pytest.raises(bitstring.InterpretError):
        _ = s.bits.uint
    assert not s.bits

    s = Reader(BitArray.from_bytes(b'\x00\x00\x00'))
    assert s.bitpos == 0
    s.read(5)
    assert s.pos == 5
    s.pos = len(s)
    with pytest.raises(bitstring.ReadError):
        s.read(1)


def test_reader_byte_position_and_lax_seek():
    s = Reader(BitArray.from_bytes(b'\x00\x00\x00'))
    assert s.bytepos == 0
    s.read(10)
    with pytest.raises(bitstring.ByteAlignError):
        _ = s.bytepos
    s.read(6)
    assert s.bytepos == 2

    s = Reader(BitArray.from_bytes(b'\x00\x00\x00\x00\x00\xab'))
    s.bytepos = 5
    assert s.read(8).hex == 'ab'
    s.pos = -1
    assert s.pos == -1
    with pytest.raises(ValueError):
        s.read(1)
    s.bitpos = 6 * 8 + 1
    assert s.bitpos == 49
    with pytest.raises(ValueError):
        s.read(0)


def test_append_and_prepend():
    s1 = BitArray('0b00000')
    s1.append(BitArray(bool=True))
    assert s1.bin == '000001'
    assert (BitArray('0x0102') + BitArray('0x0304')).hex == '01020304'

    s1 = BitArray('0xf0')[:6]
    s1.append(s1)
    assert s1.bin == '111100111100'

    s = BitArray.from_bytes(b'\x28\x28', offset=1)
    s.append('0b0')
    assert s.hex == '5050'

    s = BitArray('0b000')
    s.prepend('0b11')
    assert s.bin == '11000'
    s.prepend(s)
    assert s.bin == '1100011000'
    s.prepend('')
    assert s.bin == '1100011000'


def test_reader_bytealign():
    s = Reader(BitArray(hex='0001ff23'))
    s.bytealign()
    assert s.bytepos == 0
    s.pos += 11
    s.bytealign()
    assert s.bytepos == 2
    s.pos -= 10
    s.bytealign()
    assert s.bytepos == 1


def test_insert_and_overwrite():
    s = BitArray('0x0011')
    s.insert(BitArray('0x22'), 8)
    assert s.hex == '002211'
    s = BitArray.from_zeros(0)
    s.insert(BitArray(bin='101'), 0)
    assert s.bin == '101'

    s1 = BitArray(hex='0x123456')
    s2 = BitArray(hex='0xff')
    s1.insert(s2, 8)
    assert s1.hex == '12ff3456'
    s1.insert('0xee', 24)
    assert s1.hex == '12ff34ee56'
    with pytest.raises(ValueError):
        s1.insert('0b1', -1000)
    with pytest.raises(ValueError):
        s1.insert('0b1', 1000)

    s = BitArray(bin='0')
    s.overwrite(BitArray(bin='1'), 0)
    assert s.bin == '1'
    s = BitArray(bin='0b11111')
    s.overwrite(BitArray(bin='000'), 0)
    assert s.bin == '00011'
    s.overwrite('0b000', 2)
    assert s.bin == '00000'


def test_truncate_and_delete():
    s = BitArray('0b1')
    del s[0]
    assert not s
    s = BitArray(hex='1234')
    del s[:4]
    assert s.hex == '234'
    del s[:9]
    assert s.bin == '100'
    del s[:2]
    assert s.bin == '0'
    del s[:1]
    assert not s

    s = BitArray.from_bytes(b'\x12\x34')
    del s[-4:]
    assert s.hex == '123'
    del s[-9:]
    assert s.bin == '000'
    del s[-3:]
    assert not s


def test_slice_and_join():
    s = BitArray(hex='0x123456')
    assert s[8:16].hex == '34'
    s = s[8:24]
    assert len(s) == 16
    assert s.hex == '3456'
    s = s[0:8]
    assert s.hex == '34'

    s1 = BitArray(bin='0')
    s2 = BitArray(bin='1')
    s3 = BitArray(bin='000')
    s4 = BitArray(bin='111')
    strings = [s1, s2, s1, s3, s4]
    assert BitArray().join(strings).bin == '010000111'


def test_split_variants():
    s = BitArray(hex='0x1234aa1234bbcc1234ffff')
    delimiter = BitArray(hex='1234')
    bsl = s.split(delimiter)
    assert [b.hex for b in bsl] == ['', '1234aa', '1234bbcc', '1234ffff']

    s = BitArray(hex='aa471234fedc43 47112233 47 4723 472314')
    delimiter = BitArray(hex='47')
    bsl = s.split(delimiter, start=0)
    assert [b.hex for b in bsl] == ['aa', '471234fedc43', '47112233', '47', '4723', '472314']

    s = BitArray(hex='aaffaaffaaffaaffaaff')
    bsl = s.split(BitArray(hex='aaffaa'))
    assert [b.hex for b in bsl] == ['', 'aaffaaff', 'aaffaaffaaff']


def test_adding_and_equality():
    s1 = BitArray(hex='0x0102')
    s2 = BitArray(hex='0x0304')
    s3 = s1 + s2
    assert s1.hex == '0102'
    assert s2.hex == '0304'
    assert s3.hex == '01020304'
    s3 += s1
    assert s3.hex == '010203040102'
    assert s2[9:16].bin == '0000100'
    assert s1[0:9].bin == '000000010'
    s4 = BitArray(bin='000000010') + BitArray(bin='0000100')
    assert s4.bin == '0000000100000100'
    s5 = s1[0:9] + s2[9:16]
    assert s5.bin == '0000000100000100'

    s1 = BitArray('0b01010101')
    s2 = BitArray('0b01010101')
    assert s1 == s2
    assert BitArray.from_bytes(b'\xff', offset=2, length=3) == BitArray('0b111')


def test_peek_with_reader():
    s = Reader(BitArray(bin='01'))
    assert s.peek(1) == [0]
    assert s.peek(1) == [0]
    assert s.read(1) == [0]
    assert s.peek(1) == [1]
    assert s.peek(1) == [1]

    s = Reader(BitArray.from_bytes(b'\x1f', offset=3))
    assert len(s) == 5
    assert s.peek(5).bin == '11111'
    s.pos += 1
    with pytest.raises(bitstring.ReadError):
        _ = s.peek(5)

    s = Reader(BitArray(hex='001122334455'))
    assert s.peek(8).hex == '00'
    assert s.read(8).hex == '00'
    s.pos += 33
    with pytest.raises(bitstring.ReadError):
        _ = s.peek(8)


def test_auto_initialisation_and_auto_methods():
    assert BitArray('0xff').hex == 'ff'
    assert BitArray('0b00011').bin == '00011'
    with pytest.raises(bitstring.CreationError):
        _ = BitArray('hello')
    with pytest.raises(TypeError):
        _ = BitArray(1.2)

    s = BitArray('0xff')
    s.insert('0x00', 4)
    assert s.hex == 'f00f'
    with pytest.raises(ValueError):
        s.insert('ff', 0)

    s = BitArray('0x0110')
    s.overwrite('0b1', 0)
    assert s.hex == '8110'
    s.overwrite('', 0)
    assert s.hex == '8110'
    with pytest.raises(ValueError):
        s.overwrite('0bf', 0)


def test_findall_contains_and_slice_steps():
    a = BitArray('0b11111')
    assert list(a.findall('0b1')) == [0, 1, 2, 3, 4]
    assert list(a.findall('0b11')) == [0, 1, 2, 3]
    assert list(a.findall('0b10')) == []
    a = BitArray('0x4733eeff66554747335832434547')
    assert list(a.findall('0x47', bytealigned=True)) == [0, 6 * 8, 7 * 8, 13 * 8]
    assert list(a.findall('0x4733', bytealigned=True)) == [0, 7 * 8]

    a = BitArray('0b1') + '0x0001dead0001'
    assert '0xdead' in a
    assert '0xfeed' not in a

    a = BitArray('0b0011000111')
    assert a[7:3:-1] == '0b1000'
    assert a[9:2:-1] == '0b1110001'
    assert a[8:2:-2] == '0b100'
    assert a[100:-20:-3] == '0b1010'


def test_repr_print_iter_and_offsets():
    for bs in ['', '0b1', '0o5', '0x43412424f41', '0b00101001010101']:
        a = BitArray(bs)
        b = eval(a.__repr__())
        assert a == b
    assert repr(BitArray('0b1')) == "BitArray('0b1')"
    assert str(BitArray('0b11010')) == '0b11010'

    a = BitArray('0b001010')
    b = BitArray()
    for bit in a:
        b.append(Bits(bool=bit))
    assert a == b

    a = BitArray.from_bytes(b'\xff', offset=2)
    b = BitArray('0b00')
    b += a
    assert b == '0b0011 1111'
    assert a.tobytes() == b'\xfc'


def test_init_slice_with_int_and_reverse():
    a = BitArray(length=8)
    a[:] = 100
    assert a.uint == 100
    a[0] = 1
    assert a.bin == '11100100'
    a[1] = 0
    assert a.bin == '10100100'
    a[-1] = -1
    assert a.bin == '10100101'
    a[-3:] = -2
    assert a.bin == '10100110'

    with pytest.raises(ValueError):
        a[0:4] = 16
    with pytest.raises(ValueError):
        a[0:4] = -9

    a = BitArray('0x0012ff')
    a.reverse()
    assert a == '0xff4800'
    a.reverse(start=8, end=16)
    assert a == '0xff1200'
    with pytest.raises(ValueError):
        a.reverse(start=-1, end=4)


def test_initialise_from_iterables_and_cut():
    a = BitArray.from_bools([])
    assert not a
    a = BitArray.from_bools([True, False, [], [0], 'hello'])
    assert a == '0b10011'
    a += []
    assert a == '0b10011'
    a += [True, False, True]
    assert a == '0b10011101'
    assert [1, 0, False, True] == BitArray('0b1001')
    assert [True] + BitArray('0b1') == '0b11'

    a = BitArray.from_bools(())
    assert not a
    a = BitArray.from_bools((0, 1, '0', '1'))
    assert '0b0111' == a
    a.replace((True, True), [])
    assert a == (False, True)

    a = BitArray('0x00112233445')
    assert list(a.cut(8)) == ['0x00', '0x11', '0x22', '0x33', '0x44', '0x5']
    assert list(a.cut(4, start=8, end=16)) == ['0x1', '0x1']
    assert list(a.cut(4, start=0, end=44, count=4)) == ['0x0', '0x0', '0x1', '0x1']


def test_reader_intelligent_reads():
    a = Reader(BitArray(uint=123, length=23))
    assert a.read('uint:23') == 123
    assert a.pos == len(a)
    b = Reader(BitArray(int=-12, length=44))
    assert b.read('int:44') == -12
    assert b.pos == len(b)
    r = Reader(a.bits + b.bits)
    assert r.readlist('uint:23, int:44') == [123, -12]

    a = Reader(BitArray(ue=822))
    assert a.read('ue') == 822
    b = Reader(BitArray(se=-1001))
    assert b.read('se') == -1001
    r = Reader(b.bits + 2 * a.bits)
    assert r.readlist('se, ue, ue') == [-1001, 822, 822]

    a = Reader(BitArray('0x123') + '0b11101')
    assert a.read('hex:12') == '123'
    assert a.read(' bin : 5 ') == '11101'


def test_reader_intelligent_read_errors_and_peek():
    a = Reader(BitArray('0x1234'))
    assert a.readlist('bin:0, oct:0, hex:0, bits:0')[:3] == ['', '', '']
    a.pos = 0
    with pytest.raises(ValueError):
        _ = a.read('int:0')
    with pytest.raises(ValueError):
        _ = a.read('uint:0')
    assert a.pos == 0

    a = Reader(BitArray('0x123456'))
    for t in ['hex:1', 'oct:1', '-5', 'fred', 'bin:-2', 'uint:p', 'uint:-2', 'int:u', 'int:-3', 'ses', 'uee', '-14']:
        with pytest.raises(ValueError):
            _ = a.read(t)

    a = Reader(BitArray('0b01, 0x43, 0o4, uint:23=2, se=5, ue=3'))
    b, c, e = a.peeklist('bin:2, hex:8, oct:3')
    assert (b, c, e) == ('01', '43', '4')
    assert a.pos == 0
    a.pos = 13
    f, g, h = a.peeklist('uint:23, se, ue')
    assert (f, g, h) == (2, 5, 3)
    assert a.pos == 13


def test_reader_multiple_bit_reads():
    s = Reader(BitArray('0x123456789abcdef'))
    a, b = s.readlist([4, 4])
    assert a == '0x1'
    assert b == '0x2'
    c, d, e = s.readlist([8, 16, 8])
    assert c == '0x34'
    assert d == '0x5678'
    assert e == '0x9a'

    s = Reader(BitArray('0b1101, 0o721, 0x2234567'))
    a, b, c, d = s.peeklist([2, 1, 1, 9])
    assert a == '0b11'
    assert bool(b) is True
    assert bool(c) is True
    assert d == '0o721'
    assert s.pos == 0


def test_to_bytes_to_file_and_token_parser(tmp_path):
    a = BitArray.from_bytes(b'\xab\x00')
    b = a.tobytes()
    assert a.bytes == b
    for _ in range(7):
        del a[-1:]
        assert a.tobytes() == b'\xab\x00'
    del a[-1:]
    assert a.tobytes() == b'\xab'

    filename = tmp_path / 'temp_bitstring_unit_testing_file'
    a = BitArray('0x0000ff')[:17]
    with open(filename, 'wb') as f:
        a.tofile(f)
    b = BitArray.from_file(filename)
    assert b == '0x000080'

    tp = bitstring.utils.tokenparser
    assert tp('hex') == (True, [('hex', None, None)])
    assert tp('hex=14') == (True, [('hex', None, '14')])
    assert tp('0xef') == (False, [('0x', None, 'ef')])
    assert tp('uint:12') == (False, [('uint', 12, None)])
    assert tp('2*bits:6') == (False, [('bits', 6, None), ('bits', 6, None)])


def test_endian_synonyms_and_struct_tokens():
    s = BitArray('0x12318276ef')
    assert s.int == s.ibe
    assert s.uint == s.ube
    assert BitArray(ibe=-100, length=16) == 'int:16=-100'
    assert BitArray(ube=13, length=24) == 'int:24=13'
    r = Reader(BitArray('ibe:8=2'))
    assert r.read('ibe8') == 2
    r.pos = 0
    assert r.read('ube8') == 2

    s = BitArray(uint=100, length=16)
    assert s.ule == 25600
    s = BitArray(ule=100, length=16)
    assert s.uint == 25600
    assert s.ule == 100
    s.ule += 5
    assert s.ule == 105
    s = pack('ule:24', 1001)
    assert s.ule == 1001
    assert Reader(s).read('ule24') == 1001

    assert pack('<b', 23) == BitArray('ile:8=23')
    assert pack('<B', 23) == BitArray('ule:8=23')
    assert pack('>h', 23) == BitArray('ibe:16=23')
    assert pack('>I', 23) == BitArray('ube:32=23')
    with pytest.raises(bitstring.CreationError):
        _ = pack('<B', -1)


def test_struct_tokens_require_explicit_endianness():
    for fmt in ['=b', '@Q', '=2i']:
        with pytest.raises(bitstring.CreationError, match='Native-endian struct formats'):
            _ = pack(fmt, 23, 23)

    s = pack('>hhl', 1, 2, 3)
    assert s.unpack('>hhl') == [1, 2, 3]
    s = pack('<QL, >Q \tL', 1001, 43, 21, 9999)
    assert s.unpack('<QI, >QL') == [1001, 43, 21, 9999]


def test_byteswap_variants():
    a = BitArray('0x123456')
    a.byteswap()
    assert a == '0x563412'
    b = a + '0b1'
    b.byteswap()
    assert '0x123456, 0b1' == b
    a = BitArray('0x54')
    a.byteswap()
    assert a == '0x54'
    a = BitArray()
    a.byteswap()
    assert not a

    a = BitArray('0x00112233')
    a.byteswap(0, 0, 16)
    assert a == '0x11002233'
    a.byteswap(0, 4, 28)
    assert a == '0x12302103'
    a.byteswap(start=0, end=18)
    assert a == '0x30122103'
    with pytest.raises(ValueError):
        a.byteswap(0, 10, 2)


def test_startswith_endswith_and_hashing():
    a = BitArray()
    assert a.startswith(BitArray())
    assert not a.startswith('0b0')
    a = BitArray('0x12ff')
    assert a.startswith('0x1')
    assert a.startswith('0b0001001')
    assert not a.startswith('0x2')

    a = BitArray('0xf2341')
    assert a.endswith('0x41')
    assert a.endswith('0b001')
    assert not a.endswith('0o34')

    with pytest.raises(TypeError):
        _ = {a}
    with pytest.raises(TypeError):
        _ = hash([a])


def test_bits_immutability_and_hashability():
    a = Bits('0x012345')
    assert a == '0x012345'
    b = BitArray('0xf') + a
    assert b == '0xf012345'
    with pytest.raises(AttributeError):
        a.append(b)
    with pytest.raises(AttributeError):
        a.prepend(b)
    with pytest.raises(TypeError):
        a[0] = '0b1'
    with pytest.raises(TypeError):
        del a[5]
    with pytest.raises(AttributeError):
        a.replace('0b1', '0b0')

    s = {Bits(uint=i, length=7) for i in range(15)}
    assert len(s) == 15
    s.add(Bits('0b0000011'))
    assert len(s) == 15
    with pytest.raises(TypeError):
        s.add(BitArray('0b0000011'))


def test_set_invert_and_logical_inplace():
    a = BitArray(length=16)
    a.set(True, 0)
    assert a == '0b10000000 00000000'
    a.set(1, 15)
    assert a == '0b10000000 00000001'
    b = a[4:12]
    b.set(True, 1)
    assert b == '0b01000000'
    b.set(True, -1)
    assert b == '0b01000001'
    with pytest.raises(IndexError):
        b.set(True, -9)

    a = BitArray('0b111000')
    a.invert(range(len(a)))
    assert a == '0b000111'
    a.invert([0, 1, -1])
    assert a == '0b110110'
    a.invert()
    assert a == '0b001001'

    a = BitArray('0b1101001')
    a |= '0b1110000'
    assert a == '0b1111001'
    a &= '0b1111111'
    assert a == '0b1111001'
    a ^= '0b1111111'
    assert a == '0b0000110'


def test_all_any_and_count():
    a = BitArray('0b0111')
    assert a.all(True, (1, 3))
    assert not a.all(True, (0, 1, 2))
    assert a.all(True, [-1])
    assert not a.all(True, [0])

    filename = os.path.join(THIS_DIR, 'test.m1v')
    a = BitArray.from_file(filename)
    assert a.all(True, [31])
    a = BitArray.from_file(filename)
    assert a.any(True, (31, 12))
    assert a.any(False, (0, 1, 2, 3, 4))

    assert Bits('0xf0f').count(True) == 8
    assert Bits('0xf0f').count(False) == 4
    assert BitArray().count(True) == 0
    assert BitArray().count(False) == 0


def test_float_initialisation_packing_and_reading():
    for f in (0.000001, -1.0, 1.0, 0.2, -3.14159265):
        assert BitArray(float=f, length=64).float == f
        assert BitArray('float:64=%s' % str(f)).float == f
        assert BitArray('fbe:64=%s' % str(f)).fbe == f
        assert BitArray('fle:64=%s' % str(f)).fle == f
        assert BitArray(float=f, length=32).float / f == pytest.approx(1.0)
        assert BitArray(float=f, length=16).float == pytest.approx(f, abs=0.01)

    a = BitArray(pack('>d', 0.01))
    assert a.float == 0.01
    assert a.fbe == 0.01
    a.byteswap()
    assert a.fle == 0.01
    d = pack('>5d', 10.0, 5.0, 2.5, 1.25, 0.1)
    assert d.unpack('>5d') == [10.0, 5.0, 2.5, 1.25, 0.1]

    a = Reader(BitArray('fle:64=12, fbe:64=-0.01, f:64=3e33'))
    assert a.readlist('fle:64, fbe:64, f:64') == [12.0, -0.01, 3e33]


def test_float_errors_and_rotations():
    a = BitArray('0x3')
    with pytest.raises(bitstring.InterpretError):
        _ = a.float
    with pytest.raises(bitstring.CreationError):
        a.float = -0.2
    for le in (8, 10, 12, 18, 30, 128, 200):
        with pytest.raises(ValueError):
            _ = BitArray(float=1.0, length=le)

    a = BitArray('0b11001')
    a.ror(0)
    assert a == '0b11001'
    a.ror(1)
    assert a == '0b11100'
    a.ror(101)
    assert a == '0b01110'
    a = BitArray('0b11001')
    a.rol(1)
    assert a == '0b10011'
    a.rol(101)
    assert a == '0b00111'


def test_bytes_token_and_dedicated_reader_types():
    a = Reader(BitArray('0x510203'))
    b = a.read('bytes:1')
    assert isinstance(b, bytes)
    assert b == b'\x51'
    x, y, z = a.bits.unpack('uint:4, bytes:2, uint')
    assert x == 5
    assert y == b'\x10\x20'
    assert z == 3
    assert pack('bytes:4', b'abcd').bytes == b'abcd'

    a = Reader(BitArray('0b11, uint:43=98798798172, 0b11111'), pos=2)
    assert a.read(Dtype('int43')) == 98798798172
    assert a.pos == 45
    a = Reader(BitArray('0b111, ule:40=123516, 0b111'), pos=3)
    assert a.read('ule:40') == 123516
    a = Reader(BitArray('0b111, bfloat:16=-5.25, 0xffffffff'), pos=3)
    assert a.read('bfloatbe') == -5.25


def test_multiplicative_factors_and_brackets():
    assert BitArray('1*0b1') == '0b1'
    assert BitArray('4*0xc') == '0xcccc'
    assert BitArray('0b1, 0*0b0') == '0b1'
    assert BitArray('0*0b1001010') == ''

    s = Reader(BitArray('0xc') * 5)
    assert s.readlist('5*uint:4') == [12, 12, 12, 12, 12]
    s = Bits('2*0b101, 4*uint:7=3')
    assert s.unpack('2*bin:3, 3*uint:7') == ['101', '101', 3, 3, 3]

    be = bitstring.utils.expand_brackets
    assert be('2*(a,b)') == 'a,b,a,b'
    assert be('2*(a),3*(b)') == 'a,a,b,b,b'
    with pytest.raises(ValueError):
        _ = be('2*(x,y()')


def test_bool_token_and_integer_reads():
    a = Reader(Bits('0b1'))
    assert a.bits.bool is True
    assert a.read('bool') is True
    assert a.bits.unpack('bool')[0] is True
    b = Reader(Bits('0b0'))
    assert b.bits.bool is False
    assert b.peek('bool') is False
    assert b.bits.unpack('bool')[0] is False

    c = pack('4*bool', False, True, 'False', 'True')
    assert c == '0b0101'
    with pytest.raises(bitstring.CreationError):
        pack('bool', 'hello')

    a = Reader(Bits('0xffeedd'))
    b = a.read(8)
    assert b.hex == 'ff'
    assert a.pos == 8
    b = a.peek(8)
    assert b.hex == 'ee'
    assert a.pos == 8
    b = a.read(1)
    assert b == '0b1'


def test_bytes_initialisation_and_legacy_bugs():
    a = Bits(b'uint:5=2')
    b = Bits(b'')
    c = Bits.from_bytes(b'uint:5=2')
    assert a.bytes == b'uint:5=2'
    assert not b
    assert c == b'uint:5=2'

    a = Bits(bytearray(b'uint:5=2'))
    b = Bits(bytearray(4))
    c = Bits.from_bytes(bytearray(b'uint:5=2'))
    assert a.bytes == b'uint:5=2'
    assert b == '0x00000000'
    assert c.bytes == b'uint:5=2'

    s = Reader(Bits('0b000000001'))
    with pytest.raises(bitstring.ReadError):
        _ = s.read('ue')

    s = BitArray('0x00112233')
    li = list(s.split('0x22', start=8, bytealigned=True))
    assert li == ['0x11', '0x2233']
    s.replace('0x22', '0xffff', start=8, bytealigned=True)
    assert s == '0x0011ffff33'


def test_function_negative_indices():
    s = BitArray('0b0111')
    s.insert('0b0', -1)
    assert s == '0b01101'
    with pytest.raises(ValueError):
        s.insert('0b0', -1000)

    s.reverse(start=-2)
    assert s == '0b01110'
    t = BitArray('0x778899abcdef')
    t.reverse(start=-12, end=-4)
    assert t == '0x778899abc7bf'
    t.byteswap(0, -40, -16)
    assert t == '0x77ab9988c7bf'
    t.overwrite('0x666', -20)
    assert t == '0x77ab998666bf'

    r = Reader(t)
    assert r.find('0x998', bytealigned=True, start=-31) is None
    assert r.find('0x998', bytealigned=True, start=-32) == 16
    assert r.pos == 16


def test_pack_code_dicts_unicode_and_dict_reads():
    assert sorted(bitstring.utils.REPLACEMENTS_BE.keys()) == sorted(bitstring.utils.REPLACEMENTS_LE.keys())
    assert sorted(bitstring.utils.REPLACEMENTS_BE.keys()) == sorted(bitstring.utils.PACK_CODE_SIZE.keys())
    for key in bitstring.utils.PACK_CODE_SIZE:
        be = pack(bitstring.utils.REPLACEMENTS_BE[key], 0)
        le = pack(bitstring.utils.REPLACEMENTS_LE[key], 0)
        assert len(be) == bitstring.utils.PACK_CODE_SIZE[key] * 8
        assert len(le) == len(be)

    a = Bits('uint:12=34')
    assert a.uint == 34
    a += '0xfe'
    assert a[12:] == '0xfe'

    a = Bits('2*int:13=100, 0b111')
    x, y, z = a.unpack('13, int:m, bin:q', m=13, q=3)
    assert x == 'uint:13=100'
    assert y == 100
    assert z == '111'

    s = Reader(BitArray('0x0102'))
    x, y = s.readlist('bits8, hex:b', b=4)
    assert (x, y) == ('0x01', '0')
    assert s.pos == 12


def test_unpack_error_and_add_empty_bits_issue():
    format_with_commas = ',bytes:2,,bytes:1,'
    dp = BitArray(hex='010203').unpack(fmt=format_with_commas)
    assert dp == [b'\x01\x02', b'\x03']

    x = BitArray()
    y = x + Bits('0xff')
    assert y == '0xff'
    z = x + bitstring.BitArray('0xff')
    assert z == '0xff'

    xx = Bits()
    yy = xx + Bits('0xff')
    zz = xx + bitstring.BitArray('0xff')
    assert yy == zz == '0xff'


def test_copy_and_reader_copy_semantics_for_restored_stream_coverage():
    bits = Bits('0xabc')
    reader = Reader(bits, pos=11)
    copied_reader = copy.copy(reader)
    copied_reader.pos = 4
    assert reader.bits is copied_reader.bits
    assert reader.pos == 11
    assert copied_reader.pos == 4

    mutable = BitArray('0xabc')
    copied_mutable = copy.copy(mutable)
    mutable.append('0xf')
    assert copied_mutable == '0xabc'
    assert mutable == '0xabcf'


def test_iterable_detection_used_by_initialisation():
    assert isinstance(range(10), collections.abc.Iterable)
    s = Bits.from_bools(range(12))
    assert s == '0x7ff'


def test_multiplication_variants():
    a = BitArray('0xff')
    assert a * 8 == '0xffffffffffffffff'
    assert 4 * a == '0xffffffff'
    assert 1 * a == a * 1 == a
    assert not a * 0
    a *= 3
    assert a == '0xffffff'
    a *= 0
    assert not a
    one = BitArray('0b1')
    zero = BitArray('0b0')
    assert one * 2 + 3 * zero + 2 * one * 2 == '0b110001111'

    a = BitArray.from_file(os.path.join(THIS_DIR, 'test.m1v'))
    length = len(a)
    a *= 3
    assert len(a) == 3 * length

    with pytest.raises(ValueError):
        _ = one * -1
    with pytest.raises(ValueError):
        one *= -1
    with pytest.raises(ValueError):
        _ = -1 * one
    with pytest.raises(TypeError):
        _ = one * 1.2
    with pytest.raises(TypeError):
        _ = zero * one


@pytest.mark.parametrize(
    ("left", "op", "right", "expected"),
    [
        ('0b01101', '&', '0b00110', '0b00100'),
        ('0b01101', '&', '0b11111', '0b01101'),
        ('0b111001001', '|', '0b011100011', '0b111101011'),
        ('0b111001001', '|', '0b000000000', '0b111001001'),
        ('0b111001001', '^', '0b011100011', '0b100101010'),
        ('0b111001001', '^', '0b111100000', '0b000101001'),
        ('0xff00', '|', '0x00f0', '0xfff0'),
        ('0o707', '^', '0o777', '0o070'),
    ],
)
def test_bitwise_binary_operations(left, op, right, expected):
    a = BitArray(left)
    if op == '&':
        result = a & right
    elif op == '|':
        result = a | right
    else:
        result = a ^ right
    assert result == expected


def test_bitwise_errors_and_inplace():
    a = BitArray('0b01101')
    with pytest.raises(ValueError):
        _ = a & '0b1'
    with pytest.raises(ValueError):
        _ = a | '0b0000'
    with pytest.raises(ValueError):
        _ = a ^ '0b0000'

    a = BitArray.from_zeros(4)
    with pytest.raises(ValueError):
        a |= '0b111'
    with pytest.raises(ValueError):
        a &= '0b111'
    with pytest.raises(ValueError):
        a ^= '0b111'


def test_split_start_end_and_count_variants():
    a = BitArray('0b0 010100111 010100 0101 010')
    subs = [i.bin for i in a.split('0b010')]
    assert subs == ['0', '010100111', '010100', '0101', '010']

    a = BitArray('0b000000')
    bsl = a.split('0b1', bytealigned=False)
    assert next(bsl) == a
    with pytest.raises(StopIteration):
        next(bsl)
    b = BitArray()
    bsl = b.split('0b001', bytealigned=False)
    assert not next(bsl)
    with pytest.raises(StopIteration):
        _ = next(bsl)

    a = BitArray('0xaabbccbbccddbbccddee')
    assert len(list(a.split('0xbb', bytealigned=True))) == 4
    bsl = list(a.split('0xbb', count=1, bytealigned=True))
    assert (len(bsl), bsl[0]) == (1, '0xaa')
    bsl = list(a.split('0xbb', count=2, bytealigned=True))
    assert len(bsl) == 2
    assert bsl[0] == '0xaa'
    assert bsl[1] == '0xbbcc'

    s = BitArray('0b1100011001110110')
    for i in range(10):
        assert list(s.split('0b11', bytealigned=False, count=i)) == list(s.split('0b11', bytealigned=False))[:i]
    with pytest.raises(ValueError):
        _ = next(s.split('0b11', count=-1))


def test_split_start_end_boundaries():
    a = BitArray('0b0010101001000000001111')
    bsl = a.split('0b001', bytealigned=False, start=1)
    assert [x.bin for x in bsl] == ['010101', '001000000', '001111']
    with pytest.raises(ValueError):
        _ = next(a.split('0b001', start=-100))
    with pytest.raises(ValueError):
        _ = next(a.split('0b001', start=23))
    with pytest.raises(ValueError):
        _ = next(a.split('0b1', start=10, end=9))

    a = BitArray('0x00ffffee')
    bsl = list(a.split('0b111', start=9, bytealigned=True))
    assert [x.bin for x in bsl] == ['1111111', '11111111', '11101110']

    a = BitArray('0b000010001001011')
    bsl = list(a.split('0b1', bytealigned=False, end=14))
    assert [x.bin for x in bsl] == ['0000', '1000', '100', '10', '1']
    assert list(a[4:12].split('0b0', bytealigned=False)) == list(a.split('0b0', start=4, end=12))


def test_find_start_end_boundaries():
    a = Reader(BitArray('0b0010000100'))
    found = a.find('0b1', start=4)
    assert (found, a.bitpos) == (7, 7)
    found = a.find('0b1', start=2)
    assert (found, a.bitpos) == (2, 2)
    found = a.find('0b1', bytealigned=False, start=8)
    assert (found, a.bitpos) == (None, 2)

    a = Reader(BitArray('0b0010010000'))
    found = a.find('0b1', bytealigned=False, end=2)
    assert (found, a.bitpos) == (None, 0)
    found = a.find('0b1', end=3)
    assert (found, a.bitpos) == (2, 2)
    found = a.find('0b1', bytealigned=False, start=3, end=5)
    assert (found, a.bitpos) == (None, 2)
    found = a.find('0b1', start=3, end=6)
    assert (found, a.bitpos) == (5, 5)

    b = Reader(BitArray('0x0011223344'))
    with pytest.raises(ValueError):
        _ = b.find('0x22', bytealigned=True, start=-100)
    with pytest.raises(ValueError):
        _ = b.find('0x22', end=41, bytealigned=True)


def test_findall_generator_and_count():
    a = BitArray('0xff1234512345ff1234ff12ff')
    p = a.findall('0xff', bytealigned=True)
    assert next(p) == 0
    assert next(p) == 6 * 8
    assert next(p) == 9 * 8
    assert next(p) == 11 * 8
    with pytest.raises(StopIteration):
        _ = next(p)

    s = BitArray('0b1') * 100
    for i in [0, 1, 23]:
        assert len(list(s.findall('0b1', count=i))) == i
    with pytest.raises(ValueError):
        _ = s.findall('0b1', bytealigned=True, count=-1)


def test_set_reset_properties():
    s = BitArray()
    s.hex = '0'
    assert s.hex == '0'
    s.hex = '0x010203045'
    assert s.hex == '010203045'
    with pytest.raises(bitstring.CreationError):
        s.hex = '0x002g'

    s = BitArray(bin="000101101")
    assert s.bin == '000101101'
    assert len(s) == 9
    s.bin = '0'
    assert s.bin == '0'
    assert len(s) == 1

    s = BitArray(hex='0x000001b3')
    s.bin = ''
    assert len(s) == 0
    assert s.bin == ''


def test_overwrite_more_cases():
    s = BitArray(hex='342563fedec')
    s2 = BitArray(s)
    s.overwrite(BitArray(bin=''), 23)
    assert s.bin == s2.bin

    s = BitArray('0x123')
    s.overwrite(s, 0)
    assert s == '0x123'

    s = BitArray(bin='11111')
    with pytest.raises(ValueError):
        s.overwrite(BitArray(bin='1'), -10)
    with pytest.raises(ValueError):
        s.overwrite(BitArray(bin='1'), 6)
    s.overwrite('bin=0', 5)
    assert s.bin == '111110'
    s.overwrite(BitArray(hex='0x00'), 1)
    assert s.bin == '100000000'


def test_join_more_cases():
    s1 = BitArray(hex='00112233445566778899aabbccddeeff')
    s2 = BitArray(bin='0b000011')
    bsl = [s1[0:32], s1[4:12], s2, s2, s2, s2]
    assert BitArray().join(bsl).hex == '00112233010c30c3'

    bsl = [BitArray(uint=j, length=12) for j in range(10) for _ in range(10)]
    assert len(BitArray().join(bsl)) == 1200

    with pytest.raises(TypeError):
        _ = BitArray().join([1, 2])

    a = BitArray().join(['0xa', '0xb', '0b1111'])
    assert a == '0xabf'
    a = BitArray('0b1').join(['0b0' for _ in range(10)])
    assert a == '0b0101010101010101010'
    assert not BitArray('0xff').join([])
    a = BitArray('0xff').join([Bits.from_zeros(5), '0xab', '0xabc'])
    assert a == '0b00000, 0xffabffabc'


def test_file_object_creation_and_copy():
    filename = os.path.join(THIS_DIR, 'test.m1v')
    with open(filename, 'rb') as f:
        s = Bits.from_file(f, offset=32, length=12)
        assert s.uint == 352
        t = Bits('0xf') + Bits.from_file(f)
        assert t.startswith('0xf000001b3160')
        s2 = Bits.from_file(f)
        t2 = BitArray('0xc')
        t2.prepend(s2)
        assert t2.startswith('0x000001b3')
        assert t2.endswith('0xc')
        with open(filename, 'rb') as b:
            u = BitArray.from_bytes(b.read())
            assert u == s2

    with open(os.path.join(THIS_DIR, 'smalltestfile'), 'rb') as f:
        s = BitArray.from_file(f)
        t = BitArray(s)
        s.prepend('0b1')
        assert s[1:] == t
        s = BitArray.from_file(f)
        t = copy.copy(s)
        t.append('0b1')
        assert s == t[:-1]


def test_big_little_endian_error_cases():
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(ube=100, length=15)
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(ibe=100, length=15)
    with pytest.raises(bitstring.CreationError):
        _ = BitArray('ube:17=100')
    with pytest.raises(bitstring.CreationError):
        _ = BitArray('ibe:7=2')

    s = Reader(BitArray('0b1'))
    with pytest.raises(bitstring.InterpretError):
        _ = s.bits.ibe
    with pytest.raises(bitstring.InterpretError):
        _ = s.bits.ube
    with pytest.raises(ValueError):
        _ = s.read('ube')
    with pytest.raises(ValueError):
        _ = s.read('ibe')

    with pytest.raises(bitstring.CreationError):
        _ = BitArray('ule:15=10')
    with pytest.raises(bitstring.CreationError):
        _ = BitArray('ile:31=-999')
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(ule=100, length=15)
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(ile=100, length=15)


def test_little_endian_int_cases():
    s = BitArray(int=100, length=16)
    assert s.ile == 25600
    s = BitArray(ile=100, length=16)
    assert s.int == 25600
    assert s.ile == 100
    s.ile = 105
    assert s.ile == 105
    s = BitArray('ile:32=999')
    assert s.ile == 999
    s.byteswap()
    assert s.int == 999
    s = pack('ile:24', 1001)
    assert s.ile == 1001
    assert Reader(s).read('ile24') == 1001


@pytest.mark.parametrize(
    ("fmt", "value", "expected"),
    [
        ('<b', 23, 'ile:8=23'),
        ('<B', 23, 'ule:8=23'),
        ('<h', 23, 'ile:16=23'),
        ('<H', 23, 'ule:16=23'),
        ('<l', 23, 'ile:32=23'),
        ('<L', 23, 'ule:32=23'),
        ('<i', 23, 'ile:32=23'),
        ('<I', 23, 'ule:32=23'),
        ('<q', 23, 'ile:64=23'),
        ('<Q', 23, 'ule:64=23'),
        ('>b', 23, 'ibe:8=23'),
        ('>B', 23, 'ube:8=23'),
        ('>h', 23, 'ibe:16=23'),
        ('>H', 23, 'ube:16=23'),
        ('>l', 23, 'ibe:32=23'),
        ('>L', 23, 'ube:32=23'),
        ('>i', 23, 'ibe:32=23'),
        ('>I', 23, 'ube:32=23'),
        ('>q', 23, 'ibe:64=23'),
        ('>Q', 23, 'ube:64=23'),
    ],
)
def test_struct_token_matrix(fmt, value, expected):
    assert pack(fmt, value) == BitArray(expected)


def test_struct_token_multiplicative_factors_and_errors():
    s = pack('<2h', 1, 2)
    assert s.unpack('<2h') == [1, 2]
    s = pack('<100q', *range(100))
    assert len(s) == 100 * 64
    assert s[44 * 64:45 * 64].ule == 44

    for f in ['>>q', '<>q', 'q>', '2q', 'q', '>-2q', '@a', '@L0B2h', '=L', '>int:8', '>q2']:
        with pytest.raises(bitstring.CreationError):
            _ = pack(f, 100)


def test_byteswap_int_pack_code_iterable_and_errors():
    s = BitArray(pack('5*ule:16', *range(10, 15)))
    assert list(range(10, 15)) == s.unpack('5*ule:16')
    swaps = s.byteswap(2)
    assert list(range(10, 15)) == s.unpack('5*ube:16')
    assert swaps == 5

    s = BitArray('0xf234567f')
    swaps = s.byteswap(1, start=4)
    assert swaps == 3
    assert s == '0xf234567f'
    s.byteswap(2, start=4)
    assert s == '0xf452367f'
    s.byteswap(2, start=4, end=-4)
    assert s == '0xf234567f'
    s.byteswap(3)
    assert s == '0x5634f27f'
    s.byteswap(2, repeat=False)
    assert s == '0x3456f27f'

    s = BitArray('0x0011223344556677')
    assert s.byteswap('b') == 8
    assert s == '0x0011223344556677'
    assert s.byteswap('>3h', repeat=False) == 1
    assert s == '0x1100332255446677'

    s = BitArray('0x0011223344556677')
    assert s.byteswap(range(1, 4), repeat=False) == 1
    assert s == '0x0022115544336677'
    assert s.byteswap([2], start=8) == 3
    assert s == '0x0011224455663377'

    with pytest.raises(ValueError):
        s.byteswap('z')
    with pytest.raises(ValueError):
        s.byteswap(-1)
    with pytest.raises(ValueError):
        s.byteswap([-1])
    with pytest.raises(ValueError):
        s.byteswap([1, 'e'])
    with pytest.raises(TypeError):
        s.byteswap(5.4)


@pytest.mark.parametrize(
    ("value", "prefix", "args", "expected"),
    [
        ('0x12ff', '0x1', (), True),
        ('0x12ff', '0b0001001', (), True),
        ('0x12ff', '0x12ff', (), True),
        ('0x12ff', '0x12ff, 0b1', (), False),
        ('0x123456', '0x234', (4,), True),
        ('0x123456', '0x123', (None, 11), False),
        ('0x123456', '0x123', (None, 12), True),
        ('0x123456', '0x34', (8, 16), True),
    ],
)
def test_startswith_cases(value, prefix, args, expected):
    a = BitArray(value)
    if not args:
        assert a.startswith(prefix) is expected
    elif len(args) == 1:
        assert a.startswith(prefix, start=args[0]) is expected
    else:
        assert a.startswith(prefix, start=args[0], end=args[1]) is expected


@pytest.mark.parametrize(
    ("value", "suffix", "args", "expected"),
    [
        ('0xf2341', '0x41', (), True),
        ('0xf2341', '0b001', (), True),
        ('0xf2341', '0xf2341', (), True),
        ('0xf2341', '0x1f2341', (), False),
        ('0x123456', '0x234', (None, 16), True),
        ('0x123456', '0x456', (13,), False),
        ('0x123456', '0x456', (12,), True),
        ('0x123456', '0x34', (8, 16), True),
    ],
)
def test_endswith_cases(value, suffix, args, expected):
    a = BitArray(value)
    if not args:
        assert a.endswith(suffix) is expected
    elif len(args) == 1:
        assert a.endswith(suffix, start=args[0]) is expected
    else:
        assert a.endswith(suffix, start=args[0], end=args[1]) is expected


def test_read_unpack_peek_with_keyword_lengths():
    a = Bits('0xff, 0b000, 0xf')
    x, y, z = a.unpack('hex:a, bin, hex:b', a=8, b=4)
    assert x == 'ff'
    assert y == '000'
    assert z == 'f'

    a = Bits('0b110')
    x, = a.unpack('bin:3', notused=33)
    assert x == '110'

    a = pack('uint:p=33', p=12)
    with pytest.raises(ValueError):
        a.unpack('uint:p')
    with pytest.raises(ValueError):
        a.unpack('uint:p', p='a_string')

    s = Reader(BitArray('0x0102'))
    x, y = s.peeklist('8, hex:b', b=4)
    assert (x, y) == ('0x01', '0')
    assert s.pos == 0


def test_bytes_keyword_problem():
    s = Bits('0x01')
    x, = s.unpack('bytes:a', a=1)
    assert x == b'\x01'

    s = Bits('0x000ff00a')
    x, y, z = s.unpack('12, bytes:x, bits', x=2)
    assert (x.int, y, z) == (0, b'\xff\x00', '0xa')


def test_bool_assignment_and_errors():
    a = BitArray()
    a.bool = True
    assert a.bool is True
    a.hex = 'ee'
    a.bool = False
    assert a.bool is False
    a.bool = 'False'
    assert a.bool is False
    a.bool = 'True'
    assert a.bool is True
    a.bool = 0
    assert a.bool is False
    a.bool = 1
    assert a.bool is True

    for args in [('bool=true',), ('True',), ('bool', 2)]:
        with pytest.raises(bitstring.CreationError):
            _ = pack(*args)
    with pytest.raises(bitstring.InterpretError):
        _ = BitArray('0b11').bool
    b = BitArray()
    with pytest.raises(bitstring.InterpretError):
        _ = b.bool
    with pytest.raises(bitstring.CreationError):
        b.bool = 'false'

    a = Reader(Bits('0xf'))
    with pytest.raises(ValueError):
        _ = a.read('bool:0')
    with pytest.raises(ValueError):
        _ = a.read('bool:2')


def test_zero_bit_reads_and_read_int_list():
    a = Reader(Bits('0x123456'))
    with pytest.raises(bitstring.InterpretError):
        _ = a.read('uint:0')
    with pytest.raises(bitstring.InterpretError):
        _ = a.read('float:0')

    a = Reader(Bits('0xab, 0b110'))
    b, c = a.readlist([8, 3])
    assert b.hex == 'ab'
    assert c.bin == '110'


def test_count_with_offset_and_bytes_problem_cases():
    a = Bits('0xff0120ff')
    b = a[1:-1]
    assert b.count(1) == 16
    assert b.count(0) == 14

    b = BitArray.from_bytes(b'\x00\xaa', offset=8)
    assert b.hex == 'aa'
    b = BitArray.from_bytes(b'\x00\xaa', offset=4)
    assert b.hex == '0aa'
    b = BitArray.from_bytes(b'\x00\xaa', offset=8, length=8)
    b.invert()
    assert b.hex == '55'
    b = BitArray.from_bytes(b'\xaa\xbb', offset=8, length=4)
    b.prepend('0xe')
    assert b.hex == 'eb'
    b = BitArray.from_bytes(b'\x01\x02\x03\x04', offset=8)
    b.byteswap()
    assert b == '0x040302'


def test_format_and_cacheing_cases():
    a = Bits('0xabc')
    assert f'{a}' == '0xabc'
    a += '0b0'
    assert f'{a}' == '0b1010101111000'
    b = BitArray.from_zeros(10)
    assert f'{b}' == '0b0000000000'
    c = BitArray.from_file(os.path.join(THIS_DIR, 'test.m1v'))
    assert f'{c}'[0:10] == '0x000001b3'
    assert f'{Bits("0xf").bin}' == '1111'

    _ = BitArray('0xdeadbeef1000')
    _ = BitArray('0xdeadbeef002')
    with pytest.raises(bitstring.CreationError):
        _ = BitArray('0xdeadbeef002', length=16)


def test_operator_identity_semantics_for_bits_and_bitarray():
    a1 = Bits('0xabc')
    b1 = a1
    a1 += '0xdef'
    assert a1 == '0xabcdef'
    assert b1 == '0xabc'

    a2 = BitArray('0xabc')
    b2 = a2
    c2 = a2 + '0x0'
    a2 += '0xdef'
    assert a2 == '0xabcdef'
    assert b2 == '0xabcdef'
    assert c2 == '0xabc0'

    a1 = Bits('0xabc')
    b1 = a1
    a1 &= '0xf0f'
    assert a1 == '0xa0c'
    assert b1 == '0xabc'

    a2 = BitArray('0xabc')
    b2 = a2
    c2 = a2 & '0x00f'
    a2 &= '0xf0f'
    assert a2 == '0xa0c'
    assert b2 == '0xa0c'
    assert c2 == '0x00c'


def test_rotation_file_and_errors():
    a = BitArray()
    with pytest.raises(bitstring.Error):
        a.ror(0)
    a += '0b001'
    with pytest.raises(ValueError):
        a.ror(-1)

    a = BitArray()
    with pytest.raises(bitstring.Error):
        a.rol(0)
    a += '0b001'
    with pytest.raises(ValueError):
        a.rol(-1)

    a = BitArray.from_file(os.path.join(THIS_DIR, 'test.m1v'))
    m = len(a)
    a.rol(1)
    assert a.startswith('0x000003')
    assert len(a) == m
    assert a.endswith('0x0036e')

    a = BitArray.from_file(os.path.join(THIS_DIR, 'test.m1v'))
    m = len(a)
    a.ror(1)
    assert a.startswith('0x800000')
    assert len(a) == m
    assert a.endswith('0x000db')


def test_efficient_overwrite_and_large_counts():
    a = BitArray.from_zeros(1000000)
    a.overwrite([1], 123456)
    assert a[123456] is True
    a.overwrite('0xff', 1)
    assert a[0:32:1] == '0x7f800000'

    c = BitArray(length=1000)
    c.overwrite('0xaaaaaaaaaaaa', 81)
    assert c[81:81 + 6 * 8] == '0xaaaaaaaaaaaa'
    assert len(list(c.findall('0b1'))) == 24
    s = BitArray(length=1000)[5:]
    s.overwrite('0xffffff', 500)
    r = Reader(s, pos=500)
    assert r.read(4 * 8) == '0xffffff00'
    s.overwrite('0xff', 502)
    assert s[502:518] == '0xffff'


def test_find_remaining_corner_cases():
    s = Reader(BitArray('0xff'))
    assert s.find(s.bits) == 0
    assert s.find(BitArray(hex='0x12')) is None
    assert s.find(BitArray(hex='0xffff')) is None

    s = Reader(BitArray(hex='0x1122334455'), pos=2)
    s.find('0x66', bytealigned=True)
    assert s.pos == 2
    s.pos = 38
    s.find('0x66', bytealigned=True)
    assert s.pos == 38

    s = Reader(BitArray('0x1234'))
    assert s.find('0x1234') == 0
    assert s.find('0x1234') == 0
    s.bits.append('0b111')
    s.pos = 3
    assert s.find('0b1', start=17, bytealigned=True) is None
    assert s.pos == 3


def test_rfind_endbit_cases():
    a = Reader(BitArray('0x000fff'))
    b = a.rfind('0b011', start=0, end=14, bytealigned=False)
    assert b is not None
    assert a.rfind('0b011', start=0, end=13, bytealigned=False) is None


def test_remaining_shift_in_place_errors_and_whole_length():
    s = BitArray('0xabcd')
    s >>= len(s)
    assert s == '0x0000'

    s = BitArray()
    with pytest.raises(ValueError):
        s >>= 1
    s += '0b11'
    with pytest.raises(ValueError):
        s >>= -1

    s = BitArray()
    with pytest.raises(ValueError):
        s <<= 1
    s += '0b11'
    with pytest.raises(ValueError):
        s <<= -1


def test_replace_range_cases():
    a = BitArray('0x00114723ef4732344700')
    n = a.replace('0x47', '0x00', bytealigned=True)
    assert n == 3
    assert a.hex == '00110023ef0032340000'
    a.replace('0x00', '', bytealigned=True)
    assert a.hex == '1123ef3234'
    a.replace('0x11', '', start=1, bytealigned=True)
    assert a.hex == '1123ef3234'
    a.replace('0x11', '0xfff', end=7, bytealigned=True)
    assert a.hex == '1123ef3234'
    a.replace('0x11', '0xfff', end=8, bytealigned=True)
    assert a.hex == 'fff23ef3234'

    a = BitArray.from_string('0xab')
    b = BitArray.from_string('0xcd')
    c = BitArray.from_string('0xabef')
    c.replace(a, b)
    assert c == '0xcdef'
    assert a == '0xab'
    assert b == '0xcd'


def test_pack_uint_and_default_uint_errors():
    s = pack('uint:10, uint:5', 1, 2)
    a, b = s.unpack('10, 5')
    assert (a.uint, b.uint) == (1, 2)
    s = pack('uint:10=150, uint:12=qee', qee=3)
    assert s == 'uint:10=150, uint:12=3'
    assert BitArray('uint:100=5') == 'uint:100=5'
    with pytest.raises(bitstring.CreationError):
        _ = BitArray('5=-1')


def test_packing_long_keyword_and_variable_lengths():
    s = pack('bits=b', b=BitArray.from_zeros(128000))
    assert s == BitArray.from_zeros(128000)
    with pytest.raises(bitstring.CreationError):
        _ = pack('bin:1')
    with pytest.raises(bitstring.CreationError):
        _ = pack('', 100)
    assert pack('uint10', uint10='0b1') == '0b1'
    assert pack('0b110', **{'0b110': '0xfff'}) == '0xfff'
    for i in range(1, 11):
        assert pack('uint:n', 0, n=i).bin == '0' * i


def test_pack_capital_keywords_and_other_capitals():
    assert pack('A', A='0b1') == '0b1'
    format_ = 'bits:4=BL_OFFT, uint:12=width, uint:12=height'
    d = {'BL_OFFT': '0b1011', 'width': 352, 'height': 288}
    assert bitstring.pack(format_, **d) == '0b1011, uint:12=352, uint:12=288'
    assert pack('0X0, uint:8, hex', 45, '0XABcD') == '0x0, uint:8=45, 0xabCD'
    assert Bits('0XABC, 0O0, 0B11') == 'hex=0Xabc, oct=0, bin=0B11'


def test_file_slices_errors_and_hex_reset():
    filename = os.path.join(THIS_DIR, 'smalltestfile')
    s = BitArray.from_file(filename)
    assert s[-16:].hex == 'cdef'
    with pytest.raises(IOError):
        _ = BitArray.from_file('Idonotexist')

    s = BitArray.from_file(os.path.join(THIS_DIR, 'test.m1v'))
    assert s[0:32].hex == '000001b3'
    assert s[-32:].hex == '000001b7'
    s.hex = '0x11'
    assert s.hex == '11'


def test_file_reader_independent_positions():
    filename = os.path.join(THIS_DIR, 'test.m1v')
    s1 = Reader(BitArray.from_file(filename))
    s2 = Reader(BitArray.from_file(filename))
    assert s1.read(32).hex == '000001b3'
    assert s2.read(32).hex == '000001b3'
    s1.bytepos += 4
    assert s1.read(8).hex == '02'
    assert s2.read(5 * 8).hex == '1601208302'
    s1.pos = len(s1)
    with pytest.raises(ValueError):
        s1.pos += 1
        s1.read(0)


def test_insert_null_bits_and_self():
    s = BitArray(hex='0x123')
    s.insert(BitArray(), 3)
    assert s.hex == '123'

    one = BitArray(bin='1')
    zero = BitArray(bin='0')
    s = BitArray(bin='00')
    s.insert(one, 0)
    assert s.bin == '100'
    s.insert(zero, 0)
    assert s.bin == '0100'
    s.insert(one, len(s))
    assert s.bin == '01001'
    s.insert(s, 2)
    assert s.bin == '0101001001'


def test_more_adding_radd_and_self_append():
    s = BitArray(bin='00') + BitArray(bin='') + BitArray(bin='11')
    assert s.bin == '0011'
    s = '0b01'
    s += BitArray('0b11')
    assert s.bin == '0111'
    s = BitArray('0x00')
    t = BitArray('0x11')
    s += t
    assert s.hex == '0011'
    assert t.hex == '11'
    s += s
    assert s.hex == '00110011'
    assert ('0xff' + BitArray('0xee')).hex == 'ffee'


def test_delete_bits_bytes_and_getitems():
    s = BitArray(bin='000111100000')
    del s[4:8]
    assert s.bin == '00010000'
    del s[4:1004]
    assert s.bin == '0001'

    s = BitArray('0x00112233')
    del s[8:8]
    assert s.hex == '00112233'
    del s[8:16]
    assert s.hex == '002233'
    del s[:24]
    assert not s

    s = BitArray(bin='0b1011')
    assert [s[i] for i in range(4)] == [True, False, True, True]
    with pytest.raises(IndexError):
        _ = s[4]
    assert [s[i] for i in range(-1, -5, -1)] == [True, True, False, True]
    with pytest.raises(IndexError):
        _ = s[-5]


def test_slicing_and_negative_slicing_more():
    s = Bits(hex='0123456789')
    assert s[0:8].hex == '01'
    assert not s[0:0]
    assert not s[23:20]
    assert s[8:12].bin == '0010'
    assert s[32:80] == '0x89'

    s = Bits(hex='012345678')
    assert s[:-8].hex == '0123456'
    assert s[-16:-8].hex == '56'
    assert s[-24:].hex == '345678'
    assert s[-1000:-24] == '0x012'


def test_writing_data_and_offsets():
    strings = [BitArray(bin=x) for x in ['0', '001', '0011010010', '010010', '1011']]
    s = BitArray().join(strings)
    s2 = BitArray.from_bytes(s.bytes)
    assert s2.bin == '000100110100100100101011'
    s2.append(BitArray(bin='1'))
    s3 = BitArray.from_bytes(s2.tobytes())
    assert s3.bin == '00010011010010010010101110000000'

    s1 = BitArray.from_bytes(b'\x10')
    s2 = BitArray.from_bytes(b'\x08\x00', length=8, offset=1)
    s3 = BitArray.from_bytes(b'\x04\x00', length=8, offset=2)
    assert s1 == s2 == s3
    assert s1.bytes == s2.bytes == s3.bytes


def test_various_compositions_with_reader():
    hexes = ['12345678', '87654321', 'ffffffffff', 'ed', '12ec']
    bins = ['001010', '1101011', '0010000100101110110110', '11', '011']
    bsl = []
    for (hex_, bin_) in list(zip(hexes, bins)) * 5:
        bsl.append(BitArray(hex=hex_))
        bsl.append(BitArray(bin=bin_))
    r = Reader(BitArray().join(bsl))
    for (hex_, bin_) in list(zip(hexes, bins)) * 5:
        h = r.read(4 * len(hex_))
        b = r.read(len(bin_))
        assert h.hex == hex_
        assert b.bin == bin_

    s1 = BitArray(hex="0x1f08")[:13]
    assert s1.bin == '0001111100001'
    s2 = BitArray(bin='0101')
    s1.append(s2)
    assert s1.bin == '00011111000010101'
    assert s1[3:8].bin == '11111'


def test_reader_position_arithmetic():
    s = Reader(BitArray(hex='0xff'), pos=6)
    s.pos += 1
    assert s.bitpos == 7
    s.bitpos += 1
    assert s.pos == 8
    s.pos += 1
    with pytest.raises(ValueError):
        s.read(0)

    s = Reader(BitArray(hex='0x010203'))
    s.bytepos += 1
    assert s.bytepos == 1
    s.bytepos += 1
    assert s.bytepos == 2
    s.bytepos += 1
    assert s.bytepos == 3
    s.bytepos += 1
    with pytest.raises(ValueError):
        s.read(0)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ('bin=001', '0b001'),
        ('oct=0o007', '0o007'),
        ('hex=123abc', '0x123abc'),
        ('bin2=01', '0b01'),
        ('0xff 0Xee 0xd 0xcc', '0xffeedcc'),
        ('0b0 0B111 0b001', '0b0111001'),
        ('  0o123 0O 7 0   o1', '0o12371'),
    ],
)
def test_auto_creation_more(source, expected):
    assert BitArray(source) == expected


@pytest.mark.parametrize("source", ['bin:1=01', 'bits:4=0b1', 'oct3=000', 'hex4=0x1234'])
def test_auto_creation_error_more(source):
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(source)


def test_more_auto_methods_and_split_with_self():
    s = BitArray('0b000000010100011000')
    assert Reader(s).find('0b101') == 7
    s = BitArray('0x00004700')
    r = Reader(s)
    assert r.find('0b01000111', bytealigned=True) == 16
    assert r.bytepos == 2

    s = BitArray('0x000143563200015533000123')
    sections = s.split('0x0001')
    assert next(sections).hex == ''
    assert next(sections).hex == '0001435632'
    assert next(sections).hex == '00015533'
    assert next(sections).hex == '000123'
    with pytest.raises(StopIteration):
        next(sections)

    s = BitArray('0x1234')
    sections = s.split(s)
    assert next(sections).hex == ''
    assert next(sections).hex == '1234'
    with pytest.raises(StopIteration):
        next(sections)


def test_multiple_auto_mutations_and_reverse():
    s = BitArray('0xa')
    s.prepend('0xf')
    s.append('0xb')
    assert s == '0xfab'
    s.prepend(s)
    s.append('0x100')
    s.overwrite('0x5', 4)
    assert s == '0xf5bfab100'

    s = BitArray('0b0011')
    s.reverse()
    assert s.bin == '1100'
    s = BitArray('0b10')
    s.reverse()
    assert s.bin == '01'
    s = BitArray()
    s.reverse()
    assert s.bin == ''


def test_equality_not_equals_and_auto_copy():
    s1 = BitArray('0b01010101')
    s2 = BitArray('0b01010101')
    assert s1 == s2
    assert BitArray() == BitArray()
    s5 = BitArray.from_bytes(b'\xff', offset=2, length=3)
    assert s5 == BitArray('0b111')
    assert s5 != object()

    assert BitArray('0b0') != BitArray('0b1')
    assert not BitArray('0b0') != BitArray('0b0')

    a = BitArray('0b00110111')
    assert a == '0b00110111'
    assert a == '0x37'
    assert '0b0011 0111' == a
    assert '0x3 0x7' == a
    assert a != '0b11001000'

    s = BitArray('0xabcdef')
    t = BitArray(s)
    assert t.hex == 'abcdef'
    del s[-8:]
    assert t.hex == 'abcdef'


def test_invert_special_method_cases():
    s = BitArray('0b00011001')
    t = ~s
    assert t.bin == '11100110'
    assert (~BitArray('0b0')).bin == '1'
    assert (~BitArray('0b1')).bin == '0'
    assert ~t == s
    with pytest.raises(bitstring.Error):
        _ = ~BitArray()


def test_large_equals_and_mutation():
    s1 = BitArray.from_zeros(1000000)
    s2 = BitArray.from_zeros(1000000)
    s1.set(True, [-1, 55, 53214, 534211, 999999])
    s2.set(True, [-1, 55, 53214, 534211, 999999])
    assert s1 == s2
    s1.set(True, 800000)
    assert s1 != s2


def test_cut_problem_and_more_cut_errors():
    s = BitArray('0x1234')
    for n in list(s.cut(4)):
        s.prepend(n)
    assert s == '0x43211234'

    a = BitArray('0b1')
    with pytest.raises(ValueError):
        _ = next(a.cut(1, start=1, end=2))
    with pytest.raises(ValueError):
        _ = next(a.cut(1, start=-2, end=1))
    with pytest.raises(ValueError):
        _ = next(a.cut(0))
    with pytest.raises(ValueError):
        _ = next(a.cut(1, count=-1))


def test_token_parser_struct_codes():
    tp = bitstring.utils.tokenparser
    assert tp('>H') == (False, [('ube', 16, None)])
    assert tp('<H') == (False, [('ule', 16, None)])
    for fmt in ['=H', '@H']:
        with pytest.raises(ValueError, match='Native-endian struct formats'):
            _ = tp(fmt)
    assert tp('>b') == (False, [('i', 8, None)])
    assert tp('<b') == (False, [('i', 8, None)])


def test_file_based_all_any_more():
    filename = os.path.join(THIS_DIR, 'test.m1v')
    a = BitArray.from_file(filename)
    assert a.all(False, (0, 1, 2, 3, 4))
    b = Bits.from_file(filename, offset=16)
    assert b.startswith('0x01')
    assert not b.any(True, range(0, 7))
    assert b.any(True, range(0, 8))
    assert b.any(True)


def test_any_all_false_and_empty_whole_cases():
    a = BitArray('0b10011011')
    assert a.any(True, (1, 2, 3, 5))
    assert not a.any(True, (1, 2, 5))
    assert a.any(True, (-1,))
    assert not a.any(True, (1,))

    a = Bits('0b0010011101')
    assert a.all(False, (0, 1, 3, 4))
    assert not a.all(False, (0, 1, 2, 3, 4))
    a = Bits('0b01001110110111111111111111111')
    assert a.any(False, (4, 5, 6, 2))
    assert not a.any(False, (1, 15, 20))

    assert not Bits().any(True)
    assert not Bits().any(False)
    assert Bits().all(True)
    assert Bits().all(False)
    assert Bits('0xfff').any(True)
    assert not Bits('0xfff').any(False)
    assert Bits('0xfff').all(True)
    assert not Bits('0xfff').all(False)


def test_float_reading_more_cases():
    a = Reader(BitArray('fle:16=12, fbe:32=-0.01, f:32=3e33'))
    x, y, z = a.readlist('fle:16, fbe:32, f:32')
    assert x / 12.0 == pytest.approx(1.0)
    assert y / -0.01 == pytest.approx(1.0)
    assert z / 3e33 == pytest.approx(1.0)

    a = Reader(BitArray('0b11, fle:64=12, 0xfffff'), pos=2)
    assert a.read(Dtype('fle64')) == 12.0
    b = BitArray(fle=20, length=32)
    b.fle = 10.0
    b = [0] + b
    assert b[1:].fle == 10.0

    s = Reader(BitArray('0b1, float:32 = 10.0'))
    x, y = s.readlist('1, float:32')
    assert y == 10.0
    bits = s.bits
    bits[1:] = 'fle:32=20.0'
    x, y = bits.unpack('1, fle:32')
    assert y == 20.0


def test_float_error_more_cases():
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(fle=0.3, length=0)
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(fle=0.3, length=1)
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(float=2)
    with pytest.raises(bitstring.InterpretError):
        _ = Reader(BitArray('0x3')).read('fle:2')
    with pytest.raises(ValueError):
        Reader(BitArray('0x123123')).read('10, 5')


def test_bytes_token_more_thoroughly_restored():
    a = Reader(BitArray('0x0123456789abcdef'), pos=16)
    assert a.read('bytes:1') == b'\x45'
    assert a.read('bytes:3') == b'\x67\x89\xab'
    x, y, z = a.bits.unpack('bits:28, bytes, bits:12')
    assert y == b'\x78\x9a\xbc'


def test_dedicated_read_functions_more_cases():
    a = Reader(BitArray('0b11, ube:48=98798798172, 0b11111'), pos=2)
    assert a.read(Dtype('ube48')) == 98798798172
    assert a.pos == 50

    b = BitArray('0xff, ule:800=999, 0xffff')
    assert b[8:800].ule == 999

    a = Reader(BitArray('0b111, ile:48=999999999, 0b111111111111'), pos=3)
    assert a.read('ile48') == 999999999
    b = Reader(BitArray('0xff, ile:200=918019283740918263512351235, 0xfffffff'), pos=8)
    assert b.read(Dtype('ile', length=200)) == 918019283740918263512351235

    a = Reader(BitArray('0b111, fle:64=9.9998, 0b111'), pos=3)
    assert a.read('fle64') == 9.9998


def test_reading_problem_and_creation_exception_bug():
    a = Reader(BitArray('0x000001'))
    assert a.read('uint:24') == 1
    a.pos = 0
    with pytest.raises(bitstring.ReadError):
        _ = a.read('bytes:4')
    with pytest.raises(ValueError):
        _ = BitArray(bin=1)


def test_operator_identity_or_xor_mul_shift():
    a1 = Bits('0xabc')
    b1 = a1
    a1 |= '0xf0f'
    assert a1 == '0xfbf'
    assert b1 == '0xabc'
    a2 = BitArray('0xabc')
    b2 = a2
    c2 = a2 | '0x00f'
    a2 |= '0xf0f'
    assert a2 == '0xfbf'
    assert b2 == '0xfbf'
    assert c2 == '0xabf'

    a1 = Bits('0xabc')
    b1 = a1
    a1 ^= '0xf0f'
    assert a1 == '0x5b3'
    assert b1 == '0xabc'
    a2 = BitArray('0xabc')
    b2 = a2
    c2 = a2 ^ '0x00f'
    a2 ^= '0xf0f'
    assert a2 == '0x5b3'
    assert b2 == '0x5b3'
    assert c2 == '0xab3'


def test_operator_identity_mul_and_shifts():
    a1 = Bits('0xabc')
    b1 = a1
    a1 *= 3
    assert a1 == '0xabcabcabc'
    assert b1 == '0xabc'
    a2 = BitArray('0xabc')
    b2 = a2
    c2 = a2 * 2
    a2 *= 3
    assert a2 == '0xabcabcabc'
    assert b2 == '0xabcabcabc'
    assert c2 == '0xabcabc'

    a1 = Bits('0xabc')
    b1 = a1
    a1 <<= 4
    assert a1 == '0xbc0'
    assert b1 == '0xabc'
    a2 = BitArray('0xabc')
    b2 = a2
    c2 = a2 << 8
    a2 <<= 4
    assert a2 == '0xbc0'
    assert b2 == '0xbc0'
    assert c2 == '0xc00'

    a1 = Bits('0xabc')
    b1 = a1
    a1 >>= 4
    assert a1 == '0x0ab'
    assert b1 == '0xabc'


def test_function_negative_indices_more_cases():
    s = BitArray('0x1234151f')
    assert list(s.findall('0x1', bytealigned=True, start=-15)) == [24]
    assert list(s.findall('0x1', bytealigned=True, start=-16)) == [16, 24]
    assert list(s.findall('0x1', bytealigned=True, end=-5)) == [0, 16]
    assert list(s.findall('0x1', bytealigned=True, end=-4)) == [0, 16, 24]

    r = Reader(s)
    assert r.rfind('0x1f', end=-1) is None
    assert r.rfind('0x12', start=-31) is None

    s = BitArray('0x12345')
    assert list(s.cut(4, start=-12, end=-4)) == ['0x3', '0x4']

    s = BitArray('0xfe0012fe1200fe')
    assert list(s.split('0xfe', bytealigned=True, end=-1)) == ['', '0xfe0012', '0xfe1200f, 0b111']
    assert list(s.split('0xfe', bytealigned=True, start=-8)) == ['', '0xfe']
    assert s.startswith('0x00f', start=-16)
    assert s.startswith('0xfe00', end=-40)
    assert not s.startswith('0xfe00', end=-41)
    assert s.endswith('0x00fe', start=-16)
    assert not s.endswith('0x00fe', start=-15)
    assert not s.endswith('0x00fe', end=-1)
    assert s.endswith('0x00f', end=-4)

    s.replace('0xfe', '', end=-1)
    assert s == '0x00121200fe'
    s.replace('0x00', '', start=-24)
    assert s == '0x001212fe'


def test_rotate_start_and_end_more_cases():
    a = BitArray('0b110100001')
    a.rol(1, start=3, end=6)
    assert a == '0b110001001'
    a.ror(1, start=-4)
    assert a == '0b110001100'
    a.rol(202, end=-5)
    assert a == '0b001101100'
    a.ror(3, end=4)
    assert a == '0b011001100'
    with pytest.raises(ValueError):
        a.rol(5, start=-4, end=-6)


def test_byte_swap_from_file_and_remaining_iterable_case():
    s = BitArray.from_file(os.path.join(THIS_DIR, 'smalltestfile'))
    swaps = s.byteswap('2bh')
    assert s == '0x0123674589abefcd'
    assert swaps == 2

    s = BitArray('0x0011223344556677')
    s.byteswap(range(1, 4), repeat=False)
    s.byteswap([2], start=8)
    assert s.byteswap([2, 3], start=4) == 1
    assert s == '0x0120156452463377'


def test_bracket_tokens_and_packing_default_int_keyword():
    s = BitArray('3*(0x0, 0b1)')
    assert s == '0x0, 0b1, 0x0, 0b1, 0x0, 0b1'
    s = pack('2*(uint:12, 3*(uint:7, uint:6))', *range(3, 17))
    a = s.unpack('12, 7, 6, 7, 6, 7, 6, 12, 7, 6, 7, 6, 7, 6')
    assert [x.uint for x in a] == list(range(3, 17))
    assert a == s.unpack('2*(12,3*(7,6))')

    s = pack('uint:12', 100)
    assert s.unpack('12')[0].uint == 100
    s = pack('int:oh_no_not_the_eyes=33', oh_no_not_the_eyes=17)
    assert s.int == 33
    assert len(s) == 17


def test_hash_edge_cases_for_bits():
    a = Bits('0xabcd')
    b = Bits('0xabcd')
    c = b[1:]
    assert hash(a) == hash(b)
    assert hash(a) != hash(c)
    s = {Bits(uint=1 << 300, length=10000), Bits(uint=2 << 300, length=10000), Bits(uint=3 << 300, length=10000)}
    assert len(s) == 3


def test_bits_function_return_types_and_copy():
    s = Bits('0xf, 0b1')
    t = copy.copy(s)
    assert type(t) is Bits
    a = s + '0o3'
    assert type(a) is Bits
    assert type(a[0:4]) is Bits
    assert type(a[4:3]) is Bits
    assert type(a[5:2:-1]) is Bits
    assert type(~a) is Bits
    assert type(a << 2) is Bits
    assert type(a >> 2) is Bits
    assert type(a * 2) is Bits
    assert type(a & ~a) is Bits
    assert type(Reader(a).read(4)) is Bits


def test_bits_property_immutability_more():
    a = Bits('0x123123')
    with pytest.raises(AttributeError):
        a.hex = '0x234'
    with pytest.raises(AttributeError):
        a.oct = '0o234'
    with pytest.raises(AttributeError):
        a.bin = '0b101'
    with pytest.raises(AttributeError):
        a.ue = 3453
    with pytest.raises(AttributeError):
        a.se = -123
    with pytest.raises(AttributeError):
        a.int = 432
    with pytest.raises(AttributeError):
        a.bytes = b'hello'


def test_bytes_problem_more_cases():
    b = BitArray.from_bytes(b'\x00\xaa', offset=8, length=4)
    assert b.bin == '1010'
    b = BitArray.from_bytes(b'\x00\xaa', offset=8, length=8)
    b.prepend('0xee')
    assert b.hex == 'eeaa'


def test_add_empty_bits_issue_more():
    x = BitArray()
    assert x + Bits('0xff') == '0xff'
    assert x + bitstring.BitArray('0xff') == '0xff'
    xx = Bits()
    assert xx + Bits('0xff') == '0xff'
    assert xx + bitstring.BitArray('0xff') == '0xff'


@pytest.mark.parametrize("fmt", ['=B', '=h', '=H', '@l', '@L', '@i', '@I', '@q', '@Q'])
def test_native_struct_pack_codes_removed(fmt):
    with pytest.raises(bitstring.CreationError, match='Native-endian struct formats'):
        _ = pack(fmt, 23)


@pytest.mark.parametrize("source", [bytearray(b'uint:5=2'), memoryview(b'uint:5=2')])
def test_buffer_creation_more(source):
    bits = Bits(source)
    assert len(bits) >= 0


@pytest.mark.parametrize("source", [range(12), (0, 1, '0', '1'), [True, False, [], [0], 'hello']])
def test_bool_iterable_factory_more(source):
    bits = Bits.from_bools(source)
    assert len(bits) >= 0


@pytest.mark.parametrize("source", ['5', '+0.0001', '-1e101', '4.', '.2', '-.65', '43.21E+32'])
def test_float64_init_strings_more(source):
    a = BitArray('float:64=%s' % source)
    assert a.float == float(source)


@pytest.mark.parametrize("source", ['5', '+0.5', '-1e2', '4.', '.25', '-.75'])
def test_float16_init_strings_more(source):
    a = BitArray('float:16=%s' % source)
    assert a.f == float(source)


@pytest.mark.parametrize("token", ['hex:1', 'oct:1', '-5', 'fred', 'bin:-2', 'uint:p',
                                   'uint:-2', 'int:u', 'int:-3', 'ses', 'uee', '-14'])
def test_invalid_reader_tokens_more(token):
    with pytest.raises(ValueError):
        _ = Reader(BitArray('0x123456')).read(token)


@pytest.mark.parametrize(
    "kwargs",
    [
        {'ube': 100, 'length': 15},
        {'ibe': 100, 'length': 15},
        {'ule': 100, 'length': 15},
        {'ile': 100, 'length': 15},
        {'fle': 0.3, 'length': 0},
        {'fle': 0.3, 'length': 1},
        {'float': 2},
    ],
)
def test_creation_error_kwargs_more(kwargs):
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(**kwargs)


@pytest.mark.parametrize(
    "source",
    [
        'ube:17=100',
        'ibe:7=2',
        'ule:15=10',
        'ile:31=-999',
        'bool=true',
        'True',
        'hello',
    ],
)
def test_creation_error_strings_more(source):
    with pytest.raises(bitstring.CreationError):
        _ = BitArray(source)


@pytest.mark.parametrize("fmt", ['>>q', '<>q', 'q>', '2q', 'q', '>-2q', '@a', '>int:8', '>q2'])
def test_struct_token_error_cases_more(fmt):
    with pytest.raises(bitstring.CreationError):
        _ = pack(fmt, 100)


@pytest.mark.parametrize("fmt", ['<B', '<H', '<L', '<Q'])
def test_unsigned_struct_negative_errors_more(fmt):
    with pytest.raises(bitstring.CreationError):
        _ = pack(fmt, -1)


@pytest.mark.parametrize(
    "bad_call",
    [
        lambda s: s.byteswap('z'),
        lambda s: s.byteswap(-1),
        lambda s: s.byteswap([-1]),
        lambda s: s.byteswap([1, 'e']),
        lambda s: s.byteswap('!h'),
        lambda s: s.byteswap(2, start=-1000),
    ],
)
def test_byteswap_value_errors_more(bad_call):
    with pytest.raises(ValueError):
        bad_call(BitArray('0x0011223344556677'))


def test_byteswap_type_error_more():
    with pytest.raises(TypeError):
        BitArray('0x0011223344556677').byteswap(5.4)


@pytest.mark.parametrize("value", [-9, 16])
def test_slice_integer_assignment_value_errors_more(value):
    a = BitArray('0b0000')
    with pytest.raises(ValueError):
        a[0:4] = value


@pytest.mark.parametrize("value", [-2, 2])
def test_single_bit_assignment_value_errors_more(value):
    a = BitArray('0b0000')
    with pytest.raises(ValueError):
        a[0] = value


@pytest.mark.parametrize(
    ("method", "args", "kwargs"),
    [
        ('reverse', (), {'start': -1, 'end': 4}),
        ('reverse', (), {'start': 10, 'end': 9}),
        ('reverse', (), {'start': 1, 'end': 10000}),
        ('rol', (5,), {'start': -4, 'end': -6}),
    ],
)
def test_reverse_rotate_slice_errors_more(method, args, kwargs):
    a = BitArray('0x123')
    with pytest.raises(ValueError):
        getattr(a, method)(*args, **kwargs)


@pytest.mark.parametrize("pos", [10, -11, [1, 2, 10]])
def test_invert_index_errors_more(pos):
    a = BitArray.from_zeros(10)
    with pytest.raises(IndexError):
        a.invert(pos)


@pytest.mark.parametrize("pos", [-9, 8])
def test_set_index_errors_more(pos):
    a = BitArray('0b01000000')
    with pytest.raises(IndexError):
        a.set(True, pos)


@pytest.mark.parametrize(
    ("method_name", "indices"),
    [
        ('all', [5]),
        ('all', [-5]),
        ('any', [5]),
        ('any', [-5]),
    ],
)
def test_all_any_index_errors_more(method_name, indices):
    a = BitArray('0xf')
    with pytest.raises(IndexError):
        getattr(a, method_name)(True, indices)


@pytest.mark.parametrize(
    ("read_fmt", "exception"),
    [
        ('ube', ValueError),
        ('ibe', ValueError),
        ('ule', ValueError),
        ('ile', ValueError),
        ('bool:0', ValueError),
        ('bool:2', ValueError),
        ('fle:2', bitstring.InterpretError),
    ],
)
def test_reader_format_error_cases_more(read_fmt, exception):
    with pytest.raises(exception):
        _ = Reader(BitArray('0xf')).read(read_fmt)


@pytest.mark.parametrize(
    ("data", "offset", "length", "expected"),
    [
        (b'\x00\xaa', 8, None, '0xaa'),
        (b'\x00\xaa', 4, None, '0x0aa'),
        (b'\xaa\xbb', 8, 4, '0xb'),
        (b'\x00\xaa', 8, 4, '0xa'),
    ],
)
def test_bytes_offset_creation_cases_more(data, offset, length, expected):
    kwargs = {'offset': offset}
    if length is not None:
        kwargs['length'] = length
    assert BitArray.from_bytes(data, **kwargs) == expected
