#!/usr/bin/env python

import unittest
import sys
sys.path.insert(0, '..')
import bitstring
from bitstring import ConstBitStream as CBS

class All(unittest.TestCase):

    def testFromFile(self):
        s = CBS(filename = 'test.m1v')
        self.assertEqual(s[0:32].hex, '0x000001b3')
        self.assertEqual(s.read(8*4).hex, '0x000001b3')
        width = s.read(12).uint
        height = s.read(12).uint
        self.assertEqual((width, height), (352, 288))


class InterleavedExpGolomb(unittest.TestCase):    

    def testReading(self):
        s = CBS(uie=333)
        a = s.read('uie')
        self.assertEqual(a, 333)
        s = CBS('uie=12, sie=-9, sie=9, uie=1000000')
        u = s.unpack('uie, 2*sie, uie')
        self.assertEqual(u, [12, -9, 9, 1000000])
        
    def testReadingErrors(self):
        s = CBS(10)
        self.assertRaises(bitstring.ReadError, s.read, 'uie')
        self.assertEqual(s.pos, 0)
        self.assertRaises(bitstring.ReadError, s.read, 'sie')
        self.assertEqual(s.pos, 0)