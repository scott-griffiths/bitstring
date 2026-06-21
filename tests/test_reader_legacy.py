#!/usr/bin/env python

import io
import os
import platform

import pytest

import bitstring
from bitstring import BitArray, Bits, Reader


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def test_from_file():
    s = Reader(Bits(filename=os.path.join(THIS_DIR, 'test.m1v')))
    assert s.bits[0:32].hex == '000001b3'
    assert s.read(8 * 4).hex == '000001b3'
    width = s.read(12).uint
    height = s.read(12).uint
    assert (width, height) == (352, 288)


def test_from_file_with_offset_and_length():
    s = Reader(Bits(filename=os.path.join(THIS_DIR, 'test.m1v'), offset=24, length=8))
    assert s.bits.hex == 'b3'
    reconstructed = ''
    for bit in s.bits:
        reconstructed += '1' if bit is True else '0'
    assert reconstructed == s.bits.bin


def test_interleaved_exp_golomb_reading():
    s = Reader(Bits(uie=333))
    assert s.read('uie') == 333
    u = Bits('uie=12, sie=-9, sie=9, uie=1000000').unpack('uie, 2*sie, uie')
    assert u == [12, -9, 9, 1000000]


def test_interleaved_exp_golomb_reading_errors_restore_position():
    s = Reader(Bits.from_zeros(10))
    with pytest.raises(bitstring.ReadError):
        s.read('uie')
    assert s.pos == 0
    with pytest.raises(bitstring.ReadError):
        s.read('sie')
    assert s.pos == 0


def test_readto_byte_aligned():
    a = Reader(Bits('0xaabb00aa00bb'))
    b = a.readto('0x00', bytealigned=True)
    assert b == '0xaabb00'
    assert a.bytepos == 3
    b = a.readto('0xaa', bytealigned=True)
    assert b == '0xaa'
    with pytest.raises(bitstring.ReadError):
        Reader(b).readto('0xcc', bytealigned=True)


def test_readto_not_aligned():
    a = Reader(Bits('0b00111001001010011011'), pos=1)
    assert a.readto('0b00') == '0b011100'
    assert a.readto('0b110') == '0b10010100110'
    with pytest.raises(ValueError):
        a.readto('')


def test_readto_disallows_integers():
    a = Reader(Bits('0x0f'))
    with pytest.raises(ValueError):
        a.readto(4)


def test_reading_lines():
    s = b"This is a test\nof reading lines\nof text\n"
    b = Reader(Bits(bytes=s))
    n = Bits(bytes=b'\n')
    assert b.readto(n).bytes == b'This is a test\n'
    assert b.readto(n).bytes == b'of reading lines\n'
    assert b.readto(n).bytes == b'of text\n'


def test_pad_token_read():
    s = Reader(Bits('0b100011110001'))
    assert s.read('pad:1') is None
    assert s.pos == 1
    assert s.read(3) == Bits('0b000')
    assert s.read('pad:1') is None
    assert s.pos == 5


def test_pad_token_readlist():
    s = Reader(Bits.from_string('0b10001111001'))
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


def test_unpacking_bytes():
    s = Bits.from_zeros(80)
    t = s.unpack('bytes:1')
    assert t[0] == b'\x00'
    a, b, c = s.unpack('bytes:1, bytes, bytes2')
    assert a == b'\x00'
    assert b == b'\x00' * 7
    assert c == b'\x00' * 2


def test_unpacking_bytes_with_keywords():
    s = Bits('0x55' * 10)
    t = s.unpack('pad:a, bytes:b, bytes, pad:a', a=4, b=6)
    assert t == [b'\x55' * 6, b'\x55' * 3]


def test_read_bits_as_default():
    s = Reader(Bits('uint:31=14'))
    v = s.read(31)
    assert v.uint == 14
    s.pos = 0


def test_readlist_bits_as_default():
    s = Reader(Bits('uint:5=3, uint:3=0, uint:11=999'))
    v = s.readlist([5, 3, 11])
    assert [x.uint for x in v] == [3, 0, 999]
    s.pos = 0
    v = s.readlist(['5', '3', 11])
    assert [x.uint for x in v] == [3, 0, 999]


def test_bytesio_creation():
    f = io.BytesIO(b"\x12\xff\x77helloworld")
    s = Bits.from_bytes(f.getvalue())
    assert s[0:8] == '0x12'
    assert len(s) == 13 * 8
    s = Bits.from_bytes(f.getvalue(), offset=8, length=12)
    assert s == '0xff7'


def test_bytesio_creation_exceptions():
    f = io.BytesIO(b"123456789")
    _ = Bits.from_bytes(f.getvalue(), length=9 * 8)
    with pytest.raises(bitstring.CreationError):
        _ = Bits.from_bytes(f.getvalue(), length=9 * 8 + 1)
    with pytest.raises(bitstring.CreationError):
        _ = Bits.from_bytes(f.getvalue(), length=9 * 8, offset=1)


def test_reader_default_pos():
    s = Reader(Bits('0xabc'))
    assert s.pos == 0


def test_reader_lax_positive_pos():
    s = Reader(Bits('0xabc'), pos=0)
    assert s.pos == 0
    s = Reader(Bits('0xabc'), pos=1)
    assert s.pos == 1
    s = Reader(Bits('0xabc'), pos=12)
    assert s.pos == 12
    s = Reader(Bits('0xabc'), pos=13)
    assert s.pos == 13
    with pytest.raises(ValueError):
        s.read(0)


def test_reader_lax_negative_pos():
    s = Reader(Bits('0xabc'), pos=-1)
    assert s.pos == -1
    with pytest.raises(ValueError):
        s.read(1)
    s = Reader(Bits('0xabc'), pos=-12)
    assert s.pos == -12


def test_reader_string_representation():
    s = Reader(Bits('0b110'), pos=2)
    assert repr(s) == "Reader(<Bits of length 3 bits>, pos=2)"


def test_reader_string_representation_from_file():
    filename = os.path.join(THIS_DIR, 'test.m1v')
    s = Reader(Bits(filename=filename), pos=2001)
    assert repr(s) == "Reader(<Bits of length 1002400 bits>, pos=2001)"
    s.pos = 0
    assert repr(s) == "Reader(<Bits of length 1002400 bits>, pos=0)"


def test_windows_file_lock_bug(tmp_path):
    path = tmp_path / 'temp_unit_test_file'
    with open(path, mode='w') as f:
        f.write('Hello')
    _ = Bits(filename=path)

    try:
        with open(path, mode='w') as _:
            pass
    except OSError:
        if platform.system() == 'Windows':
            pass


def test_readerrors():
    s = Reader(Bits('0b110'))
    s.read(3)
    with pytest.raises(bitstring.ReadError):
        _ = s.read(1)
    s.pos = 1
    with pytest.raises(bitstring.ReadError):
        _ = s.read('u3')


def test_mutable_reader_uses_external_bitarray_without_position_coupling():
    bits = BitArray('0x001122')
    r = Reader(bits, pos=8)
    assert r.read('uint8') == 0x11
    bits.insert('0xff', 8)
    assert bits == '0x00ff1122'
    assert r.pos == 16
    r.pos = 8
    assert r.read('uint8') == 0xff
