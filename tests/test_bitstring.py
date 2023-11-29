#!/usr/bin/env python
"""
Module-level unit tests.
"""
import io
import unittest
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


class ModuleData(unittest.TestCase):

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


    def testPyprojectVersion(self):
        filename = os.path.join(THIS_DIR, '../pyproject.toml')
        try:
            with open(filename, 'r') as pyprojectfile:
                found = False
                for line in pyprojectfile.readlines():
                    if line.startswith("version"):
                        self.assertFalse(found)
                        self.assertTrue(bitstring.__version__ in line)
                        found = True
            self.assertTrue(found)
        except FileNotFoundError:
            pass  # Doesn't run on CI.


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
                bitstring.__main__.main()
        s = f.getvalue()
        self.assertTrue(s.find("command-line parameters") >= 0)

        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['renamed.py']):
                bitstring.__main__.main()
        s = f.getvalue()
        self.assertTrue(s.find("command-line parameters") >= 0)

    def testRunningModuleWithSingleParameter(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['', 'uint:12=352']):
                bitstring.__main__.main()
        s = f.getvalue()
        self.assertEqual(s, '0x160\n')

    def testRunningModuleWithSingleParameterAndInterpretation(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['ignored', 'u12=352', 'i']):
                bitstring.__main__.main()
        s = f.getvalue()
        self.assertEqual(s, '352\n')

    def testRunningModuleWithMultipleParameters(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'uint12=352', '0b101', '0o321', 'f32=51', 'bool=1']):
                bitstring.__main__.main()
        s = f.getvalue()
        self.assertEqual(s, '0x160ad1424c0000, 0b1\n')

    def testRunningModuleWithMultipleParametersAndInterpretation(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'ue=1000', '0xff.bin']):
                bitstring.__main__.main()
        s = f.getvalue()
        self.assertEqual(s, '000000000111110100111111111\n')

    def testShortInterpretations(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'bin=001.b']):
                bitstring.__main__.main()
        s = f.getvalue()
        self.assertEqual(s, '001\n')


@unittest.skip('Bug #261')
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


class DtypeRegister(unittest.TestCase):

    pass


class NoFixedLengthPackingBug(unittest.TestCase):

    def testPackingBytesWithNoLength(self):
        a = bitstring.pack('bytes', b'abcd')
        self.assertEqual(a.bytes, b'abcd')
        b = bitstring.pack('u12, bytes, bool', 0, b'deadbeef', True)
        self.assertEqual(b.unpack('u12, bytes, bool'), [0, b'deadbeef', True])

    def testPackingBinWithNoLength(self):
        a = bitstring.pack('bin', '0001')
        self.assertEqual(a.bin, '0001')

    def testPackingHexWithNoLength(self):
        a = bitstring.pack('hex', 'abcd')
        self.assertEqual(a.hex, 'abcd')

    def testReadingBytesWithNoLength(self):
        a = bitstring.BitStream(b'hello')
        b = a.read('bytes')
        self.assertEqual(b, b'hello')
        c = bitstring.BitStream('0xabc, u13=99')
        c += b'123abc'
        c += bitstring.Bits('bfloat=4')
        c.pos = 0
        self.assertEqual(c.readlist('h12, u13, bytes, bfloat'), ['abc', 99, b'123abc', 4.0])

    def testReadingBinWithNoLength(self):
        a = bitstring.BitStream('0b1101')
        b = a.read('bin')
        self.assertEqual(b, '1101')

    def testReadingUintWithNoLength(self):
        a = bitstring.BitStream('0b1101')
        b = a.read('uint')
        self.assertEqual(b, 13)

    def testReadingFloatWithNoLength(self):
        a = bitstring.BitStream(float=14, length=16)
        b = a.read('float')
        self.assertEqual(b, 14.0)