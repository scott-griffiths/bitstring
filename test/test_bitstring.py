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


class ModuleData(unittest.TestCase):
    def testVersion(self):
        self.assertEqual(bitstring.__version__, '4.0.0')

    def testAll(self):
        exported = ['ConstBitStream', 'BitStream', 'BitArray',
                    'Bits', 'pack', 'Error', 'ReadError',
                    'InterpretError', 'ByteAlignError', 'CreationError', 'bytealigned', 'set_lsb0', 'set_msb0']
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
        self.assertFalse(ba._datastore is ba_copy._datastore)
        self.assertTrue(ba == ba_copy)

    def testConstBitStreamCopy(self):
        cbs = bitstring.ConstBitStream(100)
        cbs.pos = 50
        cbs_copy = copy.copy(cbs)
        self.assertEqual(cbs_copy.pos, 0)
        self.assertTrue(cbs._datastore is cbs_copy._datastore)
        self.assertTrue(cbs == cbs_copy)

    def testBitStreamCopy(self):
        bs = bitstring.BitStream(100)
        bs.pos = 50
        bs_copy = copy.copy(bs)
        self.assertEqual(bs_copy.pos, 0)
        self.assertFalse(bs._datastore is bs_copy._datastore)
        self.assertTrue(bs == bs_copy)


class Interning(unittest.TestCase):
    def testBits(self):
        a = bitstring.Bits('0xf')
        b = bitstring.Bits('0xf')
        self.assertTrue(a is b)
        c = bitstring.Bits('0b1111')
        self.assertFalse(a is c)

    def testCBS(self):
        a = bitstring.ConstBitStream('0b11000')
        b = bitstring.ConstBitStream('0b11000')
        self.assertFalse(a is b)


class LSB0(unittest.TestCase):
    def testGettingAndSetting(self):
        self.assertEqual(bitstring._lsb0, False)
        bitstring.set_lsb0()
        self.assertEqual(bitstring._lsb0, True)
        bitstring.set_lsb0(False)
        self.assertEqual(bitstring._lsb0, False)
        bitstring.set_msb0(False)
        self.assertEqual(bitstring._lsb0, True)
        bitstring.set_msb0()
        self.assertEqual(bitstring._lsb0, False)


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
            with mock.patch('sys.argv', ['ignored', 'uint:12=352', 'int']):
                bitstring.main()
        s = f.getvalue()
        self.assertEqual(s, '352\n')

    def testRunningModuleWithMultipleParameters(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'uint:12=352', '0b101', '0o321', 'float:32=51', 'bin:1=1']):
                bitstring.main()
        s = f.getvalue()
        self.assertEqual(s, '0x160ad1424c0000, 0b1\n')

    def testRunningModuleWithMultipleParametersAndInterpretation(self):
        with redirect_stdout(io.StringIO()) as f:
            with mock.patch('sys.argv', ['b.py', 'ue=1000', '0xff.bin']):
                bitstring.main()
        s = f.getvalue()
        self.assertEqual(s, '000000000111110100111111111\n')
