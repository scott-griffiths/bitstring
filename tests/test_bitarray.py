#!/usr/bin/env python
"""
Unit tests for the bitarray module.
"""

import pytest
import sys
import os
import bitarray
import bitstring
from bitstring import BitArray, Bits

sys.path.insert(0, '..')


class TestAll:
    def test_creation_from_uint(self):
        s = BitArray(uint=15, length=6)
        assert s.bin == '001111'
        s = BitArray(uint=0, length=1)
        assert s.bin == '0'
        s.u = 1
        assert s.uint == 1
        s = BitArray(length=8)
        s.uint = 0
        assert s.uint == 0
        s.u8 = 255
        assert s.uint == 255
        assert s.len == 8
        with pytest.raises(bitstring.CreationError):
            s.uint = 256
        with pytest.raises(bitstring.CreationError):
            s.uint = -1

    def test_creation_from_oct(self):
        s = BitArray(oct='7')
        assert s.oct == '7'
        assert s.bin == '111'
        s.append('0o1')
        assert s.bin == '111001'
        s.oct = '12345670'
        assert s.length == 24
        assert s.bin == '001010011100101110111000'
        s = BitArray('0o123')
        assert s.oct == '123'


class TestNoPosAttribute:
    def test_replace(self):
        s = BitArray('0b01')
        s.replace('0b1', '0b11')
        assert s == '0b011'

    def test_delete(self):
        s = BitArray('0b000000001')
        del s[-1:]
        assert s == '0b00000000'

    def test_insert(self):
        s = BitArray('0b00')
        s.insert('0xf', 1)
        assert s == '0b011110'

    def test_insert_self(self):
        b = BitArray('0b10')
        b.insert(b, 0)
        assert b == '0b1010'
        c = BitArray('0x00ff')
        c.insert(c, 8)
        assert c == '0x0000ffff'
        a = BitArray('0b11100')
        a.insert(a, 3)
        assert a == '0b1111110000'

    def test_no_bit_pos_for_insert(self):
        s = BitArray(100)
        with pytest.raises(TypeError):
            s.insert('0xabc')

    def test_insert_parameters(self):
        s = BitArray('0b111')
        with pytest.raises(TypeError):
            s.insert('0x4')

    def test_overwrite(self):
        s = BitArray('0b01110')
        s.overwrite('0b000', 1)
        assert s == '0b00000'

    def test_overwrite_no_pos(self):
        s = BitArray('0x01234')
        with pytest.raises(TypeError):
            s.overwrite('0xf')

    def test_overwrite_parameters(self):
        s = BitArray('0b0000')
        with pytest.raises(TypeError):
            s.overwrite('0b111')

    def test_prepend(self):
        s = BitArray('0b0')
        s.prepend([1])
        assert s == [1, 0]

    def test_rol(self):
        s = BitArray('0b0001')
        s.rol(1)
        assert s == '0b0010'

    def test_ror(self):
        s = BitArray('0b1000')
        s.ror(1)
        assert s == '0b0100'

    def test_set_item(self):
        s = BitArray('0b000100')
        s[4:5] = '0xf'
        assert s == '0b000111110'
        s[0:1] = [1]
        assert s == '0b100111110'
        s[5:5] = BitArray()
        assert s == '0b100111110'


class TestBugs:
    def test_adding_nonsense(self):
        a = BitArray([0])
        with pytest.raises(ValueError):
            a += '3'
        with pytest.raises(ValueError):
            a += 'se'
        with pytest.raises(ValueError):
            a += 'float:32'

    def test_prepend_after_creation_from_data_with_offset(self):
        s1 = BitArray(bytes=b'\x00\x00\x07\xff\xf0\x00', offset=21, length=15)
        assert not s1.any(0)
        b = s1.tobytes()
        assert b == b'\xff\xfe'
        s1.prepend('0b0')
        assert s1.bin == '0111111111111111'
        s1.prepend('0b0')
        assert s1.bin == '00111111111111111'


class TestByteAligned:

    def test_changing_it(self):
        bitstring.bytealigned = True
        assert bitstring.bytealigned
        bitstring.bytealigned = False
        assert not bitstring.bytealigned

    def test_not_byte_aligned(self):
        a = BitArray('0x00 ff 0f f')
        li = list(a.findall('0xff'))
        assert li == [8, 20]
        p = a.find('0x0f')[0]
        assert p == 4
        p = a.rfind('0xff')[0]
        assert p == 20
        s = list(a.split('0xff'))
        assert s == ['0x00', '0xff0', '0xff']
        a.replace('0xff', '')
        assert a == '0x000'

    def test_byte_aligned(self):
        bitstring.bytealigned = True
        a = BitArray('0x00 ff 0f f')
        li = list(a.findall('0xff'))
        assert li == [8]
        p = a.find('0x0f')[0]
        assert p == 16
        p = a.rfind('0xff')[0]
        assert p == 8
        s = list(a.split('0xff'))
        assert s == ['0x00', '0xff0ff']
        a.replace('0xff', '')
        assert a == '0x000ff'
        bitstring.bytealigned = False


class TestSliceAssignment:

    def test_slice_assignment_single_bit(self):
        a = BitArray('0b000')
        a[2] = '0b1'
        assert a.bin == '001'
        a[0] = BitArray(bin='1')
        assert a.bin == '101'
        a[-1] = '0b0'
        assert a.bin == '100'
        a[-3] = '0b0'
        assert a.bin == '000'

    def test_slice_assignment_single_bit_errors(self):
        a = BitArray('0b000')
        with pytest.raises(IndexError):
            a[-4] = '0b1'
        with pytest.raises(IndexError):
            a[3] = '0b1'
        with pytest.raises(TypeError):
            a[1] = 1.3

    def test_slice_assignment_muliple_bits(self):
        a = BitArray('0b0')
        a[0] = '0b110'
        assert a.bin3 == '110'
        a[0] = '0b000'
        assert a.bin5 == '00010'
        a[0:3] = '0b111'
        assert a.b5 == '11110'
        a[-2:] = '0b011'
        assert a.bin == '111011'
        a[:] = '0x12345'
        assert a.hex == '12345'
        a[:] = ''
        assert not a

    def test_slice_assignment_multiple_bits_errors(self):
        a = BitArray()
        with pytest.raises(IndexError):
            a[0] = '0b00'
        a += '0b1'
        a[0:2] = '0b11'
        assert a == '0b11'

    def test_del_slice_step(self):
        a = BitArray(bin='100111101001001110110100101')
        del a[::2]
        assert a.bin == '0110010101100'
        del a[3:9:3]
        assert a.bin == '01101101100'
        del a[2:7:1]
        assert a.bin == '011100'
        del a[::99]
        assert a.bin == '11100'
        del a[::1]
        assert a.bin == ''

    def test_del_slice_negative_step(self):
        a = BitArray('0b0001011101101100100110000001')
        del a[5:23:-3]
        assert a.bin == '0001011101101100100110000001'
        del a[25:3:-3]
        assert a.bin == '00011101010000100001'
        del a[:6:-7]
        assert a.bin == '000111010100010000'
        del a[15::-2]
        assert a.bin == '0010000000'
        del a[::-1]
        assert a.bin == ''

    def test_del_slice_negative_end(self):
        a = BitArray('0b01001000100001')
        del a[:-5]
        assert a == '0b00001'
        a = BitArray('0b01001000100001')
        del a[-11:-5]
        assert a == '0b01000001'

    def test_del_slice_errors(self):
        a = BitArray(10)
        del a[5:3]
        assert a == Bits(10)
        del a[3:5:-1]
        assert a == Bits(10)

    def test_del_single_element(self):
        a = BitArray('0b0010011')
        del a[-1]
        assert a.bin == '001001'
        del a[2]
        assert a.bin == '00001'
        with pytest.raises(IndexError):
            del a[5]

    def test_set_slice_step(self):
        a = BitArray(bin='0000000000')
        a[::2] = '0b11111'
        assert a.bin == '1010101010'
        a[4:9:3] = [0, 0]
        assert a.bin == '1010001010'
        a[7:3:-1] = [1, 1, 1, 0]
        assert a.bin == '1010011110'
        a[7:1:-2] = [0, 0, 1]
        assert a.b == '1011001010'
        a[::-5] = [1, 1]
        assert a.bin == '1011101011'
        a[::-1] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        assert a.bin == '1000000000'

    def test_set_slice_step_with_int(self):
        a = BitArray(9)
        a[5:8] = -1
        assert a.bin == '000001110'
        a[:] = 10
        assert a.bin == '000001010'
        a[::-1] = 10
        assert a.bin == '010100000'
        a[::2] = True
        assert a.bin == '111110101'

    def test_set_slice_errors(self):
        a = BitArray(8)
        with pytest.raises(ValueError):
            a[::3] = [1]

        class A(object):
            pass
        with pytest.raises(TypeError):
            a[1:2] = A()
        with pytest.raises(ValueError):
            a[1:4:-1] = [1, 2]


class TestSubclassing:

    def test_is_instance(self):
        class SubBits(BitArray):
            pass
        a = SubBits()
        assert isinstance(a, SubBits)

    def test_class_type(self):
        class SubBits(BitArray):
            pass
        assert SubBits().__class__ == SubBits


class TestClear:

    def test_clear(self):
        s = BitArray('0xfff')
        s.clear()
        assert s.len == 0


class TestCopy:

    def test_copy_method(self):
        s = BitArray(9)
        t = s.copy()
        assert s == t
        t[0] = True
        assert t.bin == '100000000'
        assert s.bin == '000000000'


class TestModifiedByAddingBug:

    def test_adding(self):
        a = BitArray.fromstring('0b0')
        b = BitArray('0b11')
        c = a + b
        assert c == '0b011'
        assert a == '0b0'
        assert b == '0b11'


class TestLsb0Setting:

    @classmethod
    def setup_class(cls):
        bitstring.lsb0 = True

    @classmethod
    def teardown_class(cls):
        bitstring.lsb0 = False

    def test_set_single_bit(self):
        a = BitArray(10)
        a[0] = True
        assert a == '0b0000000001'
        a[1] = True
        assert a == '0b0000000011'
        a[0] = False
        assert a == '0b0000000010'
        a[9] = True
        assert a == '0b1000000010'
        with pytest.raises(IndexError):
            a[10] = True

    def test_set_single_negative_bit(self):
        a = BitArray('0o000')
        a[-1] = True
        assert a == '0b100000000'
        a[-2] = True
        assert a == '0o600'
        a[-9] = True
        assert a == '0o601'
        with pytest.raises(IndexError):
            a[-10] = True

    def test_invert_bit(self):
        a = BitArray('0b11110000')
        a.invert()
        assert a == '0x0f'
        a.invert(0)
        assert a == '0b00001110'
        a.invert(-1)
        assert a == '0b10001110'

    def test_deleting_bits(self):
        a = BitArray('0b11110')
        del a[0]
        assert a == '0xf'

    def test_deleting_range(self):
        a = BitArray('0b101111000')
        del a[0:1]
        assert a == '0b10111100'
        del a[2:6]
        assert a == '0b1000'
        a = BitArray('0xabcdef')
        del a[:8]
        assert a == '0xabcd'
        del a[-4:]
        assert a == '0xbcd'
        del a[:-4]
        assert a == '0xb'

    def test_appending_bits(self):
        a = BitArray('0b111')
        a.append('0b000')
        assert a.bin == '000111'
        a += '0xabc'
        assert a == '0xabc, 0b000111'

    def test_setting_slice(self):
        a = BitArray('0x012345678')
        a[4:12] = '0xfe'
        assert a == '0x012345fe8'
        a[0:4] = '0xbeef'
        assert a == '0x012345febeef'

    def test_truncating_start(self):
        a = BitArray('0b1110000')
        a = a[4:]
        assert a == '0b111'

    def test_truncating_end(self):
        a = BitArray('0x123456')
        a = a[:16]
        assert a == '0x3456'

    def test_all(self):
        a = BitArray('0b0000101')
        assert a.all(1, [0, 2])
        assert a.all(False, [-1, -2, -3, -4])

        b = Bits(bytes=b'\x00\xff\xff', offset=7)
        assert b.all(1, [1, 2, 3, 4, 5, 6, 7])
        assert b.all(1, [-2, -3, -4, -5, -6, -7, -8])

    def test_any(self):
        a = BitArray('0b0001')
        assert a.any(1, [0, 1, 2])

    def test_endswith(self):
        a = BitArray('0xdeadbeef')
        assert a.endswith('0xdead')

    def test_startswith(self):
        a = BitArray('0xdeadbeef')
        assert a.startswith('0xbeef')

    def test_cut(self):
        a = BitArray('0xff00ff1111ff2222')
        li = list(a.cut(16))
        assert li == ['0x2222', '0x11ff', '0xff11', '0xff00']

    def test_find(self):
        t = BitArray('0b10')
        p, = t.find('0b1')
        assert p == 1
        t = BitArray('0b1010')
        p, = t.find('0b1')
        assert p == 1
        a = BitArray('0b10101010, 0xabcd, 0b10101010, 0x0')
        p, = a.find('0b10101010', bytealigned=False)
        assert p == 4
        p, = a.find('0b10101010', start=4, bytealigned=False)
        assert p == 4
        p, = a.find('0b10101010', start=5, bytealigned=False)
        assert p == 22

    def test_find_failing(self):
        a = BitArray()
        p = a.find('0b1')
        assert p == ()
        a = BitArray('0b11111111111011')
        p = a.find('0b100')
        assert not p

    def test_find_failing2(self):
        s = BitArray('0b101')
        p, = s.find('0b1', start=2)
        assert p == 2

    def test_rfind(self):
        a = BitArray('0b1000000')
        p = a.rfind('0b1')
        assert p == (6,)
        p = a.rfind('0b000')
        assert p == (3,)

    def test_rfind_with_start_and_end(self):
        a = BitArray('0b11 0000 11 00')
        p = a.rfind('0b11', start=8)
        assert p[0] == 8
        p = a.rfind('0b110', start=8)
        assert p == ()
        p = a.rfind('0b11', end=-1)
        assert p[0] == 2

    def test_findall(self):
        a = BitArray('0b001000100001')
        b = list(a.findall('0b1'))
        assert b == [0, 5, 9]
        c = list(a.findall('0b0001'))
        assert c == [0, 5]
        d = list(a.findall('0b10'))
        assert d == [4, 8]
        e = list(a.findall('0x198273641234'))
        assert e == []

    def test_find_all_with_start_and_end(self):
        a = BitArray('0xaabbccaabbccccbb')
        b = list(a.findall('0xbb', start=0, end=8))
        assert b == [0]
        b = list(a.findall('0xbb', start=1, end=8))
        assert b == []
        b = list(a.findall('0xbb', start=0, end=7))
        assert b == []
        b = list(a.findall('0xbb', start=48))
        assert b == [48]
        b = list(a.findall('0xbb', start=47))
        assert b == [48]
        b = list(a.findall('0xbb', start=49))
        assert b == []

    def test_find_all_byte_aligned(self):
        a = BitArray('0x0550550')
        b = list(a.findall('0x55', bytealigned=True))
        assert b == [16]

    def test_find_all_with_count(self):
        a = BitArray('0b0001111101')
        b = list(a.findall([1], start=1, count=1))
        assert b == [2]

    def test_split(self):
        a = BitArray('0x4700004711472222')
        li = list(a.split('0x47', bytealigned=True))
        assert li == ['', '0x472222', '0x4711', '0x470000']

    def test_byte_swap(self):
        a = BitArray('0xaa00ff00ff00')
        n = a.byteswap(2, end=32, repeat=True)
        assert n == 2
        assert a == '0xaa0000ff00ff'

    def test_insert(self):
        a = BitArray('0x0123456')
        a.insert('0xf', 4)
        assert a == '0x012345f6'

    def test_overwrite(self):
        a = BitArray('0x00000000')
        a.overwrite('0xdead', 4)
        assert a == '0x000dead0'

    def test_replace(self):
        a = BitArray('0x5551100')
        n = a.replace('0x1', '0xabc')
        assert n == 2
        assert a == '0x555abcabc00'
        n = a.replace([1], [0], end=12)
        assert n == 2
        assert a == '0x555abcab000'

    def test_reverse(self):
        a = BitArray('0x0011223344')
        a.reverse()
        assert a == '0x22cc448800'
        a.reverse(0, 16)
        assert a == '0x22cc440011'

    def test_ror(self):
        a = BitArray('0b111000')
        a.ror(1)
        assert a == '0b011100'
        a = BitArray('0b111000')
        a.ror(1, start=2, end=6)
        assert a == '0b011100'

    def test_rol(self):
        a = BitArray('0b1')
        a.rol(12)
        assert a == '0b1'
        b = BitArray('0b000010')
        b.rol(3)
        assert b == '0b010000'

    def test_set(self):
        a = BitArray(100)
        a.set(1, [0, 2, 4])
        assert a[0]
        assert a.startswith('0b000010101')
        a = BitArray('0b111')
        a.set(False, 0)
        assert a == '0b110'

    def test_failing_repr(self):
        a = BitArray('0b010')
        a.find('0b1')
        assert repr(a) == "BitArray('0b010')"

    def test_left_shift(self):
        a = BitArray('0b11001')
        assert (a << 1).b == '10010'
        assert (a << 5).b == '00000'
        assert (a << 0).b == '11001'

    def test_right_shift(self):
        a = BitArray('0b11001')
        assert (a >> 1).b == '01100'
        assert (a >> 5).b == '00000'
        assert (a >> 0).b == '11001'

    # def testConstFileBased(self):
    #     filename = os.path.join(THIS_DIR, 'test.m1v')
    #     a = Bits(filename=filename, offset=8)
    #     self.assertTrue(a[-8])
    #     self.assertTrue(a.endswith('0x01b3'))


class TestRepr:

    def test_standard_repr(self):
        a = BitArray('0o12345')
        assert repr(a) == "BitArray('0b001010011100101')"


class TestNewProperties:

    def test_aliases(self):
        a = BitArray('0x1234567890ab')
        assert a.oct == a.o
        assert a.hex == a.h
        assert a.bin == a.b
        assert a[:32].float == a[:32].f
        assert a.int == a.i
        assert a.uint == a.u

    def test_aliases_with_lengths(self):
        a = BitArray('0x123')
        h = a.h12
        assert h == '123'
        b = a.b12
        assert b == '000100100011'
        o = a.o12
        assert o == '0443'
        u = a.u12
        assert u == a.u
        i = a.i12
        assert i == a.i
        x = BitArray('0x12345678')
        f = x.f32
        assert f == x.f

    def test_assignments(self):
        a = BitArray()
        a.f64 = 0.5
        assert a.f64 == 0.5
        a.u88 = 1244322
        assert a.u88 == 1244322
        a.i3 = -3
        assert a.i3 == -3
        a.h16 = '0x1234'
        assert a.h16 == '1234'
        a.o9 = '0o765'
        assert a.o9 == '765'
        a.b7 = '0b0001110'
        assert a.b7 == '0001110'

    def test_assignments_without_length(self):
        a = BitArray(64)
        a.f = 1234.5
        assert a.float == 1234.5
        assert a.len == 64
        a.u = 99
        assert a.uint == 99
        assert a.len == 64
        a.i = -999
        assert a.int == -999
        assert a.len == 64
        a.h = 'feedbeef'
        assert a.hex == 'feedbeef'
        a.o = '1234567'
        assert a.oct == '1234567'
        a.b = '001'
        assert a.bin == '001'

    def test_getter_length_errors(self):
        a = BitArray('0x123')
        with pytest.raises(bitstring.InterpretError):
            _ = a.h16
        with pytest.raises(bitstring.InterpretError):
            _ = a.b3317777766
        with pytest.raises(AttributeError):
            _ = a.o2
        with pytest.raises(bitstring.InterpretError):
            _ = a.f
        with pytest.raises(bitstring.InterpretError):
            _ = a.f32
        with pytest.raises(bitstring.InterpretError):
            _ = a.u13
        with pytest.raises(bitstring.InterpretError):
            _ = a.i1
        b = BitArray()
        with pytest.raises(bitstring.InterpretError):
            _ = b.u0

    def test_setter_length_errors(self):
        a = BitArray()
        a.u8 = 255
        assert a.len == 8
        with pytest.raises(ValueError):
            a.u8 = 256
        a.f32 = 10
        a.f64 = 10
        with pytest.raises(ValueError):
            a.f256 = 10
        with pytest.raises(bitstring.CreationError):
            a.u0 = 2
        with pytest.raises(bitstring.CreationError):
            a.hex4 = '0xab'
        assert len(a) == 64
        with pytest.raises(bitstring.CreationError):
            a.o3 = '0xab'
        with pytest.raises(bitstring.CreationError):
            a.b4 = '0xab'
        a.h0 = ''
        assert a.len == 0
        a.i8 = 127
        a.i8 = -128
        with pytest.raises(ValueError):
            a.i8 = 128
        with pytest.raises(ValueError):
            a.i8 = -129
        with pytest.raises(bitstring.CreationError):
            a.froggy16 = '0xabc'

    def test_unpack(self):
        a = BitArray('0xff160120')
        b = a.unpack('h8,2*u12')
        assert b == ['ff', 352, 288]

    def test_reading(self):
        a = bitstring.BitStream.fromstring('0x01ff')
        b = a.read('u8')
        assert b == 1
        assert a.pos == 8
        assert a.read('i') == -1

    def test_longer_more_general_names(self):
        a = BitArray()
        a.f64 = 0.0
        assert a.float64 == 0.0
        a.float32 = 10.5
        assert a.f32 == 10.5

    def test_bytes_properties(self):
        a = BitArray()
        a.bytes = b'hello'
        assert a.bytes5 == b'hello'
        a.bytes3 = b'123'
        assert a.bytes == b'123'
        with pytest.raises(bitstring.CreationError):
            a.bytes5 = b'123456789'
        with pytest.raises(bitstring.CreationError):
            a.bytes5 = b'123'

    def test_conversion_to_bytes(self):
        a = BitArray(bytes=b'1234')
        b = bytes(a)
        assert b == b'1234'
        a += [1]
        assert bytes(a) == b'1234\x80'
        a = BitArray()
        assert bytes(a) == b''


class TestBFloats:

    def test_creation(self):
        a = BitArray('bfloat=100.5')
        assert a.unpack('bfloat')[0] == 100.5
        b = BitArray(bfloat=20.25)
        assert b.bfloat == 20.25
        b.bfloat = -30.5
        assert b.bfloat == -30.5
        assert len(b) == 16
        fs = [0.0, -6.1, 1.52e35, 0.000001]
        a = bitstring.pack('4*bfloat', *fs)
        fsp = a.unpack('4*bfloat')
        assert len(a) == len(fs)*16
        for f, fp in zip(fs, fsp):
            assert f == pytest.approx(fp, abs=abs(f/100))
        a = BitArray(bfloat=13)
        assert a.bfloat == 13
        c = BitArray()
        with pytest.raises(ValueError):
            _ = c.bfloat


    def test_creation_errors(self):
        a = BitArray(bfloat=-0.25, length=16)
        assert len(a) == 16
        with pytest.raises(bitstring.CreationError):
            _ = BitArray(bfloat=10, length=15)
        with pytest.raises(bitstring.CreationError):
            _ = BitArray('bfloat:1=0.5')

    def test_little_endian(self):
        a = BitArray.fromstring('f32=1000')
        b = BitArray(bfloat=a.f)
        assert a[0:16] == b[0:16]

        a = BitArray('floatle:32=1000')
        b = BitArray(bfloatle=1000)
        assert a[16:32] == b
        assert b.bfloatle == 1000.0
        b.byteswap()
        assert b.bfloat == 1000.0
        assert b.bfloatbe == 1000.0

        with pytest.raises(bitstring.CreationError):
            _ = BitArray(bfloatle=-5, length=15)
        c = BitArray()
        with pytest.raises(bitstring.InterpretError):
            _ = c.bfloatle
        with pytest.raises(bitstring.InterpretError):
            _ = c.bfloatne

    def test_more_creation(self):
        a = BitArray('bfloat:16=1.0, bfloat16=2.0, bfloat=3.0')
        x, y, z = a.unpack('3*bfloat16')
        assert (x, y, z) == (1.0, 2.0, 3.0)

    def test_interpret_bug(self):
        a = BitArray(100)
        with pytest.raises(bitstring.InterpretError):
            v = a.bfloat

    def test_overflows(self):
        s = BitArray()
        inf16 = BitArray(float=float('inf'), length=16)
        inf32 = BitArray(float=float('inf'), length=32)
        inf64 = BitArray(float=float('inf'), length=64)
        infbfloat = BitArray(bfloat=float('inf'))
        
        s.f64 = 1e400
        assert s == inf64
        s.f32 = 1e60
        assert s == inf32
        s.f16 = 100000
        assert s == inf16
        s.bfloat = 1e60
        assert s == infbfloat

        ninf16 = BitArray(float=float('-inf'), length=16)
        ninf32 = BitArray(float=float('-inf'), length=32)
        ninf64 = BitArray(float=float('-inf'), length=64)
        ninfbfloat = BitArray(bfloat=float('-inf'))

        s.f64 = -1e400
        assert s == ninf64
        s.f32 = -1e60
        assert s == ninf32
        s.f16 = -100000
        assert s == ninf16
        s.bfloat = -1e60
        assert s == ninfbfloat

    def test_big_endian_string_initialisers(self):
        a = BitArray('bfloatbe=4.5')
        b = BitArray('bfloatbe:16=-2.25')
        assert a.bfloatbe == 4.5
        assert b.bfloatbe == -2.25

    def test_litte_endian_string_initialisers(self):
        a = BitArray('bfloatle=4.5')
        b = BitArray('bfloatle:16=-2.25')
        assert a.bfloatle == 4.5
        assert b.bfloatle == -2.25

    def test_native_endian_string_initialisers(self):
        a = BitArray('bfloatne=4.5')
        b = BitArray('bfloatne:16=-2.25')
        assert a.bfloatne == 4.5
        assert b.bfloatne == -2.25



THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class TestBitarray:

    def teardown_method(self) -> None:
        bitstring.lsb0 = False

    def test_to_bitarray(self):
        a = BitArray('0xff, 0b0')
        b = a.tobitarray()
        assert type(b) == bitarray.bitarray
        assert b == bitarray.bitarray('111111110')

    def test_to_bitarray_lsb0(self):
        bitstring.lsb0 = True
        a = bitstring.Bits('0xff, 0b0')
        b = a.tobitarray()
        assert type(b) == bitarray.bitarray
        assert b == bitarray.bitarray('111111110')

    def test_from_file(self):
        a = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        b = a.tobitarray()
        assert a.bin == b.to01()

    def test_with_offset(self):
        a = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        b = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'), offset=11)
        assert len(a) == len(b) + 11
        assert a[11:].tobitarray() == b.tobitarray()

    def test_with_length(self):
        a = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        b = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'), length=11)
        assert len(b) == 11
        assert a[:11].tobitarray() == b.tobitarray()

    def test_with_offset_and_length(self):
        a = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        b = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'), offset=17, length=7)
        assert len(b) == 7
        assert a[17:24].tobitarray() == b.tobitarray()


try:
    import numpy as np
    numpy_installed = True
except ImportError:
    numpy_installed = False


class TestNumpy:

    @pytest.mark.skipif(not numpy_installed, reason="numpy not installed.")
    def test_getting(self):
        a = BitArray('0b110')
        p = np.int_(1)
        assert a[p] is True
        p = np.short(0)
        assert a[p] is True

    @pytest.mark.skipif(not numpy_installed, reason="numpy not installed.")
    def test_setting(self):
        a = BitArray('0b110')
        p = np.int_(1)
        a[p] = '0b1111'
        assert a == '0b111110'

    @pytest.mark.skipif(not numpy_installed, reason="numpy not installed.")
    def test_creation(self):
        a = BitArray(np.longlong(12))
        assert a.hex == '000'


def test_bytes_from_list():
    s = Bits(bytes=[1, 2])
    assert s == '0x0102'
    s = Bits(bytes=bytearray([1, 2]))
    assert s == '0x0102'
    s = BitArray(bytes=[1, 2])
    assert s == '0x0102'
    s = BitArray(bytes=bytearray([1, 2]))
    assert s == '0x0102'
    s.bytes = [10, 20]
    assert s == '0x0a14'
