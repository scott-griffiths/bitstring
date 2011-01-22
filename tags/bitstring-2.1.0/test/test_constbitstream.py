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

