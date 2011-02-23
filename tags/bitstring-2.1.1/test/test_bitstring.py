#!/usr/bin/env python
"""
Module-level unit tests.
"""

import unittest
import sys
sys.path.insert(0, '..')
import bitstring


class ModuleData(unittest.TestCase):

    def testVersion(self):
        self.assertEqual(bitstring.__version__, '2.1.1')

#    def testAll(self):
#        exported = ['ConstBitArray', 'ConstBitStream', 'BitStream', 'BitArray',
#                    'Bits', 'BitString', 'pack', 'Error', 'ReadError',
#                    'InterpretError', 'ByteAlignError', 'CreationError']
#        self.assertEqual(set(bitstring.__all__), set(exported))

    def testReverseDict(self):
        d = bitstring.constbitarray.BYTE_REVERSAL_DICT
        for i in range(256):
            a = bitstring.ConstBitArray(uint=i, length=8)
            b = d[i]
            self.assertEqual(a.bin[2:][::-1], bitstring.ConstBitArray(bytes=b).bin[2:])


class MemoryUsage(unittest.TestCase):

    def testBaselineMemory(self):
        try:
            import pympler.asizeof.asizeof as size
        except ImportError:
            return
        # These values might be platform dependent, so don't fret too much.
        self.assertEqual(size(bitstring.ConstBitStream([0])), 120)
        self.assertEqual(size(bitstring.ConstBitArray([0])), 112)
        self.assertEqual(size(bitstring.BitStream([0])), 120)
        self.assertEqual(size(bitstring.BitArray([0])), 112)
