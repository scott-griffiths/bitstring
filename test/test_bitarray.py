#!/usr/bin/env python
"""
Unit tests for the bitarray module.
"""

import unittest
import sys
sys.path.insert(0, '..')
import bitstring
from bitstring import BitArray

class All(unittest.TestCase):

    def testCreationFromUint(self):
        s = BitArray(uint = 15, length=6)
        self.assertEqual(s.bin, '0b001111')
        s = BitArray(uint = 0, length=1)
        self.assertEqual(s.bin, '0b0')
        s.uint = 1
        self.assertEqual(s.uint, 1)
        s = BitArray(length=8)
        s.uint = 0
        self.assertEqual(s.uint, 0)
        s.uint = 255
        self.assertEqual(s.uint, 255)
        self.assertEqual(s.len, 8)
        self.assertRaises(bitstring.CreationError, s._setuint, 256)

    def testCreationFromOct(self):
        s = BitArray(oct='7')
        self.assertEqual(s.oct, '0o7')
        self.assertEqual(s.bin, '0b111')
        s.append('0o1')
        self.assertEqual(s.bin, '0b111001')
        s.oct = '12345670'
        self.assertEqual(s.length, 24)
        self.assertEqual(s.bin, '0b001010011100101110111000')
        s = BitArray('0o123')
        self.assertEqual(s.oct, '0o123')
