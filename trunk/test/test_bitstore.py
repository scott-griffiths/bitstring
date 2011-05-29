#!/usr/bin/env python

import unittest
import sys
sys.path.insert(0, '..')
import bitstring.bitstore as bitstore


class Mmap(unittest.TestCase):
    def setUp(self):
        self.f = open('smalltestfile', 'rb')

    def tearDown(self):
        self.f.close()

    def testByteArrayEquivalence(self):
        a = bitstore.MmapByteArray(self.f)
        self.assertEqual(a.bytelength, 8)
        self.assertEqual(len(a), 8)
        self.assertEqual(a[0], 0x01)
        self.assertEqual(a[1], 0x23)
        self.assertEqual(a[7], 0xef)
        self.assertEqual(a[0:1], bytearray([1]))
        self.assertEqual(a[:], bytearray([0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef]))
        self.assertEqual(a[2:4], bytearray([0x45, 0x67]))

    def testWithLength(self):
        a = bitstore.MmapByteArray(self.f, 3)
        self.assertEqual(a[0], 0x01)
        self.assertEqual(len(a), 3)

    def testWithOffset(self):
        a = bitstore.MmapByteArray(self.f, None, 5)
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0], 0xab)

    def testWithLengthAndOffset(self):
        a = bitstore.MmapByteArray(self.f, 3, 3)
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0], 0x67)
        self.assertEqual(a[:], bytearray([0x67, 0x89, 0xab]))
