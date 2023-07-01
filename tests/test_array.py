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
        with self.assertRaises(bitstring.CreationError):
            b = Array('bits:8', a)

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

        a = Array('d', [0, 0, 1])
        with self.assertRaises(ValueError):
            a.fmt = 'se'
        self.assertEqual(a[-1], 1.0)
        self.assertEqual(a.fmt, 'd')

    def testChangingFormatWithTrailingBits(self):
        a = Array('bool', 803)
        self.assertEqual(len(a), 803)
        a.fmt = 'e'
        self.assertEqual(len(a), 803 // 16)
        b = Array('f', [0])
        b.fmt = 'i3'
        self.assertEqual(b.tolist(), [0]*10)
        x = b.__repr__()

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

        c = Array('e', trailing_bits='0x0000, 0b1')
        self.assertEqual(c[0], 0.0)
        self.assertEqual(c.tolist(), [0.0])

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
        c = Array('bin:40')
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

        b = Array('h12')
        with self.assertRaises(ValueError):
            b.append('12')
        b.append('123')
        with self.assertRaises(ValueError):
            b.extend(['3456'])
        b.extend(['345'])
        self.assertEqual(b.tolist(), ['123', '345'])
        with self.assertRaises(ValueError):
            b[0] = 'abcd'
        with self.assertRaises(ValueError):
            b[0] = 12
        with self.assertRaises(ValueError):
            b[0] = Bits('0xfff')
        b[0] = 'fff'
        self.assertEqual(b.data.hex, 'fff345')

    def testEquivalence(self):
        a = Array('floatne32', [54.2, -998, 411.9])
        b = Array('floatne32')
        b.extend(a.tolist())
        self.assertEqual(a.data, b.data)

        b = array.array('f', [54.2, -998, 411.9])
        self.assertEqual(a, b)
        a.fmt = 'bool'
        self.assertNotEqual(a, b)
        a.fmt = 'floatne16'
        self.assertNotEqual(a, b)
        a.fmt = 'floatne32'
        a.data += '0x0'
        self.assertNotEqual(a, b)
        a.data += '0x0000000'
        self.assertNotEqual(a, b)
        b.append(0.0)
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
        del a.data[0]
        with self.assertRaises(ValueError):
            a.extend([1, 0])

    def testInsert(self):
        a = Array('hex:12', ['abc', 'def'])
        self.assertEqual(a.data.hex, 'abcdef')
        a.insert(0, '000')
        self.assertEqual(a.data.hex, '000abcdef')
        a.insert(-1, '111')
        self.assertEqual(a[-1], 'def')
        self.assertEqual(a[-2], '111')
        a.data += '0b1'
        self.assertEqual(a[-1], 'def')
        a.insert(1, '111')
        self.assertEqual(a.tolist(), ['000', '111', 'abc', '111', 'def'])

        with self.assertRaises(ValueError):
            a.insert(2, 'hello')
        with self.assertRaises(ValueError):
            a.insert(2, 'ab')

    def testPop(self):
        a = Array('oct:6', ['33', '21', '11', '76'])
        self.assertEqual(len(a), 4)
        x = a.pop()
        self.assertEqual(len(a), 3)
        self.assertEqual(x, '76')
        with self.assertRaises(IndexError):
            _ = a.pop(3)
        x = a.pop(2)
        self.assertEqual(x, '11')
        x = a.pop(0)
        self.assertEqual(x, '33')
        x = a.pop()
        self.assertEqual(x, '21')
        with self.assertRaises(IndexError):
            _ = a.pop()

    def testReverse(self):
        a = Array('int30', [])
        a.reverse()
        self.assertEqual(a.tolist(), [])
        a.append(2)
        a.reverse()
        self.assertEqual(a.tolist(), [2])
        a.append(3)
        a.reverse()
        self.assertEqual(a.tolist(), [3, 2])
        a.data.clear()
        a.fromlist(list(range(1000)))
        a.reverse()
        self.assertEqual(a.tolist(), list(range(999, -1, -1)))
        x = a.pop(0)
        self.assertEqual(x, 999)
        a.reverse()
        self.assertEqual(a.tolist(), list(range(0, 999)))
        a.data += '0b1'
        with self.assertRaises(ValueError):
            a.reverse()

    def testByteswap(self):
        a = Array('float16')
        a.byteswap()
        self.assertEqual(a.tolist(), [])
        b = Array('uint17')
        with self.assertRaises(ValueError):
            b.byteswap()
        a.fromlist([0.25, 104, -6])
        a.byteswap()
        self.assertEqual(a.data.unpack('3*floatle16'), [0.25, 104, -6])
        a.byteswap()
        self.assertEqual(a.tolist(), [0.25, 104, -6])

    def testToFile(self):
        filename = os.path.join(THIS_DIR, 'temp_bitstring_unit_testing_file')
        a = Array('uint5', [0, 1, 2, 3, 4, 5])
        with open(filename, 'wb') as f:
            a.tofile(f)
        with open(filename, 'rb') as f:
            b = Array('u5')
            b.fromfile(f, 1)
        self.assertEqual(b.tolist(), [0])

    def testGetting(self):
        a = Array('int17')
        with self.assertRaises(IndexError):
            _ = a[0]
        a.extend([1, 2, 3, 4])
        self.assertEqual(a[:], [1, 2, 3, 4])
        self.assertEqual(a[:1], [1])
        self.assertEqual(a[1:3], [2, 3])
        self.assertEqual(a[-2:], [3, 4])
        self.assertEqual(a[::2], [1, 3])
        self.assertEqual(a[::-2], [4, 2])

    def testSetting(self):
        a = Array('i1', [0, -1, -1, 0, 0, -1, 0])
        a[0] = -1
        self.assertEqual(a[0], -1)
        a[0:3] = [0, 0]
        self.assertEqual(a[:], [0, 0, 0, 0, -1, 0])
        b = Array('i20', a)
        with self.assertRaises(ValueError):
            b[::2] = 9
        b[::2] = [9]*3
        self.assertEqual(b[:], [9, 0, 9, 0, 9, 0])
        b[1:4] = a[-2:]
        self.assertEqual(b[:], [9, -1, 0, 9, 0])

    def testDeleting(self):
        a = Array('u99', list(range(1000)))
        del a[::2]
        self.assertEqual(len(a), 500)
        del a[-100:]
        self.assertEqual(len(a), 400)
        self.assertEqual(a[:10], [1, 3, 5, 7, 9, 11, 13, 15, 17, 19])

    def testToBytes(self):
        pass



