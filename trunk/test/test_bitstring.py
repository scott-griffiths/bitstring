#!/usr/bin/env python

import unittest
import sys
sys.path.insert(0, '..')
import bitstring
from bitstring import ConstBitArray

class ModuleData(unittest.TestCase):

    def testVersion(self):
        self.assertEqual(bitstring.__version__, '2.1.0')

    def testAll(self):
        exported = ['ConstBitArray', 'ConstBitStream', 'BitStream', 'BitArray',
                    'Bits', 'BitString', 'pack', 'Error', 'ReadError',
                    'InterpretError', 'ByteAlignError', 'CreationError']
        self.assertEqual(set(bitstring.__all__), set(exported))

    def testReverseDict(self):
        d = bitstring.constbitarray.BYTE_REVERSAL_DICT
        for i in range(256):
            a = ConstBitArray(uint=i, length=8)
            b = d[i]
            self.assertEqual(a.bin[2:][::-1], ConstBitArray(bytes=b).bin[2:])

