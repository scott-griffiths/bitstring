#!/usr/bin/env python
"""
Module-level unit tests.
"""
import io
import unittest
from unittest import mock
from contextlib import redirect_stdout
import sys
sys.path.insert(0, '..')
import bitstring
import copy
from collections import abc
import math
from bitstring.classes import fp143_fmt, fp152_fmt
import struct


class ModuleData(unittest.TestCase):
    def testVersion(self):
        self.assertEqual(bitstring.__version__, '4.1.0b1')

    def testAll(self):
        exported = ['ConstBitStream', 'BitStream', 'BitArray',
                    'Bits', 'pack', 'Error', 'ReadError', 'Array',
                    'InterpretError', 'ByteAlignError', 'CreationError', 'bytealigned', 'lsb0']
        self.assertEqual(set(bitstring.__all__), set(exported))

    def testReverseDict(self):
        d = bitstring.Bits._byteReversalDict
        for i in range(256):
            a = bitstring.Bits(uint=i, length=8)
            b = d[i]
            self.assertEqual(a.bin[::-1], bitstring.Bits(bytes=b).bin)


class Copy(unittest.TestCase):
    def testConstBitArrayCopy(self):
        cba = bitstring.Bits(100)
        cba_copy = copy.copy(cba)
        self.assertTrue(cba is cba_copy)

    def testBitArrayCopy(self):
        ba = bitstring.BitArray(100)
        ba_copy = copy.copy(ba)
        self.assertFalse(ba is ba_copy)
        self.assertFalse(ba._bitstore is ba_copy._bitstore)
        self.assertTrue(ba == ba_copy)

    def testConstBitStreamCopy(self):
        cbs = bitstring.ConstBitStream(100)
        cbs.pos = 50
        cbs_copy = copy.copy(cbs)
        self.assertEqual(cbs_copy.pos, 0)
        self.assertTrue(cbs._bitstore is cbs_copy._bitstore)
        self.assertTrue(cbs == cbs_copy)

    def testBitStreamCopy(self):
        bs = bitstring.BitStream(100)
        bs.pos = 50
        bs_copy = copy.copy(bs)
        self.assertEqual(bs_copy.pos, 0)
        self.assertFalse(bs._bitstore is bs_copy._bitstore)
        self.assertTrue(bs == bs_copy)


class Interning(unittest.TestCase):
    def testBits(self):
        a = bitstring.Bits('0xf')
        b = bitstring.Bits('0xf')
        self.assertTrue(a._bitstore is b._bitstore)
        c = bitstring.Bits('0b1111')
        self.assertFalse(a is c)

    def testCBS(self):
        a = bitstring.ConstBitStream('0b11000')
        b = bitstring.ConstBitStream('0b11000')
        self.assertTrue(a._bitstore is b._bitstore)
        self.assertFalse(a is b)


class LSB0(unittest.TestCase):
    def testGettingAndSetting(self):
        self.assertEqual(bitstring.lsb0, False)
        bitstring.lsb0 = True
        self.assertEqual(bitstring.lsb0, True)
        bitstring.lsb0 = False
        self.assertEqual(bitstring.lsb0, False)


class Main(unittest.TestCase):
    def testRunningModuleDirectlyHelp(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['bitstring.py', '-h']):
                bitstring.main()
        s = f.getvalue()
        self.assertTrue(s.find("command-line parameters") >= 0)

        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['renamed.py']):
                bitstring.main()
        s = f.getvalue()
        self.assertTrue(s.find("command-line parameters") >= 0)

    def testRunningModuleWithSingleParameter(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['', 'uint:12=352']):
                bitstring.main()
        s = f.getvalue()
        self.assertEqual(s, '0x160\n')

    def testRunningModuleWithSingleParameterAndInterpretation(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['ignored', 'u12=352', 'i']):
                bitstring.main()
        s = f.getvalue()
        self.assertEqual(s, '352\n')

    def testRunningModuleWithMultipleParameters(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'uint12=352', '0b101', '0o321', 'f32=51', 'bool=1']):
                bitstring.main()
        s = f.getvalue()
        self.assertEqual(s, '0x160ad1424c0000, 0b1\n')

    def testRunningModuleWithMultipleParametersAndInterpretation(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'ue=1000', '0xff.bin']):
                bitstring.main()
        s = f.getvalue()
        self.assertEqual(s, '000000000111110100111111111\n')

    def testShortInterpretations(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'bin=001.b']):
                bitstring.main()
        s = f.getvalue()
        self.assertEqual(s, '001\n')


@unittest.expectedFailure
class ABCs(unittest.TestCase):
    def testBaseClasses(self):
        # https://github.com/scott-griffiths/bitstring/issues/261
        bits = bitstring.Bits()
        self.assertTrue(isinstance(bits, abc.Sequence))
        self.assertFalse(isinstance(bits, abc.MutableSequence))

        bitarray = bitstring.BitArray()
        self.assertTrue(isinstance(bitarray, abc.MutableSequence))
        self.assertTrue(isinstance(bitarray, abc.Sequence))

        constbitstream = bitstring.ConstBitStream()
        self.assertTrue(isinstance(constbitstream, abc.Sequence))
        self.assertFalse(isinstance(constbitstream, abc.MutableSequence))

        bitstream = bitstring.BitArray()
        self.assertTrue(isinstance(bitstream, abc.MutableSequence))
        self.assertTrue(isinstance(bitstream, abc.Sequence))


class ConversionToFP8(unittest.TestCase):

    def testSome143Values(self):
        zero = bitstring.Bits('0b0000 0000')
        self.assertEqual(fp143_fmt.lut_int8_to_float[zero.uint], 0.0)
        max_normal = bitstring.Bits('0b0111 1111')
        self.assertEqual(fp143_fmt.lut_int8_to_float[max_normal.uint], 240.0)
        max_normal_neg = bitstring.Bits('0b1111 1111')
        self.assertEqual(fp143_fmt.lut_int8_to_float[max_normal_neg.uint], -240.0)
        min_normal = bitstring.Bits('0b0000 1000')
        self.assertEqual(fp143_fmt.lut_int8_to_float[min_normal.uint], 2**-7)
        min_subnormal = bitstring.Bits('0b0000 0001')
        self.assertEqual(fp143_fmt.lut_int8_to_float[min_subnormal.uint], 2**-10)
        max_subnormal = bitstring.Bits('0b0000 0111')
        self.assertEqual(fp143_fmt.lut_int8_to_float[max_subnormal.uint], 0.875 * 2**-7)
        nan = bitstring.Bits('0b1000 0000')
        self.assertTrue(math.isnan(fp143_fmt.lut_int8_to_float[nan.uint]))

    def testSome152Values(self):
        zero = bitstring.Bits('0b0000 0000')
        self.assertEqual(fp152_fmt.lut_int8_to_float[zero.uint], 0.0)
        max_normal = bitstring.Bits('0b0111 1111')
        self.assertEqual(fp152_fmt.lut_int8_to_float[max_normal.uint], 57344.0)
        max_normal_neg = bitstring.Bits('0b1111 1111')
        self.assertEqual(fp152_fmt.lut_int8_to_float[max_normal_neg.uint], -57344.0)
        min_normal = bitstring.Bits('0b0000 0100')
        self.assertEqual(fp152_fmt.lut_int8_to_float[min_normal.uint], 2**-15)
        min_subnormal = bitstring.Bits('0b0000 0001')
        self.assertEqual(fp152_fmt.lut_int8_to_float[min_subnormal.uint], 0.25 * 2**-15)
        max_subnormal = bitstring.Bits('0b0000 0011')
        self.assertEqual(fp152_fmt.lut_int8_to_float[max_subnormal.uint], 0.75 * 2**-15)
        nan = bitstring.Bits('0b1000 0000')
        self.assertTrue(math.isnan(fp152_fmt.lut_int8_to_float[nan.uint]))

    @unittest.skip  # Skipping as it takes a few seconds to run
    def testFloatToInt8(self):
        # Checking equivalence of the LUT method to the loop over values method.
        for fmt in [fp143_fmt, fp152_fmt]:
            for i in range(1 << 16):
                b = struct.pack('>H', i)
                f, = struct.unpack('>e', b)
                x = fmt.float_to_int8(f)
                y = fmt.slow_float_to_int8(f)
                self.assertEqual(x, y)

    def testRoundTrip(self):
        # For each possible 8bit int, convert to float, then convert that float back to an int
        for fmt in [fp143_fmt, fp152_fmt]:
            for i in range(256):
                f = fmt.lut_int8_to_float[i]
                ip = fmt.float_to_int8(f)
                self.assertEqual(ip, i)

    def testFloat16Conversion(self):
        # Convert a float16 to a float8, then convert that to a Python float. Then convert back to a float16.
        # This value should have been rounded towards zero. Convert back to a float8 again - should be the
        # same value as before or the adjacent smaller value
        for fmt in [fp143_fmt, fp152_fmt]:
            # Keeping sign bit == 0 so only positive numbers
            previous_value = 0.0
            for i in range(1 << 15):
                # Check that the f16 is a standard number
                b = struct.pack('>H', i)
                f16, = struct.unpack('>e', b)
                if math.isnan(f16):
                    continue
                # OK, it's an ordinary number - convert to a float8
                f8 = fmt.lut_float16_to_float8[i]
                # And convert back to a float
                f = fmt.lut_int8_to_float[f8]
                # This should have been rounded towards zero compared to the original
                self.assertTrue(f <= f16)
                # But not rounded more than to the previous valid value
                self.assertTrue(f >= previous_value)
                if f > previous_value:
                    previous_value = f



