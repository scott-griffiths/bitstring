#!/usr/bin/env python
"""
Unit tests for the bitarray module.
"""

import unittest
import sys
import os
import bitarray
import bitstring
from bitstring import BitArray, Bits

sys.path.insert(0, '..')


class All(unittest.TestCase):
    def testCreationFromUint(self):
        s = BitArray(uint=15, length=6)
        self.assertEqual(s.bin, '001111')
        s = BitArray(uint=0, length=1)
        self.assertEqual(s.bin, '0')
        s.u = 1
        self.assertEqual(s.uint, 1)
        s = BitArray(length=8)
        s.uint = 0
        self.assertEqual(s.uint, 0)
        s.u8 = 255
        self.assertEqual(s.uint, 255)
        self.assertEqual(s.len, 8)
        with self.assertRaises(bitstring.CreationError):
            s.uint = 256
        with self.assertRaises(bitstring.CreationError):
            s.uint = -1

    def testCreationFromOct(self):
        s = BitArray(oct='7')
        self.assertEqual(s.oct, '7')
        self.assertEqual(s.bin, '111')
        s.append('0o1')
        self.assertEqual(s.bin, '111001')
        s.oct = '12345670'
        self.assertEqual(s.length, 24)
        self.assertEqual(s.bin, '001010011100101110111000')
        s = BitArray('0o123')
        self.assertEqual(s.oct, '123')


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

    def testInsertSelf(self):
        b = BitArray('0b10')
        b.insert(b, 0)
        self.assertEqual(b, '0b1010')
        c = BitArray('0x00ff')
        c.insert(c, 8)
        self.assertEqual(c, '0x0000ffff')
        a = BitArray('0b11100')
        a.insert(a, 3)
        self.assertEqual(a, '0b1111110000')

    def testNoBitPosForInsert(self):
        s = BitArray(100)
        with self.assertRaises(TypeError):
            s.insert('0xabc')

    def testInsertParameters(self):
        s = BitArray('0b111')
        with self.assertRaises(TypeError):
            s.insert('0x4')

    def testOverwrite(self):
        s = BitArray('0b01110')
        s.overwrite('0b000', 1)
        self.assertEqual(s, '0b00000')

    def testOverwriteNoPos(self):
        s = BitArray('0x01234')
        with self.assertRaises(TypeError):
            s.overwrite('0xf')

    def testOverwriteParameters(self):
        s = BitArray('0b0000')
        with self.assertRaises(TypeError):
            s.overwrite('0b111')

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
        s[5:5] = BitArray()
        self.assertEqual(s, '0b100111110')


class Bugs(unittest.TestCase):
    def testAddingNonsense(self):
        a = BitArray([0])
        a += '0'  # a uint of length 0 - so nothing gets added.
        self.assertEqual(a, [0])
        with self.assertRaises(ValueError):
            a += '3'
        with self.assertRaises(ValueError):
            a += 'se'
        with self.assertRaises(ValueError):
            a += 'float:32'

    def testPrependAfterCreationFromDataWithOffset(self):
        s1 = BitArray(bytes=b'\x00\x00\x07\xff\xf0\x00', offset=21, length=15)
        self.assertFalse(s1.any(0))
        b = s1.tobytes()
        self.assertEqual(b, b'\xff\xfe')
        s1.prepend('0b0')
        self.assertEqual(s1.bin, '0111111111111111')
        s1.prepend('0b0')
        self.assertEqual(s1.bin, '00111111111111111')


class ByteAligned(unittest.TestCase):

    def testChangingIt(self):
        bitstring.bytealigned = True
        self.assertTrue(bitstring.bytealigned)
        bitstring.bytealigned = False
        self.assertFalse(bitstring.bytealigned)

    def testNotByteAligned(self):
        a = BitArray('0x00 ff 0f f')
        li = list(a.findall('0xff'))
        self.assertEqual(li, [8, 20])
        p = a.find('0x0f')[0]
        self.assertEqual(p, 4)
        p = a.rfind('0xff')[0]
        self.assertEqual(p, 20)
        s = list(a.split('0xff'))
        self.assertEqual(s, ['0x00', '0xff0', '0xff'])
        a.replace('0xff', '')
        self.assertEqual(a, '0x000')

    def testByteAligned(self):
        bitstring.bytealigned = True
        a = BitArray('0x00 ff 0f f')
        li = list(a.findall('0xff'))
        self.assertEqual(li, [8])
        p = a.find('0x0f')[0]
        self.assertEqual(p, 16)
        p = a.rfind('0xff')[0]
        self.assertEqual(p, 8)
        s = list(a.split('0xff'))
        self.assertEqual(s, ['0x00', '0xff0ff'])
        a.replace('0xff', '')
        self.assertEqual(a, '0x000ff')
        bitstring.bytealigned = False


class SliceAssignment(unittest.TestCase):

    def testSliceAssignmentSingleBit(self):
        a = BitArray('0b000')
        a[2] = '0b1'
        self.assertEqual(a.bin, '001')
        a[0] = BitArray(bin='1')
        self.assertEqual(a.bin, '101')
        a[-1] = '0b0'
        self.assertEqual(a.bin, '100')
        a[-3] = '0b0'
        self.assertEqual(a.bin, '000')

    def testSliceAssignmentSingleBitErrors(self):
        a = BitArray('0b000')
        with self.assertRaises(IndexError):
            a[-4] = '0b1'
        with self.assertRaises(IndexError):
            a[3] = '0b1'
        with self.assertRaises(TypeError):
            a[1] = 1.3

    def testSliceAssignmentMulipleBits(self):
        a = BitArray('0b0')
        a[0] = '0b110'
        self.assertEqual(a.bin3, '110')
        a[0] = '0b000'
        self.assertEqual(a.bin5, '00010')
        a[0:3] = '0b111'
        self.assertEqual(a.b5, '11110')
        a[-2:] = '0b011'
        self.assertEqual(a.bin, '111011')
        a[:] = '0x12345'
        self.assertEqual(a.hex, '12345')
        a[:] = ''
        self.assertFalse(a)

    def testSliceAssignmentMultipleBitsErrors(self):
        a = BitArray()
        with self.assertRaises(IndexError):
            a[0] = '0b00'
        a += '0b1'
        a[0:2] = '0b11'
        self.assertEqual(a, '0b11')

    def testDelSliceStep(self):
        a = BitArray(bin='100111101001001110110100101')
        del a[::2]
        self.assertEqual(a.bin, '0110010101100')
        del a[3:9:3]
        self.assertEqual(a.bin, '01101101100')
        del a[2:7:1]
        self.assertEqual(a.bin, '011100')
        del a[::99]
        self.assertEqual(a.bin, '11100')
        del a[::1]
        self.assertEqual(a.bin, '')

    def testDelSliceNegativeStep(self):
        a = BitArray('0b0001011101101100100110000001')
        del a[5:23:-3]
        self.assertEqual(a.bin, '0001011101101100100110000001')
        del a[25:3:-3]
        self.assertEqual(a.bin, '00011101010000100001')
        del a[:6:-7]
        self.assertEqual(a.bin, '000111010100010000')
        del a[15::-2]
        self.assertEqual(a.bin, '0010000000')
        del a[::-1]
        self.assertEqual(a.bin, '')

    def testDelSliceNegativeEnd(self):
        a = BitArray('0b01001000100001')
        del a[:-5]
        self.assertEqual(a, '0b00001')
        a = BitArray('0b01001000100001')
        del a[-11:-5]
        self.assertEqual(a, '0b01000001')

    def testDelSliceErrors(self):
        a = BitArray(10)
        del a[5:3]
        self.assertEqual(a, Bits(10))
        del a[3:5:-1]
        self.assertEqual(a, Bits(10))

    def testDelSingleElement(self):
        a = BitArray('0b0010011')
        del a[-1]
        self.assertEqual(a.bin, '001001')
        del a[2]
        self.assertEqual(a.bin, '00001')
        with self.assertRaises(IndexError):
            del a[5]

    def testSetSliceStep(self):
        a = BitArray(bin='0000000000')
        a[::2] = '0b11111'
        self.assertEqual(a.bin, '1010101010')
        a[4:9:3] = [0, 0]
        self.assertEqual(a.bin, '1010001010')
        a[7:3:-1] = [1, 1, 1, 0]
        self.assertEqual(a.bin, '1010011110')
        a[7:1:-2] = [0, 0, 1]
        self.assertEqual(a.b, '1011001010')
        a[::-5] = [1, 1]
        self.assertEqual(a.bin, '1011101011')
        a[::-1] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        self.assertEqual(a.bin, '1000000000')

    def testSetSliceStepWithInt(self):
        a = BitArray(9)
        a[5:8] = -1
        self.assertEqual(a.bin, '000001110')
        a[:] = 10
        self.assertEqual(a.bin, '000001010')
        a[::-1] = 10
        self.assertEqual(a.bin, '010100000')
        a[::2] = True
        self.assertEqual(a.bin, '111110101')

    def testSetSliceErrors(self):
        a = BitArray(8)
        with self.assertRaises(ValueError):
            a[::3] = [1]

        class A(object):
            pass
        with self.assertRaises(TypeError):
            a[1:2] = A()
        with self.assertRaises(ValueError):
            a[1:4:-1] = [1, 2]


class Subclassing(unittest.TestCase):

    def testIsInstance(self):
        class SubBits(BitArray):
            pass
        a = SubBits()
        self.assertTrue(isinstance(a, SubBits))

    def testClassType(self):
        class SubBits(BitArray):
            pass
        self.assertEqual(SubBits().__class__, SubBits)


class Clear(unittest.TestCase):

    def testClear(self):
        s = BitArray('0xfff')
        s.clear()
        self.assertEqual(s.len, 0)


class Copy(unittest.TestCase):

    def testCopyMethod(self):
        s = BitArray(9)
        t = s.copy()
        self.assertEqual(s, t)
        t[0] = True
        self.assertEqual(t.bin, '100000000')
        self.assertEqual(s.bin, '000000000')


class ModifiedByAddingBug(unittest.TestCase):

    def testAdding(self):
        a = BitArray('0b0')
        b = BitArray('0b11')
        c = a + b
        self.assertEqual(c, '0b011')
        self.assertEqual(a, '0b0')
        self.assertEqual(b, '0b11')


class Lsb0Setting(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bitstring.lsb0 = True

    @classmethod
    def tearDownClass(cls):
        bitstring.lsb0 = False

    def testSetSingleBit(self):
        a = BitArray(10)
        a[0] = True
        self.assertEqual(a, '0b0000000001')
        a[1] = True
        self.assertEqual(a, '0b0000000011')
        a[0] = False
        self.assertEqual(a, '0b0000000010')
        a[9] = True
        self.assertEqual(a, '0b1000000010')
        with self.assertRaises(IndexError):
            a[10] = True

    def testSetSingleNegativeBit(self):
        a = BitArray('0o000')
        a[-1] = True
        self.assertEqual(a, '0b100000000')
        a[-2] = True
        self.assertEqual(a, '0o600')
        a[-9] = True
        self.assertEqual(a, '0o601')
        with self.assertRaises(IndexError):
            a[-10] = True

    def testInvertBit(self):
        a = BitArray('0b11110000')
        a.invert()
        self.assertEqual(a, '0x0f')
        a.invert(0)
        self.assertEqual(a, '0b00001110')
        a.invert(-1)
        self.assertEqual(a, '0b10001110')

    def testDeletingBits(self):
        a = BitArray('0b11110')
        del a[0]
        self.assertEqual(a, '0xf')

    def testDeletingRange(self):
        a = BitArray('0b101111000')
        del a[0:1]
        self.assertEqual(a, '0b10111100')
        del a[2:6]
        self.assertEqual(a, '0b1000')
        a = BitArray('0xabcdef')
        del a[:8]
        self.assertEqual(a, '0xabcd')
        del a[-4:]
        self.assertEqual(a, '0xbcd')
        del a[:-4]
        self.assertEqual(a, '0xb')

    def testAppendingBits(self):
        a = BitArray('0b111')
        a.append('0b000')
        self.assertEqual(a.bin, '000111')
        a += '0xabc'
        self.assertEqual(a, '0xabc, 0b000111')

    def testSettingSlice(self):
        a = BitArray('0x012345678')
        a[4:12] = '0xfe'
        self.assertEqual(a, '0x012345fe8')
        a[0:4] = '0xbeef'
        self.assertEqual(a, '0x012345febeef')

    def testTruncatingStart(self):
        a = BitArray('0b1110000')
        a = a[4:]
        self.assertEqual(a, '0b111')

    def testTruncatingEnd(self):
        a = BitArray('0x123456')
        a = a[:16]
        self.assertEqual(a, '0x3456')

    def testAll(self):
        a = BitArray('0b0000101')
        self.assertTrue(a.all(1, [0, 2]))
        self.assertTrue(a.all(False, [-1, -2, -3, -4]))

        b = Bits(bytes=b'\x00\xff\xff', offset=7)
        self.assertTrue(b.all(1, [1, 2, 3, 4, 5, 6, 7]))
        self.assertTrue(b.all(1, [-2, -3, -4, -5, -6, -7, -8]))

    def testAny(self):
        a = BitArray('0b0001')
        self.assertTrue(a.any(1, [0, 1, 2]))

    def testEndswith(self):
        a = BitArray('0xdeadbeef')
        self.assertTrue(a.endswith('0xdead'))

    def testStartswith(self):
        a = BitArray('0xdeadbeef')
        self.assertTrue(a.startswith('0xbeef'))

    def testCut(self):
        a = BitArray('0xff00ff1111ff2222')
        li = list(a.cut(16))
        self.assertEqual(li, ['0x2222', '0x11ff', '0xff11', '0xff00'])

    def testFind(self):
        t = BitArray('0b10')
        p, = t.find('0b1')
        self.assertEqual(p, 1)
        t = BitArray('0b1010')
        p, = t.find('0b1')
        self.assertEqual(p, 1)
        a = BitArray('0b10101010, 0xabcd, 0b10101010, 0x0')
        p, = a.find('0b10101010', bytealigned=False)
        self.assertEqual(p, 4)
        p, = a.find('0b10101010', start=4, bytealigned=False)
        self.assertEqual(p, 4)
        p, = a.find('0b10101010', start=5, bytealigned=False)
        self.assertEqual(p, 22)

    def testFindFailing(self):
        a = BitArray()
        p = a.find('0b1')
        self.assertEqual(p, ())
        a = BitArray('0b11111111111011')
        p = a.find('0b100')
        self.assertFalse(p)

    def testFindFailing2(self):
        s = BitArray('0b101')
        p, = s.find('0b1', start=2)
        self.assertEqual(p, 2)

    def testRfind(self):
        a = BitArray('0b1000000')
        p = a.rfind('0b1')
        self.assertEqual(p, (6,))
        p = a.rfind('0b000')
        self.assertEqual(p, (3,))

    def testRfindWithStartAndEnd(self):
        a = BitArray('0b11 0000 11 00')
        p = a.rfind('0b11', start=8)
        self.assertEqual(p[0], 8)
        p = a.rfind('0b110', start=8)
        self.assertEqual(p, ())
        p = a.rfind('0b11', end=-1)
        self.assertEqual(p[0], 2)

    def testFindall(self):
        a = BitArray('0b001000100001')
        b = list(a.findall('0b1'))
        self.assertEqual(b, [0, 5, 9])
        c = list(a.findall('0b0001'))
        self.assertEqual(c, [0, 5])
        d = list(a.findall('0b10'))
        self.assertEqual(d, [4, 8])
        e = list(a.findall('0x198273641234'))
        self.assertEqual(e, [])

    def testFindAllWithStartAndEnd(self):
        a = BitArray('0xaabbccaabbccccbb')
        b = list(a.findall('0xbb', start=0, end=8))
        self.assertEqual(b, [0])
        b = list(a.findall('0xbb', start=1, end=8))
        self.assertEqual(b, [])
        b = list(a.findall('0xbb', start=0, end=7))
        self.assertEqual(b, [])
        b = list(a.findall('0xbb', start=48))
        self.assertEqual(b, [48])
        b = list(a.findall('0xbb', start=47))
        self.assertEqual(b, [48])
        b = list(a.findall('0xbb', start=49))
        self.assertEqual(b, [])

    def testFindAllByteAligned(self):
        a = BitArray('0x0550550')
        b = list(a.findall('0x55', bytealigned=True))
        self.assertEqual(b, [16])

    def testFindAllWithCount(self):
        a = BitArray('0b0001111101')
        b = list(a.findall([1], start=1, count=1))
        self.assertEqual(b, [2])

    def testSplit(self):
        a = BitArray('0x4700004711472222')
        li = list(a.split('0x47', bytealigned=True))
        self.assertEqual(li, ['', '0x472222', '0x4711', '0x470000'])

    def testByteSwap(self):
        a = BitArray('0xaa00ff00ff00')
        n = a.byteswap(2, end=32, repeat=True)
        self.assertEqual(n, 2)
        self.assertEqual(a, '0xaa0000ff00ff')

    def testInsert(self):
        a = BitArray('0x0123456')
        a.insert('0xf', 4)
        self.assertEqual(a, '0x012345f6')

    def testOverwrite(self):
        a = BitArray('0x00000000')
        a.overwrite('0xdead', 4)
        self.assertEqual(a, '0x000dead0')

    def testReplace(self):
        a = BitArray('0x5551100')
        n = a.replace('0x1', '0xabc')
        self.assertEqual(n, 2)
        self.assertEqual(a, '0x555abcabc00')
        n = a.replace([1], [0], end=12)
        self.assertEqual(n, 2)
        self.assertEqual(a, '0x555abcab000')

    def testReverse(self):
        a = BitArray('0x0011223344')
        a.reverse()
        self.assertEqual(a, '0x22cc448800')
        a.reverse(0, 16)
        self.assertEqual(a, '0x22cc440011')

    def testRor(self):
        a = BitArray('0b111000')
        a.ror(1)
        self.assertEqual(a, '0b011100')
        a = BitArray('0b111000')
        a.ror(1, start=2, end=6)
        self.assertEqual(a, '0b011100')

    def testRol(self):
        a = BitArray('0b1')
        a.rol(12)
        self.assertEqual(a, '0b1')
        b = BitArray('0b000010')
        b.rol(3)
        self.assertEqual(b, '0b010000')

    def testSet(self):
        a = BitArray(100)
        a.set(1, [0, 2, 4])
        self.assertTrue(a[0])
        self.assertTrue(a.startswith('0b000010101'))
        a = BitArray('0b111')
        a.set(False, 0)
        self.assertEqual(a, '0b110')

    def testFailingRepr(self):
        a = BitArray('0b010')
        a.find('0b1')
        self.assertEqual(repr(a), "BitArray('0b010')")

    def testLeftShift(self):
        a = BitArray('0b11001')
        self.assertEqual((a << 1).b, '10010')
        self.assertEqual((a << 5).b, '00000')
        self.assertEqual((a << 0).b, '11001')

    def testRightShift(self):
        a = BitArray('0b11001')
        self.assertEqual((a >> 1).b, '01100')
        self.assertEqual((a >> 5).b, '00000')
        self.assertEqual((a >> 0).b, '11001')

    # def testConstFileBased(self):
    #     filename = os.path.join(THIS_DIR, 'test.m1v')
    #     a = Bits(filename=filename, offset=8)
    #     self.assertTrue(a[-8])
    #     self.assertTrue(a.endswith('0x01b3'))


class Repr(unittest.TestCase):

    def testStandardRepr(self):
        a = BitArray('0o12345')
        self.assertEqual(repr(a), "BitArray('0b001010011100101')")


class NewProperties(unittest.TestCase):

    def testAliases(self):
        a = BitArray('0x1234567890ab')
        self.assertEqual(a.oct, a.o)
        self.assertEqual(a.hex, a.h)
        self.assertEqual(a.bin, a.b)
        self.assertEqual(a[:32].float, a[:32].f)
        self.assertEqual(a.int, a.i)
        self.assertEqual(a.uint, a.u)

    def testAliasesWithLengths(self):
        a = BitArray('0x123')
        h = a.h12
        self.assertEqual(h, '123')
        b = a.b12
        self.assertEqual(b, '000100100011')
        o = a.o12
        self.assertEqual(o, '0443')
        u = a.u12
        self.assertEqual(u, a.u)
        i = a.i12
        self.assertEqual(i, a.i)
        x = BitArray('0x12345678')
        f = x.f32
        self.assertEqual(f, x.f)

    def testAssignments(self):
        a = BitArray()
        a.f64 = 0.5
        self.assertEqual(a.f64, 0.5)
        a.u88 = 1244322
        self.assertEqual(a.u88, 1244322)
        a.i3 = -3
        self.assertEqual(a.i3, -3)
        a.h16 = '0x1234'
        self.assertEqual(a.h16, '1234')
        a.o9 = '0o765'
        self.assertEqual(a.o9, '765')
        a.b7 = '0b0001110'
        self.assertEqual(a.b7, '0001110')

    def testAssignmentsWithoutLength(self):
        a = BitArray(64)
        a.f = 1234.5
        self.assertEqual(a.float, 1234.5)
        self.assertEqual(a.len, 64)
        a.u = 99
        self.assertEqual(a.uint, 99)
        self.assertEqual(a.len, 64)
        a.i = -999
        self.assertEqual(a.int, -999)
        self.assertEqual(a.len, 64)
        a.h = 'feedbeef'
        self.assertEqual(a.hex, 'feedbeef')
        a.o = '1234567'
        self.assertEqual(a.oct, '1234567')
        a.b = '001'
        self.assertEqual(a.bin, '001')

    def testGetterLengthErrors(self):
        a = BitArray('0x123')
        with self.assertRaises(bitstring.InterpretError):
            _ = a.h16
        with self.assertRaises(bitstring.InterpretError):
            _ = a.b331123112313
        with self.assertRaises(bitstring.InterpretError):
            _ = a.o2
        with self.assertRaises(bitstring.InterpretError):
            _ = a.f
        with self.assertRaises(bitstring.InterpretError):
            _ = a.f32
        with self.assertRaises(bitstring.InterpretError):
            _ = a.u13
        with self.assertRaises(bitstring.InterpretError):
            _ = a.i1
        b = BitArray()
        with self.assertRaises(bitstring.InterpretError):
            _ = b.u0

    def testSetterLengthErrors(self):
        a = BitArray()
        a.u8 = 255
        self.assertEqual(a.len, 8)
        with self.assertRaises(ValueError):
            a.u8 = 256
        a.f32 = 10
        a.f64 = 10
        with self.assertRaises(ValueError):
            a.f256 = 10
        with self.assertRaises(bitstring.CreationError):
            a.u0 = 2
        with self.assertRaises(bitstring.CreationError):
            a.hex4 = '0xab'
        self.assertEqual(len(a), 64)
        with self.assertRaises(bitstring.CreationError):
            a.o3 = '0xab'
        with self.assertRaises(bitstring.CreationError):
            a.b4 = '0xab'
        a.h0 = ''
        self.assertEqual(a.len, 0)
        a.i8 = 127
        a.i8 = -128
        with self.assertRaises(ValueError):
            a.i8 = 128
        with self.assertRaises(ValueError):
            a.i8 = -129
        with self.assertRaises(bitstring.CreationError):
            a.froggy16 = '0xabc'

    def testUnpack(self):
        a = BitArray('0xff160120')
        b = a.unpack('h8,2*u12')
        self.assertEqual(b, ['ff', 352, 288])

    def testReading(self):
        a = bitstring.BitStream('0x01ff')
        b = a.read('u8')
        self.assertEqual(b, 1)
        self.assertEqual(a.pos, 8)
        self.assertEqual(a.read('i'), -1)

    def testLongerMoreGeneralNames(self):
        a = BitArray()
        a.f64 = 0.0
        self.assertEqual(a.float64, 0.0)
        a.float32 = 10.5
        self.assertEqual(a.f32, 10.5)

    def testBytesProperties(self):
        a = BitArray()
        a.bytes = b'hello'
        self.assertEqual(a.bytes5, b'hello')
        a.bytes3 = b'123'
        self.assertEqual(a.bytes, b'123')
        with self.assertRaises(bitstring.CreationError):
            a.bytes5 = b'123456789'
        with self.assertRaises(bitstring.CreationError):
            a.bytes5 = b'123'

    def testConversionToBytes(self):
        a = BitArray(bytes=b'1234')
        b = bytes(a)
        self.assertEqual(b, b'1234')
        a += [1]
        self.assertEqual(bytes(a), b'1234\x80')
        a = BitArray()
        self.assertEqual(bytes(a), b'')


class BFloats(unittest.TestCase):

    def testCreation(self):
        a = BitArray('bfloat=100.5')
        self.assertEqual(a.unpack('bfloat')[0], 100.5)
        b = BitArray(bfloat=20.25)
        self.assertEqual(b.bfloat, 20.25)
        b.bfloat = -30.5
        self.assertEqual(b.bfloat, -30.5)
        self.assertEqual(len(b), 16)
        fs = [0.0, -6.1, 1.52e35, 0.000001]
        a = bitstring.pack('4*bfloat', *fs)
        fsp = a.unpack('4*bfloat')
        self.assertEqual(len(a), len(fs)*16)
        for f, fp in zip(fs, fsp):
            self.assertAlmostEqual(f, fp, delta=max(f/100, -f/100))
        a = BitArray(bfloat=13)
        self.assertEqual(a.bfloat, 13)

    def testCreationErrors(self):
        a = BitArray(bfloat=-0.25, length=16)
        self.assertEqual(len(a), 16)
        with self.assertRaises(bitstring.CreationError):
            _ = BitArray(bfloat=10, length=15)
        with self.assertRaises(bitstring.CreationError):
            _ = BitArray('bfloat:1=0.5')

    def testLittleEndian(self):
        a = BitArray('f32=1000')
        b = BitArray(bfloat=a.f)
        self.assertEqual(a[0:16], b[0:16])

        a = BitArray('floatle:32=1000')
        b = BitArray(bfloatle=1000)
        self.assertEqual(a[16:32], b)
        self.assertEqual(b.bfloatle, 1000.0)
        b.byteswap()
        self.assertEqual(b.bfloat, 1000.0)
        self.assertEqual(b.bfloatbe, 1000.0)

        with self.assertRaises(bitstring.CreationError):
            _ = BitArray(bfloatle=-5, length=15)

    def testMoreCreation(self):
        a = BitArray('bfloat:16=1.0, bfloat16=2.0, bfloat=3.0')
        x, y, z = a.unpack('3*bfloat16')
        self.assertEqual((x, y, z), (1.0, 2.0, 3.0))

    def testInterpretBug(self):
        a = BitArray(100)
        with self.assertRaises(bitstring.InterpretError):
            v = a.bfloat

    def testOverflows(self):
        s = BitArray()
        inf16 = BitArray(float=float('inf'), length=16)
        inf32 = BitArray(float=float('inf'), length=32)
        inf64 = BitArray(float=float('inf'), length=64)
        infbfloat = BitArray(bfloat=float('inf'))
        
        s.f64 = 1e400
        self.assertEqual(s, inf64)
        s.f32 = 1e60
        self.assertEqual(s, inf32)
        s.f16 = 100000
        self.assertEqual(s, inf16)
        s.bfloat = 1e60
        self.assertEqual(s, infbfloat)

        ninf16 = BitArray(float=float('-inf'), length=16)
        ninf32 = BitArray(float=float('-inf'), length=32)
        ninf64 = BitArray(float=float('-inf'), length=64)
        ninfbfloat = BitArray(bfloat=float('-inf'))

        s.f64 = -1e400
        self.assertEqual(s, ninf64)
        s.f32 = -1e60
        self.assertEqual(s, ninf32)
        s.f16 = -100000
        self.assertEqual(s, ninf16)
        s.bfloat = -1e60
        self.assertEqual(s, ninfbfloat)

    def testBigEndianStringInitialisers(self):
        a = BitArray('bfloatbe=4.5')
        b = BitArray('bfloatbe:16=-2.25')
        self.assertEqual(a.bfloatbe, 4.5)
        self.assertEqual(b.bfloatbe, -2.25)

    def testLilleEndianStringInitialisers(self):
        a = BitArray('bfloatle=4.5')
        b = BitArray('bfloatle:16=-2.25')
        self.assertEqual(a.bfloatle, 4.5)
        self.assertEqual(b.bfloatle, -2.25)

    def testNativeEndianStringInitialisers(self):
        a = BitArray('bfloatne=4.5')
        b = BitArray('bfloatne:16=-2.25')
        self.assertEqual(a.bfloatne, 4.5)
        self.assertEqual(b.bfloatne, -2.25)



THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class BitarrayTests(unittest.TestCase):

    def tearDown(self) -> None:
        bitstring.lsb0 = False

    def testToBitarray(self):
        a = BitArray('0xff, 0b0')
        b = a.tobitarray()
        self.assertEqual(type(b), bitarray.bitarray)
        self.assertEqual(b, bitarray.bitarray('111111110'))

    def testToBitarrayLSB0(self):
        bitstring.lsb0 = True
        a = bitstring.Bits('0xff, 0b0')
        b = a.tobitarray()
        self.assertEqual(type(b), bitarray.bitarray)
        self.assertEqual(b, bitarray.bitarray('111111110'))

    def testFromFile(self):
        a = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        b = a.tobitarray()
        self.assertEqual(a.bin, b.to01())

    def testWithOffset(self):
        a = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        b = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'), offset=11)
        self.assertEqual(len(a), len(b) + 11)
        self.assertEqual(a[11:].tobitarray(), b.tobitarray())

    def testWithLength(self):
        a = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        b = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'), length=11)
        self.assertEqual(len(b), 11)
        self.assertEqual(a[:11].tobitarray(), b.tobitarray())

    def testWithOffsetAndLength(self):
        a = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'))
        b = bitstring.ConstBitStream(filename=os.path.join(THIS_DIR, 'smalltestfile'), offset=17, length=7)
        self.assertEqual(len(b), 7)
        self.assertEqual(a[17:24].tobitarray(), b.tobitarray())


try:
    import numpy as np
    numpy_installed = True
except ImportError:
    numpy_installed = False


class Numpy(unittest.TestCase):

    @unittest.skipIf(not numpy_installed, "numpy not installed.")
    def testGetting(self):
        a = BitArray('0b110')
        p = np.int_(1)
        self.assertEqual(a[p], True)
        p = np.short(0)
        self.assertEqual(a[p], True)

    @unittest.skipIf(not numpy_installed, "numpy not installed.")
    def testSetting(self):
        a = BitArray('0b110')
        p = np.int_(1)
        a[p] = '0b1111'
        self.assertEqual(a, '0b111110')

    @unittest.skipIf(not numpy_installed, "numpy not installed.")
    def testCreation(self):
        a = BitArray(np.longlong(12))
        self.assertEqual(a.hex, '000')