#!/usr/bin/env python
"""
Module-level unit tests.
"""

import unittest
import sys
sys.path.insert(0, '..')
import bitstring
import copy


class ModuleData(unittest.TestCase):
    def testVersion(self):
        self.assertEqual(bitstring.__version__, '2.2.0')

    def testAll(self):
        exported = ['ConstBitArray', 'ConstBitStream', 'BitStream', 'BitArray',
                    'Bits', 'BitString', 'pack', 'Error', 'ReadError',
                    'InterpretError', 'ByteAlignError', 'CreationError', 'bytealigned']
        self.assertEqual(set(bitstring.__all__), set(exported))

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
        self.assertEqual(size(bitstring.ConstBitStream([0])), 64)
        self.assertEqual(size(bitstring.ConstBitArray([0])), 64)
        self.assertEqual(size(bitstring.BitStream([0])), 64)
        self.assertEqual(size(bitstring.BitArray([0])), 64)
        from bitstring.bitstore import ByteArray
        self.assertEqual(size(ByteArray(bytearray())), 100)


class Copy(unittest.TestCase):
    def testConstBitArrayCopy(self):
        import copy
        cba = bitstring.ConstBitArray(100)
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
    def testCBA(self):
        a = bitstring.ConstBitArray('0xf')
        b = bitstring.ConstBitArray('0xf')
        self.assertTrue(a is b)
        c = bitstring.ConstBitArray('0b1111')
        self.assertFalse(a is c)

    def testCBS(self):
        a = bitstring.ConstBitStream('0b11000')
        b = bitstring.ConstBitStream('0b11000')
        self.assertFalse(a is b)
    #        self.assertTrue(a._datastore is b._datastore)
        
        
        
        