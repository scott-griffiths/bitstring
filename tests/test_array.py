#!/usr/bin/env python
import io
import unittest
import sys

sys.path.insert(0, '..')
import bitstring
import array
import os
from bitstring import Array, Bits, BitArray
import copy

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

    def testEqualsWithTrailingBits(self):
        a = Array('hex4', ['a', 'b', 'c', 'd', 'e', 'f'])
        c = Array('hex4')
        c.data = BitArray('0xabcdef, 0b11')
        self.assertEqual(a.tolist(), c.tolist())
        self.assertNotEqual(a, c)
        a.data.append('0b11')
        self.assertEqual(a.tolist(), c.tolist())
        self.assertEqual(a, c)

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

    def testExtendWithMixedClasses(self):
        a = Array('uint8', [1, 2, 3])
        b = array.array('B', [4, 5, 6])
        ap = Array('uint8', a[:])
        bp = array.array('B', b[:])
        a.extend(b)
        bp.extend(ap)
        self.assertEqual(a.tolist(), [1, 2, 3, 4, 5, 6])
        self.assertEqual(bp.tolist(), [4, 5, 6, 1, 2, 3])

        a.fmt = 'int8'
        ap = Array('uint8', a[:])
        self.assertNotEqual(a, ap)
        self.assertEqual(a.tolist(), ap.tolist())

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
        self.assertEqual(a[:], Array('i17', [1, 2, 3, 4]))
        self.assertEqual(a[:1], Array('i17', [1]))
        self.assertEqual(a[1:3], Array('i17', [2, 3]))
        self.assertEqual(a[-2:], Array('i17', [3, 4]))
        self.assertEqual(a[::2], Array('i17', [1, 3]))
        self.assertEqual(a[::-2], Array('i17', [4, 2]))

    def testSetting(self):
        a = Array('i1', [0, -1, -1, 0, 0, -1, 0])
        a[0] = -1
        self.assertEqual(a[0], -1)
        a[0:3] = [0, 0]
        self.assertEqual(a.tolist(), [0, 0, 0, 0, -1, 0])
        b = Array('i20', a)
        with self.assertRaises(TypeError):
            b[::2] = 9
        b[::2] = [9]*3
        self.assertEqual(b.tolist(), [9, 0, 9, 0, 9, 0])
        b[1:4] = a[-2:]
        self.assertEqual(b.tolist(), [9, -1, 0, 9, 0])

    def testDeleting(self):
        a = Array('u99', list(range(1000)))
        del a[::2]
        self.assertEqual(len(a), 500)
        del a[-100:]
        self.assertEqual(len(a), 400)
        self.assertEqual(a[:10].tolist(), [1, 3, 5, 7, 9, 11, 13, 15, 17, 19])

    def testRepr(self):
        a = Array('int5')
        b = eval(a.__repr__())
        self.assertEqual(a, b)
        a.data += '0b11'

        b = eval(a.__repr__())
        self.assertEqual(a, b)

        a.data += '0b000'
        b = eval(a.__repr__())
        self.assertEqual(a, b)

        a.fromlist([1]*9)
        b = eval(a.__repr__())
        self.assertEqual(a, b)

        a.fromlist([-4]*100)
        b = eval(a.__repr__())
        self.assertEqual(a, b)

        a.fmt = 'float32'
        b = eval(a.__repr__())
        self.assertEqual(a, b)

    def testToBytes(self):
        pass

    def test__add__(self):
        a = Array('B', [1, 2, 3])
        b = Array('B', [3, 4])
        c = a + b
        self.assertEqual(a, Array('B', [1, 2, 3]))
        self.assertEqual(c, Array('B', [1, 2, 3, 3, 4]))
        d = a + [10, 11, 12]
        self.assertEqual(d, Array('B', [1, 2, 3, 10, 11, 12]))

    def test__add__array(self):
        a = array.array('B', [10, 11])
        b = a + Array('B', [12, 13])
        self.assertEqual(b, array.array('B', [10, 11, 12, 13]))
        c = Array('B', [0, 1, 2]) + a
        self.assertEqual(c, Array('uint8', [0, 1, 2, 10, 11]))
        c.data += '0x0'
        with self.assertRaises(ValueError):
            _ = c + a

    def test__contains__(self):
        a = Array('i9', [-1, 88, 3])
        self.assertTrue(88 in a)
        self.assertFalse(89 in a)

    def test__copy__(self):
        a = Array('i4')
        a.data += '0x123451234561'
        b = copy.copy(a)
        self.assertEqual(a, b)
        a.data += '0b1010'
        self.assertNotEqual(a, b)

    def test__iadd__(self):
        a = Array('uint999')
        a += [4]
        self.assertEqual(a.tolist(), [4])
        a += 5
        a += a
        self.assertEqual(a.tolist(), [9, 9])

    def test__radd__(self):
        a = Array('f', [3, 2, 1])
        b = array.array('f', [-3, -2, -1])
        c = b + a
        self.assertEqual(c.tolist(), [-3, -2, -1, 3, 2, 1])
        self.assertEqual(c.itemsize, 32)
        self.assertTrue(isinstance(c, Array))

    def testFloat8Bug(self):
        a = Array('float8_152', [0.0, 1.5])
        b = Array('float8_143')
        b[:] = a[:]
        self.assertEqual(b[:], Array('float8_143', [0.0, 1.5]))


class ArrayOperations(unittest.TestCase):

    def testInPlaceAdd(self):
        a = Array('i7', [-9, 4, 0])
        a.__iadd__(9)
        self.assertEqual(a.tolist(), [0, 13, 9])
        self.assertEqual(len(a.data), 21)

    def testAdd(self):
        a = Array('d')
        a.fromlist([1.0, -2.0, 100.5])
        b = a + 2
        self.assertEqual(a, Array('d', [1.0, -2.0, 100.5]))
        self.assertEqual(b, Array('d', [3.0, 0.0, 102.5]))

    def testSub(self):
        a = Array('uint44', [3, 7, 10])
        b = a - 3
        self.assertEqual(b, Array('u44', [0, 4, 7]))
        with self.assertRaises(bitstring.CreationError):  # TODO: This would be more naturally an OverflowError ?
            _ = a - 4

    def testInPlaceSub(self):
        a = Array('float16', [-9, -10.5])
        a.__isub__(-1.5)
        self.assertEqual(a.tolist(), [-7.5, -9.0])

    def testMul(self):
        a = Array('i21', [-5, -4, 0, 2, 100])
        b = a * 2
        self.assertEqual(b.tolist(), [-10, -8, 0, 4, 200])


    # TODO: Tests for rmul, radd etc?

    def testInPlaceMul(self):
        a = Array('i21', [-5, -4, 0, 2, 100])
        a.__imul__(0.5)
        self.assertEqual(a.tolist(), [-2, -2, 0, 1, 50])

    def testDiv(self):
        pass

    def testInPlaceDiv(self):
        pass

    def testAnd(self):
        pass

    def testInPlaceAnd(self):
        pass

    def testOr(self):
        pass

    def testInPlaceOr(self):
        pass

    def testXor(self):
        pass

    def testInPlaceXor(self):
        pass

    def testRshift(self):
        pass

    def testInPlaceRshift(self):
        pass

    def testLshift(self):
        pass

    def testInPlaceLshift(self):
        pass