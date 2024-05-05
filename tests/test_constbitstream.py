#!/usr/bin/env python

import pytest
import sys
import bitstring
import io
import os
from bitstring import ConstBitStream as CBS
import platform

sys.path.insert(0, '..')


THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class TestAll:
    def test_from_file(self):
        s = CBS(filename=os.path.join(THIS_DIR, 'test.m1v'))
        assert s[0:32].hex == '000001b3'
        assert s.read(8 * 4).hex == '000001b3'
        width = s.read(12).uint
        height = s.read(12).uint
        assert (width, height) == (352, 288)

    def test_from_file_with_offset_and_length(self):
        s = CBS(filename=os.path.join(THIS_DIR, 'test.m1v'), offset=24, length=8)
        assert s.h == 'b3'
        reconstructed = ''
        for bit in s:
            reconstructed += '1' if bit is True else '0'
        assert reconstructed == s.bin


class TestInterleavedExpGolomb:
    def test_reading(self):
        s = CBS(uie=333)
        a = s.read('uie')
        assert a == 333
        s = CBS('uie=12, sie=-9, sie=9, uie=1000000')
        u = s.unpack('uie, 2*sie, uie')
        assert u == [12, -9, 9, 1000000]

    def test_reading_errors(self):
        s = CBS(10)
        with pytest.raises(bitstring.ReadError):
            s.read('uie')
        assert s.pos == 0
        with pytest.raises(bitstring.ReadError):
            s.read('sie')
        assert s.pos == 0


class TestReadTo:
    def test_byte_aligned(self):
        a = CBS('0xaabb00aa00bb')
        b = a.readto('0x00', bytealigned=True)
        assert b == '0xaabb00'
        assert a.bytepos == 3
        b = a.readto('0xaa', bytealigned=True)
        assert b == '0xaa'
        with pytest.raises(bitstring.ReadError):
            b.readto('0xcc', bytealigned=True)

    def test_not_aligned(self):
        a = CBS('0b00111001001010011011')
        a.pos = 1
        assert a.readto('0b00') == '0b011100'
        assert a.readto('0b110') == '0b10010100110'
        with pytest.raises(ValueError):
            a.readto('')

    def test_disallow_integers(self):
        a = CBS('0x0f')
        with pytest.raises(ValueError):
            a.readto(4)

    def test_reading_lines(self):
        s = b"This is a test\nof reading lines\nof text\n"
        b = CBS(bytes=s)
        n = bitstring.Bits(bytes=b'\n')
        assert b.readto(n).bytes == b'This is a test\n'
        assert b.readto(n).bytes == b'of reading lines\n'
        assert b.readto(n).bytes == b'of text\n'


class TestSubclassing:

    def test_is_instance(self):
        class SubBits(CBS):
            pass
        a = SubBits()
        assert isinstance(a, SubBits)

    def test_class_type(self):
        class SubBits(CBS):
            pass
        assert SubBits().__class__ == SubBits


class TestPadToken:

    def test_read(self):
        s = CBS('0b100011110001')
        a = s.read('pad:1')
        assert a == None
        assert s.pos == 1
        a = s.read(3)
        assert a == CBS('0b000')
        a = s.read('pad:1')
        assert a == None
        assert s.pos == 5

    def test_read_list(self):
        s = CBS.fromstring('0b10001111001')
        t = s.readlist('pad:1, uint:3, pad:4, uint:3')
        assert t == [0, 1]
        s.pos = 0
        t = s.readlist('pad:1, pad:5')
        assert t == []
        assert s.pos == 6
        s.pos = 0
        t = s.readlist('pad:1, bin, pad:4, uint:3')
        assert t == ['000', 1]
        s.pos = 0
        t = s.readlist('pad, bin:3, pad:4, uint:3')
        assert t == ['000', 1]


class TestReadingBytes:

    def test_unpacking_bytes(self):
        s = CBS(80)
        t = s.unpack('bytes:1')
        assert t[0] == b'\x00'
        a, b, c = s.unpack('bytes:1, bytes, bytes2')
        assert a == b'\x00'
        assert b == b'\x00'*7
        assert c == b'\x00'*2

    def test_unpacking_bytes_with_keywords(self):
        s = CBS('0x55'*10)
        t = s.unpack('pad:a, bytes:b, bytes, pad:a', a=4, b=6)
        assert t == [b'\x55'*6, b'\x55'*3]


class TestReadingBitsAsDefault:

    def test_read_bits(self):
        s = CBS('uint:31=14')
        v = s.read(31)
        assert v.uint == 14
        s.pos = 0

    def test_read_list_bits(self):
        s = CBS('uint:5=3, uint:3=0, uint:11=999')
        v = s.readlist([5, 3, 11])
        assert [x.uint for x in v] == [3, 0, 999]
        s.pos = 0
        v = s.readlist(['5', '3', 11])
        assert [x.uint for x in v] == [3, 0, 999]


class TestLsb0Reading:

    @classmethod
    def setup_class(cls):
        bitstring.lsb0 = True

    @classmethod
    def teardown_class(cls):
        bitstring.lsb0 = False

    def test_reading_hex(self):
        s = CBS('0xabcdef')
        assert s.read('hex:4') == 'f'
        assert s.read(4) == '0xe'
        assert s.pos == 8

    def test_reading_oct(self):
        s = CBS('0o123456')
        assert s.read('o6') == '56'
        assert s.pos == 6

    def test_reading_bin(self):
        s = CBS('0b00011')
        assert s.read('bin:3') == '011'
        assert s.pos == 3

    def test_reading_bytes(self):
        s = CBS(bytes=b'54321')
        assert s.pos == 0
        s.pos = 8
        assert s.read('bytes:2') == b'32'


class TestBytesIOCreation:

    def test_simple_creation(self):
        f = io.BytesIO(b"\x12\xff\x77helloworld")
        s = CBS(f)
        assert s[0:8] == '0x12'
        assert len(s) == 13 * 8
        s = CBS(f, offset=8, length=12)
        assert s == '0xff7'

    def test_exceptions(self):
        f = io.BytesIO(b"123456789")
        _ = CBS(f, length=9*8)
        with pytest.raises(bitstring.CreationError):
            _ = CBS(f, length=9*8 + 1)
        with pytest.raises(bitstring.CreationError):
            _ = CBS(f, length=9*8, offset=1)


class TestCreationWithPos:

    def test_default_creation(self):
        s = CBS('0xabc')
        assert s.pos == 0

    def test_positive_pos(self):
        s = CBS('0xabc', pos=0)
        assert s.pos == 0
        s = CBS('0xabc', pos=1)
        assert s.pos == 1
        s = CBS('0xabc', pos=12)
        assert s.pos == 12
        with pytest.raises(bitstring.CreationError):
            _ = CBS('0xabc', pos=13)

    def test_negative_pos(self):
        s = CBS('0xabc', pos=-1)
        assert s.pos == 11
        s = CBS('0xabc', pos=-12)
        assert s.pos == 0
        with pytest.raises(bitstring.CreationError):
            _ = CBS('0xabc', pos=-13)

    def test_string_representation(self):
        s = CBS('0b110', pos=2)
        assert s.__repr__() == "ConstBitStream('0b110', pos=2)"

    def test_string_representation_from_file(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        s = CBS(filename=filename, pos=2001)
        assert s.__repr__() == f"ConstBitStream(filename={repr(str(filename))}, length=1002400, pos=2001)"
        s.pos = 0
        assert s.__repr__() == f"ConstBitStream(filename={repr(str(filename))}, length=1002400)"


def test_windows_file_lock_bug():
    path = os.path.join(THIS_DIR, 'temp_unit_test_file')
    # Create the file
    with open(path, mode='w') as f:
        f.write('Hello')
    # Will this lock it?
    _ = CBS(filename=path)

    try:
        with open(path, mode='w') as _:
            pass
    except OSError:
        if platform.system() == 'Windows':
            # Expected failure. See bug #308
            pass

def test_readerrors():
    s = CBS('0b110')
    s.read(3)
    with pytest.raises(bitstring.ReadError):
        _ = s.read(1)
    s.pos = 1
    with pytest.raises(bitstring.ReadError):
        _ = s.read('u3')