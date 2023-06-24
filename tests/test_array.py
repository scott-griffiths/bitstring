#!/usr/bin/env python
import io
import unittest
import sys

sys.path.insert(0, '..')
import bitstring
import array
import os
from bitstring import Array, Bits, BitArray


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class Creation(unittest.TestCase):

    def testCreationFromInt(self):
        a = Array('u12', 20)
        self.assertEqual(len(a), 20)
        self.assertEqual(a[19], 0)
        with self.assertRaises(IndexError):
            _ = a[20]

    def testCreationFromIntList(self):
        a = Array('i4', [-3, -2, -1, 0, 7])
        self.assertEqual(len(a), 5)
        self.assertEqual(a[2], -1)
        self.assertEqual(a[-1], 7)

    def testCreationFromBytes(self):
        a = Array('hex:8', b'ABCD')
        self.assertEqual(a[0], '41')
        self.assertEqual(a[1], '42')
        self.assertEqual(a[2], '43')
        self.assertEqual(a[3], '44')

    def testCreationFromBits(self):
        a = Bits('0x000102030405')
        b = Array('bits:8', a)
        c = b.tolist()
        self.assertEqual(c[0], Bits('0x00'))
        self.assertEqual(c[-1], Bits('0x05'))

    def testCreationFromFloat8(self):
        x = b'\x7f\x00'
        a = Array('float8_143', x)
        self.assertEqual(a[0], 240.0)
        self.assertEqual(a[1], 0.0)
        b = Array('float8_143', [100000, -0.0])
        self.assertEqual(a, b)

    def testCreationFromMultiple(self):
        with self.assertRaises(ValueError):
            a = Array('2*float16')

    def testChangingFmt(self):
        a = Array('uint8', [255]*100)
        self.assertEqual(len(a), 100)
        a.fmt = 'int4'
        self.assertEqual(len(a), 200)
        self.assertEqual(a.count(-1), 200)
        a.append(5)
        self.assertEqual(len(a), 201)
        self.assertEqual(a.count(-1), 200)

    def testCreationWithTrailingBits(self):
        a = Array('bool', trailing_bits='0xf')
        self.assertEqual(a.data, '0b1111')
        self.assertEqual(len(a), 4)

        b = Array('bin:3', ['111', '000', '111'])
        self.assertEqual(len(b), 3)
        self.assertEqual(b.data, '0b111000111')
        b.fmt = 'h4'
        self.assertEqual(len(b), 2)
        with self.assertRaises(ValueError):
            b.append('f')
        del b.data[0]
        b.append('f')
        self.assertEqual(len(b), 3)

    def testCreationWithArrayCode(self):
        a = Array('f')
        self.assertEqual(a.itemsize, 32)



class ArrayMethods(unittest.TestCase):

    def testCount(self):
        a = Array('u9', [0, 4, 3, 2, 3, 4, 2, 3, 2, 1, 2, 11, 2, 1])
        self.assertEqual(a.count(0), 1)
        self.assertEqual(a.count(-1), 0)
        self.assertEqual(a.count(2), 5)

    def testFromBytes(self):
        a = Array('i16')
        self.assertEqual(len(a), 0)
        a.frombytes(bytearray([0, 0, 0, 55]))
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0], 0)
        self.assertEqual(a[1], 55)
        a.frombytes(b'\x01\x00')
        self.assertEqual(len(a), 3)
        self.assertEqual(a[-1], 256)

        a.frombytes(bytearray())
        self.assertEqual(len(a), 3)

        with self.assertRaises(TypeError):
            a.frombytes('i16=-45')
        with self.assertRaises(TypeError):
            a.frombytes(16)

    def testEquals(self):
        a = Array('hex:40')
        b = Array('h40')
        self.assertEqual(a, b)
        c = Array('bin:160')
        self.assertNotEqual(a, c)
        v = ['1234567890']
        a.extend(v)
        b.extend(v)
        self.assertEqual(a, b)
        b.extend(v)
        self.assertNotEqual(a, b)

        a = Array('uint20', [16, 32, 64, 128])
        b = Array('uint10', [0, 16, 0, 32, 0, 64, 0, 128])
        self.assertNotEqual(a, b)
        b.fmt = 'u20'
        self.assertEqual(a, b)
        a.data += '0b1'
        self.assertNotEqual(a, b)
        b.data += '0b1'
        self.assertEqual(a, b)

    def testSetting(self):
        a = Array('bool')
        a.data += b'\x00'
        a[0] = 1
        self.assertEqual(a[0], True)

    def testEquivalence(self):
        a = Array('floatne32', [54.2, -998, 411.9])
        b = Array('floatne32')
        b.extend(a.tolist())
        self.assertEqual(a.data, b.data)

        b = array.array('f', [54.2, -998, 411.9])
        self.assertEqual(a, b)

    def testExtend(self):
        a = Array('uint:3', (1, 2, 3))
        a.extend([4, 5, 6])
        self.assertEqual(a.tolist(), [1, 2, 3, 4, 5, 6])
        a.extend([])
        self.assertEqual(a.tolist(), [1, 2, 3, 4, 5, 6])
        a.extend(a)
        self.assertEqual(a.tolist(), [1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6])
        b = Array('int:3', [0])
        with self.assertRaises(TypeError):
            a.extend(b)
