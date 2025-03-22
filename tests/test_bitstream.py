#!/usr/bin/env python

import pytest
import sys
sys.path.insert(0, '..')
import bitstring
import copy
import os
import collections
from bitstring import Bits, BitStream, ConstBitStream, pack, Dtype

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestFlexibleInitialisation:
    def test_flexible_initialisation(self):
        a = BitStream('uint:8=12')
        c = BitStream(' uint : 8 =  12')
        assert a == c == BitStream(uint=12, length=8)
        assert a.uint == 12
        a = BitStream('     int:2=  -1')
        b = BitStream('int :2   = -1')
        c = BitStream(' int:  2  =-1  ')
        assert a == b == c == BitStream(int=-1, length=2)

    def test_flexible_initialisation2(self):
        h = BitStream('hex=12')
        o = BitStream('oct=33')
        b = BitStream('bin=10')
        assert h == '0x12'
        assert o == '0o33'
        assert b == '0b10'

    def test_flexible_initialisation3(self):
        for s in ['se=-1', ' se = -1 ', 'se = -1']:
            a = BitStream(s)
            assert a.se == -1
        for s in ['ue=23', 'ue =23', 'ue = 23']:
            a = BitStream(s)
            assert a.ue == 23

    def test_multiple_string_initialisation(self):
        a = BitStream('0b1 , 0x1')
        assert a == '0b10001'
        a = BitStream('ue=5, ue=1, se=-2')
        assert a.read('ue') == 5
        assert a.read('ue') == 1
        assert a.read('se') == -2
        b = BitStream('uint:32 = 12, 0b11') + 'int:100=-100, 0o44'
        assert b.read(32).uint == 12
        assert b.read(2).bin == '11'
        assert b.read(100).int == -100


class TestReading:
    def test_read_bits(self):
        s = BitStream(bytes=b'\x4d\x55')
        assert s.read(4).hex == '4'
        assert s.read(8).hex == 'd5'
        assert s.read(1) == [0]
        assert s.read(3).bin == '101'
        assert not s.read(0)

    def test_read_byte(self):
        s = BitStream(hex='4d55')
        assert s.read(8).hex == '4d'
        assert s.read(8).hex == '55'

    def test_read_bytes(self):
        s = BitStream(hex='0x112233448811')
        assert s.read(3 * 8).hex == '112233'
        with pytest.raises(ValueError):
            s.read(-16)
        s.bitpos += 1
        assert s.read(2 * 8).bin == '1000100100010000'

    def test_read_ue(self):
        with pytest.raises(bitstring.InterpretError):
            _ = BitStream('').ue
        # The numbers 0 to 8 as unsigned Exponential-Golomb codes
        s = BitStream(bin='1 010 011 00100 00101 00110 00111 0001000 0001001')
        assert s.pos == 0
        for i in range(9):
            assert s.read('ue') == i
        with pytest.raises(bitstring.ReadError):
            s.read('ue')

    def test_read_se(self):
        s = BitStream(bin='010 00110 0001010 0001000 00111')
        assert s.read('se') == 1
        assert s.read('se') == 3
        assert s.readlist(3 * ['se']) == [5, 4, -3]


class TestFind:
    def test_find1(self):
        s = ConstBitStream(bin='0b0000110110000')
        assert s.find(BitStream(bin='11011'))
        assert s.bitpos == 4
        assert s.read(5).bin == '11011'
        s.bitpos = 0
        assert not s.find('0b11001', False)

    def test_find2(self):
        s = BitStream(bin='0')
        assert s.find(s, False)
        assert s.pos == 0
        assert not s.find('0b00', False)
        with pytest.raises(ValueError):
            s.find(BitStream())

    def test_find_with_offset(self):
        s = BitStream(hex='0x112233')[4:]
        assert s.find('0x23', False)
        assert s.pos == 8

    def test_find_corner_cases(self):
        s = BitStream(bin='000111000111')
        assert s.find('0b000')
        assert s.pos == 0
        assert s.find('0b000')
        assert s.pos == 0
        assert s.find('0b0111000111')
        assert s.pos == 2
        assert s.find('0b000', start=2)
        assert s.pos == 6
        assert s.find('0b111', start=6)
        assert s.pos == 9
        s.pos += 2
        assert s.find('0b1', start=s.pos)

    def test_find_bytes(self):
        s = BitStream.fromstring('0x010203040102ff')
        assert s.find('0x05', bytealigned=True) ==()
        assert s.find('0x02', bytealigned=True) == (8,)
        assert s.read(16).hex == '0203'
        assert s.find('0x02', start=s.bitpos, bytealigned=True) == (40,)
        s.read(1)
        assert not s.find('0x02', start=s.bitpos, bytealigned=True)

    def test_find_bytes_aligned_corner_cases(self):
        s = BitStream('0xff')
        assert s.find(s)
        assert not s.find(BitStream(hex='0x12'))
        assert not s.find(BitStream(hex='0xffff'))

    def test_find_bytes_bitpos(self):
        s = BitStream(hex='0x1122334455')
        s.pos = 2
        s.find('0x66', bytealigned=True)
        assert s.pos == 2
        s.pos = 38
        s.find('0x66', bytealigned=True)
        assert s.pos == 38

    def test_find_byte_aligned(self):
        s = BitStream(hex='0x12345678')
        assert s.find(BitStream(hex='0x56'), bytealigned=True)
        assert s.bytepos == 2
        s.pos = 0
        assert not s.find(BitStream(hex='0x45'), bytealigned=True)
        s = BitStream('0x1234')
        s.find('0x1234')
        assert s.find('0x1234')
        s += '0b111'
        s.pos = 3
        s.find('0b1', start=17, bytealigned=True)
        assert not s.find('0b1', start=17, bytealigned=True)
        assert s.pos == 3

    def test_find_byte_aligned_with_offset(self):
        s = BitStream(hex='0x112233')[4:]
        assert s.find(BitStream(hex='0x23'))

    def test_find_byte_aligned_errors(self):
        s = BitStream(hex='0xffff')
        with pytest.raises(ValueError):
            s.find('')
        with pytest.raises(ValueError):
            s.find(BitStream())


class TestRfind:
    def test_rfind(self):
        a = BitStream('0b001001001')
        b = a.rfind('0b001')
        assert b == (6,)
        assert a.pos == 6
        big = BitStream(length=100000) + '0x12' + BitStream(length=10000)
        found = big.rfind('0x12', bytealigned=True)
        assert found == (100000,)
        assert big.pos == 100000

    def test_rfind_byte_aligned(self):
        a = BitStream('0x8888')
        b = a.rfind('0b1', bytealigned=True)
        assert b == (8,)
        assert a.pos == 8

    def test_rfind_startbit(self):
        a = BitStream('0x0000ffffff')
        b = a.rfind('0x0000', start=1, bytealigned=True)
        assert b == ()
        assert a.pos == 0
        b = a.rfind('0x00', start=1, bytealigned=True)
        assert b == (8,)
        assert a.pos == 8

    def test_rfind_endbit(self):
        a = BitStream('0x000fff')
        b = a.rfind('0b011', start=0, end=14, bytealigned=False)
        assert bool(b) == True
        b = a.rfind('0b011', 0, 13, False)
        assert b == ()

    def test_rfind_errors(self):
        a = BitStream('0x43234234')
        with pytest.raises(ValueError):
            a.rfind('', bytealigned=True)
        with pytest.raises(ValueError):
            a.rfind('0b1', start=-99, bytealigned=True)
        with pytest.raises(ValueError):
            a.rfind('0b1', end=33, bytealigned=True)
        with pytest.raises(ValueError):
            a.rfind('0b1', start=10, end=9, bytealigned=True)


class TestShift:
    def test_shift_left(self):
        s = BitStream.fromstring('0b1010')
        t = s << 1
        assert s.bin == '1010'
        assert t.bin == '0100'
        s = t << 0
        assert s == '0b0100'
        t = s << 100
        assert t.bin == '0000'

    def test_shift_left_errors(self):
        s = BitStream()
        with pytest.raises(ValueError):
            s << 1
        s = BitStream('0xf')
        with pytest.raises(ValueError):
            s << -1

    def test_shift_right(self):
        s = BitStream('0b1010')
        t = s >> 1
        assert s.bin == '1010'
        assert t.bin == '0101'
        q = s >> 0
        assert q == '0b1010'
        q.replace('0b1010', '')
        t = s >> 100
        assert t.bin == '0000'

    def test_shift_right_errors(self):
        s = BitStream()
        with pytest.raises(ValueError):
            s >> 1
        s = BitStream('0xf')
        with pytest.raises(ValueError):
            s >> -1

    def test_shift_right_in_place(self):
        s = BitStream.fromstring('0xffff')[4:12]
        s >>= 1
        assert s == '0b01111111'
        s = BitStream('0b11011')
        s >>= 2
        assert s.bin == '00110'
        s >>= 100000000000000
        assert s.bin == '00000'
        s = BitStream('0xff')
        s >>= 1
        assert s == '0x7f'
        s >>= 0
        assert s == '0x7f'

    def test_shift_in_place_whole_bitstring(self):
        s = BitStream('0xabcd')
        s >>= len(s)
        assert s == '0x0000'

    def test_shift_right_in_place_errors(self):
        s = BitStream()
        with pytest.raises(ValueError):
            s >>= 1
        s += '0b11'
        with pytest.raises(ValueError):
            s >>= -1

    def test_shift_left_in_place(self):
        s = BitStream('0xffff')
        t = s[4:12]
        t <<= 2
        assert t == '0b11111100'
        s = BitStream('0b11011')
        s <<= 2
        assert s.bin == '01100'
        s <<= 100000000000000000000
        assert s.bin == '00000'
        s = BitStream('0xff')
        s <<= 1
        assert s == '0xfe'
        s <<= 0
        assert s == '0xfe'

    def test_shift_left_in_place_errors(self):
        s = BitStream()
        with pytest.raises(ValueError):
            s <<= 1
        s += '0b11'
        with pytest.raises(ValueError):
            s <<= -1


class TestReplace:
    def test_replace1(self):
        a = BitStream('0b1')
        n = a.replace('0b1', '0b0', bytealigned=True)
        assert a.bin == '0'
        assert n == 1
        n = a.replace('0b1', '0b0', bytealigned=True)
        assert n == 0

    def test_replace2(self):
        a = BitStream('0b00001111111')
        n = a.replace('0b1', '0b0', bytealigned=True)
        assert a.bin == '00001111011'
        assert n == 1
        n = a.replace('0b1', '0b0', bytealigned=False)
        assert a.bin == '00000000000'
        assert n == 6

    def test_replace3(self):
        a = BitStream('0b0')
        n = a.replace('0b0', '0b110011111', bytealigned=True)
        assert n == 1
        assert a.bin == '110011111'
        n = a.replace('0b11', '', bytealigned=False)
        assert n == 3
        assert a.bin == '001'

    def test_replace4(self):
        a = BitStream('0x00114723ef4732344700')
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

    def test_replace5(self):
        a = BitStream.fromstring('0xab')
        b = BitStream.fromstring('0xcd')
        c = BitStream.fromstring('0xabef')
        c.replace(a, b)
        assert c == '0xcdef'
        assert a == '0xab'
        assert b == '0xcd'
        a = BitStream('0x0011223344')
        a.pos = 12
        a.replace('0x11', '0xfff', bytealigned=True)
        assert a.pos == 0
        assert a == '0x00fff223344'

    def test_replace_with_self(self):
        a = BitStream('0b11')
        a.replace('0b1', a)
        assert a == '0xf'
        a.replace(a, a)
        assert a == '0xf'

    def test_replace_count(self):
        a = BitStream('0x223344223344223344')
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

    def test_replace_bitpos(self):
        a = BitStream('0xff')
        a.bitpos = 8
        a.replace('0xff', '', bytealigned=True)
        assert a.bitpos == 0
        a = BitStream('0b0011110001')
        a.bitpos = 4
        a.replace('0b1', '0b000')
        assert a.bitpos == 0
        a = BitStream('0b1')
        a.bitpos = 1
        a.replace('0b1', '0b11111', bytealigned=True)
        assert a.bitpos == 0
        a.replace('0b11', '0b0', False)
        assert a.bitpos == 0
        a.append('0b00')
        a.pos = 5
        a.replace('0b00', '0b11')
        assert a.bitpos == 5

    def test_replace_errors(self):
        a = BitStream('0o123415')
        with pytest.raises(ValueError):
            a.replace('', Bits(0o7), bytealigned=True)
        with pytest.raises(ValueError):
            a.replace('0b1', '0b1', start=-100, bytealigned=True)
        with pytest.raises(ValueError):
            a.replace('0b1', '0b1', end=19, bytealigned=True)


class TestSliceAssignment:
    def test_set_slice(self):
        a = BitStream()
        a[0:0] = '0xabcdef'
        assert a.bytepos == 0
        a[4:16] = ''
        assert a == '0xaef'
        assert a.bitpos == 0
        a.pos = 4
        a[8:] = '0x00'
        assert a == '0xae00'
        assert a.bitpos == 0
        a += '0xf'
        assert a.bitpos == 20
        a[8:] = '0xe'
        assert a == '0xaee'
        assert a.bitpos == 0
        b = BitStream()
        b[0:800] = '0xffee'
        assert b == '0xffee'
        b[4:48] = '0xeed123'
        assert b == '0xfeed123'
        b[-800:8] = '0x0000'
        assert b == '0x0000ed123'
        a = BitStream('0xabcde')
        assert a[-100:-90] == ''
        assert a[-100:-16] == '0xa'
        a[-100:-16] = '0x0'
        assert a == '0x0bcde'

    def test_inserting_using_set_item(self):
        a = BitStream()
        a[0:0] = '0xdeadbeef'
        assert a == '0xdeadbeef'
        assert a.bytepos == 0
        a[16:16] = '0xfeed'
        assert a == '0xdeadfeedbeef'
        assert a.bytepos == 0
        a[0:0] = '0xa'
        assert a == '0xadeadfeedbeef'
        assert a.bitpos == 0
        a.bytepos = 6
        a[0:8] = '0xff'
        assert a.bytepos == 6
        a[8:0] = '0x000'
        assert a.startswith('0xff000ead')

    def test_slice_assignment_bit_pos(self):
        a = BitStream('int:64=-1')
        a.pos = 64
        a[0:8] = ''
        assert a.pos == 0
        a.pos = 52
        a[-16:] = '0x0000'
        assert a.pos == 52



class TestPack:
    def test_pack1(self):
        s = bitstring.pack('uint:6, bin, hex, int:6, se, ue, oct', 10, '0b110', 'ff', -1, -6, 6, '54')
        t = BitStream('uint:6=10, 0b110, 0xff, int:6=-1, se=-6, ue=6, oct=54')
        assert s == t
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

    def test_pack_with_literals(self):
        s = bitstring.pack('0xf')
        assert s == '0xf'
        assert type(s), BitStream
        s = pack('0b1')
        assert s == '0b1'
        s = pack('0o7')
        assert s == '0o7'
        s = pack('int:10=-1')
        assert s == '0b1111111111'
        s = pack('uint:10=1')
        assert s == '0b0000000001'
        s = pack('ue=12')
        assert s.ue == 12
        s = pack('se=-12')
        assert s.se == -12
        s = pack('bin=01')
        assert s.bin == '01'
        s = pack('hex=01')
        assert s.hex == '01'
        s = pack('oct=01')
        assert s.oct == '01'

    def test_pack_with_dict(self):
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

    def test_pack_with_dict2(self):
        a = pack('int:5, bin:3=b, 0x3, bin=c, se=12', 10, b='0b111', c='0b1')
        b = BitStream('int:5=10, 0b111, 0x3, 0b1, se=12')
        assert a == b
        a = pack('bits:3=b', b=BitStream('0b101'))
        assert a == '0b101'
        a = pack('bits:24=b', b=BitStream('0x001122'))
        assert a == '0x001122'

    def test_pack_with_dict3(self):
        s = pack('hex:4=e, hex:4=0xe, hex:4=e', e='f')
        assert s == '0xfef'
        s = pack('sep', sep='0b00')
        assert s == '0b00'

    def test_pack_with_dict4(self):
        s = pack('hello', hello='0xf')
        assert s == '0xf'
        s = pack('x, y, x, y, x', x='0b10', y='uint:12=100')
        t = BitStream('0b10, uint:12=100, 0b10, uint:12=100, 0b10')
        assert s == t
        a = [1, 2, 3, 4, 5]
        s = pack('int:8, div,' * 5, *a, **{'div': '0b1'})
        t = BitStream('int:8=1, 0b1, int:8=2, 0b1, int:8=3, 0b1, int:8=4, 0b1, int:8=5, 0b1')
        assert s == t

    def test_pack_with_locals(self):
        width = 352
        height = 288
        s = pack('uint:12=width, uint:12=height', **locals())
        assert s == '0x160120'

    def test_pack_with_length_restriction(self):
        _ = pack('bin:3', '0b000')
        with pytest.raises(bitstring.CreationError):
            _ = pack('bin:3', '0b0011')
        with pytest.raises(bitstring.CreationError):
            _ = pack('bin:3', '0b11')
        with pytest.raises(bitstring.CreationError):
            _ = pack('bin:3=0b0011')
        with pytest.raises(bitstring.CreationError):
            _ = pack('bin:3=0b11')

        _ = pack('hex:4', '0xf')
        with pytest.raises(bitstring.CreationError):
            _ = pack('hex:4', '0b111')
        with pytest.raises(bitstring.CreationError):
            _ = pack('hex:4', '0b11111')
        with pytest.raises(bitstring.CreationError):
            _ = pack('hex:8=0xf')

        _ = pack('oct:6', '0o77')
        with pytest.raises(bitstring.CreationError):
            _ = pack('oct:6', '0o1')
        with pytest.raises(bitstring.CreationError):
            _ = pack('oct:6', '0o111')
        with pytest.raises(bitstring.CreationError):
            _ = pack('oct:3', '0b1')
        with pytest.raises(bitstring.CreationError):
            _ = pack('oct:3=hello', hello='0o12')

        _ = pack('bits:3', BitStream('0b111'))
        with pytest.raises(bitstring.CreationError):
            _ = pack('bits:3', BitStream('0b11'))
        with pytest.raises(bitstring.CreationError):
            _ = pack('bits:3', BitStream('0b1111'))
        with pytest.raises(bitstring.CreationError):
            _ = pack('bits:12=b', b=BitStream('0b11'))

    def test_pack_null(self):
        s = pack('')
        assert not s
        s = pack(',')
        assert not s
        s = pack(',,,,,0b1,,,,,,,,,,,,,0b1,,,,,,,,,,')
        assert s == '0b11'
        s = pack(',,uint:12,,bin:3,', 100, '100')
        a, b = s.unpack('uint:12,bin:3')
        assert a == 100
        assert b == '100'

    def test_pack_uint(self):
        s = pack('uint:10, uint:5', 1, 2)
        a, b = s.unpack('10, 5')
        assert (a.uint, b.uint) == (1, 2)
        s = pack('uint:10=150, uint:12=qee', qee=3)
        assert s == 'uint:10=150, uint:12=3'
        t = BitStream('uint:100=5')
        assert t == 'uint:100=5'

    def test_pack_defualt_uint_errors(self):
        with pytest.raises(bitstring.CreationError):
            _ = BitStream('5=-1')

    def test_packing_long_keyword_bitstring(self):
        s = pack('bits=b', b=BitStream(128000))
        assert s == BitStream(128000)

    def test_packing_with_list_format(self):
        f = ['bin', 'hex', 'uint:10']
        a = pack(','.join(f), '00', '234', 100)
        b = pack(f, '00', '234', 100)
        assert a == b


class TestUnpack:
    def test_unpack1(self):
        s = BitStream('uint:13=23, hex=e, bin=010, int:41=-554, 0o44332, se=-12, ue=4')
        s.pos = 11
        a, b, c, d, e, f, g = s.unpack('uint:13, hex:4, bin:3, int:41, oct:15, se, ue')
        assert a == 23
        assert b == 'e'
        assert c == '010'
        assert d == -554
        assert e == '44332'
        assert f == -12
        assert g == 4
        assert s.pos == 11

    def test_unpack2(self):
        s = BitStream('0xff, 0b000, uint:12=100')
        a, b, c = s.unpack('bits:8, bits, uint:12')
        assert type(s) == BitStream
        assert a == '0xff'
        assert type(s) == BitStream
        assert b == '0b000'
        assert c == 100
        a, b = s.unpack(['bits:11', 'uint'])
        assert a == '0xff, 0b000'
        assert b == 100


class TestFromFile:
    def test_creation_from_file_operations(self):
        filename = os.path.join(THIS_DIR, 'smalltestfile')
        s = BitStream(filename=filename)
        s.append('0xff')
        assert s.hex == '0123456789abcdefff'

        s = ConstBitStream(filename=filename)
        t = BitStream('0xff') + s
        assert t.hex == 'ff0123456789abcdef'

        s = BitStream(filename=filename)
        del s[:1]
        assert (BitStream('0b0') + s).hex == '0123456789abcdef'

        s = BitStream(filename=filename)
        del s[:7 * 8]
        assert s.hex == 'ef'

        s = BitStream(filename=filename)
        s.insert('0xc', 4)
        assert s.hex == '0c123456789abcdef'

        s = BitStream(filename=filename)
        s.prepend('0xf')
        assert s.hex == 'f0123456789abcdef'

        s = BitStream(filename=filename)
        s.overwrite('0xaaa', 12)
        assert s.hex == '012aaa6789abcdef'

        s = BitStream(filename=filename)
        s.reverse()
        assert s.hex == 'f7b3d591e6a2c480'

        s = BitStream(filename=filename)
        del s[-60:]
        assert s.hex == '0'

        s = BitStream(filename=filename)
        del s[:60]
        assert s.hex == 'f'

    def test_file_properties(self):
        s = ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        assert s.hex == '0123456789abcdef'
        assert s.uint == 81985529216486895
        assert s.int == 81985529216486895
        assert s.bin == '0000000100100011010001010110011110001001101010111100110111101111'
        assert s[:-1].oct == '002215053170465363367'
        s.bitpos = 0
        assert s.read('se') == -72
        s.bitpos = 0
        assert s.read('ue') == 144
        assert s.bytes == b'\x01\x23\x45\x67\x89\xab\xcd\xef'
        assert s.tobytes() == b'\x01\x23\x45\x67\x89\xab\xcd\xef'

    def test_creation_from_file_with_length(self):
        test_filename = os.path.join(THIS_DIR, 'test.m1v')
        s = ConstBitStream(filename=test_filename, length=32)
        assert s.length == 32
        assert s.hex == '000001b3'
        s = ConstBitStream(filename=test_filename, length=0)
        assert not s
        small_test_filename = os.path.join(THIS_DIR, 'smalltestfile')
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(filename=small_test_filename, length=65)
        with pytest.raises(bitstring.CreationError):
            _ = ConstBitStream(filename=small_test_filename, length=64, offset=1)
        with pytest.raises(bitstring.CreationError):
            _ = ConstBitStream(filename=small_test_filename, offset=65)
        with open(small_test_filename, 'rb') as f:
            with pytest.raises(bitstring.CreationError):
                _ = ConstBitStream(f, offset=65)
            with pytest.raises(bitstring.CreationError):
                _ = ConstBitStream(f, length=65)
            with pytest.raises(bitstring.CreationError):
                _ = ConstBitStream(f, offset=60, length=5)

    def test_creation_from_file_with_offset(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        a = BitStream(filename=filename, offset=4)
        assert a.peek(4 * 8).hex == '00001b31'
        b = BitStream(filename=filename, offset=28)
        assert b.peek(8).hex == '31'

    def test_file_slices(self):
        s = BitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        assert s[-16:].hex == 'cdef'

    def test_creataion_from_file_errors(self):
        with pytest.raises(IOError):
            _ = BitStream(filename='Idonotexist')

    def test_find_in_file(self):
        s = BitStream(filename=os.path.join(THIS_DIR, 'test.m1v'))
        assert s.find('0x160120')
        assert s.bytepos == 4
        s3 = s.read(24)
        assert s3.hex == '160120'
        s.bytepos = 0
        assert s._pos == 0
        assert s.find('0x0001b2')
        assert s.bytepos == 13

    def test_hex_from_file(self):
        s = BitStream(filename=os.path.join(THIS_DIR, 'test.m1v'))
        assert s[0:32].hex == '000001b3'
        assert s[-32:].hex == '000001b7'
        s.hex = '0x11'
        assert s.hex == '11'

    def test_file_operations(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        s1 = BitStream(filename=filename)
        s2 = BitStream(filename=filename)
        assert s1.read(32).hex == '000001b3'
        assert s2.read(32).hex == '000001b3'
        s1.bytepos += 4
        assert s1.read(8).hex == '02'
        assert s2.read(5 * 8).hex == '1601208302'
        s1.pos = s1.len
        with pytest.raises(ValueError):
            s1.pos += 1

    def test_file_bit_getting(self):
        s = ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'), offset=16, length=8)
        b = s[1]
        assert b
        b = s.any(0, [-1, -2, -3])
        assert b
        b = s.all(0, [0, 1, 2])
        assert not b


class TestCreationErrors:
    def test_incorrect_bin_assignment(self):
        s = BitStream()
        with pytest.raises(bitstring.CreationError):
            s._setbin_safe('0010020')

    def test_incorrect_hex_assignment(self):
        s = BitStream()
        with pytest.raises(bitstring.CreationError):
            s.hex = '0xabcdefg'


class TestLength:
    def test_length_zero(self):
        assert BitStream('').len == 0

    def test_length(self):
        assert BitStream('0x80').len == 8

    def test_offset_length_error(self):
        with pytest.raises(bitstring.CreationError):
            BitStream(hex='0xffff', offset=-1)


class TestSimpleConversions:
    def test_convert_to_uint(self):
        assert BitStream('0x10').uint == 16
        assert BitStream('0b000111').uint == 7

    def test_convert_to_int(self):
        assert BitStream('0x10').int == 16
        assert BitStream('0b11110').int == -2

    def test_convert_to_hex(self):
        assert BitStream(bytes=b'\x00\x12\x23\xff').hex == '001223ff'
        s = BitStream('0b11111')
        with pytest.raises(bitstring.InterpretError):
            _ = s.hex


class TestEmpty:
    def test_empty_bitstring(self):
        s = BitStream()
        with pytest.raises(bitstring.ReadError):
            s.read(1)
        assert s.bin == ''
        assert s.hex == ''
        with pytest.raises(bitstring.InterpretError):
            _ = s.int
        with pytest.raises(bitstring.InterpretError):
            _ = s.uint
        assert not s

    def test_non_empty_bit_stream(self):
        s = BitStream(bin='0')
        assert not not s.len


class TestPosition:
    def test_bit_position(self):
        s = BitStream(bytes=b'\x00\x00\x00')
        assert s.bitpos == 0
        s.read(5)
        assert s.pos == 5
        s.pos = s.len
        with pytest.raises(bitstring.ReadError):
            s.read(1)

    def test_byte_position(self):
        s = BitStream(bytes=b'\x00\x00\x00')
        assert s.bytepos == 0
        s.read(10)
        with pytest.raises(bitstring.ByteAlignError):
            _ = s.bytepos
        s.read(6)
        assert s.bytepos == 2

    def test_seek_to_bit(self):
        s = BitStream(bytes=b'\x00\x00\x00\x00\x00\x00')
        s.bitpos = 0
        assert s.bitpos == 0
        with pytest.raises(ValueError):
            s.pos = -1
        with pytest.raises(ValueError):
            s.bitpos = 6 * 8 + 1
        s.bitpos = 6 * 8
        assert s.bitpos == 6 * 8

    def test_seek_to_byte(self):
        s = BitStream(bytes=b'\x00\x00\x00\x00\x00\xab')
        s.bytepos = 5
        assert s.read(8).hex == 'ab'

    def test_advance_bits_and_bytes(self):
        s = BitStream(bytes=b'\x00\x00\x00\x00\x00\x00\x00\x00')
        s.pos += 5
        assert s.pos == 5
        s.bitpos += 16
        assert s.pos == 2 * 8 + 5
        s.pos -= 8
        assert s.pos == 8 + 5

    def test_retreat_bits_and_bytes(self):
        a = BitStream(length=100)
        a.pos = 80
        a.bytepos -= 5
        assert a.bytepos == 5
        a.pos -= 5
        assert a.pos == 35


class TestAppend:
    def test_append(self):
        s1 = BitStream('0b00000')
        s1.append(BitStream(bool=True))
        assert s1.bin == '000001'
        assert (BitStream('0x0102') + BitStream('0x0304')).hex == '01020304'

    def test_append_same_bitstring(self):
        s1 = BitStream('0xf0')[:6]
        s1.append(s1)
        assert s1.bin == '111100111100'

    def test_append_with_offset(self):
        s = BitStream(bytes=b'\x28\x28', offset=1)
        s.append('0b0')
        assert s.hex == '5050'


class TestByteAlign:
    def test_byte_align(self):
        s = BitStream(hex='0001ff23')
        s.bytealign()
        assert s.bytepos == 0
        s.pos += 11
        s.bytealign()
        assert s.bytepos == 2
        s.pos -= 10
        s.bytealign()
        assert s.bytepos == 1

    def test_insert_byte_aligned(self):
        s = BitStream('0x0011')
        s.insert(BitStream('0x22'), 8)
        assert s.hex == '002211'
        s = BitStream(0)
        s.insert(BitStream(bin='101'), 0)
        assert s.bin == '101'


class TestTruncate:
    def test_truncate_start(self):
        s = BitStream('0b1')
        del s[0]
        assert not s
        s = BitStream(hex='1234')
        assert s.hex == '1234'
        del s[:4]
        assert s.hex == '234'
        del s[:9]
        assert s.bin == '100'
        del s[:2]
        assert s.bin == '0'
        assert s.len == 1
        del s[:1]
        assert not s

    def test_truncate_end(self):
        s = BitStream('0b1')
        del s[-1:]
        assert not s
        s = BitStream(bytes=b'\x12\x34')
        assert s.hex == '1234'
        del s[-4:]
        assert s.hex == '123'
        del s[-9:]
        assert s.bin == '000'
        del s[-3:]
        assert not s
        s = BitStream('0b001')
        del s[:2]
        del s[-1:]
        assert not s


class TestSlice:
    def test_byte_aligned_slice(self):
        s = BitStream(hex='0x123456')
        assert s[8:16].hex == '34'
        s = s[8:24]
        assert s.len == 16
        assert s.hex == '3456'
        s = s[0:8]
        assert s.hex == '34'
        s.hex = '0x123456'
        assert s[8:24][0:8].hex == '34'

    def test_slice(self):
        s = BitStream(bin='000001111100000')
        s1 = s[0:5]
        s2 = s[5:10]
        s3 = s[10:15]
        assert s1.bin == '00000'
        assert s2.bin == '11111'
        assert s3.bin == '00000'


class TestInsert:
    def test_insert(self):
        s1 = BitStream(hex='0x123456')
        s2 = BitStream(hex='0xff')
        s1.bytepos = 1
        s1.insert(s2)
        assert s1.bytepos == 2
        assert s1.hex == '12ff3456'
        s1.insert('0xee', 24)
        assert s1.hex == '12ff34ee56'
        assert s1.bitpos == 32
        with pytest.raises(ValueError):
            s1.insert('0b1', -1000)
        with pytest.raises(ValueError):
            s1.insert('0b1', 1000)

    def test_insert_null(self):
        s = BitStream(hex='0x123')
        s.insert(BitStream(), 3)
        assert s.hex == '123'

    def test_insert_bits(self):
        one = BitStream(bin='1')
        zero = BitStream(bin='0')
        s = BitStream(bin='00')
        s.insert(one, 0)
        assert s.bin == '100'
        s.insert(zero, 0)
        assert s.bin == '0100'
        s.insert(one, s.len)
        assert s.bin == '01001'
        s.insert(s, 2)
        assert s.bin == '0101001001'


class TestResetting:
    def test_set_hex(self):
        s = BitStream()
        s.hex = '0'
        assert s.hex == '0'
        s.hex = '0x010203045'
        assert s.hex == '010203045'
        with pytest.raises(bitstring.CreationError):
            s.hex = '0x002g'

    def test_set_bin(self):
        s = BitStream(bin="000101101")
        assert s.bin == '000101101'
        assert s.len == 9
        s.bin = '0'
        assert s.bin == '0'
        assert s.len == 1

    def test_set_empty_bin(self):
        s = BitStream(hex='0x000001b3')
        s.bin = ''
        assert s.len == 0
        assert s.bin == ''

    def test_set_invalid_bin(self):
        s = BitStream()
        with pytest.raises(bitstring.CreationError):
            s.bin = '00102'


class TestOverwriting:
    def test_overwrite_bit(self):
        s = BitStream(bin='0')
        s.overwrite(BitStream(bin='1'), 0)
        assert s.bin == '1'

    def test_overwrite_limits(self):
        s = BitStream(bin='0b11111')
        s.overwrite(BitStream(bin='000'), 0)
        assert s.bin == '00011'
        s.overwrite('0b000', 2)
        assert s.bin == '00000'

    def test_overwrite_null(self):
        s = BitStream(hex='342563fedec')
        s2 = BitStream(s)
        s.overwrite(BitStream(bin=''), 23)
        assert s.bin == s2.bin

    def test_overwrite_position(self):
        s1 = BitStream(hex='0123456')
        s2 = BitStream(hex='ff')
        s1.bytepos = 1
        s1.overwrite(s2)
        assert (s1.hex, s1.bytepos) == ('01ff456', 2)
        s1.overwrite('0xff', 0)
        assert (s1.hex, s1.bytepos) == ('ffff456', 1)

    def test_overwrite_with_self(self):
        s = BitStream('0x123')
        s.overwrite(s)
        assert s == '0x123'


class TestSplit:
    def test_split_byte_aligned_corner_cases(self):
        s = BitStream()
        bsl = s.split(BitStream(hex='0xff'))
        assert next(bsl).hex == ''
        with pytest.raises(StopIteration):
            _ = next(bsl)
        s = BitStream(hex='aabbcceeddff')
        delimiter = BitStream()
        bsl = s.split(delimiter)
        with pytest.raises(ValueError):
            _ = next(bsl)
        delimiter = BitStream(hex='11')
        bsl = s.split(delimiter)
        assert next(bsl).hex == s.hex

    def test_split_byte_aligned(self):
        s = BitStream(hex='0x1234aa1234bbcc1234ffff')
        delimiter = BitStream(hex='1234')
        bsl = s.split(delimiter)
        assert [b.hex for b in bsl] == ['', '1234aa', '1234bbcc', '1234ffff']
        assert s.pos == 0

    def test_split_byte_aligned_with_intial_bytes(self):
        s = BitStream(hex='aa471234fedc43 47112233 47 4723 472314')
        delimiter = BitStream(hex='47')
        s.find(delimiter)
        assert s.bytepos == 1
        bsl = s.split(delimiter, start=0)
        assert [b.hex for b in bsl] == ['aa', '471234fedc43', '47112233',
                                                '47', '4723', '472314']
        assert s.bytepos == 1

    def test_split_byte_aligned_with_overlapping_delimiter(self):
        s = BitStream(hex='aaffaaffaaffaaffaaff')
        bsl = s.split(BitStream(hex='aaffaa'))
        assert [b.hex for b in bsl] == ['', 'aaffaaff', 'aaffaaffaaff']


class TestAdding:
    def test_adding(self):
        s1 = BitStream(hex='0x0102')
        s2 = BitStream(hex='0x0304')
        s3 = s1 + s2
        assert s1.hex == '0102'
        assert s2.hex == '0304'
        assert s3.hex == '01020304'
        s3 += s1
        assert s3.hex == '010203040102'
        assert s2[9:16].bin == '0000100'
        assert s1[0:9].bin == '000000010'
        s4 = BitStream(bin='000000010') + BitStream(bin='0000100')
        assert s4.bin == '0000000100000100'
        s5 = s1[0:9] + s2[9:16]
        assert s5.bin == '0000000100000100'

    def test_more_adding(self):
        s = BitStream(bin='00') + BitStream(bin='') + BitStream(bin='11')
        assert s.bin == '0011'
        s = '0b01'
        s += BitStream('0b11')
        assert s.bin == '0111'
        s = BitStream('0x00')
        t = BitStream('0x11')
        s += t
        assert s.hex == '0011'
        assert t.hex == '11'
        s += s
        assert s.hex == '00110011'

    def test_radd(self):
        s = '0xff' + BitStream('0xee')
        assert s.hex == 'ffee'

    def test_truncate_asserts(self):
        s = BitStream('0x001122')
        s.bytepos = 2
        del s[-s.len:]
        # self.assertEqual(s.bytepos, 0)
        s.append('0x00')
        s.append('0x1122')
        s.bytepos = 2
        del s[:s.len]
        # self.assertEqual(s.bytepos, 0)
        s.append('0x00')

    def test_overwrite_errors(self):
        s = BitStream(bin='11111')
        with pytest.raises(ValueError):
            s.overwrite(BitStream(bin='1'), -10)
        with pytest.raises(ValueError):
            s.overwrite(BitStream(bin='1'), 6)
        s.overwrite('bin=0', 5)
        assert s.b == '111110'
        s.overwrite(BitStream(hex='0x00'), 1)
        assert s.b == '100000000'

    def test_delete_bits(self):
        s = BitStream(bin='000111100000')
        s.bitpos = 4
        del s[4:8]
        assert s.bin == '00010000'
        del s[4:1004]
        assert s.bin, '0001'

    def test_delete_bits_with_position(self):
        s = BitStream(bin='000111100000')
        del s[4:8]
        assert s.bin == '00010000'

    def test_delete_bytes(self):
        s = BitStream('0x00112233')
        del s[8:8]
        assert s.hex == '00112233'
        assert s.pos == 0
        del s[8:16]
        assert s.hex == '002233'
        assert s.bytepos == 0
        del s[:24]
        assert not s
        assert s.pos == 0

    def test_get_item_with_positive_position(self):
        s = BitStream(bin='0b1011')
        assert s[0] == True
        assert s[1] == False
        assert s[2] == True
        assert s[3] == True
        with pytest.raises(IndexError):
            _ = s[4]

    def test_get_item_with_negative_position(self):
        s = BitStream(bin='1011')
        assert s[-1] == True
        assert s[-2] == True
        assert s[-3] == False
        assert s[-4] == True
        with pytest.raises(IndexError):
            _ = s[-5]

    def test_slicing(self):
        s = ConstBitStream(hex='0123456789')
        assert s[0:8].hex == '01'
        assert not s[0:0]
        assert not s[23:20]
        assert s[8:12].bin == '0010'
        assert s[32:80] == '0x89'

    def test_negative_slicing(self):
        s = ConstBitStream(hex='012345678')
        assert s[:-8].hex == '0123456'
        assert s[-16:-8].hex == '56'
        assert s[-24:].hex == '345678'
        assert s[-1000:-24] == '0x012'

    def test_len(self):
        s = BitStream()
        assert len(s) == 0
        s.append(BitStream(bin='001'))
        assert len(s) == 3

    def test_join(self):
        s1 = BitStream(bin='0')
        s2 = BitStream(bin='1')
        s3 = BitStream(bin='000')
        s4 = BitStream(bin='111')
        strings = [s1, s2, s1, s3, s4]
        s = BitStream().join(strings)
        assert s.bin == '010000111'

    def test_join2(self):
        s1 = BitStream(hex='00112233445566778899aabbccddeeff')
        s2 = BitStream(bin='0b000011')
        bsl = [s1[0:32], s1[4:12], s2, s2, s2, s2]
        s = ConstBitStream().join(bsl)
        assert s.hex == '00112233010c30c3'

        bsl = [BitStream(uint=j, length=12) for j in range(10) for _ in range(10)]
        s = BitStream().join(bsl)
        assert s.length == 1200

    def test_join_with_ints(self):
        with pytest.raises(TypeError):
            s = BitStream().join([1, 2])

    def test_pos(self):
        s = BitStream(bin='1')
        assert s.bitpos == 0
        s.read(1)
        assert s.bitpos == 1

    def test_writing_data(self):
        strings = [BitStream(bin=x) for x in ['0', '001', '0011010010', '010010', '1011']]
        s = BitStream().join(strings)
        s2 = BitStream(bytes=s.bytes)
        assert s2.bin == '000100110100100100101011'
        s2.append(BitStream(bin='1'))
        s3 = BitStream(bytes=s2.tobytes())
        assert s3.bin == '00010011010010010010101110000000'

    def test_writing_data_with_offsets(self):
        s1 = BitStream(bytes=b'\x10')
        s2 = BitStream(bytes=b'\x08\x00', length=8, offset=1)
        s3 = BitStream(bytes=b'\x04\x00', length=8, offset=2)
        assert s1 == s2
        assert s2 == s3
        assert s1.bytes == s2.bytes
        assert s2.bytes == s3.bytes

    def test_various_things1(self):
        hexes = ['12345678', '87654321', 'ffffffffff', 'ed', '12ec']
        bins = ['001010', '1101011', '0010000100101110110110', '11', '011']
        bsl = []
        for (hex_, bin_) in list(zip(hexes, bins)) * 5:
            bsl.append(BitStream(hex=hex_))
            bsl.append(BitStream(bin=bin_))
        s = BitStream().join(bsl)
        for (hex_, bin_) in list(zip(hexes, bins)) * 5:
            h = s.read(4 * len(hex_))
            b = s.read(len(bin_))
            assert h.hex == hex_
            assert b.bin == bin_

    def test_various_things2(self):
        s1 = BitStream(hex="0x1f08")[:13]
        assert s1.bin == '0001111100001'
        s2 = BitStream(bin='0101')
        assert s2.bin == '0101'
        s1.append(s2)
        assert s1.length == 17
        assert s1.bin == '00011111000010101'
        s1 = s1[3:8]
        assert s1.bin == '11111'

    def test_various_things3(self):
        s1 = BitStream(hex='0x012480ff')[2:27]
        s2 = s1 + s1
        assert s2.length == 50
        s3 = s2[0:25]
        s4 = s2[25:50]
        assert s3.bin == s4.bin

    def test_peek_bit(self):
        s = BitStream(bin='01')
        assert s.peek(1) == [0]
        assert s.peek(1) == [0]
        assert s.read(1) == [0]
        assert s.peek(1) == [1]
        assert s.peek(1) == [1]

        s = BitStream(bytes=b'\x1f', offset=3)
        assert s.len == 5
        assert s.peek(5).bin == '11111'
        assert s.peek(5).bin == '11111'
        s.pos += 1
        with pytest.raises(bitstring.ReadError):
            _ = s.peek(5)

        s = BitStream(hex='001122334455')
        assert s.peek(8).hex == '00'
        assert s.read(8).hex == '00'
        s.pos += 33
        with pytest.raises(bitstring.ReadError):
            _ = s.peek(8)

        s = BitStream(hex='001122334455')
        assert s.peek(8 * 2).hex == '0011'
        assert s.read(8 * 3).hex == '001122'
        assert s.peek(8 * 3).hex == '334455'
        with pytest.raises(bitstring.ReadError):
            _ = s.peek(25)

    def test_advance_bit(self):
        s = BitStream(hex='0xff')
        s.bitpos = 6
        s.pos += 1
        assert s.bitpos == 7
        s.bitpos += 1
        with pytest.raises(ValueError):
            s.pos += 1

    def test_advance_byte(self):
        s = BitStream(hex='0x010203')
        s.bytepos += 1
        assert s.bytepos == 1
        s.bytepos += 1
        assert s.bytepos == 2
        s.bytepos += 1
        with pytest.raises(ValueError):
            s.bytepos += 1

    def test_retreat_bit(self):
        s = BitStream(hex='0xff')
        with pytest.raises(ValueError):
            s.pos -= 1
        s.pos = 5
        s.pos -= 1
        assert s.pos == 4

    def test_retreat_byte(self):
        s = BitStream(hex='0x010203')
        with pytest.raises(ValueError):
            s.bytepos -= 1
        s.bytepos = 3
        s.bytepos -= 1
        assert s.bytepos == 2
        assert s.read(8).hex == '03'

    def test_creation_by_auto(self):
        s = BitStream('0xff')
        assert s.hex == 'ff'
        s = BitStream('0b00011')
        assert s.bin == '00011'
        with pytest.raises(bitstring.CreationError):
            _ = BitStream('hello')
        s1 = BitStream(bytes=b'\xf5', length=3, offset=5)
        with pytest.raises(TypeError):
            _ = BitStream(1.2)

    def test_creation_by_auto2(self):
        s = BitStream('bin=001')
        assert s.bin == '001'
        s = BitStream('oct=0o007')
        assert s.oct == '007'
        s = BitStream('hex=123abc')
        assert s == '0x123abc'

        s = BitStream('bin2=01')
        assert s == '0b01'
        for s in ['bin:1=01', 'bits:4=0b1', 'oct3=000', 'hex4=0x1234']:
            with pytest.raises(bitstring.CreationError):
                _ = BitStream(s)

    def test_insert_using_auto(self):
        s = BitStream('0xff')
        s.insert('0x00', 4)
        assert s.hex == 'f00f'
        with pytest.raises(ValueError):
            s.insert('ff')

    def test_overwrite_using_auto(self):
        s = BitStream('0x0110')
        s.overwrite('0b1')
        assert s.hex == '8110'
        s.overwrite('')
        assert s.hex == '8110'
        with pytest.raises(ValueError):
            s.overwrite('0bf')

    def test_find_using_auto(self):
        s = BitStream('0b000000010100011000')
        assert s.find('0b101')
        assert s.pos == 7

    def test_findbytealigned_using_auto(self):
        s = BitStream('0x00004700')
        assert s.find('0b01000111', bytealigned=True)
        assert s.bytepos == 2

    def test_append_using_auto(self):
        s = BitStream('0b000')
        s.append('0b111')
        assert s.bin == '000111'
        s.append('0b0')
        assert s.bin == '0001110'

    def test_split_byte_aligned_using_auto(self):
        s = BitStream('0x000143563200015533000123')
        sections = s.split('0x0001')
        assert next(sections).hex == ''
        assert next(sections).hex == '0001435632'
        assert next(sections).hex == '00015533'
        assert next(sections).hex == '000123'
        pytest.raises(StopIteration, next, sections)

    def test_split_byte_aligned_with_self(self):
        s = BitStream('0x1234')
        sections = s.split(s)
        assert next(sections).hex == ''
        assert next(sections).hex == '1234'
        with pytest.raises(StopIteration):
            next(sections)

    def test_prepend(self):
        s = BitStream('0b000')
        s.prepend('0b11')
        assert s.bin == '11000'
        s.prepend(s)
        assert s.bin == '1100011000'
        s.prepend('')
        assert s.bin == '1100011000'

    def test_null_slice(self):
        s = BitStream('0x111')
        t = s[1:1]
        assert len(t) == 0

    def test_multiple_autos(self):
        s = BitStream('0xa')
        s.prepend('0xf')
        s.append('0xb')
        assert s == '0xfab'
        s.prepend(s)
        s.append('0x100')
        s.overwrite('0x5', 4)
        assert s == '0xf5bfab100'

    def test_reverse(self):
        s = BitStream('0b0011')
        s.reverse()
        assert s.bin == '1100'
        s = BitStream('0b10')
        s.reverse()
        assert s.bin == '01'
        s = BitStream()
        s.reverse()
        assert s.bin == ''

    def test_init_with_concatenated_strings(self):
        s = BitStream('0xff 0Xee 0xd 0xcc')
        assert s.hex == 'ffeedcc'
        s = BitStream('0b0 0B111 0b001')
        assert s.bin == '0111001'
        s += '0b1' + '0B1'
        assert s.bin == '011100111'
        s = BitStream(hex='ff0xee')
        assert s.hex == 'ffee'
        s = BitStream(bin='000b0b11')
        assert s.bin == '0011'
        s = BitStream('  0o123 0O 7 0   o1')
        assert s.oct == '12371'
        s += '  0 o 332'
        assert s.oct == '12371332'

    def test_equals(self):
        s1 = BitStream('0b01010101')
        s2 = BitStream('0b01010101')
        assert s1 == s2
        s3 = BitStream()
        s4 = BitStream()
        assert s3 == s4
        assert not s3 != s4
        s5 = BitStream(bytes=b'\xff', offset=2, length=3)
        s6 = BitStream('0b111')
        assert s5 == s6

        class A(object):
            pass
        assert not s5 == A()

    def test_large_equals(self):
        s1 = BitStream(1000000)
        s2 = BitStream(1000000)
        s1.set(True, [-1, 55, 53214, 534211, 999999])
        s2.set(True, [-1, 55, 53214, 534211, 999999])
        assert s1 == s2
        s1.set(True, 800000)
        assert s1 != s2

    def test_not_equals(self):
        s1 = BitStream('0b0')
        s2 = BitStream('0b1')
        assert s1 != s2
        assert not s1 != BitStream('0b0')

    def test_equality_with_auto_initialised(self):
        a = BitStream('0b00110111')
        assert a == '0b00110111'
        assert a == '0x37'
        assert '0b0011 0111' == a
        assert '0x3 0x7' == a
        assert not a == '0b11001000'
        assert not '0x3737' == a

    def test_invert_special_method(self):
        s = BitStream('0b00011001')
        assert (~s).bin == '11100110'
        assert (~BitStream('0b0')).bin == '1'
        assert (~BitStream('0b1')).bin == '0'
        assert ~~s == s

    def test_invert_bit_position(self):
        s = ConstBitStream('0xefef')
        s.pos = 8
        t = ~s
        assert s.pos == 8
        assert t.pos == 0

    def test_invert_special_method_errors(self):
        s = BitStream()
        with pytest.raises(bitstring.Error):
            _ = ~s

    def test_join_with_auto(self):
        s = BitStream().join(['0xf', '0b00', BitStream(bin='11')])
        assert s == '0b11110011'

    def test_auto_bit_string_copy(self):
        s = BitStream('0xabcdef')
        t = BitStream(s)
        assert t.hex == 'abcdef'
        del s[-8:]
        assert t.hex == 'abcdef'


class TestMultiplication:

    def test_multiplication(self):
        a = BitStream('0xff')
        b = a * 8
        assert b == '0xffffffffffffffff'
        b = 4 * a
        assert b == '0xffffffff'
        assert 1 * a == a * 1 == a
        c = a * 0
        assert not c
        a *= 3
        assert a == '0xffffff'
        a *= 0
        assert not a
        one = BitStream('0b1')
        zero = BitStream('0b0')
        mix = one * 2 + 3 * zero + 2 * one * 2
        assert mix == '0b110001111'
        q = BitStream()
        q *= 143
        assert not q
        q += [True, True, False]
        assert q.bitpos == 3
        q *= 0
        assert not q
        assert q.bitpos == 0

    def test_multiplication_with_files(self):
        a = BitStream(filename=os.path.join(THIS_DIR, 'test.m1v'))
        b = a.len
        a *= 3
        assert a.len == 3 * b

    def test_multiplication_errors(self):
        a = BitStream('0b1')
        b = BitStream('0b0')
        with pytest.raises(ValueError):
            _ = a * -1
        with pytest.raises(ValueError):
            a *= -1
        with pytest.raises(ValueError):
            _ = -1 * a
        with pytest.raises(TypeError):
            _ = a * 1.2
        with pytest.raises(TypeError):
            _ = b * a
        with pytest.raises(TypeError):
            a *= b


class TestBitWise:

    def test_bitwise_and(self):
        a = BitStream('0b01101')
        b = BitStream('0b00110')
        assert (a & b).bin == '00100'
        assert (a & '0b11111') == a
        with pytest.raises(ValueError):
            _ = a & '0b1'
        with pytest.raises(ValueError):
            _ = b & '0b110111111'
        c = BitStream('0b0011011')
        c.pos = 4
        d = c & '0b1111000'
        assert d.pos == 0
        assert d.bin == '0011000'
        d = '0b1111000' & c
        assert d.bin == '0011000'

    def test_bitwise_or(self):
        a = BitStream('0b111001001')
        b = BitStream('0b011100011')
        c = a | b
        assert c.bin == '111101011'
        assert (a | '0b000000000') == a
        with pytest.raises(ValueError):
            _ = a | '0b0000'
        with pytest.raises(ValueError):
            _ = b | (a + '0b1')
        a = '0xff00' | BitStream('0x00f0')
        assert a.hex == 'fff0'

    def test_bitwise_xor(self):
        a = BitStream('0b111001001')
        b = BitStream('0b011100011')
        c = a ^ b
        assert c.bin == '100101010'
        assert (a ^ '0b111100000').bin == '000101001'
        with pytest.raises(ValueError):
            _ = a ^ '0b0000'
        with pytest.raises(ValueError):
            _ = b ^ (a + '0b1')
        a = '0o707' ^ BitStream('0o777')
        assert a.oct == '070'


class TestSplit2:

    def test_split(self):
        a = BitStream('0b0 010100111 010100 0101 010')
        a.pos = 20
        subs = [i.bin for i in a.split('0b010')]
        assert subs == ['0', '010100111', '010100', '0101', '010']
        assert a.pos == 20

    def test_split_corner_cases(self):
        a = BitStream('0b000000')
        bsl = a.split('0b1', False)
        assert next(bsl) == a
        with pytest.raises(StopIteration):
            next(bsl)
        b = BitStream()
        bsl = b.split('0b001', False)
        assert not next(bsl)
        with pytest.raises(StopIteration):
            _ = next(bsl)

    def test_split_errors(self):
        a = BitStream('0b0')
        b = a.split('', False)
        with pytest.raises(ValueError):
            _ = next(b)

    def test_slice_with_offset(self):
        a = BitStream(bytes=b'\x00\xff\x00', offset=7)
        b = a[7:12]
        assert b.bin == '11000'

    def test_split_with_maxsplit(self):
        a = BitStream('0xaabbccbbccddbbccddee')
        assert len(list(a.split('0xbb', bytealigned=True))) == 4
        bsl = list(a.split('0xbb', count=1, bytealigned=True))
        assert (len(bsl), bsl[0]) == (1, '0xaa')
        bsl = list(a.split('0xbb', count=2, bytealigned=True))
        assert len(bsl) == 2
        assert bsl[0] == '0xaa'
        assert bsl[1] == '0xbbcc'

    def test_split_more(self):
        s = BitStream('0b1100011001110110')
        for i in range(10):
            a = list(s.split('0b11', False, count=i))
            b = list(s.split('0b11', False))[:i]
            assert a == b
        b = s.split('0b11', count=-1)
        with pytest.raises(ValueError):
            _ = next(b)

    def test_split_startbit(self):
        a = BitStream('0b0010101001000000001111')
        bsl = a.split('0b001', bytealigned=False, start=1)
        assert [x.bin for x in bsl] == ['010101', '001000000', '001111']
        b = a.split('0b001', start=-100)
        with pytest.raises(ValueError):
            _ = next(b)
        b = a.split('0b001', start=23)
        with pytest.raises(ValueError):
            _ = next(b)
        b = a.split('0b1', start=10, end=9)
        with pytest.raises(ValueError):
            _ = next(b)

    def test_split_startbit_byte_aligned(self):
        a = BitStream('0x00ffffee')
        bsl = list(a.split('0b111', start=9, bytealigned=True))
        assert [x.bin for x in bsl] == ['1111111', '11111111', '11101110']

    def test_split_endbit(self):
        a = BitStream('0b000010001001011')
        bsl = list(a.split('0b1', bytealigned=False, end=14))
        assert [x.bin for x in bsl] == ['0000', '1000', '100', '10', '1']
        assert list(a[4:12].split('0b0', False)) == list(a.split('0b0', start=4, end=12))
        try:
            list(a.split('0xffee', end=15))
        except ValueError:
            pytest.fail("ValueError raised unexpectedly")
        # Whereas this one will when we call next()
        bsl = a.split('0xffee', end=16)
        with pytest.raises(ValueError):
            _ = next(bsl)

    def test_split_endbit_byte_aligned(self):
        a = BitStream('0xff00ff')[:22]
        bsl = list(a.split('0b 0000 0000 111', end=19))
        assert [x.bin for x in bsl] == ['11111111', '00000000111']
        bsl = list(a.split('0b 0000 0000 111', end=18))
        assert [x.bin for x in bsl] == ['111111110000000011']

    def test_split_max_split(self):
        a = BitStream('0b1' * 20)
        for i in range(10):
            bsl = list(a.split('0b1', count=i))
            assert len(bsl) == i

    #######################

    def test_explicit_auto(self):
        with pytest.raises(bitstring.CreationError):
            a = BitStream(auto='0x1')

    def test_position_in_slice(self):
        a = BitStream('0x00ffff00')
        a.bytepos = 2
        b = a[8:24]
        assert b.bytepos == 0

    def test_find_byte_aligned_with_bits(self):
        a = BitStream('0x00112233445566778899')
        a.find('0b0001', bytealigned=True)
        assert a.bitpos == 8

    def test_find_startbit_not_byte_aligned(self):
        a = BitStream('0b0010000100')
        found = a.find('0b1', start=4)
        assert (found, a.bitpos) == ((7,), 7)
        found = a.find('0b1', start=2)
        assert (found, a.bitpos) == ((2,), 2)
        found = a.find('0b1', bytealigned=False, start=8)
        assert (found, a.bitpos) == ((), 2)

    def test_find_endbit_not_byte_aligned(self):
        a = BitStream('0b0010010000')
        found = a.find('0b1', bytealigned=False, end=2)
        assert (found, a.bitpos) == ((), 0)
        found = a.find('0b1', end=3)
        assert (found, a.bitpos) == ((2,), 2)
        found = a.find('0b1', bytealigned=False, start=3, end=5)
        assert (found, a.bitpos) == ((), 2)
        found = a.find('0b1', start=3, end=6)
        assert (found[0], a.bitpos) == (5, 5)

    def test_find_startbit_byte_aligned(self):
        a = BitStream('0xff001122ff0011ff')
        a.pos = 40
        found = a.find('0x22', start=23, bytealigned=True)
        assert (found, a.bytepos) == ((24,), 3)
        a.bytepos = 4
        found = a.find('0x22', start=24, bytealigned=True)
        assert (found, a.bytepos) == ((24,), 3)
        found = a.find('0x22', start=25, bytealigned=True)
        assert (found, a.pos) == ((), 24)
        found = a.find('0b111', start=40, bytealigned=True)
        assert (found, a.pos) == ((56,), 56)

    def test_find_endbit_byte_aligned(self):
        a = BitStream('0xff001122ff0011ff')
        found = a.find('0x22', end=31, bytealigned=True)
        assert not found
        assert a.pos == 0
        found = a.find('0x22', end=32, bytealigned=True)
        assert found
        assert a.pos == 24
        assert found[0] == 24

    def test_find_start_endbit_errors(self):
        a = BitStream('0b00100')
        with pytest.raises(ValueError):
            _ = a.find('0b1', bytealigned=False, start=-100)
        with pytest.raises(ValueError):
            _ = a.find('0b1', end=6)
        with pytest.raises(ValueError):
            _ = a.find('0b1', start=4, end=3)
        b = BitStream('0x0011223344')
        with pytest.raises(ValueError):
            _ = b.find('0x22', bytealigned=True, start=-100)
        with pytest.raises(ValueError):
            _ = b.find('0x22', end=41, bytealigned=True)

    def test_prepend_and_append_again(self):
        c = BitStream('0x1122334455667788')
        c.bitpos = 40
        c.append('0b1')
        assert c.bitpos == len(c)
        c = BitStream()
        c.prepend('0x1234')
        assert c.bytepos == 0
        c = BitStream()
        c.append('0x1234')
        assert c.bytepos == 2
        s = BitStream(bytes=b'\xff\xff', offset=2)
        assert s.length == 14
        t = BitStream(bytes=b'\x80', offset=1, length=2)
        s.prepend(t)
        assert s == '0x3fff'

    def test_find_all(self):
        a = BitStream('0b11111')
        p = a.findall('0b1')
        assert list(p) == [0, 1, 2, 3, 4]
        p = a.findall('0b11')
        assert list(p) == [0, 1, 2, 3]
        p = a.findall('0b10')
        assert list(p) == []
        a = BitStream('0x4733eeff66554747335832434547')
        p = a.findall('0x47', bytealigned=True)
        assert list(p) == [0, 6 * 8, 7 * 8, 13 * 8]
        p = a.findall('0x4733', bytealigned=True)
        assert list(p) == [0, 7 * 8]
        a = BitStream('0b1001001001001001001')
        p = a.findall('0b1001', bytealigned=False)
        assert list(p) == [0, 3, 6, 9, 12, 15]
        assert a.pos == 0

    def test_find_all_generator(self):
        a = BitStream('0xff1234512345ff1234ff12ff')
        p = a.findall('0xff', bytealigned=True)
        assert next(p) == 0
        assert next(p) == 6 * 8
        assert next(p) == 9 * 8
        assert next(p) == 11 * 8
        with pytest.raises(StopIteration):
            _ = next(p)

    def test_find_all_count(self):
        s = BitStream('0b1') * 100
        for i in [0, 1, 23]:
            assert len(list(s.findall('0b1', count=i))) == i
        with pytest.raises(ValueError):
            _ = s.findall('0b1', bytealigned=True, count=-1)

    def test_contains(self):
        a = BitStream('0b1') + '0x0001dead0001'
        assert '0xdead' in a
        assert a.pos == 0
        assert not '0xfeed' in a

    def test_repr(self):
        max_ = bitstring.bits.MAX_CHARS
        bls = ['', '0b1', '0o5', '0x43412424f41', '0b00101001010101']
        for bs in bls:
            a = BitStream(bs)
            b = eval(a.__repr__())
            assert a == b
        filename = os.path.join(THIS_DIR, 'test.m1v')
        for f in [ConstBitStream(filename=filename),
                  ConstBitStream(filename=filename, length=17),
                  ConstBitStream(filename=filename, length=23, offset=23102)]:
            f2 = eval(f.__repr__())
            assert f2.tobytes() == f.tobytes()
        a = BitStream('0b1')
        assert repr(a) == "BitStream('0b1')"
        a += '0b11'
        a.pos = 2
        assert repr(a) == "BitStream('0b111', pos=2)"
        a.pos = 0
        a += '0b1'
        assert repr(a) == "BitStream('0xf', pos=4)"
        a.pos = 0
        a *= max_
        assert repr(a) == "BitStream('0x" + "f" * max_ + "')"
        a += '0xf'
        assert repr(a) == "BitStream('0x" + "f" * max_ + "...', pos=1004)  # length=%d" % (max_ * 4 + 4)

    def test_print(self):
        s = BitStream(hex='0x00')
        assert '0x' + s.hex == s.__str__()
        s = BitStream(filename=os.path.join(THIS_DIR, 'test.m1v'))
        assert '0x' + s[0: bitstring.bits.MAX_CHARS * 4].hex + '...' == s.__str__()
        assert BitStream().__str__() == ''
        s = BitStream('0b11010')
        assert '0b' + s.bin == s.__str__()
        s = BitStream('0x12345678901234567890,0b1')
        assert '0x12345678901234567890, 0b1' == s.__str__()

    def test_iter(self):
        a = BitStream('0b001010')
        b = BitStream()
        for bit in a:
            b.append(ConstBitStream(bool=bit))
        assert a == b

    def test_delitem(self):
        a = BitStream('0xffee')
        del a[0:8]
        assert a.hex == 'ee'
        del a[0:8]
        assert not a
        del a[10:12]
        assert not a

    def test_non_zero_bits_at_start(self):
        a = BitStream(bytes=b'\xff', offset=2)
        b = BitStream('0b00')
        b += a
        assert b == '0b0011 1111'
        assert a.tobytes() == b'\xfc'

    def test_non_zero_bits_at_end(self):
        a = BitStream(bytes=b'\xff', length=5)
        b = BitStream('0b00')
        a += b
        assert a == '0b1111100'
        assert a.tobytes() == b'\xf8'
        with pytest.raises(ValueError):
            _ = a.bytes

    def test_new_offset_errors(self):
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(hex='ff', offset=-1)
        with pytest.raises(bitstring.CreationError):
            _ = BitStream('0xffffffff', offset=33)

    def test_slice_step(self):
        a = BitStream('0x3')
        b = a[::1]
        assert a == b
        assert a[2:4:1] == '0b11'
        assert a[0:2:1] == '0b00'
        assert a[:3] == '0o1'

        a = BitStream('0x0011223344556677')
        assert a[-8:] == '0x77'
        assert a[:-24] == '0x0011223344'
        assert a[-1000:-24] == '0x0011223344'

    def test_interesting_slice_step(self):
        a = BitStream('0b0011000111')
        assert a[7:3:-1] == '0b1000'
        assert a[9:2:-1] == '0b1110001'
        assert a[8:2:-2] == '0b100'
        assert a[100:-20:-3] == '0b1010'
        assert a[100:-20:-1] == '0b1110001100'
        assert a[10:2:-1] == '0b1110001'
        assert a[100:2:-1] == '0b1110001'

    def test_insertion_order_and_bitpos(self):
        b = BitStream()
        b[0:0] = '0b0'
        b[0:0] = '0b1'
        assert b == '0b10'
        assert b.bitpos == 0
        a = BitStream()
        a.insert('0b0')
        a.insert('0b1')
        assert a == '0b01'
        assert a.bitpos == 2

    def test_overwrite_order_and_bitpos(self):
        a = BitStream('0xff')
        a.overwrite('0xa')
        assert a == '0xaf'
        assert a.bitpos == 4
        a.overwrite('0xb')
        assert a == '0xab'
        assert a.bitpos == 8
        a.overwrite('0xa', 4)
        assert a == '0xaa'
        assert a.bitpos == 8
        a.overwrite(a, 0)
        assert a == '0xaa'

    def test_init_slice_with_int(self):
        a = BitStream(length=8)
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

    def test_init_slice_with_int_errors(self):
        a = BitStream('0b0000')
        with pytest.raises(ValueError):
            a[0:4] = 16
        with pytest.raises(ValueError):
            a[0:4] = -9
        with pytest.raises(ValueError):
            a[0] = 2
        with pytest.raises(ValueError):
            a[0] = -2

    def test_reverse_with_slice(self):
        a = BitStream('0x0012ff')
        a.reverse()
        assert a == '0xff4800'
        a.reverse(8, 16)
        assert a == '0xff1200'
        b = a[8:16]
        b.reverse()
        a[8:16] = b
        assert a == '0xff4800'

    def test_reverse_with_slice_errors(self):
        a = BitStream('0x123')
        with pytest.raises(ValueError):
            a.reverse(-1, 4)
        with pytest.raises(ValueError):
            a.reverse(10, 9)
        with pytest.raises(ValueError):
            a.reverse(1, 10000)

    def test_initialise_from_list(self):
        a = BitStream([])
        assert not a
        a = BitStream([True, False, [], [0], 'hello'])
        assert a == '0b10011'
        a += []
        assert a == '0b10011'
        a += [True, False, True]
        assert a == '0b10011101'
        a.find([12, 23])
        assert a.pos == 3
        assert [1, 0, False, True] == BitStream('0b1001')
        a = [True] + BitStream('0b1')
        assert a == '0b11'

    def test_initialise_from_tuple(self):
        a = BitStream(())
        assert not a
        a = BitStream((0, 1, '0', '1'))
        assert '0b0111' == a
        a.replace((True, True), [])
        assert a == (False, True)

    def test_cut(self):
        a = BitStream('0x00112233445')
        b = list(a.cut(8))
        assert b == ['0x00', '0x11', '0x22', '0x33', '0x44', '0x5']
        b = list(a.cut(4, 8, 16))
        assert b == ['0x1', '0x1']
        b = list(a.cut(4, 0, 44, 4))
        assert b == ['0x0', '0x0', '0x1', '0x1']
        a = BitStream()
        b = list(a.cut(10))
        assert not b

    def test_cut_errors(self):
        a = BitStream('0b1')
        b = a.cut(1, 1, 2)
        with pytest.raises(ValueError):
            _ = next(b)
        b = a.cut(1, -2, 1)
        with pytest.raises(ValueError):
            _ = next(b)
        b = a.cut(0)
        with pytest.raises(ValueError):
            _ = next(b)
        b = a.cut(1, count=-1)
        with pytest.raises(ValueError):
            _ = next(b)

    def test_cut_problem(self):
        s = BitStream('0x1234')
        for n in list(s.cut(4)):
            s.prepend(n)
        assert s == '0x43211234'

    def test_join_functions(self):
        a = BitStream().join(['0xa', '0xb', '0b1111'])
        assert a == '0xabf'
        a = BitStream('0b1').join(['0b0' for _ in range(10)])
        assert a == '0b0101010101010101010'
        a = BitStream('0xff').join([])
        assert not a
        a = BitStream('0xff').join([Bits(5), '0xab', '0xabc'])
        assert a == '0b00000, 0xffabffabc'

    def test_adding_bitpos(self):
        a = BitStream('0xff')
        b = BitStream('0x00')
        a.bitpos = b.bitpos = 8
        c = a + b
        assert c.bitpos == 0

    def test_intelligent_read1(self):
        a = BitStream(uint=123, length=23)
        u = a.read('uint:23')
        assert u == 123
        assert a.pos == a.len
        b = BitStream(int=-12, length=44)
        i = b.read('int:44')
        assert i == -12
        assert b.pos == b.len
        u2, i2 = (a + b).readlist('uint:23, int:44')
        assert (u2, i2) == (123, -12)

    def test_intelligent_read2(self):
        a = BitStream(ue=822)
        u = a.read('ue')
        assert u == 822
        assert a.pos == a.len
        b = BitStream(se=-1001)
        s = b.read('se')
        assert s == -1001
        assert b.pos == b.len
        s, u1, u2 = (b + 2 * a).readlist('se, ue, ue')
        assert (s, u1, u2) == (-1001, 822, 822)

    def test_intelligent_read3(self):
        a = BitStream('0x123') + '0b11101'
        h = a.read('hex:12')
        assert h == '123'
        b = a.read(' bin : 5 ')
        assert b == '11101'
        c = '0b' + b + a
        b, h = c.readlist('bin:5, hex:12')
        assert (b, h) == ('11101', '123')

    def test_intelligent_read4(self):
        a = BitStream('0o007')
        o = a.read('oct:9')
        assert o == '007'
        assert a.pos == a.len

    def test_intelligent_read5(self):
        a = BitStream('0x00112233')
        c0, c1, c2 = a.readlist('bits:8, bits:8, bits:16')
        assert (c0, c1, c2) == (BitStream('0x00'), BitStream('0x11'), BitStream('0x2233'))
        a.pos = 0
        c = a.read('bits:16')
        assert c == BitStream('0x0011')

    def test_intelligent_read6(self):
        a = BitStream('0b000111000')
        b1, b2, b3 = a.readlist('bin :3, int: 3, int:3')
        assert b1 == '000'
        assert b2 == -1
        assert b3 == 0

    def test_intelligent_read7(self):
        a = BitStream('0x1234')
        a1, a2, a3, a4 = a.readlist('bin:0, oct:0, hex:0, bits:0')
        assert a1 == a2 == a3 == ''
        assert not a4
        with pytest.raises(ValueError):
            _ = a.read('int:0')
        with pytest.raises(ValueError):
            _ = a.read('uint:0')
        assert a.pos == 0

    def test_intelligent_read8(self):
        a = BitStream('0x123456')
        for t in ['hex:1', 'oct:1', '-5', 'fred', 'bin:-2',
                  'uint:p', 'uint:-2', 'int:u', 'int:-3', 'ses', 'uee', '-14']:
            with pytest.raises(ValueError):
                _ = a.read(t)

    def test_intelligent_read9(self):
        a = BitStream('0xff')
        assert a.read('intle8') == -1

    def test_intelligent_peek(self):
        a = BitStream('0b01, 0x43, 0o4, uint:23=2, se=5, ue=3')
        b, c, e = a.peeklist('bin:2, hex:8, oct:3')
        assert (b, c, e) == ('01', '43', '4')
        assert a.pos == 0
        a.pos = 13
        f, g, h = a.peeklist('uint:23, se, ue')
        assert (f, g, h) == (2, 5, 3)
        assert a.pos == 13

    def test_read_multiple_bits(self):
        s = BitStream('0x123456789abcdef')
        a, b = s.readlist([4, 4])
        assert a == '0x1'
        assert b == '0x2'
        c, d, e = s.readlist([8, 16, 8])
        assert c == '0x34'
        assert d == '0x5678'
        assert e == '0x9a'

    def test_peek_multiple_bits(self):
        s = BitStream('0b1101, 0o721, 0x2234567')
        a, b, c, d = s.peeklist([2, 1, 1, 9])
        assert a == '0b11'
        assert bool(b) == True
        assert bool(c) == True
        assert d == '0o721'
        assert s.pos == 0
        a, b = s.peeklist([4, 9])
        assert a == '0b1101'
        assert b == '0o721'
        s.pos = 13
        a, b = s.peeklist([16, 8])
        assert a == '0x2234'
        assert b == '0x56'
        assert s.pos == 13

    def test_difficult_prepends(self):
        a = BitStream('0b1101011')
        b = BitStream()
        for i in range(10):
            b.prepend(a)
        assert b == a * 10

    def test_packing_wrong_number_of_things(self):
        with pytest.raises(bitstring.CreationError):
            _ = pack('bin:1')
        with pytest.raises(bitstring.CreationError):
            _ = pack('', 100)

    def test_pack_with_various_keys(self):
        a = pack('uint10', uint10='0b1')
        assert a == '0b1'
        b = pack('0b110', **{'0b110': '0xfff'})
        assert b == '0xfff'

    def test_pack_with_variable_length(self):
        for i in range(1, 11):
            a = pack('uint:n', 0, n=i)
            assert a.bin == '0' * i

    def test_to_bytes(self):
        a = BitStream(bytes=b'\xab\x00')
        b = a.tobytes()
        assert a.bytes == b
        for i in range(7):
            del a[-1:]
            assert a.tobytes() == b'\xab\x00'
        del a[-1:]
        assert a.tobytes() == b'\xab'

    def test_to_file(self):
        filename = os.path.join(THIS_DIR, 'temp_bitstring_unit_testing_file')
        a = BitStream('0x0000ff')[:17]
        with open(filename, 'wb') as f:
            a.tofile(f)
        b = BitStream(filename=filename)
        assert b == '0x000080'

        a = BitStream('int:1000000=-1')
        assert a.int == -1
        with open(filename, 'wb') as f:
            a.tofile(f)
        b = BitStream(filename=filename)
        assert b.int == -1
        assert b.len == 1000000

    def test_token_parser(self):
        tp = bitstring.utils.tokenparser
        assert tp('hex') == (True, [('hex', None, None)])
        assert tp('hex=14') == (True, [('hex', None, '14')])
        assert tp('0xef') == (False, [('0x', None, 'ef')])
        assert tp('uint:12') == (False, [('uint', 12, None)])
        assert tp('int:30=-1') == (False, [('int', 30, '-1')])
        assert tp('bits10') == (False, [('bits', 10, None)])
        assert tp('bits:10') == (False, [('bits', 10, None)])
        assert tp('123') == (False, [('bits', 123, None)])
        assert tp('123') == (False, [('bits', 123, None)])
        assert tp('hex12', ('hex12',)) == (False, [('hex12', None, None)])
        assert tp('2*bits:6') == (False, [('bits', 6, None), ('bits', 6, None)])

    def test_token_parser_struct_codes(self):
        tp = bitstring.utils.tokenparser
        assert tp('>H') == (False, [('uintbe', 16, None)])
        assert tp('<H') == (False, [('uintle', 16, None)])
        assert tp('=H') == (False, [('uintne', 16, None)])
        assert tp('@H') == (False, [('uintne', 16, None)])
        assert tp('>b') == (False, [('int', 8, None)])
        assert tp('<b') == (False, [('int', 8, None)])

    def test_auto_from_file_object(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        with open(filename, 'rb') as f:
            s = ConstBitStream(f, offset=32, length=12)
            assert s.uint == 352
            t = ConstBitStream('0xf') + f
            assert t.startswith('0xf000001b3160')
            s2 = ConstBitStream(f)
            t2 = BitStream('0xc')
            t2.prepend(s2)
            assert t2.startswith('0x000001b3')
            assert t2.endswith('0xc')
            with open(filename, 'rb') as b:
                u = BitStream(bytes=b.read())
                assert u == s2

    def test_file_based_copy(self):
        with open(os.path.join(THIS_DIR, 'smalltestfile'), 'rb') as f:
            s = BitStream(f)
            t = BitStream(s)
            s.prepend('0b1')
            assert s[1:] == t
            s = BitStream(f)
            t = copy.copy(s)
            t.append('0b1')
            assert s == t[:-1]

    def test_big_endian_synonyms(self):
        s = BitStream('0x12318276ef')
        assert s.int == s.intbe
        assert s.uint == s.uintbe
        s = BitStream(intbe=-100, length=16)
        assert s == 'int:16=-100'
        s = BitStream(uintbe=13, length=24)
        assert s == 'int:24=13'
        s = BitStream('uintbe:32=1000')
        assert s == 'uint:32=1000'
        s = BitStream('intbe:8=2')
        assert s == 'int:8=2'
        assert s.read('intbe8') == 2
        s.pos = 0
        assert s.read('uintbe8') == 2

    def test_big_endian_synonym_errors(self):
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(uintbe=100, length=15)
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(intbe=100, length=15)
        with pytest.raises(bitstring.CreationError):
            _ = BitStream('uintbe:17=100')
        with pytest.raises(bitstring.CreationError):
            _ = BitStream('intbe:7=2')
        s = BitStream('0b1')
        with pytest.raises(bitstring.InterpretError):
            _ = s.intbe
        with pytest.raises(bitstring.InterpretError):
            _ = s.uintbe
        with pytest.raises(ValueError):
            _ = s.read('uintbe')
        with pytest.raises(ValueError):
            _ = s.read('intbe')

    def test_little_endian_uint(self):
        s = BitStream(uint=100, length=16)
        assert s.uintle == 25600
        s = BitStream(uintle=100, length=16)
        assert s.uint == 25600
        assert s.uintle == 100
        s.uintle += 5
        assert s.uintle == 105
        s = BitStream('uintle:32=999')
        assert s.uintle == 999
        s.byteswap()
        assert s.uint == 999
        s = pack('uintle:24', 1001)
        assert s.uintle == 1001
        assert s.length == 24
        assert s.read('uintle24') == 1001

    def test_little_endian_int(self):
        s = BitStream(int=100, length=16)
        assert s.intle == 25600
        s = BitStream(intle=100, length=16)
        assert s.int == 25600
        assert s.intle == 100
        s.intle = 105
        assert s.intle == 105
        s = BitStream('intle:32=999')
        assert s.intle == 999
        s.byteswap()
        assert s.int == 999
        s = pack('intle:24', 1001)
        assert s.intle == 1001
        assert s.length == 24
        assert s.read('intle24') == 1001

    def test_little_endian_errors(self):
        with pytest.raises(bitstring.CreationError):
            _ = BitStream('uintle:15=10')
        with pytest.raises(bitstring.CreationError):
            _ = BitStream('intle:31=-999')
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(uintle=100, length=15)
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(intle=100, length=15)
        s = BitStream('0xfff')
        with pytest.raises(bitstring.InterpretError):
            _ = s.intle
        with pytest.raises(bitstring.InterpretError):
            _ = s.uintle
        with pytest.raises(ValueError):
            _ = s.read('uintle')
        with pytest.raises(ValueError):
            _ = s.read('intle')

    def test_struct_tokens1(self):
        assert pack('<b', 23) == BitStream('intle:8=23')
        assert pack('<B', 23) == BitStream('uintle:8=23')
        assert pack('<h', 23) == BitStream('intle:16=23')
        assert pack('<H', 23) == BitStream('uintle:16=23')
        assert pack('<l', 23) == BitStream('intle:32=23')
        assert pack('<L', 23) == BitStream('uintle:32=23')
        assert pack('<i', 23) == BitStream('intle:32=23')
        assert pack('<I', 23) == BitStream('uintle:32=23')
        assert pack('<q', 23) == BitStream('intle:64=23')
        assert pack('<Q', 23) == BitStream('uintle:64=23')
        assert pack('>b', 23) == BitStream('intbe:8=23')
        assert pack('>B', 23) == BitStream('uintbe:8=23')
        assert pack('>h', 23) == BitStream('intbe:16=23')
        assert pack('>H', 23) == BitStream('uintbe:16=23')
        assert pack('>l', 23) == BitStream('intbe:32=23')
        assert pack('>L', 23) == BitStream('uintbe:32=23')
        assert pack('>i', 23) == BitStream('intbe:32=23')
        assert pack('>I', 23) == BitStream('uintbe:32=23')
        assert pack('>q', 23) == BitStream('intbe:64=23')
        assert pack('>Q', 23) == BitStream('uintbe:64=23')
        with pytest.raises(bitstring.CreationError):
            _ = pack('<B', -1)
        with pytest.raises(bitstring.CreationError):
            _ = pack('<H', -1)
        with pytest.raises(bitstring.CreationError):
            _ = pack('<L', -1)
        with pytest.raises(bitstring.CreationError):
            _ = pack('<Q', -1)

    def test_struct_tokens2(self):
        # I couldn't find a way to test both types of native endianness
        # on a single machine, so only one set of tests will run.
        if sys.byteorder == 'little':
            assert pack('=b', 23) == BitStream('intle:8=23')
            assert pack('=B', 23) == BitStream('uintle:8=23')
            assert pack('=h', 23) == BitStream('intle:16=23')
            assert pack('=H', 23) == BitStream('uintle:16=23')
            assert pack('@l', 23) == BitStream('intle:32=23')
            assert pack('@L', 23) == BitStream('uintle:32=23')
            assert pack('@i', 23) == BitStream('intle:32=23')
            assert pack('@I', 23) == BitStream('uintle:32=23')
            assert pack('@q', 23) == BitStream('intle:64=23')
            assert pack('@Q', 23) == BitStream('uintle:64=23')
        else:
            assert pack('@b', 23) == BitStream('intbe:8=23')
            assert pack('@B', 23) == BitStream('uintbe:8=23')
            assert pack('@h', 23) == BitStream('intbe:16=23')
            assert pack('@H', 23) == BitStream('uintbe:16=23')
            assert pack('@l', 23) == BitStream('intbe:32=23')
            assert pack('@L', 23) == BitStream('uintbe:32=23')
            assert pack('@i', 23) == BitStream('intbe:32=23')
            assert pack('@I', 23) == BitStream('uintbe:32=23')
            assert pack('@q', 23) == BitStream('intbe:64=23')
            assert pack('@Q', 23) == BitStream('uintbe:64=23')

    def test_native_endianness(self):
        s = pack('=2i', 40, 40)
        if sys.byteorder == 'little':
            assert s == pack('<2i', 40, 40)
        else:
            assert sys.byteorder == 'big'
            assert s == pack('>2i', 40, 40)

    def test_struct_tokens3(self):
        s = pack('>hhl', 1, 2, 3)
        a, b, c = s.unpack('>hhl')
        assert (a, b, c) == (1, 2, 3)
        s = pack('<QL, >Q \tL', 1001, 43, 21, 9999)
        assert s.unpack('<QI, >QL') == [1001, 43, 21, 9999]

    def test_struct_tokens_multiplicative_factors(self):
        s = pack('<2h', 1, 2)
        a, b = s.unpack('<2h')
        assert (a, b) == (1, 2)
        s = pack('<100q', *range(100))
        assert s.len == 100 * 64
        assert s[44*64:45*64].uintle == 44
        s = pack('@L0B2h', 5, 5, 5)
        assert s.unpack('@Lhh') == [5, 5, 5]

    def test_struct_tokens_errors(self):
        for f in ['>>q', '<>q', 'q>', '2q', 'q', '>-2q', '@a', '>int:8', '>q2']:
            with pytest.raises(bitstring.CreationError):
                _ = pack(f, 100)

    def test_immutable_bit_streams(self):
        a = ConstBitStream('0x012345')
        assert a == '0x012345'
        b = BitStream('0xf') + a
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
        with pytest.raises(AttributeError):
            a.insert('0b11', 4)
        with pytest.raises(AttributeError):
            a.reverse()
        with pytest.raises(AttributeError):
            a.reversebytes()
        assert a == '0x012345'
        assert isinstance(a, ConstBitStream)

    def test_reverse_bytes(self):
        a = BitStream('0x123456')
        a.byteswap()
        assert a == '0x563412'
        b = a + '0b1'
        b.byteswap()
        assert '0x123456, 0b1' == b
        a = BitStream('0x54')
        a.byteswap()
        assert a == '0x54'
        a = BitStream()
        a.byteswap()
        assert not a

    def test_reverse_bytes2(self):
        a = BitStream()
        a.byteswap()
        assert not a
        a = BitStream('0x00112233')
        a.byteswap(0, 0, 16)
        assert a == '0x11002233'
        a.byteswap(0, 4, 28)
        assert a == '0x12302103'
        a.byteswap(start=0, end=18)
        assert a == '0x30122103'
        with pytest.raises(ValueError):
            a.byteswap(0, 10, 2)
        with pytest.raises(ValueError):
            a.byteswap(0, -4, 4)
        with pytest.raises(ValueError):
            a.byteswap(0, 24, 48)
        a.byteswap(0, 24)
        assert a == '0x30122103'
        a.byteswap(0, 11, 11)
        assert a == '0x30122103'

    def test_capitals_in_pack(self):
        a = pack('A', A='0b1')
        assert a == '0b1'
        format_ = 'bits:4=BL_OFFT, uint:12=width, uint:12=height'
        d = {'BL_OFFT': '0b1011', 'width': 352, 'height': 288}
        s = bitstring.pack(format_, **d)
        assert s == '0b1011, uint:12=352, uint:12=288'
        a = pack('0X0, uint:8, hex', 45, '0XABcD')
        assert a == '0x0, uint:8=45, 0xabCD'

    def test_other_capitals(self):
        a = ConstBitStream('0XABC, 0O0, 0B11')
        assert a == 'hex=0Xabc, oct=0, bin=0B11'

    def test_efficient_overwrite(self):
        a = BitStream(100000000)
        a.overwrite([1], 123456)
        assert a[123456] == True
        a.overwrite('0xff', 1)
        assert a[0:32:1] == '0x7f800000'
        b = BitStream('0xffff')
        b.overwrite('0x0000')
        assert b == '0x0000'
        assert b.pos == 16
        c = BitStream(length=1000)
        c.overwrite('0xaaaaaaaaaaaa', 81)
        assert c[81:81 + 6 * 8] == '0xaaaaaaaaaaaa'
        assert len(list(c.findall('0b1'))) == 24
        s = BitStream(length=1000)
        s = s[5:]
        s.overwrite('0xffffff', 500)
        s.pos = 500
        assert s.read(4 * 8) == '0xffffff00'
        s.overwrite('0xff', 502)
        assert s[502:518] == '0xffff'

    def test_peek_and_read_list_errors(self):
        a = BitStream('0x123456')
        with pytest.raises(ValueError):
            _ = a.read('hex:8, hex:8')
        with pytest.raises(ValueError):
            _ = a.peek('hex:8, hex:8')
        with pytest.raises(TypeError):
            _ = a.read(10, 12)
        with pytest.raises(TypeError):
            _ = a.peek(12, 14)
        with pytest.raises(TypeError):
            _ = a.read(8, 8)
        with pytest.raises(TypeError):
            _ = a.peek(80, 80)

    def test_startswith(self):
        a = BitStream()
        assert a.startswith(BitStream())
        assert not a.startswith('0b0')
        a = BitStream('0x12ff')
        assert a.startswith('0x1')
        assert a.startswith('0b0001001')
        assert a.startswith('0x12ff')
        assert not a.startswith('0x12ff, 0b1')
        assert not a.startswith('0x2')

    def test_startswith_start_end(self):
        s = BitStream('0x123456')
        assert s.startswith('0x234', 4)
        assert not s.startswith('0x123', end=11)
        assert s.startswith('0x123', end=12)
        assert s.startswith('0x34', 8, 16)
        assert not s.startswith('0x34', 7, 16)
        assert not s.startswith('0x34', 9, 16)
        assert not s.startswith('0x34', 8, 15)

    def test_endswith(self):
        a = BitStream()
        assert a.endswith('')
        assert not a.endswith(BitStream('0b1'))
        a = BitStream('0xf2341')
        assert a.endswith('0x41')
        assert a.endswith('0b001')
        assert a.endswith('0xf2341')
        assert not a.endswith('0x1f2341')
        assert not a.endswith('0o34')

    def test_endswith_start_end(self):
        s = BitStream('0x123456')
        assert s.endswith('0x234', end=16)
        assert not s.endswith('0x456', start=13)
        assert s.endswith('0x456', start=12)
        assert s.endswith('0x34', 8, 16)
        assert s.endswith('0x34', 7, 16)
        assert not s.endswith('0x34', 9, 16)
        assert not s.endswith('0x34', 8, 15)

    def test_unhashability(self):
        s = BitStream('0xf')
        with pytest.raises(TypeError):
            _ = {s}
        with pytest.raises(TypeError):
            _ = hash([s])

    def test_const_bit_stream_set_creation(self):
        sl = [ConstBitStream(uint=i, length=7) for i in range(15)]
        s = set(sl)
        assert len(s) == 15
        s.add(ConstBitStream('0b0000011'))
        assert len(s) == 15
        with pytest.raises(TypeError):
            s.add(BitStream('0b0000011'))

    def test_const_bit_stream_functions(self):
        s = ConstBitStream('0xf, 0b1')
        assert type(s) == ConstBitStream
        t = copy.copy(s)
        assert type(t) == ConstBitStream
        a = s + '0o3'
        assert type(a) == ConstBitStream
        b = a[0:4]
        assert type(b) == ConstBitStream
        b = a[4:3]
        assert type(b) == ConstBitStream
        b = a[5:2:-1]
        assert type(b) == ConstBitStream
        b = ~a
        assert type(b) == ConstBitStream
        b = a << 2
        assert type(b) == ConstBitStream
        b = a >> 2
        assert type(b) == ConstBitStream
        b = a * 2
        assert type(b) == ConstBitStream
        b = a * 0
        assert type(b) == ConstBitStream
        b = a & ~a
        assert type(b) == ConstBitStream
        b = a | ~a
        assert type(b) == ConstBitStream
        b = a ^ ~a
        assert type(b) == ConstBitStream
        b = a._slice(4, 4)
        assert type(b) == ConstBitStream
        b = a.read(4)
        assert type(b) == ConstBitStream

    def test_const_bit_stream_properties(self):
        a = ConstBitStream('0x123123')
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
            a.uint = 4412
        with pytest.raises(AttributeError):
            a.intle = 123
        with pytest.raises(AttributeError):
            a.uintle = 4412
        with pytest.raises(AttributeError):
            a.intbe = 123
        with pytest.raises(AttributeError):
            a.uintbe = 4412
        with pytest.raises(AttributeError):
            a.intne = 123
        with pytest.raises(AttributeError):
            a.uintne = 4412
        with pytest.raises(AttributeError):
            a.bytes = b'hello'

    def test_const_bit_stream_misc(self):
        a = ConstBitStream('0xf')
        b = a
        a += '0xe'
        assert b == '0xf'
        assert a == '0xfe'
        c = BitStream(a)
        assert a == c
        a = ConstBitStream('0b1')
        a += a
        assert a == '0b11'
        assert type(a) == ConstBitStream
        a._addleft(a)
        assert a == '0b1111'
        assert type(a) == ConstBitStream

    def test_const_bit_stream_hashibility(self):
        a = ConstBitStream('0x1')
        b = ConstBitStream('0x2')
        c = ConstBitStream('0x1')
        c.pos = 3
        s = {a, b, c}
        assert len(s) == 2
        assert hash(a) == hash(c)

    def test_const_hashability_again(self):
        a = ConstBitStream(uint=1 << 300, length=10000)
        b = ConstBitStream(uint=2 << 300, length=10000)
        c = ConstBitStream(uint=3 << 300, length=10000)
        s = {a, b, c}
        assert len(s) == 3

    def test_hash_edge_cases(self):
        a = ConstBitStream('0xabcd')
        b = ConstBitStream('0xabcd')
        c = b[1:]
        assert hash(a) == hash(b)
        assert hash(a) != hash(c)

    def test_const_bit_stream_copy(self):
        a = ConstBitStream('0xabc')
        a.pos = 11
        b = copy.copy(a)
        b.pos = 4
        assert id(a._bitstore) == id(b._bitstore)
        assert a.pos == 11
        assert b.pos == 4

    def test_python26stuff(self):
        s = BitStream('0xff')
        assert isinstance(s.tobytes(), bytes)
        assert isinstance(s.bytes, bytes)

    def test_read_from_bits(self):
        a = ConstBitStream('0xaabbccdd')
        b = a.read(8)
        assert b == '0xaa'
        assert a[0:8] == '0xaa'
        assert a[-1] == True
        a.pos = 0
        assert a.read(4).uint == 10


class TestSet:
    def test_set(self):
        a = BitStream(length=16)
        a.set(True, 0)
        assert a == '0b10000000 00000000'
        a.set(1, 15)
        assert a == '0b10000000 00000001'
        b = a[4:12]
        b.set(True, 1)
        assert b == '0b01000000'
        b.set(True, -1)
        assert b == '0b01000001'
        b.set(1, -8)
        assert b == '0b11000001'
        with pytest.raises(IndexError):
            b.set(True, -9)
        with pytest.raises(IndexError):
            b.set(True, 8)

    def test_set_negative_index(self):
        a = BitStream(10)
        a.set(1, -1)
        assert a.bin == '0000000001'
        a.set(1, [-1, -10])
        assert a.bin == '1000000001'
        with pytest.raises(IndexError):
            a.set(1, [-11])

    def test_file_based_set_unset(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        a = BitStream(filename=filename)
        a.set(True, (0, 1, 2, 3, 4))
        assert a[0:32] == '0xf80001b3'
        a = BitStream(filename=filename)
        a.set(False, (28, 29, 30, 31))
        assert a.startswith('0x000001b0')

    def test_set_list(self):
        a = BitStream(length=18)
        a.set(True, range(18))
        assert a.int == -1
        a.set(False, range(18))
        assert a.int == 0

    def test_unset(self):
        a = BitStream(length=16, int=-1)
        a.set(False, 0)
        assert ~a == '0b10000000 00000000'
        a.set(0, 15)
        assert ~a == '0b10000000 00000001'
        b = a[4:12]
        b.set(False, 1)
        assert ~b == '0b01000000'
        b.set(False, -1)
        assert ~b == '0b01000001'
        b.set(False, -8)
        assert ~b == '0b11000001'
        with pytest.raises(IndexError):
            b.set(False, -9)
        with pytest.raises(IndexError):
            b.set(False, 8)

    def test_set_whole_bit_stream(self):
        a = BitStream(10000)
        a.set(1)
        assert a.all(1)
        a.set(0)
        assert a.all(0)


class TestInvert:
    def test_invert_bits(self):
        a = BitStream('0b111000')
        a.invert(range(a.len))
        assert a == '0b000111'
        a.invert([0, 1, -1])
        assert a == '0b110110'

    def test_invert_whole_bit_stream(self):
        a = BitStream('0b11011')
        a.invert()
        assert a == '0b00100'

    def test_invert_single_bit(self):
        a = BitStream('0b000001')
        a.invert(0)
        assert a.bin == '100001'
        a.invert(-1)
        assert a.bin == '100000'

    def test_invert_errors(self):
        a = BitStream(10)
        with pytest.raises(IndexError):
            a.invert(10)
        with pytest.raises(IndexError):
            a.invert(-11)
        with pytest.raises(IndexError):
            a.invert([1, 2, 10])

    def test_ior(self):
        a = BitStream('0b1101001')
        a |= '0b1110000'
        assert a == '0b1111001'
        b = a[2:]
        c = a[1:-1]
        b |= c
        assert c == '0b11100'
        assert b == '0b11101'

    def test_iand(self):
        a = BitStream('0b0101010101000')
        a &= '0b1111110000000'
        assert a == '0b0101010000000'
        s = BitStream(filename=os.path.join(THIS_DIR, 'test.m1v'), offset=26, length=24)
        s &= '0xff00ff'
        assert s == '0xcc0004'

    def test_ixor(self):
        a = BitStream('0b11001100110011')
        a ^= '0b11111100000010'
        assert a == '0b00110000110001'

    def test_logical_inplace_errors(self):
        a = BitStream(4)
        with pytest.raises(ValueError):
            a |= '0b111'
        with pytest.raises(ValueError):
            a &= '0b111'
        with pytest.raises(ValueError):
            a ^= '0b111'


class TestAllAndAny:
    def test_all(self):
        a = BitStream('0b0111')
        assert a.all(True, (1, 3))
        assert not a.all(True, (0, 1, 2))
        assert a.all(True, [-1])
        assert not a.all(True, [0])

    def test_file_based_all(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        a = BitStream(filename=filename)
        assert a.all(True, [31])
        a = BitStream(filename=filename)
        assert a.all(False, (0, 1, 2, 3, 4))

    def test_file_based_any(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        a = BitStream(filename=filename)
        assert a.any(True, (31, 12))
        a = BitStream(filename=filename)
        assert a.any(False, (0, 1, 2, 3, 4))
        b = ConstBitStream(filename=filename, offset=16)
        assert b.startswith('0x01')
        assert not b.any(True, range(0, 7))
        assert b.any(True, range(0, 8))
        assert b.any(True)

    def test_any(self):
        a = BitStream('0b10011011')
        assert a.any(True, (1, 2, 3, 5))
        assert not a.any(True, (1, 2, 5))
        assert a.any(True, (-1,))
        assert not a.any(True, (1,))

    def test_all_false(self):
        a = BitStream('0b0010011101')
        assert a.all(False, (0, 1, 3, 4))
        assert not a.all(False, (0, 1, 2, 3, 4))

    def test_any_false(self):
        a = BitStream('0b01001110110111111111111111111')
        assert a.any(False, (4, 5, 6, 2))
        assert not a.any(False, (1, 15, 20))

    def test_any_empty_bitstring(self):
        a = ConstBitStream()
        assert not a.any(True)
        assert not a.any(False)

    def test_all_empty_bit_stream(self):
        a = ConstBitStream()
        assert a.all(True)
        assert a.all(False)

    def test_any_whole_bitstring(self):
        a = ConstBitStream('0xfff')
        assert a.any(True)
        assert not a.any(False)

    def test_all_whole_bitstring(self):
        a = ConstBitStream('0xfff')
        assert a.all(True)
        assert not a.all(False)

    def test_errors(self):
        a = BitStream('0xf')
        with pytest.raises(IndexError):
            a.all(True, [5])
        with pytest.raises(IndexError):
            a.all(True, [-5])
        with pytest.raises(IndexError):
            a.any(True, [5])
        with pytest.raises(IndexError):
            a.any(True, [-5])

    ###################

    def test_float_initialisation(self):
        for f in (0.000001, -1.0, 1.0, 0.2, -3.14159265):
            a = BitStream(float=f, length=64)
            a.pos = 6
            assert a.float == f
            a = BitStream('float:64=%s' % str(f))
            a.pos = 6
            assert a.float == f
            a = BitStream('floatbe:64=%s' % str(f))
            a.pos = 6
            assert a.floatbe == f
            a = BitStream('floatle:64=%s' % str(f))
            a.pos = 6
            assert a.floatle == f
            a = BitStream('floatne:64=%s' % str(f))
            a.pos = 6
            assert a.floatne == f

            b = BitStream(float=f, length=32)
            b.pos = 6
            assert b.float / f == pytest.approx(1.0)
            b = BitStream('float:32=%s' % str(f))
            b.pos = 6
            assert b.float / f == pytest.approx(1.0)
            b = BitStream('floatbe:32=%s' % str(f))
            b.pos = 6
            assert b.floatbe / f == pytest.approx(1.0)
            b = BitStream('floatle:32=%s' % str(f))
            b.pos = 6
            assert b.floatle / f == pytest.approx(1.0)
            b = BitStream('floatne:32=%s' % str(f))
            b.pos = 6
            assert b.floatne / f == pytest.approx(1.0)

            a = BitStream(float=f, length=16)
            a.pos = 6
            assert a.float == pytest.approx(f, abs=0.01)
            a = BitStream('float:16=%s' % str(f))
            a.pos = 6
            assert a.float == pytest.approx(f, abs=0.01)
            a = BitStream('floatbe:16=%s' % str(f))
            a.pos = 6
            assert a.floatbe == pytest.approx(f, abs=0.01)
            a = BitStream('floatle:16=%s' % str(f))
            a.pos = 6
            assert a.floatle == pytest.approx(f, abs=0.01)
            a = BitStream('floatne:16=%s' % str(f))
            a.pos = 6
            assert a.floatne == pytest.approx(f, abs=0.01)

        a = BitStream('0x12345678')
        a.pos = 6
        a.f = 23
        assert a.f == 23.0

    def test_float_init_strings(self):
        for s in ('5', '+0.0001', '-1e101', '4.', '.2', '-.65', '43.21E+32'):
            a = BitStream('float:64=%s' % s)
            assert a.float == float(s)
        for s in ('5', '+0.5', '-1e2', '4.', '.25', '-.75'):
            a = BitStream('float:16=%s' % s)
            assert a.f == float(s)

    def test_float_packing(self):
        a = pack('>d', 0.01)
        assert a.float == 0.01
        assert a.floatbe == 0.01
        a.byteswap()
        assert a.floatle == 0.01
        b = pack('>f', 1e10)
        assert b.float / 1e10 == pytest.approx(1.0)
        c = pack('<f', 10.3)
        assert c.floatle / 10.3 == pytest.approx(1.0)
        d = pack('>5d', 10.0, 5.0, 2.5, 1.25, 0.1)
        assert d.unpack('>5d') == [10.0, 5.0, 2.5, 1.25, 0.1]
        e = pack('>3e', -100, 100, 0.25)
        assert e.unpack('>3e') == [-100.0, 100.0, 0.25]

    def test_float_reading(self):
        a = BitStream('floatle:64=12, floatbe:64=-0.01, floatne:64=3e33')
        x, y, z = a.readlist('floatle:64, floatbe:64, floatne:64')
        assert x == 12.0
        assert y == -0.01
        assert z == 3e33
        a = BitStream('floatle:16=12, floatbe:32=-0.01, floatne:32=3e33')
        x, y, z = a.readlist('floatle:16, floatbe:32, floatne:32')
        assert x / 12.0 == pytest.approx(1.0)
        assert y / -0.01 == pytest.approx(1.0)
        assert z / 3e33 == pytest.approx(1.0)
        a = BitStream('0b11, floatle:64=12, 0xfffff')
        a.pos = 2
        floatle64 = Dtype('floatle64')
        assert a.read(floatle64) == 12.0
        b = BitStream(floatle=20, length=32)
        b.floatle = 10.0
        b = [0] + b
        assert b[1:].floatle == 10.0

    def test_non_aligned_float_reading(self):
        s = BitStream('0b1, float:32 = 10.0')
        x, y = s.readlist('1, float:32')
        assert y == 10.0
        s[1:] = 'floatle:32=20.0'
        x, y = s.unpack('1, floatle:32')
        assert y == 20.0

    def test_float_errors(self):
        a = BitStream('0x3')
        with pytest.raises(bitstring.InterpretError):
            _ = a.float
        with pytest.raises(bitstring.CreationError):
            a.float = -0.2
        for le in (8, 10, 12, 18, 30, 128, 200):
            with pytest.raises(ValueError):
                _ = BitStream(float=1.0, length=le)
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(floatle=0.3, length=0)
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(floatle=0.3, length=1)
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(float=2)
        with pytest.raises(bitstring.InterpretError):
            _ = a.read('floatle:2')

    def test_read_error_changes_pos(self):
        a = BitStream('0x123123')
        with pytest.raises(ValueError):
            a.read('10, 5')

    def test_ror(self):
        a = BitStream('0b11001')
        a.ror(0)
        assert a == '0b11001'
        a.ror(1)
        assert a == '0b11100'
        a.ror(5)
        assert a == '0b11100'
        a.ror(101)
        assert a == '0b01110'
        a = BitStream('0b1')
        a.ror(1000000)
        assert a == '0b1'

    def test_ror_errors(self):
        a = BitStream()
        with pytest.raises(bitstring.Error):
            a.ror(0)
        a += '0b001'
        with pytest.raises(ValueError):
            a.ror(-1)

    def test_rol(self):
        a = BitStream('0b11001')
        a.rol(0)
        assert a == '0b11001'
        a.rol(1)
        assert a == '0b10011'
        a.rol(5)
        assert a == '0b10011'
        a.rol(101)
        assert a == '0b00111'
        a = BitStream('0b1')
        a.rol(1000000)
        assert a == '0b1'

    def test_rol_from_file(self):
        a = BitStream(filename=os.path.join(THIS_DIR, 'test.m1v'))
        m = a.len
        a.rol(1)
        assert a.startswith('0x000003')
        assert a.len == m
        assert a.endswith('0x0036e')

    def test_ror_from_file(self):
        a = BitStream(filename=os.path.join(THIS_DIR, 'test.m1v'))
        m = a.len
        a.ror(1)
        assert a.startswith('0x800000')
        assert a.len == m
        assert a.endswith('0x000db')

    def test_rol_errors(self):
        a = BitStream()
        with pytest.raises(bitstring.Error):
            a.rol(0)
        a += '0b001'
        with pytest.raises(ValueError):
            a.rol(-1)

    def test_bytes_token(self):
        a = BitStream('0x510203')
        b = a.read('bytes:1')
        assert isinstance(b, bytes)
        assert b == b'\x51'
        x, y, z = a.unpack('uint:4, bytes:2, uint')
        assert x == 5
        assert y == b'\x10\x20'
        assert z == 3
        s = pack('bytes:4', b'abcd')
        assert s.bytes == b'abcd'

    def test_bytes_token_more_thoroughly(self):
        a = BitStream('0x0123456789abcdef')
        a.pos += 16
        assert a.read('bytes:1') == b'\x45'
        assert a.read('bytes:3') == b'\x67\x89\xab'
        x, y, z = a.unpack('bits:28, bytes, bits:12')
        assert y == b'\x78\x9a\xbc'

    def test_dedicated_read_functions(self):
        a = BitStream('0b11, uint:43=98798798172, 0b11111')
        x = a[2:45].uint
        assert x == 98798798172
        assert a.pos == 0
        a.pos = 2
        x = a.read(Dtype('int43'))
        assert x == 98798798172
        assert a.pos == 45

        a = BitStream('0b11, uintbe:48=98798798172, 0b11111')
        a.pos = 2
        x = a.read(Dtype('uintbe48'))
        assert x == 98798798172
        assert a.pos == 50

        a = BitStream('0b111, uintle:40=123516, 0b111')
        a.pos = 3
        assert a.read('uintle:40') == 123516
        b = BitStream('0xff, uintle:800=999, 0xffff')
        assert b[8:800].uintle == 999

        a = BitStream('0b111, intle:48=999999999, 0b111111111111')
        a.pos = 3
        assert a.read('intle48') == 999999999
        b = BitStream('0xff, intle:200=918019283740918263512351235, 0xfffffff')
        b.pos = 8
        assert b.read(Dtype('intle', length=200)) == 918019283740918263512351235

        a = BitStream('0b111, bfloat:16=-5.25, 0xffffffff')
        a.pos = 3
        assert a.read('bfloatbe') == -5.25

        a = BitStream('0b111, floatle:64=9.9998, 0b111')
        a.pos = 3
        assert a.read('floatle64') == 9.9998

    def test_auto_init_with_int(self):
        a = BitStream(0)
        assert not a
        a = BitStream(1)
        assert a == '0b0'
        a = BitStream(1007)
        assert a == BitStream(length=1007)
        with pytest.raises(bitstring.CreationError):
            _ = BitStream(-1)

        assert ConstBitStream(13) == Bits(13)
        with pytest.raises(TypeError):
            a += 10

    def test_reading_problems(self):
        a = BitStream('0x000001')
        b = a.read('uint:24')
        assert b == 1
        a.pos = 0
        with pytest.raises(bitstring.ReadError):
            _ = a.read('bytes:4')

    @pytest.mark.skip("Bug #266")
    def test_pos_reset_bug(self):
        a = BitStream('0x0120310230123', pos=23)
        assert a.pos == 23
        a.u8 = 14
        assert a.pos == 0
        a.pos = 5
        a.u8 = 9
        assert a.pos == 0

    def test_creation_exception_bug(self):
        with pytest.raises(ValueError):
            _ = BitStream(bin=1)

    def test_add_verses_in_place_add(self):
        a1 = ConstBitStream('0xabc')
        b1 = a1
        a1 += '0xdef'
        assert a1 == '0xabcdef'
        assert b1 == '0xabc'

        a2 = BitStream('0xabc')
        b2 = a2
        c2 = a2 + '0x0'
        a2 += '0xdef'
        assert a2 == '0xabcdef'
        assert b2 == '0xabcdef'
        assert c2 == '0xabc0'

    def test_and_verses_in_place_and(self):
        a1 = ConstBitStream('0xabc')
        b1 = a1
        a1 &= '0xf0f'
        assert a1 == '0xa0c'
        assert b1 == '0xabc'

        a2 = BitStream('0xabc')
        b2 = a2
        c2 = a2 & '0x00f'
        a2 &= '0xf0f'
        assert a2 == '0xa0c'
        assert b2 == '0xa0c'
        assert c2 == '0x00c'

    def test_or_verses_in_place_or(self):
        a1 = ConstBitStream('0xabc')
        b1 = a1
        a1 |= '0xf0f'
        assert a1 == '0xfbf'
        assert b1 == '0xabc'

        a2 = BitStream('0xabc')
        b2 = a2
        c2 = a2 | '0x00f'
        a2 |= '0xf0f'
        assert a2 == '0xfbf'
        assert b2 == '0xfbf'
        assert c2 == '0xabf'

    def test_xor_verses_in_place_xor(self):
        a1 = ConstBitStream('0xabc')
        b1 = a1
        a1 ^= '0xf0f'
        assert a1 == '0x5b3'
        assert b1 == '0xabc'

        a2 = BitStream('0xabc')
        b2 = a2
        c2 = a2 ^ '0x00f'
        a2 ^= '0xf0f'
        assert a2 == '0x5b3'
        assert b2 == '0x5b3'
        assert c2 == '0xab3'

    def test_mul_verses_in_place_mul(self):
        a1 = ConstBitStream('0xabc')
        b1 = a1
        a1 *= 3
        assert a1 == '0xabcabcabc'
        assert b1 == '0xabc'

        a2 = BitStream('0xabc')
        b2 = a2
        c2 = a2 * 2
        a2 *= 3
        assert a2 == '0xabcabcabc'
        assert b2 == '0xabcabcabc'
        assert c2 == '0xabcabc'

    def test_lshift_verses_in_place_lshift(self):
        a1 = ConstBitStream('0xabc')
        b1 = a1
        a1 <<= 4
        assert a1 == '0xbc0'
        assert b1 == '0xabc'

        a2 = BitStream('0xabc')
        b2 = a2
        c2 = a2 << 8
        a2 <<= 4
        assert a2 == '0xbc0'
        assert b2 == '0xbc0'
        assert c2 == '0xc00'

    def test_rshift_verses_in_place_rshift(self):
        a1 = ConstBitStream('0xabc')
        b1 = a1
        a1 >>= 4
        assert a1 == '0x0ab'
        assert b1 == '0xabc'

        a2 = BitStream('0xabc')
        b2 = a2
        c2 = a2 >> 8
        a2 >>= 4
        assert a2 == '0x0ab'
        assert b2 == '0x0ab'
        assert c2 == '0x00a'

    def test_auto_from_bool(self):
        with pytest.raises(TypeError):
            a = ConstBitStream() + True + False + True


class TestBugs:
    def test_bug_in_replace(self):
        s = BitStream('0x00112233')
        li = list(s.split('0x22', start=8, bytealigned=True))
        assert li == ['0x11', '0x2233']
        s = BitStream('0x00112233')
        s.replace('0x22', '0xffff', start=8, bytealigned=True)
        assert s == '0x0011ffff33'
        s = BitStream('0x0123412341234')
        s.replace('0x23', '0xf', start=9, bytealigned=True)
        assert s == '0x012341f41f4'

    def test_truncateleft_bug(self):
        a = BitStream('0b000000111')[2:]
        a._truncateleft(6)
        assert a == '0b1'

    def test_null_bits(self):
        s = ConstBitStream(bin='')
        t = ConstBitStream(oct='')
        u = ConstBitStream(hex='')
        v = ConstBitStream(bytes=b'')
        assert not s
        assert not t
        assert not u
        assert not v

    def test_multiplicative_factors_creation(self):
        s = BitStream('1*0b1')
        assert s == '0b1'
        s = BitStream('4*0xc')
        assert s == '0xcccc'
        s = BitStream('0b1, 0*0b0')
        assert s == '0b1'
        s = BitStream('0b1, 3*uint:8=34, 2*0o755')
        assert s == '0b1, uint:8=34, uint:8=34, uint:8=34, 0o755755'
        s = BitStream('0*0b1001010')
        assert not s

    def test_multiplicative_factors_reading(self):
        s = BitStream('0xc') * 5
        a, b, c, d, e = s.readlist('5*uint:4')
        assert a == b == c == d == e == 12
        s = ConstBitStream('2*0b101, 4*uint:7=3')
        a, b, c, d, e = s.readlist('2*bin:3, 3*uint:7')
        assert a == b == '101'
        assert c == d == e == 3

    def test_multiplicative_factors_packing(self):
        s = pack('3*bin', '1', '001', '101')
        assert s == '0b1001101'
        s = pack('hex, 2*se=-56, 3*uint:37', '34', 1, 2, 3)
        a, b, c, d, e, f = s.unpack('hex:8, 2*se, 3*uint:37')
        assert a == '34'
        assert b == -56
        assert c == -56
        assert (d, e, f) == (1, 2, 3)

    def test_multiplicative_factors_unpacking(self):
        s = ConstBitStream('0b10111')
        a, b, c, d = s.unpack('3*bool, bin')
        assert (a, b, c) == (True, False, True)
        assert d == '11'

    def test_packing_default_int_with_keyword(self):
        s = pack('uint:12', 100)
        assert s.unpack('12')[0].uint == 100
        s = pack('int:oh_no_not_the_eyes=33', oh_no_not_the_eyes=17)
        assert s.int == 33
        assert s.len == 17

    def test_init_from_iterable(self):
        assert isinstance(range(10), collections.abc.Iterable)
        s = ConstBitStream(range(12))
        assert s == '0x7ff'

    def test_function_negative_indices(self):
        # insert
        s = BitStream('0b0111')
        s.insert('0b0', -1)
        assert s == '0b01101'
        with pytest.raises(ValueError):
            s.insert('0b0', -1000)

        # reverse
        s.reverse(-2)
        assert s == '0b01110'
        t = BitStream('0x778899abcdef')
        t.reverse(-12, -4)
        assert t == '0x778899abc7bf'

        # reversebytes
        t.byteswap(0, -40, -16)
        assert t == '0x77ab9988c7bf'

        # overwrite
        t.overwrite('0x666', -20)
        assert t == '0x77ab998666bf'

        # find
        found = t.find('0x998', bytealigned=True, start=-31)
        assert not found
        found = t.find('0x998', bytealigned=True, start=-32)
        assert found
        assert t.pos == 16
        t.pos = 0
        found = t.find('0x988', bytealigned=True, end=-21)
        assert not found
        found = t.find('0x998', bytealigned=True, end=-20)
        assert found
        assert t.pos == 16

        # findall
        s = BitStream('0x1234151f')
        li = list(s.findall('0x1', bytealigned=True, start=-15))
        assert li == [24]
        li = list(s.findall('0x1', bytealigned=True, start=-16))
        assert li == [16, 24]
        li = list(s.findall('0x1', bytealigned=True, end=-5))
        assert li == [0, 16]
        li = list(s.findall('0x1', bytealigned=True, end=-4))
        assert li == [0, 16, 24]

        # rfind
        found = s.rfind('0x1f', end=-1)
        assert not found
        found = s.rfind('0x12', start=-31)
        assert not found

        # cut
        s = BitStream('0x12345')
        li = list(s.cut(4, start=-12, end=-4))
        assert li == ['0x3', '0x4']

        # split
        s = BitStream('0xfe0012fe1200fe')
        li = list(s.split('0xfe', bytealigned=True, end=-1))
        assert li == ['', '0xfe0012', '0xfe1200f, 0b111']
        li = list(s.split('0xfe', bytealigned=True, start=-8))
        assert li == ['', '0xfe']

        # startswith
        assert s.startswith('0x00f', start=-16)
        assert s.startswith('0xfe00', end=-40)
        assert not s.startswith('0xfe00', end=-41)

        # endswith
        assert s.endswith('0x00fe', start=-16)
        assert not s.endswith('0x00fe', start=-15)
        assert not s.endswith('0x00fe', end=-1)
        assert s.endswith('0x00f', end=-4)

        # replace
        s.replace('0xfe', '', end=-1)
        assert s == '0x00121200fe'
        s.replace('0x00', '', start=-24)
        assert s == '0x001212fe'

    def test_rotate_start_and_end(self):
        a = BitStream('0b110100001')
        a.rol(1, 3, 6)
        assert a == '0b110001001'
        a.ror(1, start=-4)
        assert a == '0b110001100'
        a.rol(202, end=-5)
        assert a == '0b001101100'
        a.ror(3, end=4)
        assert a == '0b011001100'
        with pytest.raises(ValueError):
            a.rol(5, start=-4, end=-6)

    def test_byte_swap_int(self):
        s = pack('5*uintle:16', *range(10, 15))
        assert list(range(10, 15)) == s.unpack('5*uintle:16')
        swaps = s.byteswap(2)
        assert list(range(10, 15)) == s.unpack('5*uintbe:16')
        assert swaps == 5
        s = BitStream('0xf234567f')
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
        swaps = s.byteswap(5)
        assert swaps == 0
        swaps = s.byteswap(4, repeat=False)
        assert swaps == 1
        assert s == '0x7ff25634'

    def test_byte_swap_pack_code(self):
        s = BitStream('0x0011223344556677')
        swaps = s.byteswap('b')
        assert s == '0x0011223344556677'
        assert swaps == 8
        swaps = s.byteswap('>3h', repeat=False)
        assert s == '0x1100332255446677'
        assert swaps == 1

    def test_byte_swap_iterable(self):
        s = BitStream('0x0011223344556677')
        swaps = s.byteswap(range(1, 4), repeat=False)
        assert swaps == 1
        assert s == '0x0022115544336677'
        swaps = s.byteswap([2], start=8)
        assert s == '0x0011224455663377'
        assert 3 == swaps
        swaps = s.byteswap([2, 3], start=4)
        assert swaps == 1
        assert s == '0x0120156452463377'

    def test_byte_swap_errors(self):
        s = BitStream('0x0011223344556677')
        with pytest.raises(ValueError):
            s.byteswap('z')
        with pytest.raises(ValueError):
            s.byteswap(-1)
        with pytest.raises(ValueError):
            s.byteswap([-1])
        with pytest.raises(ValueError):
            s.byteswap([1, 'e'])
        with pytest.raises(ValueError):
            s.byteswap('!h')
        with pytest.raises(ValueError):
            s.byteswap(2, start=-1000)
        with pytest.raises(TypeError):
            s.byteswap(5.4)

    def test_byte_swap_from_file(self):
        s = BitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        swaps = s.byteswap('2bh')
        assert s == '0x0123674589abefcd'
        assert swaps == 2

    def test_bracket_expander(self):
        be = bitstring.utils.expand_brackets
        assert be('hello') == 'hello'
        assert be('(hello)') == 'hello'
        assert be('1*(hello)') == 'hello'
        assert be('2*(hello)') == 'hello,hello'
        assert be('1*(a,b)') == 'a,b'
        assert be('2*(a,b)') == 'a,b,a,b'
        assert be('2*(a),3*(b)') == 'a,a,b,b,b'
        assert be('2*(a,b,3*(c,d),e)') == 'a,b,c,d,c,d,c,d,e,a,b,c,d,c,d,c,d,e'
        with pytest.raises(ValueError):
            _ = be('2*(x,y()')

    def test_bracket_tokens(self):
        s = BitStream('3*(0x0, 0b1)')
        assert s == '0x0, 0b1, 0x0, 0b1, 0x0, 0b1'
        s = pack('2*(uint:12, 3*(uint:7, uint:6))', *range(3, 17))
        a = s.unpack('12, 7, 6, 7, 6, 7, 6, 12, 7, 6, 7, 6, 7, 6')
        assert [x.uint for x in a] == list(range(3, 17))
        b = s.unpack('2*(12,3*(7,6))')
        assert a == b

    def test_pack_code_dicts(self):
        assert sorted(bitstring.utils.REPLACEMENTS_BE.keys()) == \
                         sorted(bitstring.utils.REPLACEMENTS_LE.keys())
        assert sorted(bitstring.utils.REPLACEMENTS_BE.keys()) == \
                         sorted(bitstring.utils.PACK_CODE_SIZE.keys())
        for key in bitstring.utils.PACK_CODE_SIZE:
            be = pack(bitstring.utils.REPLACEMENTS_BE[key], 0)
            le = pack(bitstring.utils.REPLACEMENTS_LE[key], 0)
            assert be.len == bitstring.utils.PACK_CODE_SIZE[key] * 8
            assert le.len == be.len

    def test_unicode(self):
        a = ConstBitStream(u'uint:12=34')
        assert a.uint == 34
        a += u'0xfe'
        assert a[12:] == '0xfe'
        a = BitStream('0x1122')
        c = a.byteswap(u'h')
        assert c == 1
        assert a == u'0x2211'


class TestUnpackWithDict:
    def test_length_keywords(self):
        a = ConstBitStream('2*int:13=100, 0b111')
        x, y, z = a.unpack('13, int:m, bin:q', m=13, q=3)
        assert x == 'uint:13=100'
        assert y == 100
        assert z == '111'

    def test_length_keywords_with_stretch(self):
        a = ConstBitStream('0xff, 0b000, 0xf')
        x, y, z = a.unpack('hex:a, bin, hex:b', a=8, b=4)
        assert y == '000'

    def test_unused_keyword(self):
        a = ConstBitStream('0b110')
        x, = a.unpack('bin:3', notused=33)
        assert x == '110'

    def test_length_keyword_errors(self):
        a = pack('uint:p=33', p=12)
        with pytest.raises(ValueError):
            a.unpack('uint:p')
        with pytest.raises(ValueError):
            a.unpack('uint:p', p='a_string')


class TestReadWithDict:
    def test_length_keywords(self):
        s = BitStream('0x0102')
        x, y = s.readlist('bits8, hex:b', b=4)
        assert (x, y) == ('0x01', '0')
        assert s.pos == 12

    def test_bytes_keyword_problem(self):
        s = BitStream('0x01')
        x, = s.unpack('bytes:a', a=1)
        assert x == b'\x01'

        s = BitStream('0x000ff00a')
        x, y, z = s.unpack('12, bytes:x, bits', x=2)
        assert (x.int, y, z) == (0, b'\xff\x00', '0xa')


class TestPeekWithDict:
    def test_length_keywords(self):
        s = BitStream('0x0102')
        x, y = s.peeklist('8, hex:b', b=4)
        assert (x, y) == ('0x01', '0')
        assert s.pos == 0


class TestBoolToken:
    def test_interpretation(self):
        a = ConstBitStream('0b1')
        assert a.bool == True
        assert a.read('bool') == True
        assert a.unpack('bool')[0] == True
        b = ConstBitStream('0b0')
        assert b.bool == False
        assert b.peek('bool') == False
        assert b.unpack('bool')[0] == False

    def test_pack(self):
        a = pack('bool=True')
        b = pack('bool=False')
        assert a.bool == True
        assert b.bool == False
        c = pack('4*bool', False, True, 'False', 'True')
        assert c == '0b0101'

    def test_assignment(self):
        a = BitStream()
        a.bool = True
        assert a.bool == True
        a.hex = 'ee'
        a.bool = False
        assert a.bool == False
        a.bool = 'False'
        assert a.bool == False
        a.bool = 'True'
        assert a.bool == True
        a.bool = 0
        assert a.bool == False
        a.bool = 1
        assert a.bool == True

    def test_errors(self):
        with pytest.raises(bitstring.CreationError):
            pack('bool', 'hello')
        with pytest.raises(bitstring.CreationError):
            pack('bool=true')
        with pytest.raises(bitstring.CreationError):
            pack('True')
        with pytest.raises(bitstring.CreationError):
            pack('bool', 2)
        with pytest.raises(bitstring.CreationError):
            _ = pack('bool', 'hello')
        with pytest.raises(bitstring.CreationError):
            _ = pack('bool=true')
        with pytest.raises(bitstring.CreationError):
            _ = pack('True')
        with pytest.raises(bitstring.CreationError):
            _ = pack('bool', 2)
        a = BitStream('0b11')
        with pytest.raises(bitstring.InterpretError):
            _ = a.bool
        b = BitStream()
        with pytest.raises(bitstring.InterpretError):
            _ = b.bool
        with pytest.raises(bitstring.CreationError):
            b.bool = 'false'

    def test_length_with_bool_read(self):
        a = ConstBitStream('0xf')
        with pytest.raises(ValueError):
            _ = a.read('bool:0')
        with pytest.raises(ValueError):
            _ = a.read('bool:2')


class TestReadWithIntegers:
    def test_read_int(self):
        a = ConstBitStream('0xffeedd')
        b = a.read(8)
        assert b.hex == 'ff'
        assert a.pos == 8
        b = a.peek(8)
        assert b.hex == 'ee'
        assert a.pos == 8
        b = a.peek(1)
        assert b == '0b1'
        b = a.read(1)
        assert b == '0b1'

    def test_read_int_list(self):
        a = ConstBitStream('0xab, 0b110')
        b, c = a.readlist([8, 3])
        assert b.hex == 'ab'
        assert c.bin == '110'


# class FileReadingStrategy(unittest.TestCase):
#
#
#     def testBitStreamIsAlwaysRead(self):
#         filename = os.path.join(THIS_DIR, 'smalltestfile')
#         a = BitStream(filename=filename)
#         self.assertTrue(isinstance(a._datastore, bitstring.ByteStore))
#         with open(filename, 'rb') as f:
#             b = BitStream(f)
#             self.assertTrue(isinstance(b._datastore, bitstring.ByteStore))
#
#
#     def testBitsIsNeverRead(self):
#         filename = os.path.join(THIS_DIR, 'smalltestfile')
#         a = ConstBitStream(filename=filename)
#         self.assertTrue(isinstance(a._datastore.rawarray, bitstring.MmapByteArray))
#         with open(filename, 'rb') as f:
#             b = ConstBitStream(f)
#             self.assertTrue(isinstance(b._datastore.rawarray, bitstring.MmapByteArray))


class TestCount:
    def test_count(self):
        a = ConstBitStream('0xf0f')
        assert a.count(True) == 8
        assert a.count(False) == 4

        b = BitStream()
        assert b.count(True) == 0
        assert b.count(False) == 0

    def test_count_with_offset_data(self):
        a = ConstBitStream('0xff0120ff')
        b = a[1:-1]
        assert b.count(1) == 16
        assert b.count(0) == 14


class TestZeroBitReads:
    def test_integer(self):
        a = ConstBitStream('0x123456')
        with pytest.raises(bitstring.InterpretError):
            _ = a.read('uint:0')
        with pytest.raises(bitstring.InterpretError):
            _ = a.read('float:0')


class TestInitialiseFromBytes:
    def test_bytes_behaviour(self):
        a = ConstBitStream(b'uint:5=2')
        b = ConstBitStream(b'')
        c = ConstBitStream(bytes=b'uint:5=2')
        assert a.bytes == b'uint:5=2'
        assert not b
        assert c == b'uint:5=2'

    def test_bytearray_behaviour(self):
        a = ConstBitStream(bytearray(b'uint:5=2'))
        b = ConstBitStream(bytearray(4))
        c = ConstBitStream(bytes=bytearray(b'uint:5=2'))
        assert a.bytes == b'uint:5=2'
        assert b == '0x00000000'
        assert c.bytes == b'uint:5=2'


class TestCoverageCompletion:
    def test_ue_read_error(self):
        s = ConstBitStream('0b000000001')
        with pytest.raises(bitstring.ReadError):
            _ = s.read('ue')

    def test_overwrite_with_self(self):
        s = BitStream('0b1101')
        s.overwrite(s)
        assert s == '0b1101'


class TestSubclassing:

    def test_is_instance(self):
        b = BitStream()
        assert isinstance(b, BitStream)
        class SubBits(BitStream):
            pass
        a = SubBits()
        assert isinstance(a, SubBits)

    def test_class_type(self):
        class SubBits(BitStream):
            pass
        assert SubBits().__class__ == SubBits


class TestBytesProblems:

    def test_offset_but_no_length(self):
        b = BitStream(bytes=b'\x00\xaa', offset=8)
        assert b.hex == 'aa'
        b = BitStream(bytes=b'\x00\xaa', offset=4)
        assert b.hex == '0aa'

    def test_invert(self):
        b = BitStream(bytes=b'\x00\xaa', offset=8, length=8)
        assert b.hex == 'aa'
        b.invert()
        assert b.hex == '55'

    def test_prepend(self):
        b = BitStream(bytes=b'\xaa\xbb', offset=8, length=4)
        assert b.hex == 'b'
        b.prepend('0xe')
        assert b.hex == 'eb'
        b = BitStream(bytes=b'\x00\xaa', offset=8, length=8)
        b.prepend('0xee')
        assert b.hex == 'eeaa'

    def test_byte_swap(self):
        b = BitStream(bytes=b'\x01\x02\x03\x04', offset=8)
        b.byteswap()
        assert b == '0x040302'

    def test_bin_property(self):
        b = BitStream(bytes=b'\x00\xaa', offset=8, length=4)
        assert b.bin == '1010'


class TestLsb0Streaming:

    @classmethod
    def setup_class(cls):
        bitstring.lsb0 = True

    @classmethod
    def teardown_class(cls):
        bitstring.lsb0 = False

    def test_simple_bit_positions(self):
        s = BitStream('0x00000f')
        assert s.pos == 0
        v = s.read('uint:8')
        assert v == 15
        assert s.pos == 8
        v = s.read(10)
        assert v == Bits(10)
        assert s.pos == 18

    def test_bit_pos_after_find(self):
        s = BitStream('0b01100001000011 0000')
        s.find('0b11', start=1)
        assert s.pos == 4

    def test_iter(self):
        s = BitStream('0b11000')
        assert list(s) == [False, False, False, True, True]

    def test_bit_pos_after_rfind(self):
        s = BitStream('0b011 000010000110000')
        s.rfind('0b11')
        assert s.pos == 15

    def test_bit_pos_after_findall(self):
        pass

    def test_bit_pos_after_insert(self):
        pass

    def test_bit_pos_after_overwrite(self):
        pass

    def test_bit_pos_after_replace(self):
        pass

    def test_read_list(self):
        a = BitStream('0x0123456789abcdef')
        
        vals = a.readlist('uint:4, uint:4, uint:24, uint:12, uint:12, uint:8')
        assert vals == [15, 14, 0x89abcd, 0x567, 0x234, 1]


class TestLsb0PackingUnpacking:

    @classmethod
    def setup_class(cls):
        bitstring.lsb0 = True

    @classmethod
    def teardown_class(cls):
        bitstring.lsb0 = False

    def test_bin(self):
        lsb0 = bitstring.pack('2*b4', '0b0000', '1111')
        assert lsb0 == '0b11110000'
        a, b = lsb0.unpack('2*h4')
        assert [a, b] == ['0', 'f']
        a, b = lsb0.unpack('2*bits4')
        assert [a, b] == ['0x0', '0xf']
        a, b = lsb0.unpack('2*bin4')
        assert [a, b] == ['0000', '1111']

    def test_float(self):
        lsb0 = bitstring.pack('2*bfloat', 0.5, 15)
        assert lsb0 == '0x4170 3f00'
        a, b = lsb0.unpack('2*bfloat')
        assert [a, b] == [0.5, 15]

    def test_simplest(self):
        lsb0 = bitstring.pack('uint:2', 1)
        assert lsb0.unpack('uint:2') == [1]
        lsb0 = bitstring.pack('0xab, 0xc')
        assert lsb0.unpack('hex8, hex4') == ['ab', 'c']

    def test_slightly_harder(self):
        lsb0 = bitstring.pack('float:32, hex', 0.25, 'ac')
        x = lsb0.unpack('float:32, hex')
        assert x == [0.25, 'ac']

    def test_more_complex(self):
        lsb0 = bitstring.pack('uint:10, hex, int:13, 0b11', 130, '3d', -23)
        x = lsb0.unpack('uint:10, hex, int:13, bin:2')
        assert x == [130, '3d', -23, '11']

    def test_golomb_codes(self):
        v = [10, 8, 6, 4, 100, -9]
        # Exp-Golomb codes can only be read in msb0 mode. So also doesn't
        # make sense for creation with pack
        with pytest.raises(bitstring.CreationError):
            _ = bitstring.pack('5*ue, sie', *v)
        # with self.assertRaises(bitstring.CreationError):
        #     _ = BitStream('ue=34')
        lsb0 = BitStream('0b0010010')
        with pytest.raises(bitstring.ReadError):
            _ = lsb0.unpack('5*ue, sie')
        with pytest.raises(bitstring.ReadError):
            _ = lsb0.read('ue')
        with pytest.raises(bitstring.ReadError):
            _ = lsb0.read('uie')
        with pytest.raises(bitstring.ReadError):
            _ = lsb0.read('se')
        with pytest.raises(bitstring.ReadError):
            _ = lsb0.read('sie')


class TestRepr:

    def test_without_pos(self):
        a = BitStream('0x12345', pos=0)
        assert repr(a) == "BitStream('0x12345')"

    def test_with_pos(self):
        a = BitStream('0b00111', pos=-1)
        assert a.pos == 4
        assert repr(a) == "BitStream('0b00111', pos=4)"


class TestFormat:

    def test_simple_format_strings(self):
        a = Bits('0xabc')
        s = f'{a}'
        assert s == '0xabc'
        a += '0b0'
        assert f'{a}' == '0b1010101111000'
        b = BitStream(10, pos=4)
        assert f'{b}' == '0b0000000000'
        c = BitStream(filename=os.path.join(THIS_DIR, 'test.m1v'))
        assert f'{c}'[0:10] == '0x000001b3'

    def test_format_strings_with_interpretation(self):
        a = Bits('0xf')
        assert f'{a.bin}' == '1111'


class TestCacheingIssues:

    def test_cache_with_offset(self):
        y = BitStream('0xdeadbeef1000')
        with pytest.raises(bitstring.CreationError):
            x = BitStream('0xdeadbeef1000', offset=8)

    def test_cache_with_pos(self):
        y = BitStream('0xdeadbeef1001', pos=3)
        assert y.pos == 3
        x = BitStream('0xdeadbeef1001', pos=5)
        assert x.pos == 5

    def test_cache_with_length(self):
        y = BitStream('0xdeadbeef002')
        with pytest.raises(bitstring.CreationError):
            x = BitStream('0xdeadbeef002', length=16)


def test_unpack_error():
    format_with_commas = ',bytes:2,,bytes:1,'
    dp = BitStream(hex='010203').unpack(fmt=format_with_commas)
    assert dp == [b'\x01\x02', b'\x03']


def test_add_pos_issue():
    x = BitStream()
    y = x + Bits('0xff')
    assert x.pos == 0
    assert y == '0xff'
    z = x + bitstring.BitArray('0xff')
    assert z == '0xff'
    q = x + ConstBitStream('0xff')
    assert q == '0xff'

    xx = ConstBitStream()
    yy = xx + Bits('0xff')
    zz = xx + bitstring.BitArray('0xff')
    qq = xx + BitStream('0xff')
    assert yy == zz == qq == '0xff'

