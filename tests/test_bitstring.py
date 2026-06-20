#!/usr/bin/env python
"""
Module-level unit tests.
"""
import bitstring
import copy
from collections import abc
import sys
import os


sys.path.insert(0, '..')
THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestModuleData:

    def test_all(self):
        exported = ['Reader', 'BitArray',
                    'Bits', 'pack', 'Error', 'ReadError', 'Array',
                    'InterpretError', 'ByteAlignError', 'CreationError', 'Dtype', 'options']
        assert set(bitstring.__all__) == set(exported)

    def test_pyproject_version(self):
        filename = os.path.join(THIS_DIR, '../pyproject.toml')
        try:
            with open(filename) as pyprojectfile:
                found = False
                for line in pyprojectfile.readlines():
                    if line.startswith("version"):
                        assert not found
                        assert bitstring.__version__ in line
                        found = True
            assert found
        except FileNotFoundError:
            pass  # Doesn't run on CI.


class TestCopy:
    def test_const_bit_array_copy(self):
        cba = bitstring.Bits.from_zeros(100)
        cba_copy = copy.copy(cba)
        assert cba is cba_copy

    def test_bit_array_copy(self):
        ba = bitstring.BitArray.from_zeros(100)
        ba_copy = copy.copy(ba)
        assert not ba is ba_copy
        assert not ba._bitstore is ba_copy._bitstore
        assert ba == ba_copy

    def test_reader_copy(self):
        bits = bitstring.Bits.from_zeros(100)
        r = bitstring.Reader(bits, 50)
        r_copy = copy.copy(r)
        assert r_copy.pos == 50
        assert r_copy.bits is bits


class TestInterning:
    def test_bits(self):
        a = bitstring.Bits('0xf')
        b = bitstring.Bits('0xf')
        assert a._bitstore is b._bitstore
        c = bitstring.Bits('0b1111')
        assert not a is c

    def test_bits_cache(self):
        a = bitstring.Bits('0b11000')
        b = bitstring.Bits('0b11000')
        assert a._bitstore is b._bitstore
        assert not a is b


class TestABCs:
    def test_base_classes(self):
        # The classes deliberately do not conform to the sequence ABCs.
        # see https://github.com/scott-griffiths/bitstring/issues/261
        bits = bitstring.Bits()
        assert not isinstance(bits, abc.Sequence)
        assert not isinstance(bits, abc.MutableSequence)

        bitarray = bitstring.BitArray()
        assert not isinstance(bitarray, abc.MutableSequence)
        assert not isinstance(bitarray, abc.Sequence)

        bitarray = bitstring.BitArray()
        assert not isinstance(bitarray, abc.MutableSequence)
        assert not isinstance(bitarray, abc.Sequence)


class TestNoFixedLengthPackingBug:

    def test_packing_bytes_with_no_length(self):
        a = bitstring.pack('bytes', b'abcd')
        assert a.bytes == b'abcd'

    def test_packing_bin_with_no_length(self):
        a = bitstring.pack('bin', '0001')
        assert a.bin == '0001'

    def test_packing_hex_with_no_length(self):
        a = bitstring.pack('hex', 'abcd')
        assert a.hex == 'abcd'

    def test_reading_bytes_with_no_length(self):
        a = bitstring.Reader(bitstring.Bits(b'hello'))
        b = a.read('bytes')
        assert b == b'hello'

    def test_reading_bin_with_no_length(self):
        a = bitstring.Reader(bitstring.Bits('0b1101'))
        b = a.read('bin')
        assert b == '1101'

    def test_reading_uint_with_no_length(self):
        a = bitstring.Reader(bitstring.Bits('0b1101'))
        b = a.read('uint')
        assert b == 13

    def test_reading_float_with_no_length(self):
        a = bitstring.Reader(bitstring.Bits(float=14, length=16))
        b = a.read('float')
        assert b == 14.0

    def test_pack_returns_bits(self):
        a = bitstring.pack('uint8=1')
        assert type(a) is bitstring.Bits
