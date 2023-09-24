#!/usr/bin/env python
import unittest
import sys
import bitstring
import array
import os
from bitstring import Array, Bits, BitArray
import copy
import itertools
import io

sys.path.insert(0, '..')


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

    def testCreationFromBytesExplicit(self):
        a = Array('hex:8')
        a.data.bytes = b'ABCD'
        self.assertEqual(a[0], '41')
        self.assertEqual(a[1], '42')
        self.assertEqual(a[2], '43')
        self.assertEqual(a[3], '44')

    def testCreationFromBitsFormat(self):
        a = Bits('0x000102030405')
        b = Array('bits:8', a)
        c = Array('bits:8', [Bits('0x00'), Bits('0x01'), Bits('0x02'), Bits('0x03'), Bits('0x04'), Bits('0x05')])
        self.assertTrue(b.equals(c))

    def testCreationFromFloat8(self):
        a = Array('e4m3float')
        a.data.bytes = b'\x7f\x00'
        self.assertEqual(a[0], 240.0)
        self.assertEqual(a[1], 0.0)
        b = Array('e4m3float', [100000, -0.0])
        self.assertTrue(a.equals(b))

    def testCreationFromMultiple(self):
        with self.assertRaises(ValueError):
            _ = Array('2*float16')

    def testChangingFmt(self):
        a = Array('uint8', [255]*100)
        self.assertEqual(len(a), 100)
        a.dtype = 'int4'
        self.assertEqual(len(a), 200)
        self.assertEqual(a.count(-1), 200)
        a.append(5)
        self.assertEqual(len(a), 201)
        self.assertEqual(a.count(-1), 200)

        a = Array('>d', [0, 0, 1])
        with self.assertRaises(ValueError):
            a.dtype = 'se'
        self.assertEqual(a[-1], 1.0)
        self.assertEqual(a.dtype, '>d')

    def testChangingFormatWithTrailingBits(self):
        a = Array('bool', 803)
        self.assertEqual(len(a), 803)
        a.dtype = '>e'
        self.assertEqual(len(a), 803 // 16)
        b = Array('>f', [0])
        b.dtype = 'i3'
        self.assertEqual(b.tolist(), [0]*10)

    def testCreationWithTrailingBits(self):
        a = Array('bool', trailing_bits='0xf')
        self.assertEqual(a.data, '0b1111')
        self.assertEqual(len(a), 4)

        b = Array('bin:3', ['111', '000', '111'])
        self.assertEqual(len(b), 3)
        self.assertEqual(b.data, '0b111000111')
        b.dtype = 'h4'
        self.assertEqual(len(b), 2)
        with self.assertRaises(ValueError):
            b.append('f')
        del b.data[0]
        b.append('f')
        self.assertEqual(len(b), 3)

        c = Array('>e', trailing_bits='0x0000, 0b1')
        self.assertEqual(c[0], 0.0)
        self.assertEqual(c.tolist(), [0.0])

    def testCreationWithArrayCode(self):
        a = Array('<f')
        self.assertEqual(a.itemsize, 32)

    def testCreationFromBytes(self):
        a = Array('u8', b'ABC')
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0], 65)
        self.assertFalse(a.trailing_bits)

    def testCreationFromBytearray(self):
        a = Array('u7', bytearray(range(70)))
        self.assertEqual(len(a), 80)
        self.assertFalse(a.trailing_bits)

    def testCreationFromMemoryview(self):
        x = b'1234567890'
        m = memoryview(x[2:5])
        self.assertEqual(m, b'345')
        a = Array('u8', m)
        self.assertEqual(a.tolist(), [ord('3'), ord('4'), ord('5')])

    def testCreationFromBits(self):
        a = bitstring.pack('20*i19', *range(-10, 10))
        b = Array('i19', a)
        self.assertEqual(b.tolist(), list(range(-10, 10)))

    def testCreationFromArrayArray(self):
        a = array.array('H', [10, 20, 30, 40])
        b = Array('uintne16', a)
        self.assertEqual(a.tolist(), b.tolist())
        self.assertEqual(a.tobytes(), b.tobytes())
        with self.assertRaises(ValueError):
            _ = Array('float16', a)

    def testCreationFromFile(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        with open(filename, 'rb') as f:
            a = Array('uint8', f)
            self.assertEqual(a[0:4].tobytes(), b'\x00\x00\x01\xb3')

    def testDifferentTypeCodes(self):
        a = Array('>H', [10, 20])
        self.assertEqual(a.data.unpack('2*uint16'), a.tolist())
        a = Array('<h', [-10, 20])
        self.assertEqual(a.data.unpack('2*intle16'), a.tolist())
        a = Array('<e', [0.25, -1000])
        self.assertEqual(a.data.unpack('2*floatle16'), a.tolist())

    def testFormatChanges(self):
        a = Array('uint8', [5, 4, 3])
        with self.assertRaises(ValueError):
            a.dtype = 'ue3'
        b = a[:]
        b.dtype = 'int8'
        self.assertEqual(a.tolist(), b.tolist())
        self.assertNotEqual(a, b)
        with self.assertRaises(ValueError):
            b.dtype = 'hello_everyone'
        with self.assertRaises(ValueError):
            b.dtype = 'float'
        with self.assertRaises(ValueError):
            b.dtype = 'uintle12'
        with self.assertRaises(ValueError):
            b.dtype = 'float17'


class ArrayMethods(unittest.TestCase):

    def testCount(self):
        a = Array('u9', [0, 4, 3, 2, 3, 4, 2, 3, 2, 1, 2, 11, 2, 1])
        self.assertEqual(a.count(0), 1)
        self.assertEqual(a.count(-1), 0)
        self.assertEqual(a.count(2), 5)

    def testCountNan(self):
        a = Array('uint8', [0, 10, 128, 128, 4, 2, 1])
        a.dtype = 'e5m2float'
        self.assertEqual(a.count(float('nan')), 2)

    def testFromBytes(self):
        a = Array('i16')
        self.assertEqual(len(a), 0)
        a.data += bytearray([0, 0, 0, 55])
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0], 0)
        self.assertEqual(a[1], 55)
        a.data += b'\x01\x00'
        self.assertEqual(len(a), 3)
        self.assertEqual(a[-1], 256)
        a.data += bytearray()
        self.assertEqual(len(a), 3)

    def testEquals(self):
        a = Array('hex:40')
        b = Array('h40')
        self.assertTrue(a.equals(b))
        c = Array('bin:40')
        self.assertFalse(a.equals(c))
        v = ['1234567890']
        a.extend(v)
        b.extend(v)
        self.assertTrue(a.equals(b))
        b.extend(v)
        self.assertFalse(a.equals(b))

        a = Array('uint20', [16, 32, 64, 128])
        b = Array('uint10', [0, 16, 0, 32, 0, 64, 0, 128])
        self.assertFalse(b.equals(a))
        b.dtype = 'u20'
        self.assertTrue(a.equals(b))
        a.data += '0b1'
        self.assertFalse(a.equals(b))
        b.data += '0b1'
        self.assertTrue(a.equals(b))

        c = Array('uint8', [1, 2])
        self.assertFalse(c.equals('hello'))
        self.assertFalse(c.equals(array.array('B', [1, 3])))

    def testEqualsWithTrailingBits(self):
        a = Array('hex4', ['a', 'b', 'c', 'd', 'e', 'f'])
        c = Array('hex4')
        c.data = BitArray('0xabcdef, 0b11')
        self.assertEqual(a.tolist(), c.tolist())
        self.assertNotEqual(a, c)
        a.data.append('0b11')
        self.assertEqual(a.tolist(), c.tolist())
        self.assertTrue(a.equals(c))

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

    def testSettingFromIterable(self):
        a = Array('uint99', range(100))
        x = itertools.chain([1, 2, 3], [4, 5])
        a[10:15] = x
        self.assertEqual(a[10:15].tolist(), list(range(1, 6)))
        x = itertools.chain([1, 2, 3], [4, 5])
        a[50:60:2] = x
        self.assertEqual(a[50:60:2].tolist(), list(range(1, 6)))

    def testEquivalence(self):
        a = Array('floatne32', [54.2, -998, 411.9])
        b = Array('floatne32')
        b.extend(a.tolist())
        self.assertEqual(a.data, b.data)

        b = array.array('f', [54.2, -998, 411.9])
        self.assertEqual(a, b)
        a.dtype = 'bool'
        self.assertNotEqual(a, b)
        a.dtype = 'floatne16'
        self.assertNotEqual(a, b)
        a.dtype = 'floatne32'
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
        del a.data[-2:]
        with self.assertRaises(TypeError):
            a.extend('uint:3=3')  # Can't extend with a str even though it's iterable

    def testExtendWithMixedClasses(self):
        a = Array('uint8', [1, 2, 3])
        b = array.array('B', [4, 5, 6])
        ap = Array('uint8', a[:])
        bp = array.array('B', b[:])
        a.extend(b)
        bp.extend(ap)
        self.assertEqual(a.tolist(), [1, 2, 3, 4, 5, 6])
        self.assertEqual(bp.tolist(), [4, 5, 6, 1, 2, 3])

        a.dtype = 'int8'
        ap = Array('uint8', a.tolist())
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
        with self.assertRaises(IndexError):
            _ = a.pop(4)
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
        a.extend(list(range(1000)))
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
        a.extend([0.25, 104, -6])
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
        self.assertTrue(a[:].equals(Array('i17', [1, 2, 3, 4])))
        self.assertTrue(a[:1].equals(Array('i17', [1])))
        self.assertTrue(a[1:3].equals(Array('i17', [2, 3])))
        self.assertTrue(a[-2:].equals(Array('i17', [3, 4])))
        self.assertTrue(a[::2].equals(Array('i17', [1, 3])))
        self.assertTrue(a[::-2].equals(Array('i17', [4, 2])))

    def testMoreSetting(self):
        a = Array('i1', [0, -1, -1, 0, 0, -1, 0])
        a[0] = -1
        self.assertEqual(a[0], -1)
        a[0:3] = [0, 0]
        self.assertEqual(a.tolist(), [0, 0, 0, 0, -1, 0])
        b = Array('i20', a.tolist())
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
        with self.assertRaises(IndexError):
            del a[len(a)]
        with self.assertRaises(IndexError):
            del a[-len(a) - 1]

    def testDeletingMoreRanges(self):
        a = Array('uint:18', [1, 2, 3, 4, 5, 6])
        del a[3:1:-1]
        self.assertEqual(a.tolist(), [1, 2, 5, 6])


    def testRepr(self):
        a = Array('int5')
        b = eval(a.__repr__())
        self.assertTrue(a.equals(b))
        a.data += '0b11'

        b = eval(a.__repr__())
        self.assertTrue(a.equals(b))

        a.data += '0b000'
        b = eval(a.__repr__())
        self.assertTrue(a.equals(b))

        a.extend([1]*9)
        b = eval(a.__repr__())
        self.assertTrue(a.equals(b))

        a.extend([-4]*100)
        b = eval(a.__repr__())
        self.assertTrue(a.equals(b))

        a.dtype = 'float32'
        b = eval(a.__repr__())
        self.assertTrue(a.equals(b))

    def test__add__(self):
        a = Array('=B', [1, 2, 3])
        b = Array('u8', [3, 4])
        c = a[:]
        c.extend(b)
        self.assertTrue(a.equals(Array('=B', [1, 2, 3])))
        self.assertTrue(c.equals(Array('=B', [1, 2, 3, 3, 4])))
        d = a[:]
        d.extend([10, 11, 12])
        self.assertTrue(d.equals(Array('uint:8', [1, 2, 3, 10, 11, 12])))

    def test__contains__(self):
        a = Array('i9', [-1, 88, 3])
        self.assertTrue(88 in a)
        self.assertFalse(89 in a)

    def test__copy__(self):
        a = Array('i4')
        a.data += '0x123451234561'
        b = copy.copy(a)
        self.assertTrue(a.equals(b))
        a.data += '0b1010'
        self.assertFalse(a.equals(b))

    def test__iadd__(self):
        a = Array('uint999')
        a.extend([4])
        self.assertEqual(a.tolist(), [4])
        a += 5
        a.extend(a)
        self.assertEqual(a.tolist(), [9, 9])

    def testFloat8Bug(self):
        a = Array('e5m2float', [0.0, 1.5])
        b = Array('e4m3float')
        b[:] = a[:]
        self.assertTrue(b[:].equals(Array('e4m3float', [0.0, 1.5])))

    def testPp(self):
        a = Array('bfloat', [-3, 1, 2])
        s = io.StringIO()
        a.pp('hex', stream=s)
        self.assertEqual(s.getvalue(),  "<Array fmt='hex16', length=3, itemsize=16 bits, total data size=6 bytes>\n"
                                        "[\n"
                                        "c040 3f80 4000\n"
                                        "]\n")
        a.data += '0b110'
        a.dtype='hex16'
        s = io.StringIO()
        a.pp(stream=s)
        self.assertEqual(s.getvalue(),  """<Array dtype='hex16', length=3, itemsize=16 bits, total data size=7 bytes>
[
c040 3f80 4000
] + trailing_bits = 0b110\n""")

    def testPpUint(self):
        a = Array('uint32', [12, 100, 99])
        s = io.StringIO()
        a.pp(stream=s)
        self.assertEqual(s.getvalue(), """<Array dtype='uint32', length=3, itemsize=32 bits, total data size=12 bytes>
[
        12        100         99
]\n""")

    def testPpBits(self):
        a = Array('bits2', b'89')
        s = io.StringIO()
        a.pp(stream=s, width=0, show_offset=True)
        self.assertEqual(s.getvalue(), """<Array dtype='bits2', length=8, itemsize=2 bits, total data size=2 bytes>
[
 0: 0b00
 1: 0b11
 2: 0b10
 3: 0b00
 4: 0b00
 5: 0b11
 6: 0b10
 7: 0b01
]\n""")

    def testPpTwoFormats(self):
        a = Array('float16', bytearray(20))
        s = io.StringIO()
        a.pp(stream=s, fmt='e5m2float, bin')
        self.assertEqual(s.getvalue(), """<Array fmt='e5m2float, bin', length=20, itemsize=8 bits, total data size=20 bytes>
[
                0.0                 0.0                 0.0                 0.0 : 00000000 00000000 00000000 00000000
                0.0                 0.0                 0.0                 0.0 : 00000000 00000000 00000000 00000000
                0.0                 0.0                 0.0                 0.0 : 00000000 00000000 00000000 00000000
                0.0                 0.0                 0.0                 0.0 : 00000000 00000000 00000000 00000000
                0.0                 0.0                 0.0                 0.0 : 00000000 00000000 00000000 00000000
]\n""")

    def testPpTwoFormatsNoLength(self):
        a = Array('float16', bytearray(range(50, 56)))
        s = io.StringIO()
        a.pp(stream=s, fmt='u, b')
        self.assertEqual(s.getvalue(), """<Array fmt='u, b16', length=3, itemsize=16 bits, total data size=6 bytes>
[
12851 13365 13879 : 0011001000110011 0011010000110101 0011011000110111
]\n""")


class ArrayOperations(unittest.TestCase):

    def testInPlaceAdd(self):
        a = Array('i7', [-9, 4, 0])
        a += 9
        self.assertEqual(a.tolist(), [0, 13, 9])
        self.assertEqual(len(a.data), 21)

    def testAdd(self):
        a = Array('>d')
        a.extend([1.0, -2.0, 100.5])
        b = a + 2
        self.assertTrue(a.equals(Array('>d', [1.0, -2.0, 100.5])))
        self.assertTrue(b.equals(Array('>d', [3.0, 0.0, 102.5])))

    def testSub(self):
        a = Array('uint44', [3, 7, 10])
        b = a - 3
        self.assertTrue(b.equals(Array('u44', [0, 4, 7])))
        with self.assertRaises(ValueError):
            _ = a - 4

    def testInPlaceSub(self):
        a = Array('float16', [-9, -10.5])
        a -= -1.5
        self.assertEqual(a.tolist(), [-7.5, -9.0])

    def testMul(self):
        a = Array('i21', [-5, -4, 0, 2, 100])
        b = a * 2
        self.assertEqual(b.tolist(), [-10, -8, 0, 4, 200])
        a = Array('int9', [-1, 0, 3])
        b = a * 2
        self.assertEqual(a.tolist(), [-1, 0, 3])
        self.assertEqual(b.tolist(), [-2, 0, 6])
        c = a * 2.5
        self.assertEqual(c.tolist(), [-2, 0, 7])

    def testInPlaceMul(self):
        a = Array('i21', [-5, -4, 0, 2, 100])
        a *= 0.5
        self.assertEqual(a.tolist(), [-2, -2, 0, 1, 50])

    def testDiv(self):
        a = Array('i32', [-2, -1, 0, 1, 2])
        b = a // 2
        self.assertEqual(a.tolist(), [-2, -1, 0, 1, 2])
        self.assertEqual(b.tolist(), [-1, -1, 0, 0, 1])

    def testInPlaceDiv(self):
        a = Array('i10', [-4, -3, -2, -1, 0, 1, 2])
        a //= 2
        self.assertTrue(a.equals(Array('i10', [-2, -2, -1, -1, 0, 0, 1])))

    def testTrueDiv(self):
        a = Array('float16', [5, 10, -6])
        b = a / 4
        self.assertTrue(a.equals(Array('float16', [5.0, 10.0, -6.0])))
        self.assertTrue(b.equals(Array('float16', [1.25, 2.5, -1.5])))

    def testInPlaceTrueDiv(self):
        a = Array('int71', [-4, -3, -2, -1, 0, 1, 2])
        a /= 2
        self.assertTrue(a.equals(Array('int71', [-2, -1, -1, 0, 0, 0, 1])))

    def testAnd(self):
        a = Array('int16', [-1, 100, 9])
        with self.assertRaises(TypeError):
            _ = a & 0
        b = a & '0x0001'
        self.assertEqual(b.tolist(), [1, 0, 1])
        b = a & '0xffff'
        self.assertEqual(b.dtype, 'int16')
        self.assertEqual(b.tolist(), [-1, 100, 9])

    def testInPlaceAnd(self):
        a = Array('bool', [True, False, True])
        with self.assertRaises(TypeError):
            a &= 0b1
        a = Array('uint10', a.tolist())
        a <<= 3
        self.assertEqual(a.tolist(), [8, 0, 8])
        a += 1
        self.assertEqual(a.tolist(), [9, 1, 9])
        with self.assertRaises(ValueError):
            a &= '0b111'
        a &= '0b0000000111'
        self.assertEqual(a.data, '0b 0000000001 0000000001 0000000001')

    def testOr(self):
        a = Array('e4m3float', [-4, 2.5, -9, 0.25])
        b = a | '0b10000000'
        self.assertEqual(a.tolist(), [-4,  2.5, -9,  0.25])
        self.assertEqual(b.tolist(), [-4, -2.5, -9, -0.25])

    def testInPlaceOr(self):
        a = Array('hex:12')
        a.append('f0f')
        a.extend(['000', '111'])
        a |= '0x00f'
        self.assertEqual(a.tolist(), ['f0f', '00f', '11f'])
        with self.assertRaises(TypeError):
            a |= 12

    def testXor(self):
        a = Array('hex8', ['00', 'ff', 'aa'])
        b = a ^ '0xff'
        self.assertEqual(a.tolist(), ['00', 'ff', 'aa'])
        self.assertEqual(b.tolist(), ['ff', '00', '55'])

    def testInPlaceXor(self):
        a = Array('u10', [0, 0xf, 0x1f])
        a ^= '0b00, 0x0f'

    def testRshift(self):
        a = Array(dtype='u8')
        a.data = Bits('0x00010206')
        b = a >> 1
        self.assertEqual(a.tolist(), [0, 1, 2, 6])
        self.assertEqual(b.tolist(), [0, 0, 1, 3])

        a = Array('i10', [-1, 0, -20, 10])
        b = a >> 1
        self.assertEqual(b.tolist(), [-1, 0, -10, 5])
        c = a >> 0
        self.assertEqual(c.tolist(), [-1, 0, -20, 10])
        with self.assertRaises(ValueError):
            _ = a >> -1

    def testInPlaceRshift(self):
        a = Array('i8', [-8, -1, 0, 1, 100])
        a >>= 1
        self.assertEqual(a.tolist(), [-4, -1, 0, 0, 50])
        a >>= 100000
        self.assertEqual(a.tolist(), [-1, -1, 0, 0, 0])

    def testLshift(self):
        a = Array('e5m2float', [0.3, 1.2])
        with self.assertRaises(TypeError):
            _ = a << 3
        a = Array('int16', [-2, -1, 0, 128])
        b = a << 4
        self.assertEqual(a.tolist(), [-2, -1, 0, 128])
        self.assertEqual(b.tolist(), [-32, -16, 0, 2048])
        with self.assertRaises(ValueError):
            _ = a << 1000

    def testInPlaceLshift(self):
        a = Array('u11', [0, 5, 10, 1, 2, 3])
        a <<= 2
        self.assertEqual(a.tolist(), [0, 20, 40, 4, 8, 12])
        a <<= 0
        self.assertEqual(a.tolist(), [0, 20, 40, 4, 8, 12])
        with self.assertRaises(ValueError):
            a <<= -1

    def testNeg(self):
        a = Array('i92', [-1, 1, 0, 100, -100])
        b = -a
        self.assertEqual(b.tolist(), [1, -1, 0, -100, 100])
        self.assertEqual(b.dtype, 'int92')

    def testAbs(self):
        a = Array('float16', [-2.0, 0, -0, 100, -5.5])
        b = abs(a)
        self.assertTrue(b.equals(Array('float16', [2.0, 0, 0, 100, 5.5])))


class CreationFromBits(unittest.TestCase):

    def testAppendingAuto(self):
        a = Array('bits8')
        a.append('0xff')
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0], Bits('0xff'))
        with self.assertRaises(TypeError):
            a += 8
        a.append(Bits(8))
        self.assertTrue(a[:].equals(Array('bits:8', ['0b1111 1111', Bits('0x00')])))
        a.extend(['0b10101011'])
        self.assertEqual(a[-1].hex, 'ab')


class SameSizeArrayOperations(unittest.TestCase):

    def testAddingSameTypes(self):
        a = Array('u8', [1, 2, 3, 4])
        b = Array('u8', [5, 5, 5, 4])
        c = a + b
        self.assertEqual(c.tolist(), [6, 7, 8, 8])
        self.assertEqual(c.dtype, 'uint8')

    def testAddingDifferentTypes(self):
        a = Array('u8', [1, 2, 3, 4])
        b = Array('i6', [5, 5, 5, 4])
        c = a + b
        self.assertEqual(c.tolist(), [6, 7, 8, 8])
        self.assertEqual(c.dtype, 'int6')
        d = Array('float16', [-10, 0, 5, 2])
        e = d + a
        self.assertEqual(e.tolist(), [-9.0, 2.0, 8.0, 6.0])
        self.assertEqual(e.dtype, 'float16')
        e = a + d
        self.assertEqual(e.tolist(), [-9.0, 2.0, 8.0, 6.0])
        self.assertEqual(e.dtype, 'float16')
        x1 = a[:]
        x2 = a[:]
        x1.dtype = 'e5m2float'
        x2.dtype = 'e4m3float'
        y = x1 + x2
        self.assertEqual(y.dtype, x1.dtype)

    def testAddingErrors(self):
        a = Array('float16', [10, 100, 1000])
        b = Array('i3', [-1, 2])
        with self.assertRaises(ValueError):
            _ = a + b
        b.append(0)
        c = a + b
        self.assertEqual(c.tolist(), [9, 102, 1000])
        a.dtype='hex16'
        with self.assertRaises(ValueError):
            _ = a + b


class ComparisonOperators(unittest.TestCase):

    def testLessThanWithScalar(self):
        a = Array('u16', [14, 16, 100, 2, 100])
        b = a < 80
        self.assertEqual(b.tolist(), [True, True, False, True, False])
        self.assertEqual(b.dtype, 'bool')

    def testLessThanWithArray(self):
        a = Array('u16', [14, 16, 100, 2, 100])
        b = Array('bfloat', [1000, -54, 0.2, 55, 9])
        c = a < b
        self.assertEqual(c.tolist(), [True, False, False, True, False])
        self.assertEqual(c.dtype, 'bool')

    def testArrayEquals(self):
        a = Array('i12', [1, 2, -3, 4, -5, 6])
        b = Array('i12', [6, 5, 4, 3, 2, 1])
        self.assertEqual(abs(a), b[::-1])
        self.assertNotEqual(a, b)


class AsType(unittest.TestCase):

    def testSwitchingIntTypes(self):
        a = Array('u8', [15, 42, 1])
        b = a.astype('i8')
        self.assertEqual(a.tolist(), b.tolist())
        self.assertEqual(b.dtype, 'i8')

    def testSwitchingFloatTypes(self):
        a = Array('float64', [-990, 34, 1, 0.25])
        b = a.astype('float16')
        self.assertEqual(a.tolist(), b.tolist())
        self.assertEqual(b.dtype, 'float16')


class ReverseMethods(unittest.TestCase):

    def testRadd(self):
        a = Array('u6', [1,2,3])
        b = 5 + a
        self.assertTrue(b.equals(Array('uint:6', [6, 7, 8])))

    def testRmul(self):
        a = Array('bfloat', [4, 2, 8])
        b = 0.5 * a
        self.assertTrue(b.equals(Array('bfloat16', [2.0, 1.0, 4.0])))

    def testRsub(self):
        a = Array('i90', [-1, -10, -100])
        b = 100 - a
        self.assertTrue(b.equals(Array('int90', [101, 110, 200])))

    def testRmod(self):
        a = Array('i8', [1, 2, 4, 8, 10])
        with self.assertRaises(TypeError):
            _ = 15 % a

    def testRfloordiv(self):
        a = Array('>H', [1, 2, 3, 4, 5])
        with self.assertRaises(TypeError):
            _ = 100 // a

    def testRtruediv(self):
        a = Array('>H', [1, 2, 3, 4, 5])
        with self.assertRaises(TypeError):
            _ = 100 / a

    def testRand(self):
        a = Array('u8', [255, 8, 4, 2, 1, 0])
        b = '0x0f' & a
        self.assertEqual(b.tolist(), [15, 8, 4, 2, 1, 0])

    def testRor(self):
        a = Array('u8', [255, 8, 4, 2, 1, 0])
        b = '0x0f' | a
        self.assertEqual(b.tolist(), [255, 15, 15, 15, 15, 15])

    def testRxor(self):
        a = Array('u8', [255, 8, 4, 2, 1, 0])
        b = '0x01' ^ a
        self.assertEqual(b.tolist(), [254, 9, 5, 3, 0, 1])
