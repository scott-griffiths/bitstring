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

class NoPosAttribute(unittest.TestCase):

    def testReplace(self):
        s = BitArray('0b01')
        s.replace('0b1', '0b11')
        self.assertEqual(s, '0b011')

    def testDelete(self):
        s = BitArray('0b000000001')
        del s[-1:]
        self.assertEqual(s, '0b00000000')

    def testInsert(self):
        s = BitArray('0b00')
        s.insert('0xf', 1)
        self.assertEqual(s, '0b011110')

    def testInsertParameters(self):
        s = BitArray('0b111')
        self.assertRaises(TypeError, s.insert, '0x4')

    def testOverwrite(self):
        s = BitArray('0b01110')
        s.overwrite('0b000', 1)
        self.assertEqual(s, '0b00000')

    def testOverwriteParameters(self):
        s = BitArray('0b0000')
        self.assertRaises(TypeError, s.overwrite, '0b111')

    def testPrepend(self):
        s = BitArray('0b0')
        s.prepend([1])
        self.assertEqual(s, [1, 0])

    def testRol(self):
        s = BitArray('0b0001')
        s.rol(1)
        self.assertEqual(s, '0b0010')

    def testRor(self):
        s = BitArray('0b1000')
        s.ror(1)
        self.assertEqual(s, '0b0100')

    def testSetItem(self):
        s = BitArray('0b000100')
        s[4:5] = '0xf'
        self.assertEqual(s, '0b000111110')
        s[0:1] = [1]
        self.assertEqual(s, '0b100111110')

class Bugs(unittest.TestCase):
    
    def testAddingNonsense(self):
        a = BitArray([0])
        a += '0' # a uint of length 0 - so nothing gets added.
        self.assertEqual(a, [0])
        self.assertRaises(ValueError, a.__iadd__, '3')
        self.assertRaises(ValueError, a.__iadd__, 'se')
        self.assertRaises(ValueError, a.__iadd__, 'float:32')
