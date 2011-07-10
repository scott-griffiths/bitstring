#!/usr/bin/env python

import unittest
import sys
sys.path.insert(0, '..')
import bitstring.bitstore as bitstore
from bitstring.bitstore import ByteStore, ConstByteStore


class OffsetCopy(unittest.TestCase):
    def testStraightCopy(self):
        s = ByteStore(bytearray([10, 5, 1]), 24, 0)
        t = bitstore.offsetcopy(s, 0)
        self.assertEqual(t._rawarray, bytearray([10, 5, 1]))

    def testOffsetIncrease(self):
        s = ByteStore(bytearray([1, 1, 1]), 24, 0)
        t = bitstore.offsetcopy(s, 4)
        self.assertEqual(t.bitlength, 24)
        self.assertEqual(t.offset, 4)
        self.assertEqual(t._rawarray, bytearray([0, 16, 16, 16]))


class Equals(unittest.TestCase):

    def testBothSingleByte(self):
        s = ByteStore(bytearray([128]), 3, 0)
        t = ByteStore(bytearray([64]), 3, 1)
        u = ByteStore(bytearray([32]), 3, 2)
        self.assertTrue(bitstore.equal(s, t))
        self.assertTrue(bitstore.equal(s, u))
        self.assertTrue(bitstore.equal(u, t))

    def testOneSingleByte(self):
        s = ByteStore(bytearray([1, 0]), 2, 7)
        t = ByteStore(bytearray([64]), 2, 1)
        self.assertTrue(bitstore.equal(s, t))
        self.assertTrue(bitstore.equal(t, s))