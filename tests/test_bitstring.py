#!/usr/bin/env python
"""
Module-level unit tests.
"""
import io
from unittest import mock
from contextlib import redirect_stdout
import bitstring
import copy
from collections import abc
import sys
import os
from bitstring import __main__


sys.path.insert(0, '..')
THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestModuleData:

    def test_all(self):
        exported = ['ConstBitStream', 'BitStream', 'BitArray',
                    'Bits', 'pack', 'Error', 'ReadError', 'Array',
                    'InterpretError', 'ByteAlignError', 'CreationError', 'bytealigned', 'lsb0', 'Dtype', 'options']
        assert set(bitstring.__all__) == set(exported)

    def test_pyproject_version(self):
        filename = os.path.join(THIS_DIR, '../pyproject.toml')
        try:
            with open(filename, 'r') as pyprojectfile:
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
        cba = bitstring.Bits(100)
        cba_copy = copy.copy(cba)
        assert cba is cba_copy

    def test_bit_array_copy(self):
        ba = bitstring.BitArray(100)
        ba_copy = copy.copy(ba)
        assert not ba is ba_copy
        assert not ba._bitstore is ba_copy._bitstore
        assert ba == ba_copy

    def test_const_bit_stream_copy(self):
        cbs = bitstring.ConstBitStream(100)
        cbs.pos = 50
        cbs_copy = copy.copy(cbs)
        assert cbs_copy.pos == 0
        assert cbs._bitstore is cbs_copy._bitstore
        assert cbs == cbs_copy

    def test_bit_stream_copy(self):
        bs = bitstring.BitStream(100)
        bs.pos = 50
        bs_copy = copy.copy(bs)
        assert bs_copy.pos == 0
        assert not bs._bitstore is bs_copy._bitstore
        assert bs == bs_copy


class TestInterning:
    def test_bits(self):
        a = bitstring.Bits('0xf')
        b = bitstring.Bits('0xf')
        assert a._bitstore is b._bitstore
        c = bitstring.Bits('0b1111')
        assert not a is c

    def test_cbs(self):
        a = bitstring.ConstBitStream('0b11000')
        b = bitstring.ConstBitStream('0b11000')
        assert a._bitstore is b._bitstore
        assert not a is b


class TestLSB0:
    def test_getting_and_setting(self):
        assert bitstring.lsb0 == False
        bitstring.lsb0 = True
        assert bitstring.lsb0 == True
        bitstring.lsb0 = False
        assert bitstring.lsb0 == False


class TestMain:
    def test_running_module_directly_help(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['bitstring.py', '-h']):
                bitstring.__main__.main()
        s = f.getvalue()
        assert s.find("command-line parameters") >= 0

        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['renamed.py']):
                bitstring.__main__.main()
        s = f.getvalue()
        assert s.find("command-line parameters") >= 0

    def test_running_module_with_single_parameter(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['', 'uint:12=352']):
                bitstring.__main__.main()
        s = f.getvalue()
        assert s == '0x160\n'

    def test_running_module_with_single_parameter_and_interpretation(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['ignored', 'u12=352', 'i']):
                bitstring.__main__.main()
        s = f.getvalue()
        assert s == '352\n'

    def test_running_module_with_multiple_parameters(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'uint12=352', '0b101', '0o321', 'f32=51', 'bool=1']):
                bitstring.__main__.main()
        s = f.getvalue()
        assert s == '0x160ad1424c0000, 0b1\n'

    def test_running_module_with_multiple_parameters_and_interpretation(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'ue=1000', '0xff.bin']):
                bitstring.__main__.main()
        s = f.getvalue()
        assert s == '000000000111110100111111111\n'

    def test_short_interpretations(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'bin=001.b']):
                bitstring.__main__.main()
        s = f.getvalue()
        assert s == '001\n'


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

        constbitstream = bitstring.ConstBitStream()
        assert not isinstance(constbitstream, abc.Sequence)
        assert not isinstance(constbitstream, abc.MutableSequence)

        bitstream = bitstring.BitArray()
        assert not isinstance(bitstream, abc.MutableSequence)
        assert not isinstance(bitstream, abc.Sequence)


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
        a = bitstring.BitStream(b'hello')
        b = a.read('bytes')
        assert b == b'hello'

    def test_reading_bin_with_no_length(self):
        a = bitstring.BitStream('0b1101')
        b = a.read('bin')
        assert b == '1101'

    def test_reading_uint_with_no_length(self):
        a = bitstring.BitStream('0b1101')
        b = a.read('uint')
        assert b == 13

    def test_reading_float_with_no_length(self):
        a = bitstring.BitStream(float=14, length=16)
        b = a.read('float')
        assert b == 14.0
