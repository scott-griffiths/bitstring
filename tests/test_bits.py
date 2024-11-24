#!/usr/bin/env python
import pytest
import io
import sys
import bitarray
import bitstring
import array
import os
import re
from bitstring import InterpretError, Bits, BitArray
from hypothesis import given, assume, reproduce_failure, settings
import hypothesis.strategies as st
from bitstring.bitstore import offset_slice_indices_lsb0

sys.path.insert(0, '..')

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def remove_unprintable(s: str) -> str:
    colour_escape = re.compile(r'(?:\x1B[@-_])[0-?]*[ -/]*[@-~]')
    return colour_escape.sub('', s)


@settings(max_examples=500)
@given(length=st.integers(0, 9),
       start=st.integers(-20, 20),
       stop=st.integers(-20, 20),
       step=st.integers(0, 7))
def test_lsb0_slicing(length, start, stop, step):
    if start == -20:
        start = None
    if stop == -20:
        stop = None
    if step == 0:
        step = None
    values_fwd = list(range(0, length))
    values_bwd = list(range(0, length))
    values_bwd.reverse()

    # Convert the start, stop, step to a range over the length
    start1, stop1, step1 = slice(start, stop, step).indices(length)
    values1 = values_fwd[start1:stop1:step1]

    lsb0key = offset_slice_indices_lsb0(slice(start, stop, step), length)
    values2 = values_bwd[lsb0key.start:lsb0key.stop:lsb0key.step]
    values2.reverse()
    assert values1 == values2


class TestCreation:
    def test_creation_from_bytes(self):
        s = Bits(bytes=b'\xa0\xff')
        assert (s.len, s.hex) == (16, 'a0ff')
        s = Bits(bytes=b'abc', length=0)
        assert s == ''

    @given(st.binary())
    def test_creation_from_bytes_roundtrip(self, data):
        s = Bits(bytes=data)
        assert s.bytes == data

    def test_creation_from_bytes_errors(self):
        with pytest.raises(bitstring.CreationError):
            Bits(bytes=b'abc', length=25)

    def test_creation_from_data_with_offset(self):
        s1 = Bits(bytes=b'\x0b\x1c\x2f', offset=0, length=20)
        s2 = Bits(bytes=b'\xa0\xb1\xC2', offset=4)
        assert (s2.len, s2.hex) == (20, '0b1c2')
        assert (s1.len, s1.hex) == (20, '0b1c2')
        assert s1 == s2

    def test_creation_from_hex(self):
        s = Bits(hex='0xA0ff')
        assert (s.len, s.hex) == (16, 'a0ff')
        s = Bits(hex='0x0x0X')
        assert (s.length, s.hex) == (0, '')

    def test_creation_from_hex_with_whitespace(self):
        s = Bits(hex='  \n0 X a  4e       \r3  \n')
        assert s.hex == 'a4e3'

    @pytest.mark.parametrize("bad_val", ['0xx0', '0xX0', '0Xx0', '-2e'])
    def test_creation_from_hex_errors(self, bad_val: str):
        with pytest.raises(bitstring.CreationError):
            Bits(hex=bad_val)
        with pytest.raises(bitstring.CreationError):
            Bits('0x2', length=2)
        with pytest.raises(bitstring.CreationError):
            Bits('0x3', offset=1)

    def test_creation_from_bin(self):
        s = Bits(bin='1010000011111111')
        assert (s.length, s.hex) == (16, 'a0ff')
        s = Bits(bin='00')[:1]
        assert s.bin == '0'
        s = Bits(bin=' 0000 \n 0001\r ')
        assert s.bin == '00000001'

    def test_creation_from_bin_with_whitespace(self):
        s = Bits(bin='  \r\r\n0   B    00   1 1 \t0 ')
        assert s.bin == '00110'

    def test_creation_from_oct_errors(self):
        s = Bits('0b00011')
        with pytest.raises(bitstring.InterpretError):
            _ = s.oct
        with pytest.raises(bitstring.CreationError):
            _ = Bits('oct=8')

    def test_creation_from_uint_with_offset(self):
        with pytest.raises(bitstring.CreationError):
            Bits(uint=12, length=8, offset=1)

    def test_creation_from_uint_errors(self):
        with pytest.raises(bitstring.CreationError):
            Bits(uint=-1, length=10)
        with pytest.raises(bitstring.CreationError):
            Bits(uint=12)
        with pytest.raises(bitstring.CreationError):
            Bits(uint=4, length=2)
        with pytest.raises(bitstring.CreationError):
            Bits(uint=0, length=0)
        with pytest.raises(bitstring.CreationError):
            Bits(uint=12, length=-12)

    def test_creation_from_int(self):
        s = Bits(int=0, length=4)
        assert s.bin == '0000'
        s = Bits(int=1, length=2)
        assert s.bin == '01'
        s = Bits(int=-1, length=11)
        assert s.bin == '11111111111'
        s = Bits(int=12, length=7)
        assert s.int == 12
        s = Bits(int=-243, length=108)
        assert (s.int, s.length) == (-243, 108)
        for length in range(6, 10):
            for value in range(-17, 17):
                s = Bits(int=value, length=length)
                assert (s.int, s.length) == (value, length)
        _ = Bits(int=10, length=8)

    @pytest.mark.parametrize("int_, length", [[-1, 0], [12, None], [4, 3], [-5, 3]])
    def test_creation_from_int_errors(self, int_, length):
        with pytest.raises(bitstring.CreationError):
            _ = Bits(int=int_, length=length)

    def test_creation_from_se(self):
        for i in range(-100, 10):
            s = Bits(se=i)
            assert s.se == i
        with pytest.raises(bitstring.CreationError):
            _ = Bits(se=10, length=40)

    def test_creation_from_se_with_offset(self):
        with pytest.raises(bitstring.CreationError):
            Bits(se=-13, offset=1)

    def test_creation_from_se_errors(self):
        with pytest.raises(bitstring.CreationError):
            Bits(se=-5, length=33)
        with pytest.raises(bitstring.CreationError):
            Bits('se2=0')
        s = Bits(bin='001000')
        with pytest.raises(bitstring.InterpretError):
            _ = s.se

    def test_creation_from_ue(self):
        for i in range(0, 20):
            assert Bits(ue=i).ue == i

    def test_creation_from_ue_with_offset(self):
        with pytest.raises(bitstring.CreationError):
            Bits(ue=104, offset=2)

    def test_creation_from_ue_errors(self):
        with pytest.raises(bitstring.CreationError):
            Bits(ue=-1)
        with pytest.raises(bitstring.CreationError):
            Bits(ue=1, length=12)
        s = Bits(bin='10')
        with pytest.raises(bitstring.InterpretError):
            _ = s.ue

    def test_creation_from_bool(self):
        a = Bits('bool=1')
        assert a == 'bool=1'
        b = Bits('bool:1=0')
        assert b == [0]
        c = bitstring.pack('bool=1, 2*bool', 0, 1)
        assert c == '0b101'
        d = bitstring.pack('bool:1=1, 2*bool1', 1, 0)
        assert d == '0b110'

    def test_creation_from_bool_errors(self):
        with pytest.raises(ValueError):
            _ = Bits('bool=3')
        with pytest.raises(bitstring.CreationError):
            _ = Bits(bool=0, length=2)

    def test_creation_keyword_error(self):
        with pytest.raises(bitstring.CreationError):
            Bits(squirrel=5)

    def test_creation_from_bitarray(self):
        ba = bitarray.bitarray('0010')
        bs = Bits(ba)
        assert bs.bin == '0010'
        bs2 = Bits(bitarray=ba)
        assert bs2.bin == '0010'

    def test_creation_from_frozen_bitarray(self):
        fba = bitarray.frozenbitarray('111100001')
        ba = Bits(fba)
        assert ba.bin == '111100001'
        bs2 = Bits(bitarray=fba)
        assert bs2.bin == '111100001'
        bs3 = Bits(bitarray=fba, offset=4)
        assert bs3.bin == '00001'
        bs3 = Bits(bitarray=fba, offset=4, length=4)
        assert bs3.bin == '0000'

    def test_creation_from_bitarray_errors(self):
        ba = bitarray.bitarray('0101')
        with pytest.raises(bitstring.CreationError):
            _ = Bits(bitarray=ba, length=5)
        with pytest.raises(bitstring.CreationError):
            _ = Bits(bitarray=ba, offset=5)
        with pytest.raises(bitstring.CreationError):
            _ = Bits(ba, length=-1)

    def test_creation_from_memoryview(self):
        x = bytes(bytearray(range(20)))
        m = memoryview(x[10:15])
        b = Bits(m)
        assert b.unpack('5*u8') == [10, 11, 12, 13, 14]


class TestInitialisation:
    def test_empty_init(self):
        a = Bits()
        assert a == ''

    def test_no_pos(self):
        a = Bits('0xabcdef')
        with pytest.raises(AttributeError):
            _ = a.pos

    def test_find(self):
        a = Bits('0xabcd')
        r = a.find('0xbc')
        assert r[0] == 4
        r = a.find('0x23462346246', bytealigned=True)
        assert not r

    def test_rfind(self):
        a = Bits('0b11101010010010')
        b = a.rfind('0b010')
        assert b[0] == 11

    def test_find_all(self):
        a = Bits('0b0010011')
        b = list(a.findall([1]))
        assert b == [2, 5, 6]
        t = BitArray('0b10')
        tp = list(t.findall('0b1'))
        assert tp == [0]


class TestCut:
    def test_cut(self):
        s = Bits('0b000111'*10)
        for t in s.cut(6):
            assert t.bin == '000111'


class TestInterleavedExpGolomb:
    def test_creation(self):
        s1 = Bits(uie=0)
        s2 = Bits(uie=1)
        assert s1 == [1]
        assert s2 == [0, 0, 1]
        s1 = Bits(sie=0)
        s2 = Bits(sie=-1)
        s3 = Bits(sie=1)
        assert s1 == [1]
        assert s2 == [0, 0, 1, 1]
        assert s3 == [0, 0, 1, 0]

    def test_creation_from_property(self):
        s = BitArray()
        s.uie = 45
        assert s.uie == 45
        s.sie = -45
        assert s.sie == -45

    def test_interpretation(self):
        for x in range(101):
            assert Bits(uie=x).uie == x
        for x in range(-100, 100):
            assert Bits(sie=x).sie == x

    def test_errors(self):
        for f in ['sie=100, 0b1001', '0b00', 'uie=100, 0b1001']:
            s = Bits.fromstring(f)
            with pytest.raises(bitstring.InterpretError):
                _ = s.sie
            with pytest.raises(bitstring.InterpretError):
                _ = s.uie
        with pytest.raises(ValueError):
            Bits(uie=-10)


class TestFileBased:
    def setup_method(self):
        filename = os.path.join(THIS_DIR, 'smalltestfile')
        self.a = Bits(filename=filename)
        self.b = Bits(filename=filename, offset=16)
        self.c = Bits(filename=filename, offset=20, length=16)
        self.d = Bits(filename=filename, offset=20, length=4)

    def test_creation_with_offset(self):
        assert str(self.a) == '0x0123456789abcdef'
        assert str(self.b) == '0x456789abcdef'
        assert str(self.c) == '0x5678'

    def test_bit_operators(self):
        x = self.b[4:20]
        assert x == '0x5678'
        assert (x & self.c).hex == self.c.hex
        assert self.c ^ self.b[4:20] == Bits(16)
        assert self.a[23:36] | self.c[3:] == self.c[3:]
        y = x & self.b[4:20]
        assert y == self.c
        assert repr(y) == repr(self.c)

    def test_addition(self):
        _ = self.d + '0x1'
        x = self.a[20:24] + self.c[-4:] + self.c[8:12]
        assert x == '0x587'
        x = self.b + x
        assert x.h == '456789abcdef587'
        x = BitArray(x)
        del x[12:24]
        assert x == '0x456abcdef587'


class TestComparisons:
    def test_unorderable(self):
        a = Bits(5)
        b = Bits(5)
        with pytest.raises(TypeError):
            _ = a < b
        with pytest.raises(TypeError):
            _ = a > b
        with pytest.raises(TypeError):
            _ = a <= b
        with pytest.raises(TypeError):
            _ = a >= b


class TestSubclassing:

    def test_is_instance(self):
        class SubBits(bitstring.Bits):
            pass
        a = SubBits()
        assert isinstance(a, SubBits)

    def test_class_type(self):
        class SubBits(bitstring.Bits):
            pass
        assert SubBits().__class__ == SubBits


class TestLongBoolConversion:

    def test_long_bool(self):
        a = Bits(1000)
        b = bool(a)
        assert b is True


class TestPadToken:

    def test_creation(self):
        a = Bits.fromstring('pad:10')
        assert a == Bits(10)
        b = Bits('pad:0')
        assert b == Bits()
        c = Bits('0b11, pad:1, 0b111')
        assert c == Bits('0b110111')

    def test_pack(self):
        s = bitstring.pack('0b11, pad:3, 0b1')
        assert s.bin == '110001'
        d = bitstring.pack('pad:c', c=12)
        assert d == Bits(12)
        e = bitstring.pack('0xf, uint12, pad:1, bin, pad4, 0b10', 0, '111')
        assert e.bin == '11110000000000000111000010'

    def test_unpack(self):
        s = Bits('0b111000111')
        x, y = s.unpack('3, pad:3, 3')
        assert (x, y.u) == ('0b111', 7)
        x, y = s.unpack('2, pad2, bin')
        assert (x.u2, y) == (3, '00111')
        x = s.unpack('pad:1, pad:2, pad:3')
        assert x == []

    def test_unpack_bug(self):
        t = Bits('0o755, ue=12, int3=-1')
        a, b = t.unpack('pad:9, ue, int3')
        assert (a, b) == (12, -1)


class TestModifiedByAddingBug:

    def test_adding(self):
        a = Bits('0b0')
        b = Bits('0b11')
        c = a + b
        assert c == '0b011'
        assert a == '0b0'
        assert b == '0b11'

    def test_adding2(self):
        a = Bits(100)
        b = Bits(101)
        c = a + b
        assert a == Bits(100)
        assert b == Bits(101)
        assert c == Bits(201)


class TestWrongTypeBug:

    def test_append_to_bits(self):
        a = Bits(BitArray())
        with pytest.raises(AttributeError):
            a.append('0b1')
        assert type(a) == Bits
        b = bitstring.ConstBitStream(bitstring.BitStream())
        assert type(b) == bitstring.ConstBitStream


class TestInitFromArray:

    @given(st.sampled_from(['B', 'H', 'I', 'L', 'Q', 'f', 'd']))
    def test_empty_array(self, t):
        a = array.array(t)
        b = Bits(a)
        assert b.length == 0

    def test_single_byte(self):
        a = array.array('B', b'\xff')
        b = Bits(a)
        assert b.length == 8
        assert b.hex == 'ff'

    def test_signed_short(self):
        a = array.array('h')
        a.append(10)
        a.append(-1)
        b = Bits(a)
        assert b.length == 32
        assert b.bytes == a.tobytes()

    def test_double(self):
        a = array.array('d', [0.0, 1.0, 2.5])
        b = Bits(a)
        assert b.length == 192
        c, d, e = b.unpack('3*floatne:64')
        assert (c, d, e) == (0.0, 1.0, 2.5)


class TestIteration:

    def test_iterate_empty_bits(self):
        assert list(Bits([])) == []
        assert list(Bits([1, 0])[1:1]) == []

    def test_iterate_non_empty_bits(self):
        assert list(Bits([1, 0])) == [True, False]
        assert list(Bits([1, 0, 0, 1])[1:3]) == [False, False]

    def test_iterate_long_bits(self):
        assert list(Bits([1, 0]) * 1024) == \
            [True, False] * 1024

        
class TestContainsBug:

    def test_contains(self):
        a = Bits('0b1, 0x0001dead0001')
        assert '0xdead' in a
        assert not '0xfeed' in a

        assert '0b1' in Bits('0xf')
        assert not '0b0' in Bits('0xf')


class TestByteStoreImmutablity:

    def test_immutability_bug_append(self):
        a = Bits('0b111')
        b = a + '0b000'
        c = BitArray(b)
        c[1] = 0
        assert c.bin == '101000'
        assert a.b3 == '111'
        assert b.bin == '111000'

    def test_immutability_bug_prepend(self):
        a = Bits('0b111')
        b = '0b000' + a
        c = BitArray(b)
        c[1] = 1
        assert b.bin == '000111'
        assert c.bin == '010111'


class TestLsb0Indexing:

    @classmethod
    def setup_class(cls):
        bitstring.lsb0 = True

    @classmethod
    def teardown_class(cls):
        bitstring.lsb0 = False

    def test_get_single_bit(self):
        a = Bits('0b000001111')
        assert a[0] is True
        assert a[3] is True
        assert a[4] is False
        assert a[8] is False
        with pytest.raises(IndexError):
            _ = a[9]
        assert a[-1] is False
        assert a[-5] is False
        assert a[-6] is True
        assert a[-9] is True
        with pytest.raises(IndexError):
            _ = a[-10]

    def test_simple_slicing(self):
        a = Bits('0xabcdef')
        assert a[0:4] == '0xf'
        assert a[4:8] == '0xe'
        assert a[:] == '0xabcdef'
        assert a[4:] == '0xabcde'
        assert a[-4:] == '0xa'
        assert a[-8:-4] == '0xb'
        assert a[:-8] == '0xcdef'

    def test_extended_slicing(self):
        a = Bits('0b0100000100100100')
        assert a[2::3] == '0b10111'

    def test_all(self):
        a = Bits('0b000111')
        assert a.all(1, [0, 1, 2])
        assert a.all(0, [3, 4, 5])

    def test_any(self):
        a = Bits('0b00000110')
        assert a.any(1, [0, 1])
        assert a.any(0, [5, 6])

    def test_startswith(self):
        a = Bits('0b0000000111')
        assert a.startswith('0b111')
        assert not a.startswith('0b0')
        assert a.startswith('0b011', start=1)
        assert not a.startswith('0b0111', end=3)
        assert a.startswith('0b0111', end=4)

    def test_ends_with(self):
        a = Bits('0x1234abcd')
        assert a.endswith('0x123')
        assert not a.endswith('0xabcd')

    def test_lsb0_slicing_error(self):
        a = Bits('0b01')
        b = a[::-1]
        assert b == '0b10'
        t = Bits('0xf0a')[::-1]
        assert t == '0x50f'
        s = Bits('0xf0a')[::-1][::-1]
        assert s == '0xf0a'


class TestLsb0Interpretations:

    @classmethod
    def setup_class(cls):
        bitstring.lsb0 = True

    @classmethod
    def teardown_class(cls):
        bitstring.lsb0 = False

    def test_uint(self):
        a = Bits('0x01')
        assert a == '0b00000001'
        assert a.uint == 1
        assert a[0] is True

    def test_float(self):
        a = Bits(float=0.25, length=32)
        try:
            bitstring.lsb0 = False
            b = Bits(float=0.25, length=32)
        finally:
            bitstring.lsb0 = True
        assert a.float == 0.25
        assert b.float == 0.25
        assert a.bin == b.bin

    def test_golomb(self):
        with pytest.raises(bitstring.CreationError):
            _ = Bits(ue=2)
        with pytest.raises(bitstring.CreationError):
            _ = Bits(se=2)
        with pytest.raises(bitstring.CreationError):
            _ = Bits(uie=2)
        with pytest.raises(bitstring.CreationError):
            _ = Bits(sie=2)

    def test_bytes(self):
        a = Bits.fromstring('0xabcdef')
        b = a.bytes
        assert b == b'\xab\xcd\xef'
        b = a.bytes3
        assert b == b'\xab\xcd\xef'


class TestUnderscoresInLiterals:

    def test_hex_creation(self):
        a = Bits(hex='ab_cd__ef')
        assert a.hex == 'abcdef'
        b = Bits('0x0102_0304')
        assert b.uint == 0x0102_0304

    def test_binary_creation(self):
        a = Bits(bin='0000_0001_0010')
        assert a.bin == '000000010010'
        b = Bits.fromstring('0b0011_1100_1111_0000')
        assert b.bin == '0011110011110000'
        v = 0b1010_0000
        c = Bits(uint=0b1010_0000, length=8)
        assert c.uint == v

    def test_octal_creation(self):
        a = Bits(oct='0011_2233_4455_6677')
        assert a.uint == 0o001122334455_6677
        b = Bits('0o123_321_123_321')
        assert b.uint == 0o123_321_123321


class TestPrettyPrinting:

    def test_simplest_cases(self):
        a = Bits('0b101011110000')
        s = io.StringIO()
        a.pp(stream=s)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='bin', length=12 bits> [
 0: 10101111 0000    
]
"""

        s = io.StringIO()
        a.pp('hex', stream=s)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='hex', length=12 bits> [
 0: af 0 
]
"""

        s = io.StringIO()
        a.pp('oct', stream=s)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='oct', length=12 bits> [
 0: 5360
]
"""

    def test_small_width(self):
        a = Bits(20)
        s = io.StringIO()
        a.pp(fmt='b', stream=s, width=5)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='bin', length=20 bits> [
 0: 00000000
 8: 00000000
16: 0000    
]
"""

    def test_separator(self):
        a = Bits('0x0f0f')*9
        s = io.StringIO()
        a.pp('hex:32', sep='!-!', stream=s)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='hex32', length=144 bits> [
  0: 0f0f0f0f!-!0f0f0f0f!-!0f0f0f0f!-!0f0f0f0f
] + trailing_bits = 0x0f0f
"""

    def test_multi_line(self):
        a = Bits(100)
        s = io.StringIO()
        a.pp('bin', sep='', stream=s, width=80)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='bin', length=100 bits> [
  0: 000000000000000000000000000000000000000000000000000000000000000000000000
 72: 0000000000000000000000000000                                            
]
"""

    def test_multiformat(self):
        a = Bits('0b1111000011110000')
        s = io.StringIO()
        a.pp(stream=s, fmt='bin, hex')
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='bin, hex', length=16 bits> [
 0: 11110000 11110000 : f0 f0
]
"""
        s = io.StringIO()
        a.pp(stream=s, fmt='hex, bin:12')
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='hex, bin12', length=16 bits> [
 0: f0f : 111100001111
] + trailing_bits = 0x0
"""

    def test_multi_line_multi_format(self):
        a = Bits(int=-1, length=112)
        s = io.StringIO()
        a.pp(stream=s, fmt='bin:8, hex:8', width=42)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='bin8, hex8', length=112 bits> [
  0: 11111111 11111111 11111111 : ff ff ff
 24: 11111111 11111111 11111111 : ff ff ff
 48: 11111111 11111111 11111111 : ff ff ff
 72: 11111111 11111111 11111111 : ff ff ff
 96: 11111111 11111111          : ff ff   
]
"""
        s = io.StringIO()
        a.pp(stream=s, fmt='bin, hex', width=41)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='bin, hex', length=112 bits> [
  0: 11111111 11111111 : ff ff
 16: 11111111 11111111 : ff ff
 32: 11111111 11111111 : ff ff
 48: 11111111 11111111 : ff ff
 64: 11111111 11111111 : ff ff
 80: 11111111 11111111 : ff ff
 96: 11111111 11111111 : ff ff
]
"""

        a = bytearray(range(0, 256))
        b = Bits(bytes=a)
        s = io.StringIO()
        b.pp(stream=s, fmt='bytes')
        assert remove_unprintable(s.getvalue()) == r"""<Bits, fmt='bytes', length=2048 bits> [
   0: ĀāĂă ĄąĆć ĈĉĊċ ČčĎď ĐđĒē ĔĕĖė ĘęĚě ĜĝĞğ  !"# $%&' ()*+ ,-./ 0123 4567 89:; <=>? @ABC DEFG HIJK LMNO PQRS TUVW XYZ[
 736: \]^_ `abc defg hijk lmno pqrs tuvw xyz{ |}~ſ ƀƁƂƃ ƄƅƆƇ ƈƉƊƋ ƌƍƎƏ ƐƑƒƓ ƔƕƖƗ Ƙƙƚƛ ƜƝƞƟ ƠơƢƣ ƤƥƦƧ ƨƩƪƫ ƬƭƮƯ ưƱƲƳ ƴƵƶƷ
1472: Ƹƹƺƻ Ƽƽƾƿ ǀǁǂǃ ǄǅǆǇ ǈǉǊǋ ǌǍǎǏ ǐǑǒǓ ǔǕǖǗ ǘǙǚǛ ǜǝǞǟ ǠǡǢǣ ǤǥǦǧ ǨǩǪǫ ǬǭǮǯ ǰǱǲǳ ǴǵǶǷ ǸǹǺǻ ǼǽǾÿ                         
]
"""

    def test_group_size_errors(self):
        a = Bits(120)
        with pytest.raises(ValueError):
            a.pp('hex:3')
        with pytest.raises(ValueError):
            a.pp('hex:4, oct')

    def test_zero_group_size(self):
        a = Bits(600)
        s = io.StringIO()
        a.pp('b0', stream=s, show_offset=False)
        expected_output = """<Bits, fmt='bin0', length=600 bits> [
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output

        a = Bits(400)
        s = io.StringIO()
        a.pp(stream=s, fmt='hex:0', show_offset=False, width=80)
        expected_output = """<Bits, fmt='hex0', length=400 bits> [
00000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000                                                            
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output

        s = io.StringIO()
        a = Bits(uint=10, length=48)
        a.pp(stream=s, width=20, fmt='hex:0, oct:0', show_offset=False)
        expected_output = """<Bits, fmt='hex0, oct0', length=48 bits> [
000000 : 00000000
00000a : 00000012
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output

    def test_oct(self):
        a = Bits('0o01234567'*20)
        s = io.StringIO()
        a.pp(stream=s, fmt='o', show_offset=False, width=20)
        expected_output = """<Bits, fmt='oct', length=480 bits> [
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
0123 4567 0123 4567
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output

        t = io.StringIO()
        a.pp('h, oct:0', width=1, show_offset=False, stream=t)
        expected_output = """<Bits, fmt='hex, oct0', length=480 bits> [
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
053977 : 01234567
]
"""
        assert remove_unprintable(t.getvalue()) == expected_output

    def test_bytes(self):
        a = Bits(bytes=b'helloworld!!'*5)
        s = io.StringIO()
        a.pp(stream=s, fmt='bytes', show_offset=False, width=48)
        expected_output = (
"""<Bits, fmt='bytes', length=480 bits> [
hell owor ld!! hell owor ld!! hell owor ld!!
hell owor ld!! hell owor ld!!               
]
""")
        assert remove_unprintable(s.getvalue()) == expected_output
        s = io.StringIO()
        a.pp(stream=s, fmt='bytes0', show_offset=False, width=40)
        expected_output = (
"""<Bits, fmt='bytes0', length=480 bits> [
helloworld!!helloworld!!helloworld!!hell
oworld!!helloworld!!                    
]
"""
        )
        assert remove_unprintable(s.getvalue()) == expected_output

    def test_bool(self):
        a = Bits('0b1100')
        s = io.StringIO()
        a.pp(stream=s, fmt='bool', show_offset=False, width=20)
        expected_output = """<Bits, fmt='bool', length=4 bits> [
1 1 0 0
]
"""
        assert remove_unprintable(s.getvalue()) == expected_output


class TestPrettyPrintingErrors:

    def test_wrong_formats(self):
        a = Bits('0x12341234')
        with pytest.raises(ValueError):
            a.pp('binary')
        with pytest.raises(ValueError):
            a.pp('bin, bin, bin')

    def test_interpret_problems(self):
        a = Bits(7)
        with pytest.raises(InterpretError):
            a.pp('oct')
        with pytest.raises(InterpretError):
            a.pp('hex')
        with pytest.raises(InterpretError):
            a.pp('bin, bytes')


class TestPrettyPrinting_LSB0:

    def setup_method(self) -> None:
        bitstring.lsb0 = True

    def teardown_method(self) -> None:
        bitstring.lsb0 = False

    def test_bin(self):
        a = Bits(bin='1111 0000 0000 1111 1010')
        s = io.StringIO()
        a.pp('bin', stream=s, width=5)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='bin', length=20 bits> [
11111010 :0 
00000000 :8 
    1111 :16
]
"""

class TestPrettyPrinting_NewFormats:

    def test_float(self):
        a = Bits('float32=10.5')
        s = io.StringIO()
        a.pp('float32', stream=s)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='float32', length=32 bits> [
 0:                    10.5
]
"""
        s = io.StringIO()
        a.pp('float16', stream=s)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='float16', length=32 bits> [
 0:                2.578125                     0.0
]
"""

    def test_uint(self):
        a = Bits().join([Bits(uint=x, length=12) for x in range(40, 105)])
        s = io.StringIO()
        a.pp('uint, h12', stream=s)
        assert remove_unprintable(s.getvalue()) == """<Bits, fmt='uint, hex12', length=780 bits> [
  0:   40   41   42   43   44   45   46   47   48   49   50   51 : 028 029 02a 02b 02c 02d 02e 02f 030 031 032 033
144:   52   53   54   55   56   57   58   59   60   61   62   63 : 034 035 036 037 038 039 03a 03b 03c 03d 03e 03f
288:   64   65   66   67   68   69   70   71   72   73   74   75 : 040 041 042 043 044 045 046 047 048 049 04a 04b
432:   76   77   78   79   80   81   82   83   84   85   86   87 : 04c 04d 04e 04f 050 051 052 053 054 055 056 057
576:   88   89   90   91   92   93   94   95   96   97   98   99 : 058 059 05a 05b 05c 05d 05e 05f 060 061 062 063
720:  100  101  102  103  104                                    : 064 065 066 067 068                            
]
"""

    def test_float(self):
        a = BitArray(float=76.25, length=64) + '0b11111'
        s = io.StringIO()
        a.pp('i64, float', stream=s)
        assert remove_unprintable(s.getvalue()) == """<BitArray, fmt='int64, float', length=69 bits> [
 0:  4635066033680416768 :                    76.25
] + trailing_bits = 0b11111
"""

class TestCopy:

    def test_copy_method(self):
        s = Bits('0xc00dee')
        t = s.copy()
        assert s == t


class TestNativeEndianIntegers:

    def test_uintne(self):
        s = Bits(uintne=454, length=160)
        t = Bits('uintne160=454')
        assert s == t

    def test_intne(self):
        s = Bits(intne=-1000, length=64)
        t = Bits('intne:64=-1000')
        assert s == t


class TestNonNativeEndianIntegers:

    def setup_method(self) -> None:
        bitstring.byteorder = 'little' if bitstring.byteorder == 'big' else 'little'

    def teardown_method(self) -> None:
        self.setup_method()

    def test_uintne(self):
        s = Bits(uintne=454, length=160)
        t = Bits('uintne160=454')
        assert s == t

    def test_intne(self):
        s = Bits(intne=-1000, length=64)
        t = Bits('intne:64=-1000')
        assert s == t
