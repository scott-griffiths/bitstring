#!/usr/bin/env python
"""
Unit tests for the bitstring module.
http://python-bitstring.googlecode.com
"""

__licence__ = """
The MIT License

Copyright (c) 2006-2010 Scott Griffiths (scott@griffiths.name)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import unittest
import sys
sys.path.insert(0, '..')
import bitstring
import copy
import os
import collections
from bitstring import BitString, BitStringError, Bits, pack

class ModuleData(unittest.TestCase):

    def testVersion(self):
        self.assertEqual(bitstring.__version__, '1.3.0')

    def testAll(self):
        a = bitstring.__all__
        self.assertEqual(len(a), 3)
        self.assertTrue('Bits' in a)
        self.assertTrue('BitString' in a)
        self.assertTrue('pack' in a)

    def testReverseDict(self):
        d = bitstring.BYTE_REVERSAL_DICT
        for i in range(256):
            a = BitString(uint=i, length=8)
            b = d[i]
            self.assertEqual(a.bin[2:][::-1], BitString(bytes=b).bin[2:])

class Creation(unittest.TestCase):

    def testFromFile(self):
        s = BitString(filename = 'test.m1v')
        self.assertEqual(s[0:32].hex, '0x000001b3')
        self.assertEqual(s.readbytes(4).hex, '0x000001b3')
        width = s.readbits(12).uint
        height = s.readbits(12).uint
        self.assertEqual((width, height), (352, 288))

    def testCreationFromData(self):
        s = Bits(bytes=b'\xa0\xff')
        self.assertEqual((s.len, s.hex), (16, '0xa0ff'))

    def testCreationFromDataWithOffset(self):
        s1 = BitString(bytes=b'\x0b\x1c\x2f', offset=0, length=20)
        s2 = Bits(bytes=b'\xa0\xb1\xC2', offset=4)
        self.assertEqual((s2.len, s2.hex), (20, '0x0b1c2'))
        self.assertEqual((s1.len, s1.hex), (20, '0x0b1c2'))
        self.assertTrue(s1 == s2)

    def testCreationFromHex(self):
        s = BitString(hex='0xA0ff')
        self.assertEqual((s.len, s.hex), (16, '0xa0ff'))
        s = BitString(hex='0x0x0X')
        self.assertEqual((s.length, s.hex), (0, ''))

    def testCreationFromHexWithOffset(self):
        s = BitString(hex='0xa0b1c2', offset = 4)
        self.assertEqual((s.length, s.hex), (20, '0x0b1c2'))

    def testCreationFromHexWithWhitespace(self):
        s = BitString(hex='  \n0 X a  4e       \r3  \n')
        self.assertEqual(s.hex, '0xa4e3')

    def testCreationFromHexWithLength(self):
        s = BitString(hex='0x12', length=4)
        self.assertEqual(s, '0x1')
        s = BitString(hex='0x12', length=0)
        self.assertFalse(s)
        self.assertRaises(ValueError, BitString, hex='0x12', length=-1)

    def testCreationFromHexErrors(self):
        self.assertRaises(ValueError, BitString, hex='0xx0')
        self.assertRaises(ValueError, BitString, hex='0xX0')
        self.assertRaises(ValueError, BitString, hex='0Xx0')
        self.assertRaises(ValueError, BitString, hex='-2e')

    def testCreationFromBin(self):
        s = BitString(bin='1010000011111111')
        self.assertEqual((s.length, s.hex), (16, '0xa0ff'))
        self.assertEqual(s.bitpos, 0)
        s = BitString(bin='00', length=1)
        self.assertEqual(s.bin, '0b0')
        s = BitString(bin='00', length=0)
        self.assertEqual(s.bin, '')
        s = BitString(bin=' 0000 \n 0001\r ')
        self.assertEqual(s.bin, '0b00000001')

    def testCreationFromBinWithOffset(self):
        s = BitString(bin='0', offset=1)
        self.assertFalse(s)
        s = BitString(bin='00111', offset=2)
        self.assertEqual(s.bin, '0b111')

    def testCreationFromBinWithLength(self):
        s = BitString(bin='0011100', length=3, offset=2)
        self.assertEqual(s, '0b111')
        s = BitString(bin='00100101010', length=0)
        self.assertFalse(s)
        self.assertRaises(ValueError, BitString, bin='001', length=-1)

    def testCreationFromBinWithWhitespace(self):
        s = BitString(bin='  \r\r\n0   B    00   1 1 \t0 ')
        self.assertEqual(s.bin, '0b00110')

    def testCreationFromOct(self):
        s = BitString(oct='7')
        self.assertEqual(s.oct, '0o7')
        self.assertEqual(s.bin, '0b111')
        s.append('0o1')
        self.assertEqual(s.bin, '0b111001')
        s.oct = '12345670'
        self.assertEqual(s.length, 24)
        self.assertEqual(s.bin, '0b001010011100101110111000')
        s = BitString('0o123')
        self.assertEqual(s.oct, '0o123')

    def testCreationFromOctWithLength(self):
        s = BitString(oct='123', offset=3, length=3)
        self.assertEqual(s, '0o2')
        s = BitString(oct='123', offset=1, length=0)
        self.assertFalse(s)
        self.assertRaises(ValueError, BitString, oct='75', length=-1)

    def testCreationFromOctErrors(self):
        s = BitString('0b00011')
        self.assertRaises(ValueError, s._getoct)
        self.assertRaises(ValueError, s._setoct, '8')

    def testCreationFromUint(self):
        s = BitString(uint = 15, length=6)
        self.assertEqual(s.bin, '0b001111')
        s = BitString(uint = 0, length=1)
        self.assertEqual(s.bin, '0b0')
        s.uint = 1
        self.assertEqual(s.uint, 1)
        s = BitString(length=8)
        s.uint = 0
        self.assertEqual(s.uint, 0)
        s.uint = 255
        self.assertEqual(s.uint, 255)
        self.assertRaises(ValueError, s._setuint, 256)

    def testCreationFromUintWithOffset(self):
        self.assertRaises(BitStringError, BitString, uint=12, length=8, offset=1)

    def testCreationFromUintErrors(self):
        self.assertRaises(ValueError, BitString, uint=-1, length=10)
        self.assertRaises(ValueError, Bits, uint=12)
        self.assertRaises(ValueError, BitString, uint=4, length=2)
        self.assertRaises(ValueError, BitString, uint=0, length=0)
        self.assertRaises(ValueError, BitString, uint=12, length=-12)

    def testCreationFromInt(self):
        s = BitString(int=0, length=4)
        self.assertEqual(s.bin, '0b0000')
        s = BitString(int=1, length=2)
        self.assertEqual(s.bin, '0b01')
        s = BitString(int=-1, length=11)
        self.assertEqual(s.bin, '0b11111111111')
        s = Bits(int=12, length=7)
        self.assertEqual(s.int, 12)
        s = BitString(int=-243, length=108)
        self.assertEqual((s.int, s.length), (-243, 108))
        for length in range(6, 10):
            for value in range(-17, 17):
                s = BitString(int=value, length=length)
                self.assertEqual((s.int, s.length), (value, length))
        s = BitString(int=10, length=8)
        s.int = 20
        self.assertEqual(s.int, 20)
        self.assertEqual(s.length, 8)

    def testCreationFromIntWithOffset(self):
        self.assertRaises(BitStringError, BitString, int=12, length=8, offset=1)

    def testCreationFromIntErrors(self):
        self.assertRaises(ValueError, BitString, int=-1, length=0)
        self.assertRaises(ValueError, BitString, int=12)
        self.assertRaises(ValueError, BitString, int=4, length=3)
        self.assertRaises(ValueError, BitString, int=-5, length=3)

    def testCreationFromSe(self):
        for i in range(-100, 10):
            s = BitString(se=i)
            self.assertEqual(s.se, i)

    def testCreationFromSeWithOffset(self):
        self.assertRaises(BitStringError, BitString, se=-13, offset=1)

    def testCreationFromSeErrors(self):
        self.assertRaises(BitStringError, BitString, se=-5, length=33)
        s = BitString(bin='001000')
        self.assertRaises(BitStringError, s._getse)

    def testCreationFromUe(self):
        [self.assertEqual(BitString(ue=i).ue, i) for i in range(0, 20)]

    def testCreationFromUeWithOffset(self):
        self.assertRaises(BitStringError, BitString, ue=104, offset=2)

    def testCreationFromUeErrors(self):
        self.assertRaises(ValueError, BitString, ue=-1)
        self.assertRaises(BitStringError, BitString, ue=1, length=12)
        s = BitString(bin='10')
        self.assertRaises(BitStringError, s._getue)

class FlexibleInitialisation(unittest.TestCase):

    def testFlexibleInitialisation(self):
        a = BitString('uint:8=12')
        c = BitString(' uint : 8 =  12')
        self.assertTrue(a == c == BitString(uint=12, length=8))
        a = BitString('     int:2=  -1')
        b = BitString('int :2   = -1')
        c = BitString(' int:  2  =-1  ')
        self.assertTrue(a == b == c == BitString(int=-1, length=2))

    def testFlexibleInitialisation2(self):
        h = BitString('hex=12')
        o = BitString('oct=33')
        b = BitString('bin=10')
        self.assertEqual(h, '0x12')
        self.assertEqual(o, '0o33')
        self.assertEqual(b, '0b10')

    def testFlexibleInitialisation3(self):
        for s in ['se=-1', ' se = -1 ', 'se = -1']:
            a = BitString(s)
            self.assertEqual(a.se, -1)
        for s in ['ue=23', 'ue =23', 'ue = 23']:
            a = BitString(s)
            self.assertEqual(a.ue, 23)

    def testMultipleStringInitialisation(self):
        a = BitString('0b1 , 0x1')
        self.assertEqual(a, '0b10001')
        a = BitString('ue=5, ue=1, se=-2')
        self.assertEqual(a.read('ue'), 5)
        self.assertEqual(a.read('ue'), 1)
        self.assertEqual(a.read('se'), -2)
        b = BitString('uint:32 = 12, 0b11') + 'int:100=-100, 0o44'
        self.assertEqual(b.readbits(32).uint, 12)
        self.assertEqual(b.readbits(2).bin, '0b11')
        self.assertEqual(b.readbits(100).int, -100)
        self.assertEqual(b.readbits(1000), '0o44')

class Reading(unittest.TestCase):

    def testReadBits(self):
        s = BitString(bytes=b'\x4d\x55')
        self.assertEqual(s.readbits(4).hex, '0x4')
        self.assertEqual(s.readbits(8).hex, '0xd5')
        self.assertEqual(s.readbits(1).bin, '0b0')
        self.assertEqual(s.readbits(3).bin, '0b101')
        self.assertFalse(s.readbits(0))

    def testReadByte(self):
        s = BitString(hex='4d55')
        self.assertEqual(s.readbyte().hex, '0x4d')
        self.assertEqual(s.readbyte().hex, '0x55')

    def testReadBytes(self):
        s = BitString(hex='0x112233448811')
        self.assertEqual(s.readbytes(3).hex, '0x112233')
        self.assertRaises(ValueError, s.readbytes, -2)
        s.bitpos += 1
        self.assertEqual(s.readbytes(2).bin, '0b1000100100010000')

    def testReadUE(self):
        self.assertRaises(BitStringError, BitString('')._getue)
        # The numbers 0 to 8 as unsigned Exponential-Golomb codes
        s = BitString(bin='1 010 011 00100 00101 00110 00111 0001000 0001001')
        self.assertEqual(s.pos, 0)
        for i in range(9):
            self.assertEqual(s.read('ue'), i)
        self.assertRaises(BitStringError, s.read, 'ue')

    def testReadSE(self):
        s = BitString(bin='010 00110 0001010 0001000 00111')
        self.assertEqual(s.read('se'), 1)
        self.assertEqual(s.read('se'), 3)
        self.assertEqual(s.readlist('se, se, se'), [5, 4, -3])


class Find(unittest.TestCase):

    def testFind1(self):
        s = Bits(bin='0b0000110110000')
        self.assertTrue(s.find(BitString(bin='11011'), False))
        self.assertEqual(s.bitpos, 4)
        self.assertEqual(s.readbits(5).bin, '0b11011')
        s.bitpos = 0
        self.assertFalse(s.find('0b11001', False))

    def testFind2(self):
        s = BitString(bin='0')
        self.assertTrue(s.find(s, False))
        self.assertEqual(s.pos, 0)
        self.assertFalse(s.find('0b00', False))
        self.assertRaises(ValueError, s.find, BitString(), False)

    def testFindWithOffset(self):
        s = BitString(hex='0x112233', offset = 4)
        self.assertTrue(s.find('0x23', False))
        self.assertEqual(s.pos, 8)

    def testFindCornerCases(self):
        s = BitString(bin='000111000111')
        self.assertTrue(s.find('0b000'))
        self.assertEqual(s.pos, 0)
        self.assertTrue(s.find('0b000'))
        self.assertEqual(s.pos, 0)
        self.assertTrue(s.find('0b0111000111'))
        self.assertEqual(s.pos, 2)
        self.assertTrue(s.find('0b000', start=2))
        self.assertEqual(s.pos, 6)
        self.assertTrue(s.find('0b111', start=6))
        self.assertEqual(s.pos, 9)
        s.pos += 2
        self.assertTrue(s.find('0b1', start=s.pos))

    def testFindBytes(self):
        s = BitString('0x010203040102ff')
        self.assertFalse(s.find('0x05', bytealigned=True))
        self.assertTrue(s.find('0x02', bytealigned=True))
        self.assertEqual(s.readbytes(2).hex, '0x0203')
        self.assertTrue(s.find('0x02', start=s.bitpos, bytealigned=True))
        s.readbit()
        self.assertFalse(s.find('0x02', start=s.bitpos, bytealigned=True))

    def testFindBytesAlignedCornerCases(self):
        s = BitString('0xff')
        self.assertTrue(s.find(s))
        self.assertFalse(s.find(BitString(hex='0x12')))
        self.assertFalse(s.find(BitString(hex='0xffff')))

    def testFindBytesBitpos(self):
        s = BitString(hex='0x1122334455')
        s.pos = 2
        s.find('0x66', bytealigned=True)
        self.assertEqual(s.pos, 2)
        s.pos = 38
        s.find('0x66', bytealigned=True)
        self.assertEqual(s.pos, 38)

    def testFindByteAligned(self):
        s = BitString(hex='0x12345678')
        self.assertTrue(s.find(BitString(hex='0x56'), bytealigned=True))
        self.assertEqual(s.bytepos, 2)
        s.pos = 0
        self.assertFalse(s.find(BitString(hex='0x45'), bytealigned=True))
        s = BitString('0x1234')
        s.find('0x1234')
        self.assertTrue(s.find('0x1234'))
        s += '0b111'
        s.pos = 3
        s.find('0b1', start=17, bytealigned=True)
        self.assertFalse(s.find('0b1', start=17, bytealigned=True))
        self.assertEqual(s.pos, 3)

    def testFindByteAlignedWithOffset(self):
        s = BitString(hex='0x112233', offset=4)
        self.assertTrue(s.find(BitString(hex='0x23')))

    def testFindByteAlignedErrors(self):
        s = BitString(hex='0xffff')
        self.assertRaises(ValueError, s.find, '')
        self.assertRaises(ValueError, s.find, BitString())



class Rfind(unittest.TestCase):
    def testRfind(self):
        a = BitString('0b001001001')
        b = a.rfind('0b001')
        self.assertEqual(b, True)
        self.assertEqual(a.pos, 6)
        big = BitString(length=100000) + '0x12' + BitString(length=10000)
        found = big.rfind('0x12', bytealigned=True)
        self.assertTrue(found)
        self.assertEqual(big.pos, 100000)

    def testRfindByteAligned(self):
        a = BitString('0x8888')
        b = a.rfind('0b1', bytealigned=True)
        self.assertEqual(b, True)
        self.assertEqual(a.pos, 8)

    def testRfindStartbit(self):
        a = BitString('0x0000ffffff')
        b = a.rfind('0x0000', start=1, bytealigned=True)
        self.assertEqual(b, False)
        self.assertEqual(a.pos, 0)
        b = a.rfind('0x00', start=1, bytealigned=True)
        self.assertEqual(b, True)
        self.assertEqual(a.pos, 8)

    def testRfindEndbit(self):
        a = BitString('0x000fff')
        b = a.rfind('0b011', bytealigned=False, start=0, end=14)
        self.assertEqual(b, True)
        b = a.rfind('0b011', False, 0, 13)
        self.assertEqual(b, False)

    def testRfindErrors(self):
        a = BitString('0x43234234')
        self.assertRaises(ValueError, a.rfind, '', bytealigned=True)
        self.assertRaises(ValueError, a.rfind, '0b1', start=-99, bytealigned=True)
        self.assertRaises(ValueError, a.rfind, '0b1', end=33, bytealigned=True)
        self.assertRaises(ValueError, a.rfind, '0b1', start=10, end=9, bytealigned=True)


class Shift(unittest.TestCase):

    def testShiftLeft(self):
        s = BitString('0b1010')
        t = s << 1
        self.assertEqual(s.bin, '0b1010')
        self.assertEqual(t.bin, '0b0100')
        t = t << 100
        self.assertEqual(t.bin, '0b0000')

    def testShiftLeftErrors(self):
        s = BitString()
        self.assertRaises(ValueError, s.__lshift__, 1)
        s = BitString('0xf')
        self.assertRaises(ValueError, s.__lshift__, -1)

    def testShiftRight(self):
        s = BitString('0b1010')
        t = s >> 1
        self.assertEqual(s.bin, '0b1010')
        self.assertEqual(t.bin, '0b0101')
        s = s >> 100
        self.assertEqual(s.bin, '0b0000')

    def testShiftRightErrors(self):
        s = BitString()
        self.assertRaises(ValueError, s.__rshift__, 1)
        s = BitString('0xf')
        self.assertRaises(ValueError, s.__rshift__, -1)

    def testShiftRightInPlace(self):
        s = BitString('0b11011')
        s >>= 2
        self.assertEqual(s.bin, '0b00110')
        s >>= 1000
        self.assertEqual(s.bin, '0b00000')

    def testShiftRightInPlaceErrors(self):
        s = BitString()
        self.assertRaises(ValueError, s.__irshift__, 1)
        s += '0b11'
        self.assertRaises(ValueError, s.__irshift__, -1)

    def testShiftLeftInPlace(self):
        s = BitString('0b11011')
        s <<= 2
        self.assertEqual(s.bin, '0b01100')
        s <<= 1000
        self.assertEqual(s.bin, '0b00000')

    def testShiftLeftInPlaceErrors(self):
        s = BitString()
        self.assertRaises(ValueError, s.__ilshift__, 1)
        s += '0b11'
        self.assertRaises(ValueError, s.__ilshift__, -1)


class SliceAssignment(unittest.TestCase):
    def testSliceAssignmentSingleBit(self):
        a = BitString('0b000')
        a[2] = '0b1'
        self.assertEqual(a.bin, '0b001')
        self.assertEqual(a.bitpos, 0)
        a[0] = BitString(bin='1')
        self.assertEqual(a.bin, '0b101')
        a[-1] = '0b0'
        self.assertEqual(a.bin, '0b100')
        a[-3] = '0b0'
        self.assertEqual(a.bin, '0b000')

    def testSliceAssignmentSingleBitErrors(self):
        a = BitString('0b000')
        self.assertRaises(IndexError, a.__setitem__, -4, '0b1')
        self.assertRaises(IndexError, a.__setitem__, 3, '0b1')
        self.assertRaises(TypeError, a.__setitem__, 1, 1.3)

    def testSliceAssignmentMulipleBits(self):
        a = BitString('0b0')
        a[0] = '0b110'
        self.assertEqual(a.bin, '0b110')
        self.assertEqual(a.bitpos, 3)
        a[0] = '0b000'
        self.assertEqual(a.bin, '0b00010')
        a[0:3] = '0b111'
        self.assertEqual(a.bin, '0b11110')
        self.assertEqual(a.bitpos, 3)
        a[-2:] = '0b011'
        self.assertEqual(a.bin, '0b111011')
        a[:] = '0x12345'
        self.assertEqual(a.hex, '0x12345')
        a[:] = ''
        self.assertFalse(a)

    def testSliceAssignmentBitPos(self):
        a = BitString('int:64=-1')
        a.pos = 64
        a[0:8] = ''
        self.assertEqual(a.pos, 0)
        a.pos = 52
        a[48:56] = '0x0000'
        self.assertEqual(a.pos, 64)
        a[10:10] = '0x0'
        self.assertEqual(a.pos, 14)
        a[56:68] = '0x000'
        self.assertEqual(a.pos, 14)

    def testSliceAssignmentMultipleBitsErrors(self):
        a = BitString()
        self.assertRaises(IndexError, a.__setitem__, 0, '0b00')
        a += '0b1'
        a[0:2] = '0b11'
        self.assertEqual(a, '0b11')



class Replace(unittest.TestCase):

    def testReplace1(self):
        a = BitString('0b1')
        n = a.replace('0b1', '0b0', bytealigned=True)
        self.assertEqual(a.bin, '0b0')
        self.assertEqual(n, 1)
        n = a.replace('0b1', '0b0', bytealigned=True)
        self.assertEqual(n, 0)

    def testReplace2(self):
        a = BitString('0b00001111111')
        n = a.replace('0b1', '0b0', bytealigned=True)
        self.assertEqual(a.bin, '0b00001111011')
        self.assertEqual(n, 1)
        n = a.replace('0b1', '0b0', bytealigned=False)
        self.assertEqual(a.bin, '0b00000000000')
        self.assertEqual(n, 6)

    def testReplace3(self):
        a = BitString('0b0')
        n = a.replace('0b0', '0b110011111', bytealigned=True)
        self.assertEqual(n, 1)
        self.assertEqual(a.bin, '0b110011111')
        n = a.replace('0b11', '', bytealigned=False)
        self.assertEqual(n, 3)
        self.assertEqual(a.bin, '0b001')

    def testReplace4(self):
        a = BitString('0x00114723ef4732344700')
        n = a.replace('0x47', '0x00', bytealigned=True)
        self.assertEqual(n, 3)
        self.assertEqual(a.hex, '0x00110023ef0032340000')
        a.replace('0x00', '', bytealigned=True)
        self.assertEqual(a.hex, '0x1123ef3234')
        a.replace('0x11', '', start=1, bytealigned=True)
        self.assertEqual(a.hex, '0x1123ef3234')
        a.replace('0x11', '0xfff', end=7, bytealigned=True)
        self.assertEqual(a.hex, '0x1123ef3234')
        a.replace('0x11', '0xfff', end=8, bytealigned=True)
        self.assertEqual(a.hex, '0xfff23ef3234')

    def testReplace5(self):
        a = BitString('0xab')
        b = BitString('0xcd')
        c = BitString('0xabef')
        c.replace(a, b)
        self.assertEqual(c, '0xcdef')
        self.assertEqual(a, '0xab')
        self.assertEqual(b, '0xcd')
        a = BitString('0x0011223344')
        a.pos = 12
        a.replace('0x11', '0xfff', bytealigned=True)
        self.assertEqual(a.pos, 8)
        self.assertEqual(a, '0x00fff223344')

    def testReplaceWithSelf(self):
        a = BitString('0b11')
        a.replace('0b1', a)
        self.assertEqual(a, '0xf')
        a.replace(a, a)
        self.assertEqual(a, '0xf')

    def testReplaceCount(self):
        a = BitString('0x223344223344223344')
        n = a.replace('0x2', '0x0', count=0, bytealigned=True)
        self.assertEqual(n, 0)
        self.assertEqual(a.hex, '0x223344223344223344')
        n = a.replace('0x2', '0x0', count=1, bytealigned=True)
        self.assertEqual(n, 1)
        self.assertEqual(a.hex, '0x023344223344223344')
        n = a.replace('0x33', '', count=2, bytealigned=True)
        self.assertEqual(n, 2)
        self.assertEqual(a.hex, '0x02442244223344')
        n = a.replace('0x44', '0x4444', count=1435, bytealigned=True)
        self.assertEqual(n, 3)
        self.assertEqual(a.hex, '0x02444422444422334444')

    def testReplaceBitpos(self):
        a = BitString('0xff')
        a.bitpos = 8
        a.replace('0xff', '', bytealigned=True)
        self.assertEqual(a.bitpos, 0)
        a = BitString('0b0011110001')
        a.bitpos = 4
        a.replace('0b1', '0b000')
        self.assertEqual(a.bitpos, 8)
        a = BitString('0b1')
        a.bitpos = 1
        a.replace('0b1', '0b11111', bytealigned=True)
        self.assertEqual(a.bitpos, 5)
        a.replace('0b11', '0b0', False)
        self.assertEqual(a.bitpos, 3)
        a.append('0b00')
        a.replace('0b00', '0xffff')
        self.assertEqual(a.bitpos, 17)

    def testReplaceErrors(self):
        a = BitString('0o123415')
        self.assertRaises(ValueError, a.replace, '', '0o7', bytealigned=True)
        self.assertRaises(ValueError, a.replace, '0b1', '0b1', start=-100, bytealigned=True)
        self.assertRaises(ValueError, a.replace, '0b1', '0b1', end=19, bytealigned=True)


class SliceAssignmentWithStep(unittest.TestCase):
    def testDelSliceStep(self):
        a = BitString('0x000ff00')
        del a[3:5:4]
        self.assertEqual(a, '0x00000')
        del a[10:200:0]
        self.assertEqual(a, '0x00000')

    def testDelSliceNegativeStep(self):
        a = BitString('0x1234567')
        del a[3:1:-4]
        self.assertEqual(a, '0x12567')
        self.assertRaises(ValueError, a.__delitem__, slice(0, 4, -1))
        self.assertEqual(a, '0x12567')
        del a[100:80:-1]
        self.assertEqual(a, '0x12567')

    def testSetSliceStep(self):
        a = BitString()
        a[0:0:12] = '0xabcdef'
        self.assertEqual(a.bytepos, 3)
        a[1:4:4] = ''
        self.assertEqual(a, '0xaef')
        self.assertEqual(a.bitpos, 4)
        a[1::8] = '0x00'
        self.assertEqual(a, '0xae00')
        self.assertEqual(a.bytepos, 2)
        a += '0xf'
        a[1::8] = '0xe'
        self.assertEqual(a, '0xaee')
        self.assertEqual(a.bitpos, 12)
        b = BitString()
        b[0:100:8] = '0xffee'
        self.assertEqual(b, '0xffee')
        b[1:12:4] = '0xeed123'
        self.assertEqual(b, '0xfeed123')
        b[-100:2:4] = '0x0000'
        self.assertEqual(b, '0x0000ed123')
        a = BitString('0xabcde')
        self.assertEqual(a[-100:-90:4], '')
        self.assertEqual(a[-100:-4:4], '0xa')
        a[-100:-4:4] = '0x0'
        self.assertEqual(a, '0x0bcde')
        self.assertRaises(ValueError, a.__setitem__, slice(2, 0, 4), '0x33')

    def testSetSliceNegativeStep(self):
        a = BitString('0x000000')
        a[1::-8] = '0x1122'
        self.assertEqual(a, '0x221100')
        a[-1:-3:-4] = '0xaeebb'
        self.assertEqual(a, '0x2211bbeea')
        a[-1::-8] = '0xffdd'
        self.assertEqual(a, '0xddff')
        self.assertRaises(ValueError, a.__setitem__, slice(3, 4, -1), '0x12')
        b = BitString('0x00')
        b[::-1] = '0b10001111'
        self.assertEqual(b, '0xf1')

    def testInsertingUsingSetItem(self):
        a = BitString()
        a[0:0] = '0xdeadbeef'
        self.assertEqual(a, '0xdeadbeef')
        self.assertEqual(a.bytepos, 4)
        a[4:4:4] = '0xfeed'
        self.assertEqual(a, '0xdeadfeedbeef')
        self.assertEqual(a.bytepos, 4)
        a[14232:442232:0] = '0xa'
        self.assertEqual(a, '0xadeadfeedbeef')
        self.assertEqual(a.bitpos, 4)
        a.bytepos = 6
        a[0:0] = '0xff'
        self.assertEqual(a.bytepos, 1)
        a[8:0] = '0x00000'
        self.assertTrue(a.startswith('0xff00000adead'))




class Pack(unittest.TestCase):
    def testPack1(self):
        s = bitstring.pack('uint:6, bin, hex, int:6, se, ue, oct', 10, '0b110', 'ff', -1, -6, 6, '54')
        t = BitString('uint:6=10, 0b110, 0xff, int:6=-1, se=-6, ue=6, oct=54')
        self.assertEqual(s, t)
        self.assertRaises(ValueError, pack, 'tomato', '0')
        self.assertRaises(ValueError, pack, 'uint', 12)
        self.assertRaises(ValueError, pack, 'hex', 'penguin')
        self.assertRaises(ValueError, pack, 'hex12', '0x12')

    def testPackWithLiterals(self):
        s = bitstring.pack('0xf')
        self.assertEqual(s, '0xf')
        self.assertTrue(type(s), BitString)
        s = pack('0b1')
        self.assertEqual(s, '0b1')
        s = pack('0o7')
        self.assertEqual(s, '0o7')
        s = pack('int:10=-1')
        self.assertEqual(s, '0b1111111111')
        s = pack('uint:10=1')
        self.assertEqual(s, '0b0000000001')
        s = pack('ue=12')
        self.assertEqual(s.ue, 12)
        s = pack('se=-12')
        self.assertEqual(s.se, -12)
        s = pack('bin=01')
        self.assertEqual(s.bin, '0b01')
        s = pack('hex=01')
        self.assertEqual(s.hex, '0x01')
        s = pack('oct=01')
        self.assertEqual(s.oct, '0o01')

    def testPackWithDict(self):
        a = pack('uint:6=width, se=height', height=100, width=12)
        w, h = a.unpack('uint:6, se')
        self.assertEqual(w, 12)
        self.assertEqual(h, 100)
        d = {}
        d['w'] = '0xf'
        d['300'] = 423
        d['e'] = '0b1101'
        a = pack('int:100=300, bin=e, uint:12=300', **d)
        x, y, z = a.unpack('int:100, bin, uint:12')
        self.assertEqual(x, 423)
        self.assertEqual(y, '0b1101')
        self.assertEqual(z, 423)

    def testPackWithDict2(self):
        a = pack('int:5, bin:3=b, 0x3, bin=c, se=12', 10, b='0b111', c='0b1')
        b = BitString('int:5=10, 0b111, 0x3, 0b1, se=12')
        self.assertEqual(a, b)
        a = pack('bits:3=b', b=BitString('0b101'))
        self.assertEqual(a, '0b101')
        a = pack('bits:24=b', b=BitString('0x001122'))
        self.assertEqual(a, '0x001122')

    def testPackWithDict3(self):
        s = pack('hex:4=e, hex:4=0xe, hex:4=e', e='f')
        self.assertEqual(s, '0xfef')
        s = pack('sep', sep='0b00')
        self.assertEqual(s, '0b00')

    def testPackWithDict4(self):
        s = pack('hello', hello='0xf')
        self.assertEqual(s, '0xf')
        s = pack('x, y, x, y, x', x='0b10', y='uint:12=100')
        t = BitString('0b10, uint:12=100, 0b10, uint:12=100, 0b10')
        self.assertEqual(s, t)
        a = [1,2,3,4,5]
        s = pack('int:8, div,'*5, *a, **{'div': '0b1'})
        t = BitString('int:8=1, 0b1, int:8=2, 0b1, int:8=3, 0b1, int:8=4, 0b1, int:8=5, 0b1')
        self.assertEqual(s, t)

    def testPackWithLocals(self):
        width = 352
        height = 288
        s = pack('uint:12=width, uint:12=height', **locals())
        self.assertEqual(s, '0x160120')

    def testPackWithLengthRestriction(self):
        s = pack('bin:3', '0b000')
        self.assertRaises(ValueError, pack, 'bin:3', '0b0011')
        self.assertRaises(ValueError, pack, 'bin:3', '0b11')
        self.assertRaises(ValueError, pack, 'bin:3=0b0011')
        self.assertRaises(ValueError, pack, 'bin:3=0b11')

        s = pack('hex:4', '0xf')
        self.assertRaises(ValueError, pack, 'hex:4', '0b111')
        self.assertRaises(ValueError, pack, 'hex:4', '0b11111')
        self.assertRaises(ValueError, pack, 'hex:8=0xf')

        s = pack('oct:6', '0o77')
        self.assertRaises(ValueError, pack, 'oct:6', '0o1')
        self.assertRaises(ValueError, pack, 'oct:6', '0o111')
        self.assertRaises(ValueError, pack, 'oct:3', '0b1')
        self.assertRaises(ValueError, pack, 'oct:3=hello', hello='0o12')

        s = pack('bits:3', BitString('0b111'))
        self.assertRaises(ValueError, pack, 'bits:3', BitString('0b11'))
        self.assertRaises(ValueError, pack, 'bits:3', BitString('0b1111'))
        self.assertRaises(ValueError, pack, 'bits:12=b', b=BitString('0b11'))

    def testPackNull(self):
        s = pack('')
        self.assertFalse(s)
        s = pack(',')
        self.assertFalse(s)
        s = pack(',,,,,0b1,,,,,,,,,,,,,0b1,,,,,,,,,,')
        self.assertEqual(s, '0b11')
        s = pack(',,uint:12,,bin:3,', 100, '100')
        a, b = s.unpack(',,,uint:12,,,,bin:3,,,')
        self.assertEqual(a, 100)
        self.assertEqual(b, '0b100')

    def testPackDefaultUint(self):
        s = pack('10, 5', 1, 2)
        a, b = s.unpack('10, 5')
        self.assertEqual((a, b), (1, 2))
        s = pack('10=150, 12=qee', qee=3)
        self.assertEqual(s, 'uint:10=150, uint:12=3')
        t = BitString('100=5')
        self.assertEqual(t, 'uint:100=5')

    def testPackDefualtUintErrors(self):
        self.assertRaises(ValueError, BitString, '5=-1')

class Unpack(unittest.TestCase):

    def testUnpack1(self):
        s = BitString('uint:13=23, hex=e, bin=010, int:41=-554, 0o44332, se=-12, ue=4')
        s.pos = 11
        a, b, c, d, e, f, g = s.unpack('uint:13, hex:4, bin:3, int:41, oct:15, se, ue')
        self.assertEqual(a, 23)
        self.assertEqual(b, '0xe')
        self.assertEqual(c, '0b010')
        self.assertEqual(d, -554)
        self.assertEqual(e, '0o44332')
        self.assertEqual(f, -12)
        self.assertEqual(g, 4)
        self.assertEqual(s.pos, 11)

    def testUnpack2(self):
        s = BitString('0xff, 0b000, uint:12=100')
        a, b, c = s.unpack('bits:8, bits, uint:12')
        self.assertEqual(type(s), BitString)
        self.assertEqual(a, '0xff')
        self.assertEqual(type(s), BitString)
        self.assertEqual(b, '0b000')
        self.assertEqual(c, 100)
        a, b  = s.unpack('bits:11', 'uint')
        self.assertEqual(a, '0xff, 0b000')
        self.assertEqual(b, 100)

    def testUnpackNull(self):
        s = pack('0b1, , , 0xf,')
        a, b = s.unpack('bin:1,,,hex:4,')
        self.assertEqual(a, '0b1')
        self.assertEqual(b, '0xf')

class FromFile(unittest.TestCase):

    def testCreationFromFileOperations(self):
        s = BitString(filename='smalltestfile')
        s.append('0xff')
        self.assertEqual(s.hex, '0x0123456789abcdefff')

        s = BitString(filename='smalltestfile')
        t = BitString('0xff') + s
        self.assertEqual(t.hex, '0xff0123456789abcdef')

        s = BitString(filename='smalltestfile')
        del s[:1]
        self.assertEqual((BitString('0b0') + s).hex, '0x0123456789abcdef')

        s = BitString(filename='smalltestfile')
        del s[:7*8]
        self.assertEqual(s.hex, '0xef')

        s = BitString(filename='smalltestfile')
        s.insert('0xc', 4)
        self.assertEqual(s.hex, '0x0c123456789abcdef')

        s = BitString(filename='smalltestfile')
        s.prepend('0xf')
        self.assertEqual(s.hex, '0xf0123456789abcdef')

        s = BitString(filename='smalltestfile')
        s.overwrite('0xaaa', 12)
        self.assertEqual(s.hex, '0x012aaa6789abcdef')

        s = BitString(filename='smalltestfile')
        s.reverse()
        self.assertEquals(s.hex, '0xf7b3d591e6a2c480')

        s = BitString(filename='smalltestfile')
        del s[-60:]
        self.assertEqual(s.hex, '0x0')

        s = BitString(filename='smalltestfile')
        del s[:60]
        self.assertEqual(s.hex, '0xf')

    def testFileProperties(self):
        s = Bits(filename='smalltestfile')
        self.assertEqual(s.hex, '0x0123456789abcdef')
        self.assertEqual(s.uint, 81985529216486895)
        self.assertEqual(s.int, 81985529216486895)
        self.assertEqual(s.bin, '0b0000000100100011010001010110011110001001101010111100110111101111')
        self.assertEqual(s[:-1].oct, '0o002215053170465363367')
        s.bitpos = 0
        self.assertEqual(s.read('se'), -72)
        s.bitpos = 0
        self.assertEqual(s.read('ue'), 144)
        self.assertEqual(s.bytes, b'\x01\x23\x45\x67\x89\xab\xcd\xef')

    def testCreationFromFileWithLength(self):
        s = Bits(filename='test.m1v', length = 32)
        self.assertEqual(s.length, 32)
        self.assertEqual(s.hex, '0x000001b3')
        s = Bits(filename='test.m1v', length = 0)
        self.assertFalse(s)
        self.assertRaises(ValueError, BitString, filename='test.m1v', length=999999999999)

    def testCreationFromFileWithOffset(self):
        a = BitString(filename='test.m1v', offset=4)
        self.assertEqual(a.peekbytes(4).hex, '0x00001b31')
        b = BitString(filename='test.m1v', offset=28)
        self.assertEqual(b.peekbyte().hex, '0x31')

    def testFileSlices(self):
        s = BitString(filename='smalltestfile')
        t = s[-2::8]
        self.assertEqual(s[-2::8].hex, '0xcdef')

    def testCreataionFromFileErrors(self):
        self.assertRaises(IOError, BitString, filename='Idonotexist')

    def testFindInFile(self):
        s = BitString(filename = 'test.m1v')
        self.assertTrue(s.find('0x160120'))
        self.assertEqual(s.bytepos, 4)
        s3 = s.readbytes(3)
        self.assertEqual(s3.hex, '0x160120')
        s.bytepos = 0
        self.assertTrue(s._pos == 0)
        self.assertTrue(s.find('0x0001b2'))
        self.assertEqual(s.bytepos, 13)

    def testHexFromFile(self):
        s = BitString(filename='test.m1v')
        self.assertEqual(s[0:32].hex, '0x000001b3')
        self.assertEqual(s[-32:].hex, '0x000001b7')
        s.hex = '0x11'
        self.assertEqual(s.hex, '0x11')

    def testFileOperations(self):
        s1 = BitString(filename='test.m1v')
        s2 = BitString(filename='test.m1v')
        self.assertEqual(s1.readbytes(4).hex, '0x000001b3')
        self.assertEqual(s2.readbytes(4).hex, '0x000001b3')
        s1.bytepos += 4
        self.assertEqual(s1.readbyte().hex, '0x02')
        self.assertEqual(s2.readbytes(5).hex, '0x1601208302')
        s1.pos = s1.len
        try:
            s1.pos += 1
            self.assertTrue(False)
        except ValueError:
            pass

    def testVeryLargeFiles(self):
        # This uses an 11GB file which isn't distributed for obvious reasons
        # and so this test won't work for anyone except me!
        try:
            s = Bits(filename='11GB.mkv')
        except IOError:
            return
        self.assertEqual(s.len, 11743020505*8)
        self.assertEqual(s[1000000000:1000000100].hex, '0xbdef7335d4545f680d669ce24')
        self.assertEqual(s[-4::8].hex, '0xbbebf7a1')
class CreationErrors(unittest.TestCase):

    def testIncorrectBinAssignment(self):
        s = BitString()
        self.assertRaises(ValueError, s._setbin, '0010020')

    def testIncorrectHexAssignment(self):
        s = BitString()
        self.assertRaises(ValueError, s._sethex, '0xabcdefg')

class Length(unittest.TestCase):

    def testLengthZero(self):
        self.assertEqual(BitString('').len, 0)

    def testLength(self):
        self.assertEqual(BitString('0x80').len, 8)
        self.assertEqual(BitString('0x80', 5).length, 5)
        self.assertEqual(BitString('0x80', 0).length, 0)

    def testLengthErrors(self):
        self.assertRaises(ValueError, BitString, bin='111', length=-1)
        self.assertRaises(ValueError, BitString, bin='111', length=4)

    def testOffsetLengthError(self):
        self.assertRaises(ValueError, BitString, hex='0xffff', offset=-1)

class SimpleConversions(unittest.TestCase):

    def testConvertToUint(self):
        self.assertEqual(BitString('0x10').uint, 16)
        self.assertEqual(BitString('0x1f', 6).uint, 7)

    def testConvertToInt(self):
        self.assertEqual(BitString('0x10').int, 16)
        self.assertEqual(BitString('0xf0', 5).int, -2)

    def testConvertToHex(self):
        self.assertEqual(BitString(bytes=b'\x00\x12\x23\xff').hex, '0x001223ff')
        s = BitString('0b11111')
        self.assertRaises(ValueError, s._gethex)

    def testConvertToBin(self):
        self.assertEqual(BitString('0x00',1).bin, '0b0')
        self.assertEqual(BitString('0x80',1).bin, '0b1')
        self.assertEqual(BitString(bytes=b'\x00\x12\x23\xff').bin, '0b00000000000100100010001111111111')

class Empty(unittest.TestCase):

    def testEmptyBitstring(self):
        s = BitString()
        self.assertFalse(s.readbits(120))
        self.assertEqual(s.bin, '')
        self.assertEqual(s.hex, '')
        self.assertRaises(ValueError, s._getint)
        self.assertRaises(ValueError, s._getuint)
        self.assertFalse(s)

    def testNonEmptyBitString(self):
        s = BitString(bin='0')
        self.assertFalse(not s)

class Position(unittest.TestCase):

    def testBitPosition(self):
        s = BitString(bytes=b'\x00\x00\x00')
        self.assertEqual(s.bitpos, 0)
        s.readbits(5)
        self.assertEqual(s.pos, 5)
        s.pos = s.len
        self.assertFalse(s.readbit())

    def testBytePosition(self):
        s = BitString(bytes=b'\x00\x00\x00')
        self.assertEqual(s.bytepos, 0)
        s.readbits(10)
        self.assertRaises(BitStringError, s._getbytepos)
        s.readbits(6)
        self.assertEqual(s.bytepos, 2)

    def testSeekToBit(self):
        s = BitString(bytes=b'\x00\x00\x00\x00\x00\x00')
        s.bitpos = 0
        self.assertEqual(s.bitpos, 0)
        self.assertRaises(ValueError, s._setbitpos, -1)
        self.assertRaises(ValueError, s._setbitpos, 6*8 + 1)
        s.bitpos = 6*8
        self.assertEqual(s.bitpos, 6*8)

    def testSeekToByte(self):
        s = BitString(bytes=b'\x00\x00\x00\x00\x00\xab')
        s.bytepos = 5
        self.assertEqual(s.readbits(8).hex, '0xab')

    def testAdvanceBitsAndBytes(self):
        s = BitString(bytes=b'\x00\x00\x00\x00\x00\x00\x00\x00')
        s.pos += 5
        self.assertEqual(s.pos, 5)
        s.bitpos += 16
        self.assertEqual(s.pos, 2*8 + 5)
        s.pos -= 8
        self.assertEqual(s.pos, 8 + 5)

    def testRetreatBitsAndBytes(self):
        a = BitString(length=100)
        a.pos = 80
        a.bytepos -= 5
        self.assertEqual(a.bytepos, 5)
        a.pos -= 5
        self.assertEqual(a.pos, 35)


class Offset(unittest.TestCase):

    def testOffset1(self):
        s = BitString(bytes=b'\x00\x1b\x3f', offset=4)
        self.assertEqual(s.readbits(8).bin, '0b00000001')
        self.assertEqual(s.length, 20)

    def testOffset2(self):
        s1 = BitString(bytes=b'\xf1\x02\x04')
        s2 = BitString(bytes=b'\xf1\x02\x04', length=23)
        for i in [1,2,3,4,5,6,7,6,5,4,3,2,1,0,7,3,5,1,4]:
            s1._datastore.setoffset(i)
            self.assertEqual(s1.hex, '0xf10204')
            s2._datastore.setoffset(i)
            self.assertEqual(s2.bin, '0b11110001000000100000010')

class Append(unittest.TestCase):

    def testAppend(self):
        s1 = BitString('0x00', 5)
        s1.append(BitString('0xff', 1))
        self.assertEqual(s1.bin, '0b000001')
        self.assertEqual((BitString('0x0102') + BitString('0x0304')).hex, '0x01020304')

    def testAppendSameBitstring(self):
        s1 = BitString('0xf0', 6)
        s1.append(s1)
        self.assertEqual(s1.bin, '0b111100111100')

    def testAppendWithOffset(self):
        s = BitString(bytes=b'\x28\x28', offset=1)
        s.append('0b0')
        self.assertEqual(s.hex, '0x5050')

class ByteAlign(unittest.TestCase):

    def testByteAlign(self):
        s = BitString(hex='0001ff23')
        s.bytealign()
        self.assertEqual(s.bytepos, 0)
        s.pos += 11
        s.bytealign()
        self.assertEqual(s.bytepos, 2)
        s.pos -= 10
        s.bytealign()
        self.assertEqual(s.bytepos, 1)

    def testByteAlignWithOffset(self):
        s = BitString(hex='0112233')
        s._datastore.setoffset(3)
        bitstoalign = s.bytealign()
        self.assertEqual(bitstoalign, 0)
        self.assertEqual(s.readbits(5).bin, '0b00001')

    def testInsertByteAligned(self):
        s = BitString('0x0011')
        s.insert(BitString('0x22'), 8)
        self.assertEqual(s.hex, '0x002211')
        s = BitString('0xff', length=0)
        s.insert(BitString(bin='101'), 0)
        self.assertEqual(s.bin, '0b101')

class Truncate(unittest.TestCase):

    def testTruncateStart(self):
        s = BitString('0b1')
        del s[:1]
        self.assertFalse(s)
        s = BitString(hex='1234')
        self.assertEqual(s.hex, '0x1234')
        del s[:4]
        self.assertEqual(s.hex, '0x234')
        del s[:9]
        self.assertEqual(s.bin, '0b100')
        del s[:2]
        self.assertEqual(s.bin, '0b0')
        self.assertEqual(s.len, 1)
        del s[:1]
        self.assertFalse(s)

    def testTruncateEnd(self):
        s = BitString('0b1')
        del s[-1:]
        self.assertFalse(s)
        s = BitString(bytes=b'\x12\x34')
        self.assertEqual(s.hex, '0x1234')
        del s[-4:]
        self.assertEqual(s.hex, '0x123')
        del s[-9:]
        self.assertEqual(s.bin, '0b000')
        del s[-3:]
        self.assertFalse(s)
        s = BitString('0b001')
        del s[:2]
        del s[-1:]
        self.assertFalse(s)

class Slice(unittest.TestCase):

    def testByteAlignedSlice(self):
        s = BitString(hex='0x123456')
        self.assertEqual(s[8:16].hex, '0x34')
        s = s[8:24]
        self.assertEqual(s.len, 16)
        self.assertEqual(s.hex, '0x3456')
        s = s[0:8]
        self.assertEqual(s.hex, '0x34')
        s.hex = '0x123456'
        self.assertEqual(s[8:24][0:8].hex, '0x34')

    def testSlice(self):
        s = BitString(bin='000001111100000')
        s1 = s[0:5]
        s2 = s[5:10]
        s3 = s[10:15]
        self.assertEqual(s1.bin, '0b00000')
        self.assertEqual(s2.bin, '0b11111')
        self.assertEqual(s3.bin, '0b00000')

class Insert(unittest.TestCase):

    def testInsert(self):
        s1 = BitString(hex='0x123456')
        s2 = BitString(hex='0xff')
        s1.bytepos = 1
        s1.insert(s2)
        self.assertEqual(s1.bytepos, 2)
        self.assertEqual(s1.hex, '0x12ff3456')
        s1.insert('0xee', 24)
        self.assertEqual(s1.hex, '0x12ff34ee56')
        self.assertEqual(s1.bitpos, 32)
        self.assertRaises(ValueError, s1.insert, '0b1', -1000)
        self.assertRaises(ValueError, s1.insert, '0b1', 1000)

    def testInsertNull(self):
        s = BitString(hex='0x123').insert(BitString(), 3)
        self.assertEqual(s.hex, '0x123')

    def testInsertBits(self):
        one = BitString(bin='1')
        zero = BitString(bin='0')
        s = BitString(bin='00')
        s.insert(one, 0)
        self.assertEqual(s.bin, '0b100')
        s.insert(zero, 0)
        self.assertEqual(s.bin, '0b0100')
        s.insert(one, s.len)
        self.assertEqual(s.bin, '0b01001')
        s.insert(s, 2)
        self.assertEqual(s.bin, '0b0101001001')

class Resetting(unittest.TestCase):

    def testSetHex(self):
        s = BitString()
        s.hex = '0'
        self.assertEqual(s.hex, '0x0')
        s.hex = '0x010203045'
        self.assertEqual(s.hex, '0x010203045')
        self.assertRaises(ValueError, s._sethex, '0x002g')

    def testSetHexWithLength(self):
        s = BitString(hex='0xffff', length = 9)
        self.assertEqual(s.bin, '0b111111111')
        s2 = s[0:4]
        self.assertEqual(s2.hex, '0xf')

    def testSetBin(self):
        s = BitString(bin="000101101")
        self.assertEqual(s.bin, '0b000101101')
        self.assertEqual(s.len, 9)
        s.bin = '0'
        self.assertEqual(s.bin, '0b0')
        self.assertEqual(s.len, 1)

    def testSetEmptyBin(self):
        s = BitString(hex='0x000001b3')
        s.bin = ''
        self.assertEqual(s.len, 0)
        self.assertEqual(s.bin, '')

    def testSetInvalidBin(self):
        s = BitString()
        self.assertRaises(ValueError, s._setbin, '00102')


class Adding(unittest.TestCase):

    def testAdding(self):
        s1 = BitString(hex='0x0102')
        s2 = BitString(hex='0x0304')
        s3 = s1 + s2
        self.assertEqual(s1.hex, '0x0102')
        self.assertEqual(s2.hex, '0x0304')
        self.assertEqual(s3.hex, '0x01020304')
        s3 += s1
        self.assertEqual(s3.hex, '0x010203040102')
        self.assertEqual(s2[9:16].bin, '0b0000100')
        self.assertEqual(s1[0:9].bin, '0b000000010')
        s4 = BitString(bin='000000010', length=9) + \
             BitString(bin='0000100', length=7)
        self.assertEqual(s4.bin, '0b0000000100000100')
        s2p = s2[9:16]
        s1p = s1[0:9]
        s5p = s1p + s2p
        s5 = s1[0:9] + s2[9:16]
        self.assertEqual(s5.bin, '0b0000000100000100')

    def testMoreAdding(self):
        s = BitString(bin='00') + BitString(bin='') + BitString(bin='11')
        self.assertEqual(s.bin, '0b0011')
        s = '0b01'
        s += BitString('0b11')
        self.assertEqual(s.bin, '0b0111')
        s = BitString('0x00')
        t = BitString('0x11')
        s += t
        self.assertEquals(s.hex, '0x0011')
        self.assertEquals(t.hex, '0x11')
        s += s
        self.assertEquals(s.hex, '0x00110011')

    def testAddingWithOffset(self):
        s = BitString(bin='000011111') + BitString(bin='1110001', offset=3)
        self.assertEqual(s.bin, '0b0000111110001')

    def testRadd(self):
        s = '0xff' + BitString('0xee')
        self.assertEqual(s.hex, '0xffee')

    def testOverwriteBit(self):
        s = BitString(bin='0')
        s.overwrite(BitString(bin='1'), 0)
        self.assertEqual(s.bin, '0b1')

    def testOverwriteLimits(self):
        s = BitString(bin='0b11111')
        s.overwrite(BitString(bin='000'), 0)
        self.assertEqual(s.bin, '0b00011')
        s.overwrite('0b000', 2)
        self.assertEqual(s.bin, '0b00000')

    def testOverwriteNull(self):
        s = BitString(hex='342563fedec')
        s2 = BitString(s)
        s.overwrite(BitString(bin=''), 23)
        self.assertEqual(s.bin, s2.bin)

    def testOverwritePosition(self):
        s1 = BitString(hex='0123456')
        s2 = BitString(hex='ff')
        s1.bytepos = 1
        s1.overwrite(s2)
        self.assertEqual((s1.hex, s1.bytepos), ('0x01ff456', 2))
        s1.overwrite('0xff', 0)
        self.assertEqual((s1.hex, s1.bytepos), ('0xffff456', 1))

    def testOverwriteWithSelf(self):
        s = BitString('0x123')
        s.overwrite(s)
        self.assertEqual(s, '0x123')

    def testTruncateAsserts(self):
        s = BitString('0x001122')
        s.bytepos = 2
        del s[-s.len:]
        self.assertEqual(s.bytepos, 0)
        s.append('0x00')
        s.append('0x1122')
        s.bytepos = 2
        del s[:s.len]
        self.assertEqual(s.bytepos, 0)
        s.append('0x00')

    def testOverwriteErrors(self):
        s = BitString(bin='11111')
        self.assertRaises(ValueError, s.overwrite, BitString(bin='1'), -10)
        self.assertRaises(ValueError, s.overwrite, BitString(bin='1'), 6)
        self.assertRaises(ValueError, s.overwrite, BitString(bin='11111'), 1)

    def testDeleteBits(self):
        s = BitString(bin='000111100000')
        s.bitpos = 4
        del s[4:8]
        self.assertEqual(s.bin, '0b00010000')
        del s[4:1004]
        self.assertTrue(s.bin, '0b0001')

    def testDeleteBitsWithPosition(self):
        s = BitString(bin='000111100000')
        del s[4:8]
        self.assertEqual(s.bin, '0b00010000')

    def testDeleteBytes(self):
        s = BitString('0x00112233')
        del s[8:8]
        self.assertEqual(s.hex, '0x00112233')
        self.assertEqual(s.pos, 8)
        del s[8:16]
        self.assertEqual(s.hex, '0x002233')
        self.assertEqual(s.bytepos, 1)
        del s[:3:8]
        self.assertFalse(s)
        self.assertEqual(s.pos, 0)

    def testGetItemWithPositivePosition(self):
        s = BitString(bin='0b1011')
        self.assertEqual(s[0].bin, '0b1')
        self.assertEqual(s[1].bin, '0b0')
        self.assertEqual(s[2].bin, '0b1')
        self.assertEqual(s[3].bin, '0b1')
        self.assertRaises(IndexError, s.__getitem__, 4)

    def testGetItemWithNegativePosition(self):
        s = BitString(bin='1011')
        self.assertEqual(s[-1].bin, '0b1')
        self.assertEqual(s[-2].bin, '0b1')
        self.assertEqual(s[-3].bin, '0b0')
        self.assertEqual(s[-4].bin, '0b1')
        self.assertRaises(IndexError, s.__getitem__, -5)

    def testSlicing(self):
        s = Bits(hex='0123456789')
        self.assertEqual(s[0:8].hex, '0x01')
        self.assertFalse(s[0:0])
        self.assertFalse(s[23:20])
        self.assertEqual(s[8:12].bin, '0b0010')
        self.assertEqual(s[8:20:4], '0x89')

    def testNegativeSlicing(self):
        s = Bits(hex='0x012345678')
        self.assertEqual(s[:-8].hex, '0x0123456')
        self.assertEqual(s[-16:-8].hex, '0x56')
        self.assertEqual(s[-24:].hex, '0x345678')
        self.assertEqual(s[-1000:-6:4], '0x012')

    def testLen(self):
        s = BitString()
        self.assertEqual(len(s), 0)
        s.append(BitString(bin='001'))
        self.assertEqual(len(s), 3)

    def testJoin(self):
        s1 = BitString(bin='0')
        s2 = BitString(bin='1')
        s3 = BitString(bin='000')
        s4 = BitString(bin='111')
        strings = [s1, s2, s1, s3, s4]
        s = BitString().join(strings)
        self.assertEqual(s.bin, '0b010000111')

    def testJoin2(self):
        s1 = BitString(hex='00112233445566778899aabbccddeeff')
        s2 = BitString(bin='0b000011')
        bsl = [s1[0:32], s1[4:12], s2, s2, s2, s2]
        s = Bits().join(bsl)
        self.assertEqual(s.hex, '0x00112233010c30c3')

        bsl = [BitString(uint=j, length=12) for j in range(10) for i in range(10)]
        s = BitString().join(bsl)
        self.assertEqual(s.length, 1200)

    def testSplitByteAlignedCornerCases(self):
        s = BitString()
        bsl = s.split(BitString(hex='0xff'))
        self.assertEqual(next(bsl).hex, '')
        self.assertRaises(StopIteration, next, bsl)
        s = BitString(hex='aabbcceeddff')
        delimiter = BitString()
        bsl = s.split(delimiter)
        self.assertRaises(ValueError, next, bsl)
        delimiter = BitString(hex='11')
        bsl = s.split(delimiter)
        self.assertEqual(next(bsl).hex, s.hex)

    def testSplitByteAligned(self):
        s = BitString(hex='0x1234aa1234bbcc1234ffff')
        delimiter = BitString(hex='1234')
        bsl = s.split(delimiter)
        self.assertEqual([b.hex for b in bsl], ['', '0x1234aa', '0x1234bbcc', '0x1234ffff'])

    def testSplitByteAlignedWithIntialBytes(self):
        s = BitString(hex='aa471234fedc43 47112233 47 4723 472314')
        delimiter = BitString(hex='47')
        s.find(delimiter)
        self.assertEqual(s.bytepos, 1)
        bsl = s.split(delimiter, start=0)
        self.assertEqual([b.hex for b in bsl], ['0xaa', '0x471234fedc43', '0x47112233',
                                                  '0x47', '0x4723', '0x472314'])

    def testSplitByteAlignedWithOverlappingDelimiter(self):
        s = BitString(hex='aaffaaffaaffaaffaaff')
        bsl = s.split(BitString(hex='aaffaa'))
        self.assertEqual([b.hex for b in bsl], ['', '0xaaffaaff', '0xaaffaaffaaff'])

    def testPos(self):
        s = BitString(bin='1')
        self.assertEqual(s.bitpos, 0)
        s.readbits(1)
        self.assertEqual(s.bitpos, 1)

    def testWritingData(self):
        strings = [BitString(bin=x) for x in ['0','001','0011010010','010010','1011']]
        s = BitString().join(strings)
        s2 = BitString(bytes=s.bytes)
        self.assertEqual(s2.bin, '0b000100110100100100101011')
        s2.append(BitString(bin='1'))
        s3 = BitString(bytes=s2.tobytes())
        self.assertEqual(s3.bin, '0b00010011010010010010101110000000')

    def testWritingDataWithOffsets(self):
        s1 = BitString(bytes=b'\x10')
        s2 = BitString(bytes=b'\x08\x00', length=8, offset=1)
        s3 = BitString(bytes=b'\x04\x00', length=8, offset=2)
        self.assertTrue(s1 == s2)
        self.assertTrue(s2 == s3)
        self.assertTrue(s1.bytes == s2.bytes)
        self.assertTrue(s2.bytes == s3.bytes)

    def testVariousThings1(self):
        hexes = ['0x12345678', '0x87654321', '0xffffffffff', '0xed', '0x12ec']
        bins = ['0b001010', '0b1101011', '0b0010000100101110110110', '0b0', '0b011']
        bsl = []
        for (hex, bin) in list(zip(hexes, bins))*5:
            bsl.append(BitString(hex=hex))
            bsl.append(BitString(bin=bin))
        s = BitString().join(bsl)
        for (hex, bin) in list(zip(hexes, bins))*5:
            h = s.readbytes((len(hex)-2)//2)
            b = s.readbits(len(bin)-2)
            self.assertEqual(h.hex, hex)
            self.assertEqual(b.bin, bin)

    def testVariousThings2(self):
        s1 = BitString(hex="0x1f08", length=13)
        self.assertEqual(s1.bin, '0b0001111100001')
        s2 = BitString(bin='0101011000', length=4)
        self.assertEqual(s2.bin, '0b0101')
        s1.append(s2)
        self.assertEqual(s1.length, 17)
        self.assertEqual(s1.bin, '0b00011111000010101')
        s1 = s1[3:8]
        self.assertEqual(s1.bin, '0b11111')

    def testVariousThings3(self):
        s1 = BitString(hex='0x012480ff', length=25, offset=2)
        s2 = s1 + s1
        self.assertEqual(s2.length, 50)
        s3 = s2[0:25]
        s4 = s2[25:50]
        self.assertEqual(s3.bin, s4.bin)

    def testPeekBit(self):
        s = BitString(bin='01')
        self.assertEqual(s.peekbit().bin, '0b0')
        self.assertEqual(s.peekbit().bin, '0b0')
        self.assertEqual(s.readbit().bin, '0b0')
        self.assertEqual(s.peekbit().bin, '0b1')
        self.assertEqual(s.peekbit().bin, '0b1')

    def testPeekBits(self):
        s = BitString(bytes=b'\x1f', offset=3)
        self.assertEqual(s.len, 5)
        self.assertEqual(s.peekbits(5).bin, '0b11111')
        self.assertEqual(s.peekbits(5).bin, '0b11111')
        s.pos += 1
        self.assertEqual(s.peekbits(5), '0b1111')

    def testPeekByte(self):
        s = BitString(hex='001122334455')
        self.assertEqual(s.peekbyte().hex, '0x00')
        self.assertEqual(s.readbyte().hex, '0x00')
        s.pos += 33
        self.assertEqual(s.peekbyte(), '0b1010101')

    def testPeekBytes(self):
        s = BitString(hex='001122334455')
        self.assertEqual(s.peekbytes(2).hex, '0x0011')
        self.assertEqual(s.readbytes(3).hex, '0x001122')
        self.assertEqual(s.peekbytes(3).hex, '0x334455')
        self.assertEqual(s.peekbytes(4).hex, '0x334455')

    def testAdvanceBit(self):
        s = BitString(hex='0xff')
        s.bitpos = 6
        s.pos += 1
        self.assertEqual(s.bitpos, 7)
        s.bitpos += 1
        try:
            s.pos += 1
            self.assertTrue(False)
        except ValueError:
            pass

    def testAdvanceByte(self):
        s = BitString(hex='0x010203')
        s.bytepos += 1
        self.assertEqual(s.bytepos, 1)
        s.bytepos += 1
        self.assertEqual(s.bytepos, 2)
        s.bytepos += 1
        try:
            s.bytepos += 1
            self.assertTrue(False)
        except ValueError:
            pass

    def testRetreatBit(self):
        s = BitString(hex='0xff')
        try:
            s.pos -= 1
            self.assertTrue(False)
        except ValueError:
            pass
        s.pos = 5
        s.pos -= 1
        self.assertEqual(s.pos, 4)

    def testRetreatByte(self):
        s = BitString(hex='0x010203')
        try:
            s.bytepos -= 1
            self.assertTrue(False)
        except ValueError:
            pass
        s.bytepos = 3
        s.bytepos -= 1
        self.assertEqual(s.bytepos, 2)
        self.assertEqual(s.readbyte().hex, '0x03')

    def testCreationByAuto(self):
        s = BitString('0xff')
        self.assertEqual(s.hex, '0xff')
        s = BitString('0b00011')
        self.assertEqual(s.bin, '0b00011')
        self.assertRaises(ValueError, BitString, 'hello')
        s = BitString([True, False, True], length=1, offset=1)
        self.assertEqual(s, '0b0')
        s = BitString('0o5', length=1, offset=1)
        self.assertEqual(s, '0b0')
        s = BitString('0x9', length=2, offset=1)
        self.assertEqual(s, '0b00')
        s1 = BitString(bytes=b'\xf5', length=3, offset=5)
        s2 = BitString(s1, length=1, offset=1)
        self.assertEqual(s2, '0b0')
        s = BitString('0b00100', offset=2, length=1)
        self.assertEqual(s, '0b1')
        s = BitString(bytes=b'\xff', offset=2)
        t = BitString(s, offset=2)
        self.assertEqual(t, '0b1111')
        self.assertRaises(TypeError, BitString, auto=1.2)

    def testCreationByAuto2(self):
        s = BitString('bin=001')
        self.assertEqual(s.bin, '0b001')
        s = BitString('oct=0o007')
        self.assertEqual(s.oct, '0o007')
        s = BitString('hex=123abc')
        self.assertEqual(s, '0x123abc')

        s = BitString('bin:2=01', length=1)
        self.assertEqual(s, '0b0')
        for s in ['bin:1=01', 'bits:4=0b1', 'oct:3=000', 'hex:4=0x1234']:
            self.assertRaises(ValueError, BitString, s)

    def testInsertUsingAuto(self):
        s = BitString('0xff')
        s.insert('0x00', 4)
        self.assertEqual(s.hex, '0xf00f')
        self.assertRaises(ValueError, s.insert, 'ff')

    def testOverwriteUsingAuto(self):
        s = BitString('0x0110')
        s.overwrite('0b1')
        self.assertEqual(s.hex, '0x8110')
        s.overwrite('')
        self.assertEqual(s.hex, '0x8110')
        self.assertRaises(ValueError, s.overwrite, '0bf')

    def testFindUsingAuto(self):
        s = BitString('0b000000010100011000')
        self.assertTrue(s.find('0b101'))
        self.assertEqual(s.pos, 7)

    def testFindbytealignedUsingAuto(self):
        s = BitString('0x00004700')
        self.assertTrue(s.find('0b01000111', bytealigned=True))
        self.assertEqual(s.bytepos, 2)

    def testAppendUsingAuto(self):
        s = BitString('0b000')
        s.append('0b111')
        self.assertEqual(s.bin, '0b000111')
        s.append('0b0')
        self.assertEqual(s.bin, '0b0001110')

    def testSplitByteAlignedUsingAuto(self):
        s = BitString('0x000143563200015533000123')
        sections = s.split('0x0001')
        self.assertEqual(next(sections).hex, '')
        self.assertEqual(next(sections).hex, '0x0001435632')
        self.assertEqual(next(sections).hex, '0x00015533')
        self.assertEqual(next(sections).hex, '0x000123')
        self.assertRaises(StopIteration, next, sections)

    def testSplitByteAlignedWithSelf(self):
        s = BitString('0x1234')
        sections = s.split(s)
        self.assertEqual(next(sections).hex, '')
        self.assertEqual(next(sections).hex, '0x1234')
        self.assertRaises(StopIteration, next, sections)

    def testPrepend(self):
        s = BitString('0b000')
        s.prepend('0b11')
        self.assertEquals(s.bin, '0b11000')
        s.prepend(s)
        self.assertEquals(s.bin, '0b1100011000')
        s.prepend('')
        self.assertEqual(s.bin, '0b1100011000')

    def testNullSlice(self):
        s = BitString('0x111')
        t = s[1:1]
        self.assertEqual(t._datastore.bytelength, 0)

    def testMultipleAutos(self):
        s = BitString('0xa')
        s.prepend('0xf')
        s.append('0xb')
        self.assertEqual(s.hex, '0xfab')
        s.prepend(s)
        s.append('0x100')
        s.overwrite('0x5', 4)
        self.assertEqual(s.hex, '0xf5bfab100')

    def testReverse(self):
        s = BitString('0b0011')
        s.reverse()
        self.assertEqual(s.bin, '0b1100')
        s = BitString('0b10')
        s.reverse()
        self.assertEqual(s.bin, '0b01')
        s = BitString()
        s.reverse()
        self.assertEqual(s.bin, '')

    def testInitWithConcatenatedStrings(self):
        s = BitString('0xff 0Xee 0xd 0xcc')
        self.assertEqual(s.hex, '0xffeedcc')
        s = BitString('0b0 0B111 0b001')
        self.assertEqual(s.bin, '0b0111001')
        s += '0b1' + '0B1'
        self.assertEqual(s.bin, '0b011100111')
        s = BitString(hex='ff0xee')
        self.assertEqual(s.hex, '0xffee')
        s = BitString(bin='000b0b11')
        self.assertEqual(s.bin, '0b0011')
        s = BitString('  0o123 0O 7 0   o1')
        self.assertEqual(s.oct, '0o12371')
        s += '  0 o 332'
        self.assertEqual(s.oct, '0o12371332')

    def testEquals(self):
        s1 = BitString('0b01010101')
        s2 = BitString('0b01010101')
        self.assertTrue(s1 == s2)
        s2._datastore.setoffset(4)
        self.assertTrue(s1 == s2)
        s3 = BitString()
        s4 = BitString()
        self.assertTrue(s3 == s4)
        self.assertFalse(s3 != s4)
        s5 = BitString(bytes=b'\xff', offset=2, length=3)
        s6 = BitString('0b111')
        self.assertTrue(s5 == s6)

    def testNotEquals(self):
        s1 = BitString('0b0')
        s2 = BitString('0b1')
        self.assertTrue(s1 != s2)
        self.assertFalse(s1 != BitString('0b0'))

    def testEqualityWithAutoInitialised(self):
        a = BitString('0b00110111')
        self.assertTrue(a == '0b00110111')
        self.assertTrue(a == '0x37')
        self.assertTrue('0b0011 0111' == a)
        self.assertTrue('0x3 0x7' == a)
        self.assertFalse(a == '0b11001000')
        self.assertFalse('0x3737' == a)

    def testInvertSpecialMethod(self):
        s = BitString('0b00011001')
        self.assertEqual((~s).bin, '0b11100110')
        self.assertEqual((~BitString('0b0')).bin, '0b1')
        self.assertEqual((~BitString('0b1')).bin, '0b0')
        self.assertTrue(~~s == s)

    def testInvertSpecialMethodErrors(self):
        s = BitString()
        self.assertRaises(BitStringError, s.__invert__)



    def testJoinWithAuto(self):
        s = BitString().join(['0xf', '0b00', BitString(bin='11')])
        self.assertEqual(s.bin, '0b11110011')

    def testAutoBitStringCopy(self):
        s = BitString('0xabcdef')
        t = BitString(s)
        self.assertEqual(t.hex, '0xabcdef')
        del s[-8:]
        self.assertEqual(t.hex, '0xabcdef')


    def testMultiplication(self):
        a = BitString('0xff')
        b = a*8
        self.assertEqual(b.hex, '0xffffffffffffffff')
        b = 4*a
        self.assertEqual(b.hex, '0xffffffff')
        self.assertTrue(1*a == a*1 == a)
        c = a*0
        self.assertFalse(c)
        a *= 3
        self.assertEqual(a.hex, '0xffffff')
        a *= 0
        self.assertFalse(a)
        one = BitString('0b1')
        zero = BitString('0b0')
        mix = one*2 + 3*zero + 2*one*2
        self.assertEqual(mix.bin, '0b110001111')
        q = BitString()
        q *= 143
        self.assertFalse(q)
        q += [True, True, False]
        q.pos += 2
        q *= 0
        self.assertFalse(q)
        self.assertEqual(q.bitpos, 0)

    def testMultiplicationWithFiles(self):
        a = BitString(filename='test.m1v')
        b = a.len
        a *= 3
        self.assertEqual(a.len, 3*b)

    def testMultiplicationErrors(self):
        a = BitString('0b1')
        b = BitString('0b0')
        self.assertRaises(ValueError, a.__mul__, -1)
        self.assertRaises(ValueError, a.__imul__, -1)
        self.assertRaises(ValueError, a.__rmul__, -1)
        self.assertRaises(TypeError, a.__mul__, 1.2)
        self.assertRaises(TypeError, a.__rmul__, b)
        self.assertRaises(TypeError, a.__imul__, b)

    def testFileAndMemEquivalence(self):
        a = BitString(filename='smalltestfile')
        b = BitString(filename='smalltestfile')[:]
        self.assertTrue(isinstance(a._datastore, bitstring.FileArray))
        self.assertTrue(isinstance(b._datastore, bitstring.MemArray))
        self.assertEqual(a._datastore[0], b._datastore[0])
        self.assertEqual(a._datastore[1:5], bytearray(b._datastore[1:5]))

    def testByte2Bits(self):
        for i in range(256):
            s = BitString(bin=bitstring.BYTE_TO_BITS[i])
            self.assertEqual(i, s.uint)
            self.assertEqual(s.length, 8)

    def testBitwiseAnd(self):
        a = BitString('0b01101')
        b = BitString('0b00110')
        self.assertEqual((a&b).bin, '0b00100')
        self.assertEqual((a&'0b11111'), a)
        self.assertRaises(ValueError, a.__and__, '0b1')
        self.assertRaises(ValueError, b.__and__, '0b110111111')
        c = BitString('0b0011011')
        c.pos = 4
        d = c & '0b1111000'
        self.assertEqual(d.pos, 0)
        self.assertEqual(d.bin, '0b0011000')
        d = '0b1111000' & c
        self.assertEqual(d.bin, '0b0011000')

    def testBitwiseOr(self):
        a = BitString('0b111001001')
        b = BitString('0b011100011')
        self.assertEqual((a | b).bin, '0b111101011')
        self.assertEqual((a | '0b000000000'), a)
        self.assertRaises(ValueError, a.__or__, '0b0000')
        self.assertRaises(ValueError, b.__or__, a + '0b1')
        a = '0xff00' | BitString('0x00f0')
        self.assertEquals(a.hex, '0xfff0')

    def testBitwiseXor(self):
        a = BitString('0b111001001')
        b = BitString('0b011100011')
        self.assertEqual((a ^ b).bin, '0b100101010')
        self.assertEqual((a ^ '0b111100000').bin, '0b000101001')
        self.assertRaises(ValueError, a.__xor__, '0b0000')
        self.assertRaises(ValueError, b.__xor__, a + '0b1')
        a = '0o707' ^ BitString('0o777')
        self.assertEqual(a.oct, '0o070')

    def testSplit(self):
        a = BitString('0b0 010100111 010100 0101 010')
        a.pos = 20
        subs = [i.bin for i in a.split('0b010')]
        self.assertEqual(subs, ['0b0', '0b010100111', '0b010100', '0b0101', '0b010'])
        self.assertEqual(a.pos, 20)

    def testSplitCornerCases(self):
        a = BitString('0b000000')
        bsl = a.split('0b1', False)
        self.assertEqual(next(bsl), a)
        self.assertRaises(StopIteration, next, bsl)
        b = BitString()
        bsl = b.split('0b001', False)
        self.assertFalse(next(bsl))
        self.assertRaises(StopIteration, next, bsl)

    def testSplitErrors(self):
        a = BitString('0b0')
        b = a.split('', False)
        self.assertRaises(ValueError, next, b)

    def testPositionInSlice(self):
        a = BitString('0x00ffff00')
        a.bytepos = 2
        b = a[8:24]
        self.assertEqual(b.bytepos, 0)

    def testSliceWithOffset(self):
        a = BitString(bytes=b'\x00\xff\x00', offset=7)
        b = a[7:12]
        self.assertEqual(b.bin, '0b11000')

    def testSplitWithMaxsplit(self):
        a = BitString('0xaabbccbbccddbbccddee')
        self.assertEqual(len(list(a.split('0xbb', bytealigned=True))), 4)
        bsl = list(a.split('0xbb', count=1, bytealigned=True))
        self.assertEqual((len(bsl), bsl[0]), (1, '0xaa'))
        bsl = list(a.split('0xbb', count=2, bytealigned=True))
        self.assertEqual(len(bsl), 2)
        self.assertEqual(bsl[0], '0xaa')
        self.assertEqual(bsl[1], '0xbbcc')

    def testSplitMore(self):
        s = BitString('0b1100011001110110')
        for i in range(10):
            a = list(s.split('0b11', False, count=i))
            b = list(s.split('0b11', False))[:i]
            self.assertEqual(a, b)
        b = s.split('0b11', count=-1)
        self.assertRaises(ValueError, next, b)

    def testFindByteAlignedWithBits(self):
        a = BitString('0x00112233445566778899')
        a.find('0b0001', bytealigned=True)
        self.assertEqual(a.bitpos, 8)

    def testFindStartbitNotByteAligned(self):
        a = BitString('0b0010000100')
        found = a.find('0b1', start=4)
        self.assertEqual((found, a.bitpos), (True, 7))
        found = a.find('0b1', start=2)
        self.assertEqual((found, a.bitpos), (True, 2))
        found = a.find('0b1', bytealigned=False, start=8)
        self.assertEqual((found, a.bitpos), (False, 2))

    def testFindEndbitNotByteAligned(self):
        a = BitString('0b0010010000')
        found = a.find('0b1', bytealigned=False, end=2)
        self.assertEqual((found, a.bitpos), (False, 0))
        found = a.find('0b1', end=3)
        self.assertEqual((found, a.bitpos), (True, 2))
        found = a.find('0b1', bytealigned=False, start=3, end=5)
        self.assertEqual((found, a.bitpos), (False, 2))
        found = a.find('0b1', start=3, end=6)
        self.assertEqual((found, a.bitpos), (True, 5))

    def testFindStartbitByteAligned(self):
        a = BitString('0xff001122ff0011ff')
        a.pos = 40
        found = a.find('0x22', start=23, bytealigned=True)
        self.assertEqual((found, a.bytepos), (True, 3))
        a.bytepos = 4
        found = a.find('0x22', start=24, bytealigned=True)
        self.assertEqual((found, a.bytepos), (True, 3))
        found = a.find('0x22', start=25, bytealigned=True)
        self.assertEqual((found, a.pos), (False, 24))
        found = a.find('0b111', start=40, bytealigned=True)
        self.assertEqual((found, a.pos), (True, 56))

    def testFindEndbitByteAligned(self):
        a = BitString('0xff001122ff0011ff')
        found = a.find('0x22', end=31, bytealigned=True)
        self.assertEqual((found, a.pos), (False, 0))
        found = a.find('0x22', end=32, bytealigned=True)
        self.assertEqual((found, a.pos), (True, 24))

    def testFindStartEndbitErrors(self):
        a = BitString('0b00100')
        self.assertRaises(ValueError, a.find, '0b1', bytealigned=False, start=-100)
        self.assertRaises(ValueError, a.find, '0b1', end=6)
        self.assertRaises(ValueError, a.find, '0b1', start=4, end=3)
        b = BitString('0x0011223344')
        self.assertRaises(ValueError, a.find, '0x22', bytealigned=True, start=-100)
        self.assertRaises(ValueError, a.find, '0x22', end=41, bytealigned=True)

    def testSplitStartbit(self):
        a = BitString('0b0010101001000000001111')
        bsl = a.split('0b001', bytealigned=False, start=1)
        self.assertEqual([x.bin for x in bsl], ['0b010101', '0b001000000', '0b001111'])
        b = a.split('0b001', start=-100)
        self.assertRaises(ValueError, next, b)
        b = a.split('0b001', start=23)
        self.assertRaises(ValueError, next, b)
        b = a.split('0b1', start=10, end=9)
        self.assertRaises(ValueError, next, b)

    def testSplitStartbitByteAligned(self):
        a = BitString('0x00ffffee')
        bsl = list(a.split('0b111', start=9, bytealigned=True))
        self.assertEqual([x.bin for x in bsl], ['0b1111111', '0b11111111', '0b11101110'])

    def testSplitEndbit(self):
        a = BitString('0b000010001001011')
        bsl = list(a.split('0b1', bytealigned=False, end=14))
        self.assertEqual([x.bin for x in bsl], ['0b0000', '0b1000', '0b100', '0b10', '0b1'])
        self.assertEqual(list(a[4:12].split('0b0', False)), list(a.split('0b0', start=4, end=12)))
        # Shouldn't raise ValueError
        bsl = list(a.split('0xffee', end=15))
        # Whereas this one will when we call next()
        bsl = a.split('0xffee', end=16)
        self.assertRaises(ValueError, next, bsl)

    def testSplitEndbitByteAligned(self):
        a = BitString('0xff00ff', length=22)
        bsl = list(a.split('0b 0000 0000 111', end=19))
        self.assertEqual([x.bin for x in bsl], ['0b11111111', '0b00000000111'])
        bsl = list(a.split('0b 0000 0000 111', end=18))
        self.assertEqual([x.bin for x in bsl], ['0b111111110000000011'])

    def testSplitMaxSplit(self):
        a = BitString('0b1'*20)
        for i in range(10):
            bsl = list(a.split('0b1', count=i))
            self.assertEqual(len(bsl), i)

    def testPrependAndAppendAgain(self):
        c = BitString('0x1122334455667788')
        c.bitpos = 40
        c.prepend('0b1')
        self.assertEqual(c.bitpos, 41)
        c = BitString()
        c.prepend('0x1234')
        self.assertEqual(c.bytepos, 2)
        c = BitString()
        c.append('0x1234')
        self.assertEqual(c.bytepos, 0)
        s = BitString(bytes=b'\xff\xff', offset=2)
        self.assertEqual(s.length, 14)
        t = BitString(bytes=b'\x80', offset=1, length=2)
        s.prepend(t)
        self.assertEqual(s, '0x3fff')

    def testFindAll(self):
        a = BitString('0b11111')
        p = a.findall('0b1')
        self.assertEqual(list(p), [0,1,2,3,4])
        p = a.findall('0b11')
        self.assertEqual(list(p), [0,1,2,3])
        p = a.findall('0b10')
        self.assertEqual(list(p), [])
        a = BitString('0x4733eeff66554747335832434547')
        p = a.findall('0x47', bytealigned=True)
        self.assertEqual(list(p), [0, 6*8, 7*8, 13*8])
        p = a.findall('0x4733', bytealigned=True)
        self.assertEqual(list(p), [0, 7*8])
        a = BitString('0b1001001001001001001')
        p = a.findall('0b1001', bytealigned=False)
        self.assertEqual(list(p), [0, 3, 6, 9, 12, 15])

    def testFindAllGenerator(self):
        a = BitString('0xff1234512345ff1234ff12ff')
        p = a.findall('0xff', bytealigned=True)
        self.assertEqual(next(p), 0)
        self.assertEqual(next(p), 6*8)
        self.assertEqual(next(p), 9*8)
        self.assertEqual(next(p), 11*8)
        self.assertRaises(StopIteration, next, p)

    def testFindAllCount(self):
        s = BitString('0b1')*100
        for i in [0, 1, 23]:
            self.assertEqual(len(list(s.findall('0b1', count=i))), i)
        b = s.findall('0b1', bytealigned=True, count=-1)
        self.assertRaises(ValueError, next, b)

    def testContains(self):
        a = BitString('0b1') + '0x0001dead0001'
        self.assertTrue('0xdead' in a)
        self.assertFalse('0xfeed' in a)

    def testRepr(self):
        max = bitstring.MAX_CHARS
        bls = ['', '0b1', '0o5', '0x43412424f41', '0b00101001010101']
        for bs in bls:
            a = BitString(bs)
            b = eval(a.__repr__())
            self.assertTrue(a == b)
        for f in [BitString(filename='test.m1v'),
                  BitString(filename='test.m1v', length=307),
                  BitString(filename='test.m1v', length=23, offset=23102)]:
            f2 = eval(f.__repr__())
            self.assertEqual(f._datastore.source.name, f2._datastore.source.name)
            self.assertTrue(f2 == f)
        a = BitString('0b1')
        self.assertEqual(repr(a), "BitString('0b1')")
        a += '0b11'
        self.assertEqual(repr(a), "BitString('0b111')")
        a += '0b1'
        self.assertEqual(repr(a), "BitString('0xf')")
        a *= max
        self.assertEqual(repr(a), "BitString('0x" + "f"*max + "')")
        a += '0xf'
        self.assertEqual(repr(a), "BitString('0x" + "f"*max + "...', length=%d)" % (max*4 + 4))

    def testPrint(self):
        s = BitString(hex='0x00')
        self.assertEqual(s.hex, s.__str__())
        s = BitString(filename='test.m1v')
        self.assertEqual(s[0:bitstring.MAX_CHARS*4].hex+'...', s.__str__())
        self.assertEqual(BitString().__str__(), '')

    def testIter(self):
        a = BitString('0b001010')
        b = BitString()
        for bit in a:
            b.append(bit)
        self.assertEqual(a, b)

    def testDelitem(self):
        a = BitString('0xffee')
        del a[0:8]
        self.assertEqual(a.hex, '0xee')
        del a[0:8]
        self.assertFalse(a)
        del a[10:12]
        self.assertFalse(a)

    def testNonZeroBitsAtStart(self):
        a = BitString(bytes=b'\xff', offset=2)
        b = BitString('0b00')
        b += a
        self.assertTrue(b == '0b0011 1111')
        #self.assertEqual(a._datastore.rawbytes, b'\xff')
        self.assertEqual(a.tobytes(), b'\xfc')

    def testNonZeroBitsAtEnd(self):
        a = BitString(bytes=b'\xff', length=5)
        #self.assertEqual(a._datastore.rawbytes, b'\xff')
        b = BitString('0b00')
        a += b
        self.assertTrue(a == '0b1111100')
        self.assertEqual(a.tobytes(), b'\xf8')
        self.assertRaises(ValueError, a._getbytes)

    def testLargeOffsets(self):
        a = BitString('0xffffffff', offset=31)
        self.assertEquals(a.bin, '0b1')
        a = BitString('0xffffffff', offset=32)
        self.assertFalse(a)
        b = BitString(bin='1111 1111 1111 1111 1111 1111 1111 110', offset=30)
        self.assertEqual(b, '0b0')
        o = BitString(oct='123456707', offset=24)
        self.assertEqual(o, '0o7')
        d = BitString(bytes=b'\x00\x00\x00\x00\x0f', offset=33, length=5)
        self.assertEqual(d, '0b00011')

    def testNewOffsetErrors(self):
        self.assertRaises(ValueError, BitString, hex='ff', offset=-1)
        self.assertRaises(ValueError, BitString, '0xffffffff', offset=33)

    def testSliceStep(self):
        a = BitString('0x3')
        b = a[::1]
        self.assertEqual(a, b)
        self.assertEqual(a[1:2:2], '0b11')
        self.assertEqual(a[0:1:2], '0b00')
        self.assertEqual(a[:1:3], '0o1')
        self.assertEqual(a[::4], a)
        self.assertFalse(a[::5])
        a = BitString('0x0011223344556677')
        self.assertEqual(a[3:5:8], '0x3344')
        self.assertEqual(a[5::8], '0x556677')
        self.assertEqual(a[-1::8], '0x77')
        self.assertEqual(a[-2::4], '0x77')
        self.assertEqual(a[:-3:8], '0x0011223344')
        self.assertEqual(a[-1000:-3:8], '0x0011223344')
        a.append('0b1')
        self.assertEqual(a[5::8], '0x556677')
        self.assertEqual(a[5:100:8], '0x556677')

    def testSliceNegativeStep(self):
        a = BitString('0o 01 23 45 6')
        self.assertEqual(a[::-3], '0o6543210')
        self.assertFalse(a[1:3:-6])
        self.assertEqual(a[2:0:-6], '0o4523')
        self.assertEqual(a[2::-6], '0o452301')
        b = a[::-1]
        a.reverse()
        self.assertEqual(b, a)
        b = BitString('0x01020408') + '0b11'
        self.assertEqual(b[::-8], '0x08040201')
        self.assertEqual(b[::-4], '0x80402010')
        self.assertEqual(b[::-2], '0b11' + BitString('0x20108040'))
        self.assertEqual(b[::-33], b[:33])
        self.assertEqual(b[::-34], b)
        self.assertFalse(b[::-35])
        self.assertEqual(b[-1:-3:-8], '0x0402')

    def testInsertionOrderAndBitpos(self):
        b = BitString()
        b[0:0] = '0b0'
        b[0:0] = '0b1'
        self.assertEqual(b, '0b10')
        self.assertEqual(b.bitpos, 1)
        a = BitString()
        a.insert('0b0')
        a.insert('0b1')
        self.assertEqual(a, '0b01')
        self.assertEqual(a.bitpos, 2)

    def testOverwriteOrderAndBitpos(self):
        a = BitString('0xff')
        a.overwrite('0xa')
        self.assertEqual(a, '0xaf')
        self.assertEqual(a.bitpos, 4)
        a.overwrite('0xb')
        self.assertEqual(a, '0xab')
        self.assertEqual(a.bitpos, 8)
        self.assertRaises(ValueError, a.overwrite, '0b1')
        a.overwrite('0xa', 4)
        self.assertEqual(a, '0xaa')
        self.assertEqual(a.bitpos, 8)

    def testInitSliceWithInt(self):
        a = BitString(length=8)
        a[:] = 100
        self.assertEqual(a.uint, 100)
        a[0] = 1
        self.assertEqual(a.bin, '0b11100100')
        a[1] = 0
        self.assertEqual(a.bin, '0b10100100')
        a[-1] = -1
        self.assertEqual(a.bin, '0b10100101')
        a[-3:] = -2
        self.assertEqual(a.bin, '0b10100110')

    def testInitSliceWithIntErrors(self):
        a = BitString('0b0000')
        self.assertRaises(ValueError, a.__setitem__, slice(0, 4), 16)
        self.assertRaises(ValueError, a.__setitem__, slice(0, 4), -9)
        self.assertRaises(ValueError, a.__setitem__, 0, 2)
        self.assertRaises(ValueError, a.__setitem__, 0, -2)

    def testReverseWithSlice(self):
        a = BitString('0x0012ff')
        a.reverse()
        self.assertEqual(a, '0xff4800')
        a.reverse(8, 16)
        self.assertEqual(a, '0xff1200')
        b = a[8:16]
        b.reverse()
        a[8:16] = b
        self.assertEqual(a, '0xff4800')

    def testReverseWithSliceErrors(self):
        a = BitString('0x123')
        self.assertRaises(ValueError, a.reverse, -1, 4)
        self.assertRaises(ValueError, a.reverse, 10, 9)
        self.assertRaises(ValueError, a.reverse, 1, 10000)

    def testInitialiseFromList(self):
        a = BitString([])
        self.assertFalse(a)
        a = BitString([True, False, [], [0], 'hello'])
        self.assertEqual(a, '0b10011')
        a += []
        self.assertEqual(a, '0b10011')
        a += [True, False, True]
        self.assertEqual(a, '0b10011101')
        a.find([12, 23])
        self.assertEqual(a.pos, 3)
        self.assertEqual([1, 0, False, True], BitString('0b1001'))
        a = [True] + BitString('0b1')
        self.assertEqual(a, '0b11')

    def testInitialiseFromTuple(self):
        a = BitString(())
        self.assertFalse(a)
        a = BitString((0, 1, '0', '1'))
        self.assertEqual('0b0111', a)
        a.replace((True, True), [])
        self.assertEqual(a, (False, True))

    def testCut(self):
        a = BitString('0x00112233445')
        b = list(a.cut(8))
        self.assertEqual(b, ['0x00', '0x11', '0x22', '0x33', '0x44'])
        b = list(a.cut(4, 8, 16))
        self.assertEqual(b, ['0x1', '0x1'])
        b = list(a.cut(4, 0, 44, 4))
        self.assertEqual(b, ['0x0', '0x0', '0x1', '0x1'])
        a = BitString()
        b = list(a.cut(10))
        self.assertTrue(not b)

    def testCutErrors(self):
        a = BitString('0b1')
        b = a.cut(1, 1, 2)
        self.assertRaises(ValueError, next, b)
        b = a.cut(1, -2, 1)
        self.assertRaises(ValueError, next, b)
        b = a.cut(0)
        self.assertRaises(ValueError, next, b)
        b = a.cut(1, count=-1)
        self.assertRaises(ValueError, next, b)

    def testCutProblem(self):
        s = BitString('0x1234')
        for n in list(s.cut(4)):
            s.prepend(n)
        self.assertEqual(s, '0x43211234')

    def testJoinFunctions(self):
        a = BitString().join(['0xa', '0xb', '0b1111'])
        self.assertEqual(a, '0xabf')
        a = BitString('0b1').join(['0b0' for i in range(10)])
        self.assertEqual(a, '0b0101010101010101010')
        a = BitString('0xff').join([])
        self.assertFalse(a)

    def testAddingBitpos(self):
        a = BitString('0xff')
        b = BitString('0x00')
        a.bitpos = b.bitpos = 8
        c = a + b
        self.assertEqual(c.bitpos, 0)



    def testIntelligentRead1(self):
        a = BitString(uint=123, length=23)
        u = a.read('uint:23')
        self.assertEqual(u, 123)
        self.assertEqual(a.pos, a.len)
        b = BitString(int=-12, length=44)
        i = b.read('int:44')
        self.assertEqual(i, -12)
        self.assertEqual(b.pos, b.len)
        u2, i2 = (a+b).readlist('uint:23, int:44')
        self.assertEqual((u2, i2), (123, -12))

    def testIntelligentRead2(self):
        a = BitString(ue=822)
        u = a.read('ue')
        self.assertEqual(u, 822)
        self.assertEqual(a.pos, a.len)
        b = BitString(se=-1001)
        s = b.read('se')
        self.assertEqual(s, -1001)
        self.assertEqual(b.pos, b.len)
        s, u1, u2 = (b+2*a).readlist('se, ue, ue')
        self.assertEqual((s, u1, u2), (-1001, 822, 822))

    def testIntelligentRead3(self):
        a = BitString('0x123') + '0b11101'
        h = a.read('hex:12')
        self.assertEqual(h, '0x123')
        b = a.read('bin: 5')
        self.assertEqual(b, '0b11101')
        c = b + a
        b, h = c.readlist('bin:5, hex:12')
        self.assertEqual((b, h), ('0b11101', '0x123'))

    def testIntelligentRead4(self):
        a = BitString('0o007')
        o = a.read('oct:9')
        self.assertEqual(o, '0o007')
        self.assertEqual(a.pos, a.len)

    def testIntelligentRead5(self):
        a = BitString('0x00112233')
        c0, c1, c2 = a.readlist('bits:8, bits:8, bits:16')
        self.assertEqual((c0, c1, c2), (BitString('0x00'), BitString('0x11'), BitString('0x2233')))
        a.pos = 0
        c = a.read('bits:16')
        self.assertEqual(c, BitString('0x0011'))

    def testIntelligentRead6(self):
        a = BitString('0b000111000')
        b1, b2, b3 = a.readlist('bin :3, int: 3, int:3')
        self.assertEqual(b1, '0b000')
        self.assertEqual(b2, -1)
        self.assertEqual(b3, 0)

    def testIntelligentRead7(self):
        a = BitString('0x1234')
        a1, a2, a3, a4 = a.readlist('bin:0, oct:0, hex:0, bits:0')
        self.assertTrue(a1 == a2 == a3 == '')
        self.assertFalse(a4)
        self.assertRaises(ValueError, a.read, 'int:0')
        self.assertRaises(ValueError, a.read, 'uint:0')
        self.assertEqual(a.pos, 0)

    def testIntelligentRead8(self):
        a = BitString('0x123456')
        for t in ['hex:1', 'oct:1', 'hex4', '-5', 'fred', 'bin:-2',
                  'uint:p', 'uint:-2', 'int:u', 'int:-3', 'ses', 'uee', '-14']:
            self.assertRaises(ValueError, a.read, t)

    def testIntelligentRead9(self):
        a = BitString('0xff')
        self.assertEqual(a.read('intle'), -1)

    def testFillerReads1(self):
        s = BitString('0x012345')
        t = s.read('bits')
        self.assertEqual(s, t)
        s.pos = 0
        a, b = s.readlist('hex:8, hex')
        self.assertEqual(a, '0x01')
        self.assertEqual(b, '0x2345')
        self.assertTrue(isinstance(b, str))
        s.bytepos = 0
        a, b = s.readlist('bin, hex:20')
        self.assertEqual(a, '0b0000')
        self.assertEqual(b, '0x12345')
        self.assertTrue(isinstance(a, str))

    def testFillerReads2(self):
        s = BitString('0xabcdef')
        self.assertRaises(BitStringError, s.readlist, 'bits, se')
        self.assertRaises(BitStringError, s.readlist, 'hex:4, bits, ue, bin:4')

    def testIntelligentPeek(self):
        a = BitString('0b01, 0x43, 0o4, uint:23=2, se=5, ue=3')
        b, c, e = a.peeklist('bin:2, hex:8, oct:3')
        self.assertEquals((b, c, e), ('0b01', '0x43', '0o4'))
        self.assertEqual(a.pos, 0)
        a.pos = 13
        f, g, h = a.peeklist('uint:23, se, ue')
        self.assertEqual((f, g, h), (2, 5, 3))
        self.assertEqual(a.pos, 13)

    def testReadMultipleBits(self):
        s = BitString('0x123456789abcdef')
        a, b = s.readbitlist(4, 4)
        self.assertEqual(a, '0x1')
        self.assertEqual(b, '0x2')
        c, d, e = s.readbytelist(1, 2, 1)
        self.assertEqual(c, '0x34')
        self.assertEqual(d, '0x5678')
        self.assertEqual(e, '0x9a')

    def testPeekMultipleBits(self):
        s = BitString('0b1101, 0o721, 0x2234567')
        a, b, c, d = s.peekbitlist(2, 1, 1, 9)
        self.assertEqual(a, '0b11')
        self.assertEqual(b, '0b0')
        self.assertEqual(c, '0b1')
        self.assertEqual(d, '0o721')
        self.assertEqual(s.pos, 0)
        a, b = s.peekbitlist(4, 9)
        self.assertEqual(a, '0b1101')
        self.assertEqual(b, '0o721')
        s.pos = 13
        a, b = s.peekbytelist(2, 1)
        self.assertEqual(a, '0x2234')
        self.assertEqual(b, '0x56')
        self.assertEqual(s.pos, 13)

    def testDifficultPrepends(self):
        a = BitString('0b1101011')
        b = BitString()
        for i in range(10):
            b.prepend(a)
        self.assertEqual(b, a*10)



    def testPackingWrongNumberOfThings(self):
        self.assertRaises(ValueError, pack, 'bin:1')
        self.assertRaises(ValueError, pack, '', 100)

    def testPackWithVariousKeys(self):
        a = pack('uint10', uint10='0b1')
        self.assertEqual(a, '0b1')
        b = pack('0b110', **{'0b110' : '0xfff'})
        self.assertEqual(b, '0xfff')

    def testPackWithVariableLength(self):
        for i in range(1, 11):
            a = pack('uint:n', 0, n=i)
            self.assertEqual(a.bin, '0b'+'0'*i)

    def testToBytes(self):
        a = BitString(bytes=b'\xab\x00')
        b = a.tobytes()
        self.assertEqual(a.bytes, b)
        for i in range(7):
            del a[-1:]
            self.assertEqual(a.tobytes(), b'\xab\x00')
        del a[-1:]
        self.assertEqual(a.tobytes(), b'\xab')

    def testToFile(self):
        a = BitString('0x0000ff', length=17)
        f = open('temp_bitstring_unit_testing_file', 'wb')
        a.tofile(f)
        f.close()
        b = BitString(filename='temp_bitstring_unit_testing_file')
        self.assertEqual(b, '0x000080')

        a = BitString('0x911111')
        del a[:1]
        self.assertEqual(a+'0b0', '0x222222')
        f = open('temp_bitstring_unit_testing_file', 'wb')
        a.tofile(f)
        f.close()
        b = BitString(filename='temp_bitstring_unit_testing_file')
        self.assertEqual(b, '0x222222')
        os.remove('temp_bitstring_unit_testing_file')

    def testToFileWithLargerFile(self):
        a = BitString(length=16000000)
        a[1] = '0b1'
        a[-2] = '0b1'
        f = open('temp_bitstring_unit_testing_file' ,'wb')
        a.tofile(f)
        f.close()
        b = BitString(filename='temp_bitstring_unit_testing_file')
        self.assertEqual(b.len, 16000000)
        self.assertEqual(b[1], '0b1')

        # This is needed for complete code coverage, but takes ages at the moment!
        #f = open('temp_bitstring_unit_testing_file' ,'wb')
        #a[1:].tofile(f)
        #f.close()
        #b = BitString(filename='temp_bitstring_unit_testing_file')
        #self.assertEqual(b.len, 16000000)
        #self.assertEqual(b[0], '0b1')
        #os.remove('temp_bitstring_unit_testing_file')

    def testTokenParser(self):
        tp = bitstring.tokenparser
        self.assertEqual(tp('hex'), (True, [('hex', None, None)]))
        self.assertEqual(tp('hex=14'), (True, [('hex', None, '14')]))
        self.assertEqual(tp('se'), (False, [('se', None, None)]))
        self.assertEqual(tp('ue=12'), (False, [('ue', None, '12')]))
        self.assertEqual(tp('0xef'), (False, [('0x', None, 'ef')]))
        self.assertEqual(tp('uint:12'), (False, [('uint', 12, None)]))
        self.assertEqual(tp('int:30=-1'), (False, [('int', 30, '-1')]))
        self.assertEqual(tp('bits:10'), (False, [('bits', 10, None)]))
        self.assertEqual(tp('bits:10'), (False, [('bits', 10, None)]))
        self.assertEqual(tp('123'), (False, [('uint', 123, None)]))
        self.assertEqual(tp('123'), (False, [('uint', 123, None)]))
        self.assertRaises(ValueError, tp, 'hex12')
        self.assertEqual(tp('hex12', ('hex12',)), (False, [('hex12', None, None)]))

        self.assertEqual(tp('2*bits:6'), (False, [('bits', 6, None), ('bits', 6, None)]))

    def testAutoFromFileObject(self):
        f = open('test.m1v', 'rb')
        s = BitString(f, offset=32, length=12)
        self.assertEqual(s.uint, 352)
        t = BitString('0xf') + f
        self.assertTrue(t.startswith('0xf000001b3160'))
        u = BitString(bytes=open('test.m1v', 'rb').read())
        self.assertEqual(u, f)
        f.close()

    def testFileBasedCopy(self):
        f = open('smalltestfile', 'rb')
        s = BitString(f)
        t = BitString(s)
        s.prepend('0b1')
        self.assertEqual(s[1:], t)
        s = BitString(f)
        t = copy.copy(s)
        t.append('0b1')
        self.assertEqual(s, t[:-1])

    def testBigEndianSynonyms(self):
        s = BitString('0x12318276ef')
        self.assertEqual(s.int, s.intbe)
        self.assertEqual(s.uint, s.uintbe)
        s = BitString(intbe=-100, length=16)
        self.assertEqual(s, 'int:16=-100')
        s = BitString(uintbe=13, length=24)
        self.assertEqual(s, 'int:24=13')
        s = BitString('uintbe:32=1000')
        self.assertEqual(s, 'uint:32=1000')
        s = BitString('intbe:8=2')
        self.assertEqual(s, 'int:8=2')
        self.assertEqual(s.read('intbe'), 2)
        s.pos = 0
        self.assertEqual(s.read('uintbe'), 2)

    def testBigEndianSynonymErrors(self):
        self.assertRaises(ValueError, BitString, uintbe=100, length=15)
        self.assertRaises(ValueError, BitString, intbe=100, length=15)
        self.assertRaises(ValueError, BitString, 'uintbe:17=100')
        self.assertRaises(ValueError, BitString, 'intbe:7=2')
        s = BitString('0b1')
        self.assertRaises(ValueError, s._getintbe)
        self.assertRaises(ValueError, s._getuintbe)
        self.assertRaises(ValueError, s.read, 'uintbe')
        self.assertRaises(ValueError, s.read, 'intbe')

    def testLittleEndianUint(self):
        s = BitString(uint=100, length=16)
        self.assertEqual(s.uintle, 25600)
        s = BitString(uintle=100, length=16)
        self.assertEqual(s.uint, 25600)
        self.assertEqual(s.uintle, 100)
        s.uintle += 5
        self.assertEqual(s.uintle, 105)
        s = BitString('uintle:32=999')
        self.assertEqual(s.uintle, 999)
        self.assertEqual(s[::-8].uint, 999)
        s = pack('uintle:24', 1001)
        self.assertEqual(s.uintle, 1001)
        self.assertEqual(s.length, 24)
        self.assertEqual(s.read('uintle'), 1001)

    def testLittleEndianInt(self):
        s = BitString(int=100, length=16)
        self.assertEqual(s.intle, 25600)
        s = BitString(intle=100, length=16)
        self.assertEqual(s.int, 25600)
        self.assertEqual(s.intle, 100)
        s.intle += 5
        self.assertEqual(s.intle, 105)
        s = BitString('intle:32=999')
        self.assertEqual(s.intle, 999)
        self.assertEqual(s[::-8].int, 999)
        s = pack('intle:24', 1001)
        self.assertEqual(s.intle, 1001)
        self.assertEqual(s.length, 24)
        self.assertEqual(s.read('intle'), 1001)

    def testLittleEndianErrors(self):
        self.assertRaises(ValueError, BitString, 'uintle:15=10')
        self.assertRaises(ValueError, BitString, 'intle:31=-999')
        self.assertRaises(ValueError, BitString, uintle=100, length=15)
        self.assertRaises(ValueError, BitString, intle=100, length=15)
        s = BitString('0xfff')
        self.assertRaises(ValueError, s._getintle)
        self.assertRaises(ValueError, s._getuintle)
        self.assertRaises(ValueError, s.read, 'uintle')
        self.assertRaises(ValueError, s.read, 'intle')

    def testStructTokens1(self):
        self.assertEqual(pack('<b', 23), BitString('intle:8=23'))
        self.assertEqual(pack('<B', 23), BitString('uintle:8=23'))
        self.assertEqual(pack('<h', 23), BitString('intle:16=23'))
        self.assertEqual(pack('<H', 23), BitString('uintle:16=23'))
        self.assertEqual(pack('<l', 23), BitString('intle:32=23'))
        self.assertEqual(pack('<L', 23), BitString('uintle:32=23'))
        self.assertEqual(pack('<q', 23), BitString('intle:64=23'))
        self.assertEqual(pack('<Q', 23), BitString('uintle:64=23'))
        self.assertEqual(pack('>b', 23), BitString('intbe:8=23'))
        self.assertEqual(pack('>B', 23), BitString('uintbe:8=23'))
        self.assertEqual(pack('>h', 23), BitString('intbe:16=23'))
        self.assertEqual(pack('>H', 23), BitString('uintbe:16=23'))
        self.assertEqual(pack('>l', 23), BitString('intbe:32=23'))
        self.assertEqual(pack('>L', 23), BitString('uintbe:32=23'))
        self.assertEqual(pack('>q', 23), BitString('intbe:64=23'))
        self.assertEqual(pack('>Q', 23), BitString('uintbe:64=23'))
        self.assertRaises(ValueError, pack, '<B', -1)
        self.assertRaises(ValueError, pack, '<H', -1)
        self.assertRaises(ValueError, pack, '<L', -1)
        self.assertRaises(ValueError, pack, '<Q', -1)

    def testStructTokens2(self):
        endianness = sys.byteorder
        sys.byteorder = 'little'
        self.assertEqual(pack('@b', 23), BitString('intle:8=23'))
        self.assertEqual(pack('@B', 23), BitString('uintle:8=23'))
        self.assertEqual(pack('@h', 23), BitString('intle:16=23'))
        self.assertEqual(pack('@H', 23), BitString('uintle:16=23'))
        self.assertEqual(pack('@l', 23), BitString('intle:32=23'))
        self.assertEqual(pack('@L', 23), BitString('uintle:32=23'))
        self.assertEqual(pack('@q', 23), BitString('intle:64=23'))
        self.assertEqual(pack('@Q', 23), BitString('uintle:64=23'))
        sys.byteorder = 'big'
        self.assertEqual(pack('@b', 23), BitString('intbe:8=23'))
        self.assertEqual(pack('@B', 23), BitString('uintbe:8=23'))
        self.assertEqual(pack('@h', 23), BitString('intbe:16=23'))
        self.assertEqual(pack('@H', 23), BitString('uintbe:16=23'))
        self.assertEqual(pack('@l', 23), BitString('intbe:32=23'))
        self.assertEqual(pack('@L', 23), BitString('uintbe:32=23'))
        self.assertEqual(pack('@q', 23), BitString('intbe:64=23'))
        self.assertEqual(pack('@Q', 23), BitString('uintbe:64=23'))
        sys.byteorder = endianness

    def testNativeEndianness(self):
        s = pack('@2L', 40, 40)
        if sys.byteorder == 'little':
            self.assertEqual(s, pack('<2L', 40, 40))
        else:
            self.assertEqual(sys.byteorder, 'big')
            self.assertEqual(s, pack('>2L', 40, 40))

    def testStructTokens2(self):
        s = pack('>hhl', 1, 2, 3)
        a, b, c = s.unpack('>hhl')
        self.assertEqual((a, b, c), (1, 2, 3))
        s = pack('<QL, >Q \tL', 1001, 43, 21, 9999)
        self.assertEqual(s.unpack('<QL, >QL'), [1001, 43, 21, 9999])

    def testStructTokensMultiplicativeFactors(self):
        s = pack('<2h', 1, 2)
        a, b = s.unpack('<2h')
        self.assertEqual((a, b), (1, 2))
        s = pack('<100q', *range(100))
        self.assertEqual(s.len, 100*64)
        self.assertEqual(s[44:45:64].uintle, 44)
        s = pack('@L0B2h', 5, 5, 5)
        self.assertEqual(s.unpack('@Lhh'), [5, 5, 5])

    def testStructTokensErrors(self):
        for f in ['>>q', '<>q', 'q>', '2q', 'q', '>-2q', '@a', '>int:8', '>q2']:
            self.assertRaises(ValueError, pack, f, 100)

    def testImmutableBitStrings(self):
        a = Bits('0x012345')
        self.assertEqual(a, '0x012345')
        b = BitString('0xf') + a
        self.assertEqual(b, '0xf012345')
        try:
            a.append(b)
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.prepend(b)
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a[0] = '0b1'
            self.assertTrue(False)
        except TypeError:
            pass
        try:
            del a[5]
            self.assertTrue(False)
        except TypeError:
            pass
        try:
            a.replace('0b1', '0b0')
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.insert('0b11', 4)
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.reverse()
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.reversebytes()
            self.assertTrue(False)
        except AttributeError:
            pass
        self.assertEqual(a, '0x012345')
        self.assertTrue(isinstance(a, Bits))

    def testReverseBytes(self):
        a = BitString('0x123456')
        a.reversebytes()
        self.assertEqual(a, '0x563412')
        self.assertRaises(BitStringError, (a + '0b1').reversebytes)
        a = BitString('0x54')
        a.reversebytes()
        self.assertEqual(a, '0x54')
        a = BitString()
        a.reversebytes()
        self.assertFalse(a)

    def testReverseBytes2(self):
        a = BitString()
        a.reversebytes()
        self.assertFalse(a)
        a = BitString('0x00112233')
        a.reversebytes(0, 16)
        self.assertEqual(a, '0x11002233')
        a.reversebytes(4, 28)
        self.assertEqual(a, '0x12302103')
        self.assertRaises(BitStringError, a.reversebytes, 0, 11)
        self.assertRaises(ValueError, a.reversebytes, 10, 2)
        self.assertRaises(ValueError, a.reversebytes, -4, 4)
        self.assertRaises(ValueError, a.reversebytes, 24, 48)
        a.reversebytes(24)
        self.assertEqual(a, '0x12302103')
        a.reversebytes(11, 11)
        self.assertEqual(a, '0x12302103')

    def testCapitalsInPack(self):
        a = pack('A', A='0b1')
        self.assertEqual(a, '0b1')
        format = 'bits:4=BL_OFFT, uint:12=width, uint:12=height'
        d = {'BL_OFFT': '0b1011', 'width': 352, 'height': 288}
        s = bitstring.pack(format, **d)
        self.assertEqual(s, '0b1011, uint:12=352, uint:12=288')
        a = pack('0X0, UinT:8, HeX', 45, '0XABcD')
        self.assertEqual(a, '0x0, UiNt:8=45, 0xabCD')

##    def testEfficientOverwrite(self):
##        a = BitString(length=1000000000)
##        a.overwrite('0b1', 123456)
##        self.assertEqual(a[123456], '0b1')
##        a.overwrite('0xff', 1)
##        self.assertEqual(a[0:4:8], '0x7f800000')
##        b = BitString('0xffff')
##        b.overwrite('0x0000')
##        self.assertEqual(b, '0x0000')
##        c = BitString(length=1000)
##        c.overwrite('0xaaaaaaaaaaaa', 81)
##        self.assertEqual(c[81:81+6*8], '0xaaaaaaaaaaaa')
##        self.assertEqual(len(list(c.findall('0b1'))), 24)
##        s = BitString(length=1000)
##        s = s[5:]
##        s.overwrite('0xffffff', 500)
##        s.pos = 500
##        self.assertEqual(s.readbytes(4), '0xffffff00')
##        s.overwrite('0xff', 502)
##        self.assertEqual(s[502:518], '0xffff')

    def testPeekAndReadListErrors(self):
        a = BitString('0x123456')
        self.assertRaises(ValueError, a.read, 'hex:8, hex:8')
        self.assertRaises(ValueError, a.peek, 'hex:8, hex:8')
        self.assertRaises(TypeError, a.readbits, 10, 12)
        self.assertRaises(TypeError, a.peekbits, 12, 14)
        self.assertRaises(TypeError, a.readbytes, 1, 1)
        self.assertRaises(TypeError, a.peekbytes, 10, 10)

    def testStartswith(self):
        a = BitString()
        self.assertTrue(a.startswith(BitString()))
        self.assertFalse(a.startswith('0b0'))
        a = BitString('0x12ff')
        self.assertTrue(a.startswith('0x1'))
        self.assertTrue(a.startswith('0b0001001'))
        self.assertTrue(a.startswith('0x12ff'))
        self.assertFalse(a.startswith('0x12ff, 0b1'))
        self.assertFalse(a.startswith('0x2'))

    def testStartswithStartEnd(self):
        s = BitString('0x123456')
        self.assertTrue(s.startswith('0x234', 4))
        self.assertFalse(s.startswith('0x123', end=11))
        self.assertTrue(s.startswith('0x123', end=12))
        self.assertTrue(s.startswith('0x34', 8, 16))
        self.assertFalse(s.startswith('0x34', 7, 16))
        self.assertFalse(s.startswith('0x34', 9, 16))
        self.assertFalse(s.startswith('0x34', 8, 15))

    def testEndswith(self):
        a = BitString()
        self.assertTrue(a.endswith(''))
        self.assertFalse(a.endswith(BitString('0b1')))
        a = BitString('0xf2341')
        self.assertTrue(a.endswith('0x41'))
        self.assertTrue(a.endswith('0b001'))
        self.assertTrue(a.endswith('0xf2341'))
        self.assertFalse(a.endswith('0x1f2341'))
        self.assertFalse(a.endswith('0o34'))

    def testEndswithStartEnd(self):
        s = BitString('0x123456')
        self.assertTrue(s.endswith('0x234', end=16))
        self.assertFalse(s.endswith('0x456', start=13))
        self.assertTrue(s.endswith('0x456', start=12))
        self.assertTrue(s.endswith('0x34', 8, 16))
        self.assertTrue(s.endswith('0x34', 7, 16))
        self.assertFalse(s.endswith('0x34', 9, 16))
        self.assertFalse(s.endswith('0x34', 8, 15))

    def testUnhashability(self):
        s = BitString('0xf')
        self.assertRaises(TypeError, set, s)
        self.assertRaises(TypeError, hash, s)

    def testConstBitStringSetCreation(self):
        sl = [Bits(uint=i, length=7) for i in range(15)]
        s = set(sl)
        self.assertEqual(len(s), 15)
        s.add(Bits('0b0000011'))
        self.assertEqual(len(s), 15)
        self.assertRaises(TypeError, s.add, BitString('0b0000011'))

    def testConstBitStringFunctions(self):
        s = Bits('0xf, 0b1')
        self.assertEqual(type(s), Bits)
        t = copy.copy(s)
        self.assertEqual(type(t), Bits)
        a = s + '0o3'
        self.assertEqual(type(a), Bits)
        b = a[0:4]
        self.assertEqual(type(b), Bits)
        b = a[4:3]
        self.assertEqual(type(b), Bits)
        b = a[5:2:-1]
        self.assertEqual(type(b), Bits)
        b = ~a
        self.assertEqual(type(b), Bits)
        b = a << 2
        self.assertEqual(type(b), Bits)
        b = a >> 2
        self.assertEqual(type(b), Bits)
        b = a*2
        self.assertEqual(type(b), Bits)
        b = a*0
        self.assertEqual(type(b), Bits)
        b = a & ~a
        self.assertEqual(type(b), Bits)
        b = a | ~a
        self.assertEqual(type(b), Bits)
        b = a ^ ~a
        self.assertEqual(type(b), Bits)
        b = a._slice(4, 4)
        self.assertEqual(type(b), Bits)
        b = a.readbits(4)
        self.assertEqual(type(b), Bits)

    def testConstBitStringProperties(self):
        a = Bits('0x123123')
        try:
            a.hex = '0x234'
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.oct = '0o234'
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.bin = '0b101'
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.ue = 3453
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.se = -123
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.int = 432
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.uint = 4412
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.intle = 123
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.uintle = 4412
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.intbe = 123
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.uintbe = 4412
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.intne = 123
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.uintne = 4412
            self.assertTrue(False)
        except AttributeError:
            pass
        try:
            a.bytes = 'hello'
            self.assertTrue(False)
        except AttributeError:
            pass

    def testConstBitStringMisc(self):
        a = Bits('0xf')
        b = a
        a += '0xe'
        self.assertEqual(b, '0xf')
        self.assertEqual(a, '0xfe')
        c = BitString(a)
        self.assertEqual(a, c)
        a = Bits('0b1')
        a._append(a)
        self.assertEqual(a, '0b11')
        self.assertEqual(type(a), Bits)
        a._prepend(a)
        self.assertEqual(a, '0b1111')
        self.assertEqual(type(a), Bits)

    def testConstBitStringHashibility(self):
        a = Bits('0x1')
        b = Bits('0x2')
        c = Bits('0x1')
        c.pos = 3
        s = set((a, b, c))
        self.assertEqual(len(s), 2)
        self.assertEqual(hash(a), hash(c))

    def testConstBitStringCopy(self):
        a = Bits('0xabc')
        a.pos = 11
        b = copy.copy(a)
        b.pos = 4
        self.assertEqual(id(a._datastore), id(b._datastore))
        self.assertEqual(a.pos, 11)
        self.assertEqual(b.pos, 4)

    def testPython26stuff(self):
        s = BitString('0xff')
        self.assertTrue(isinstance(s.tobytes(), bytes))
        self.assertTrue(isinstance(s.bytes, bytes))

    def testPython3stuff(self):
        if bitstring.PYTHON_VERSION == 3:
            pass

    def testReadFromBits(self):
        a = Bits('0xaabbccdd')
        b = a.readbits(8)
        self.assertEqual(b, '0xaa')
        self.assertEqual(a[0:8], '0xaa')
        self.assertEqual(a[-1], '0b1')
        a.pos = 0
        self.assertEqual(a.readbits(4).uint, 10)

    def testSet(self):
        a = BitString(length=16)
        a.set(0)
        self.assertEqual(a, '0b10000000 00000000')
        a.set(15)
        self.assertEqual(a, '0b10000000 00000001')
        b = a[4:12]
        b.set(1)
        self.assertEqual(b, '0b01000000')
        b.set(-1)
        self.assertEqual(b, '0b01000001')
        b.set(-8)
        self.assertEqual(b, '0b11000001')
        self.assertRaises(IndexError, b.set, -9)
        self.assertRaises(IndexError, b.set, 8)

    def testFileBasedSetUnset(self):
        a = BitString(filename='test.m1v')
        a.set((0, 1, 2, 3, 4))
        self.assertEqual(a[0:4:8], '0xf80001b3')
        a = BitString(filename='test.m1v')
        a.unset((28, 29, 30, 31))
        self.assertTrue(a.startswith('0x000001b0'))

    def testSetList(self):
        a = BitString(length=18)
        a.set(range(18))
        self.assertEqual(a.int, -1)
        a.unset(range(18))
        self.assertEqual(a.int, 0)

    def testUnset(self):
        a = BitString(length=16, int=-1)
        a.unset(0)
        self.assertEqual(~a, '0b10000000 00000000')
        a.unset(15)
        self.assertEqual(~a, '0b10000000 00000001')
        b = a[4:12]
        b.unset(1)
        self.assertEqual(~b, '0b01000000')
        b.unset(-1)
        self.assertEqual(~b, '0b01000001')
        b.unset(-8)
        self.assertEqual(~b, '0b11000001')
        self.assertRaises(IndexError, b.unset, -9)
        self.assertRaises(IndexError, b.unset, 8)

    def testInvertBits(self):
        a = BitString('0b111000')
        a.invert(range(a.len))
        self.assertEqual(a, '0b000111')

    def testIor(self):
        a = BitString('0b1101001')
        a |= '0b1110000'
        self.assertEqual(a, '0b1111001')
        b = a[2:]
        c = a[1:-1]
        b |= c
        self.assertEqual(c, '0b11100')
        self.assertEqual(b, '0b11101')

    def testIand(self):
        a = BitString('0b0101010101000')
        a &= '0b1111110000000'
        self.assertEqual(a, '0b0101010000000')
        s = BitString(filename='test.m1v', offset=26, length=24)
        s &= '0xff00ff'
        self.assertEqual(s, '0xcc0004')

    def testIxor(self):
        a = BitString('0b11001100110011')
        a ^= '0b11111100000010'
        self.assertEqual(a, '0b00110000110001')

    def testAllSet(self):
        a = BitString('0b0111')
        self.assertTrue(a.allset((1, 3)))
        self.assertFalse(a.allset((0, 1, 2)))

    def testFileBasedAllSetUnset(self):
        a = BitString(filename='test.m1v')
        self.assertTrue(a.allset(31))
        a = BitString(filename='test.m1v')
        self.assertTrue(a.allunset((0, 1, 2, 3, 4)))

    def testFileBasedAnySetUnset(self):
        a = BitString(filename='test.m1v')
        self.assertTrue(a.anyset((31, 12)))
        a = BitString(filename='test.m1v')
        self.assertTrue(a.anyunset((0, 1, 2, 3, 4)))

    def testAnySet(self):
        a = BitString('0b10011011')
        self.assertTrue(a.anyset((1, 2, 3, 5)))
        self.assertFalse(a.anyset((1, 2, 5)))

    def testAllUnset(self):
        a = BitString('0b0010011101')
        self.assertTrue(a.allunset((0, 1, 3, 4)))
        self.assertFalse(a.allunset((0, 1, 2, 3, 4)))

    def testAnyUnset(self):
        a = BitString('0b01001110110111111111111111111')
        self.assertTrue(a.anyunset((4, 5, 6, 2)))
        self.assertFalse(a.anyunset((1, 15, 20)))

    def testFloatInitialisation(self):
        for f in (0.0000001, -1.0, 1.0, 0.2, -3.1415265, 1.331e32):
            a = BitString(float=f, length=64)
            a.pos = 6
            self.assertEqual(a.float, f)
            a = BitString('float:64=%s' % str(f))
            a.pos = 6
            self.assertEqual(a.float, f)
            a = BitString('floatbe:64=%s' % str(f))
            a.pos = 6
            self.assertEqual(a.floatbe, f)
            a = BitString('floatle:64=%s' % str(f))
            a.pos = 6
            self.assertEqual(a.floatle, f)
            a = BitString('floatne:64=%s' % str(f))
            a.pos = 6
            self.assertEqual(a.floatne, f)
            b = BitString(float=f, length=32)
            b.pos = 6
            self.assertAlmostEqual(b.float/f, 1.0)
            b = BitString('float:32=%s' % str(f))
            b.pos = 6
            self.assertAlmostEqual(b.float/f, 1.0)
            b = BitString('floatbe:32=%s' % str(f))
            b.pos = 6
            self.assertAlmostEqual(b.floatbe/f, 1.0)
            b = BitString('floatle:32=%s' % str(f))
            b.pos = 6
            self.assertAlmostEqual(b.floatle/f, 1.0)
            b = BitString('floatne:32=%s' % str(f))
            b.pos = 6
            self.assertAlmostEqual(b.floatne/f, 1.0)
        a = BitString('0x12345678')
        a.pos = 6
        a.float = 23
        self.assertEqual(a.float, 23.0)

    def testFloatInitStrings(self):
        for s in ('5', '+0.0001', '-1e101', '4.', '.2', '-.65', '43.21E+32'):
            a = BitString('float:64=%s' % s)
            self.assertEqual(a.float, float(s))

    def testFloatPacking(self):
        a = pack('>d', 0.01)
        self.assertEqual(a.float, 0.01)
        self.assertEqual(a.floatbe, 0.01)
        self.assertEqual(a[::-8].floatle, 0.01)
        b = pack('>f', 1e10)
        self.assertAlmostEqual(b.float/1e10, 1.0)
        c = pack('<f', 10.3)
        self.assertAlmostEqual(c.floatle/10.3, 1.0)
        d = pack('>5d', 10.0, 5.0, 2.5, 1.25, 0.1)
        self.assertEqual(d.unpack('>5d'), [10.0, 5.0, 2.5, 1.25, 0.1])

    def testFloatReading(self):
        a = BitString('floatle:64=12, floatbe:64=-0.01, floatne:64=3e33')
        x, y, z = a.readlist('floatle:64, floatbe:64, floatne:64')
        self.assertEqual(x, 12.0)
        self.assertEqual(y, -0.01)
        self.assertEqual(z, 3e33)
        a = BitString('floatle:32=12, floatbe:32=-0.01, floatne:32=3e33')
        x, y, z = a.readlist('floatle:32, floatbe:32, floatne:32')
        self.assertAlmostEqual(x/12.0, 1.0)
        self.assertAlmostEqual(y/-0.01, 1.0)
        self.assertAlmostEqual(z/3e33, 1.0)
        a = BitString('0b11, floatle:64=12, 0xfffff')
        a.pos = 2
        self.assertEqual(a.read('floatle:64'), 12.0)

    def testFloatErrors(self):
        a = BitString('0x3')
        self.assertRaises(ValueError, a._getfloat)
        self.assertRaises(ValueError, a._setfloat, -0.2)
        for l in (8, 10, 12, 16, 30, 128, 200):
            self.assertRaises(ValueError, BitString, float=1.0, length=l)

    def testReadErrorChangesPos(self):
        a = BitString('0x123123')
        try:
            a.read('10, 5')
        except ValueError:
            pass
        self.assertEqual(a.pos, 0)

    def testRor(self):
        a = BitString('0b11001')
        a.ror(0)
        self.assertEqual(a, '0b11001')
        a.ror(1)
        self.assertEqual(a, '0b11100')
        a.ror(5)
        self.assertEqual(a, '0b11100')
        a.ror(101)
        self.assertEqual(a, '0b01110')
        a = BitString('0b1')
        a.ror(1000000)
        self.assertEqual(a, '0b1')

    def testRorErrors(self):
        a = BitString()
        self.assertRaises(BitStringError, a.ror, 0)
        a += '0b001'
        self.assertRaises(ValueError, a.ror, -1)

    def testRol(self):
        a = BitString('0b11001')
        a.rol(0)
        self.assertEqual(a, '0b11001')
        a.rol(1)
        self.assertEqual(a, '0b10011')
        a.rol(5)
        self.assertEqual(a, '0b10011')
        a.rol(101)
        self.assertEqual(a, '0b00111')
        a = BitString('0b1')
        a.rol(1000000)
        self.assertEqual(a, '0b1')

    def testRolFromFile(self):
        a = BitString(filename='test.m1v')
        l = a.len
        a.rol(1)
        self.assertTrue(a.startswith('0x000003'))
        self.assertEqual(a.len, l)
        self.assertTrue(a.endswith('0x0036e'))

    def testRorFromFile(self):
        a = BitString(filename='test.m1v')
        l = a.len
        a.ror(1)
        self.assertTrue(a.startswith('0x800000'))
        self.assertEqual(a.len, l)
        self.assertTrue(a.endswith('0x000db'))

    def testRolErrors(self):
        a = BitString()
        self.assertRaises(BitStringError, a.rol, 0)
        a += '0b001'
        self.assertRaises(ValueError, a.rol, -1)

    def testBytesToken(self):
        a = BitString('0x010203')
        b = a.read('bytes:1')
        self.assertTrue(isinstance(b, bytes))
        self.assertEqual(b, b'\x01')
        x, y, z = a.unpack('4, bytes:2, uint')
        self.assertEqual(x, 0)
        self.assertEqual(y, b'\x10\x20')
        self.assertEqual(z, 3)
        s = pack('bytes:4', b'abcd')
        self.assertEqual(s.bytes, b'abcd')

    def testDedicatedReadFunctions(self):
        a = BitString('0b11, uint:43=98798798172, 0b11111')
        x = a._readuint(43, 2)
        self.assertEqual(x, 98798798172)
        self.assertEqual(a.pos, 0)
        x = a._readint(43, 2)
        self.assertEqual(x, 98798798172)
        self.assertEqual(a.pos, 0)

        a = BitString('0b11, uintbe:48=98798798172, 0b11111')
        x = a._readuintbe(48, 2)
        self.assertEqual(x, 98798798172)
        self.assertEqual(a.pos, 0)
        x = a._readintbe(48, 2)
        self.assertEqual(x, 98798798172)
        self.assertEqual(a.pos, 0)

        a = BitString('0b111, uintle:40=123516, 0b111')
        self.assertEqual(a._readuintle(40, 3), 123516)
        b = BitString('0xff, uintle:800=999, 0xffff')
        self.assertEqual(b._readuintle(800, 8), 999)

        a = BitString('0b111, intle:48=999999999, 0b111111111111')
        self.assertEqual(a._readintle(48, 3), 999999999)
        b = BitString('0xff, intle:200=918019283740918263512351235, 0xfffffff')
        self.assertEqual(b._readintle(200, 8), 918019283740918263512351235)

        a = BitString('0b111, floatbe:64=-5.32, 0xffffffff')
        self.assertEqual(a._readfloat(64, 3), -5.32)

        a = BitString('0b111, floatle:64=9.9998, 0b111')
        self.assertEqual(a._readfloatle(64, 3), 9.9998)

    def testAutoInitWithInt(self):
        a = BitString(0)
        self.assertFalse(a)
        a = BitString(1)
        self.assertEqual(a, '0b0')
        a = BitString(1007)
        self.assertEqual(a, BitString(length=1007))
        self.assertRaises(ValueError, BitString, -1)

        a = 6 + Bits('0b1') + 3
        self.assertEqual(a, '0b0000001000')
        a += 1
        self.assertEqual(a, '0b00000010000')
        self.assertEqual(Bits(13), 13)

    def testReadingProblems(self):
        a = BitString('0x000001')
        b = a.read('uint:32')
        self.assertEqual(b, 1)
        a.pos = 0
        b = a.read('bytes:4')
        self.assertEqual(b, b'\x00\x00\x01')
        a.pos = 0
        b = a.read('bits:32')
        self.assertEqual(b, '0x000001')

    def testAddVersesInPlaceAdd(self):
        a1 = Bits('0xabc')
        b1 = a1
        a1 += '0xdef'
        self.assertEqual(a1, '0xabcdef')
        self.assertEqual(b1, '0xabc')

        a2 = BitString('0xabc')
        b2 = a2
        c2 = a2 + '0x0'
        a2 += '0xdef'
        self.assertEqual(a2, '0xabcdef')
        self.assertEqual(b2, '0xabcdef')
        self.assertEqual(c2, '0xabc0')

    def testAndVersesInPlaceAnd(self):
        a1 = Bits('0xabc')
        b1 = a1
        a1 &= '0xf0f'
        self.assertEqual(a1, '0xa0c')
        self.assertEqual(b1, '0xabc')

        a2 = BitString('0xabc')
        b2 = a2
        c2 = a2 & '0x00f'
        a2 &= '0xf0f'
        self.assertEqual(a2, '0xa0c')
        self.assertEqual(b2, '0xa0c')
        self.assertEqual(c2, '0x00c')

    def testOrVersesInPlaceOr(self):
        a1 = Bits('0xabc')
        b1 = a1
        a1 |= '0xf0f'
        self.assertEqual(a1, '0xfbf')
        self.assertEqual(b1, '0xabc')

        a2 = BitString('0xabc')
        b2 = a2
        c2 = a2 | '0x00f'
        a2 |= '0xf0f'
        self.assertEqual(a2, '0xfbf')
        self.assertEqual(b2, '0xfbf')
        self.assertEqual(c2, '0xabf')

    def testXorVersesInPlaceXor(self):
        a1 = Bits('0xabc')
        b1 = a1
        a1 ^= '0xf0f'
        self.assertEqual(a1, '0x5b3')
        self.assertEqual(b1, '0xabc')

        a2 = BitString('0xabc')
        b2 = a2
        c2 = a2 ^ '0x00f'
        a2 ^= '0xf0f'
        self.assertEqual(a2, '0x5b3')
        self.assertEqual(b2, '0x5b3')
        self.assertEqual(c2, '0xab3')

    def testMulVersesInPlaceMul(self):
        a1 = Bits('0xabc')
        b1 = a1
        a1 *= 3
        self.assertEqual(a1, '0xabcabcabc')
        self.assertEqual(b1, '0xabc')

        a2 = BitString('0xabc')
        b2 = a2
        c2 = a2 * 2
        a2 *= 3
        self.assertEqual(a2, '0xabcabcabc')
        self.assertEqual(b2, '0xabcabcabc')
        self.assertEqual(c2, '0xabcabc')

    def testLshiftVersesInPlaceLshift(self):
        a1 = Bits('0xabc')
        b1 = a1
        a1 <<= 4
        self.assertEqual(a1, '0xbc0')
        self.assertEqual(b1, '0xabc')

        a2 = BitString('0xabc')
        b2 = a2
        c2 = a2 << 8
        a2 <<= 4
        self.assertEqual(a2, '0xbc0')
        self.assertEqual(b2, '0xbc0')
        self.assertEqual(c2, '0xc00')

    def testRshiftVersesInPlaceRshift(self):
        a1 = Bits('0xabc')
        b1 = a1
        a1 >>= 4
        self.assertEqual(a1, '0x0ab')
        self.assertEqual(b1, '0xabc')

        a2 = BitString('0xabc')
        b2 = a2
        c2 = a2 >> 8
        a2 >>= 4
        self.assertEqual(a2, '0x0ab')
        self.assertEqual(b2, '0x0ab')
        self.assertEqual(c2, '0x00a')

    def testAutoFromBool(self):
        a = Bits() + True + False + True
        self.assertEqual(a, '0b101')
        b = Bits(False)
        self.assertEqual(b, '0b0')
        c = Bits(True)
        self.assertEqual(c, '0b1')
        self.assertEqual(b, False)
        self.assertEqual(c, True)
        self.assertEqual(b & True, False)

    def testTruncateStartBug(self):
        a = BitString('0b000000111', offset=2)
        a._truncatestart(6)
        self.assertEqual(a, '0b1')

    def testBugInReplace(self):
        s = BitString('0x00112233')
        l = list(s.split('0x22', start=8, bytealigned=True))
        self.assertEqual(l, ['0x11', '0x2233'])
        s = BitString('0x00112233')
        s.replace('0x22', '0xffff', start=8, bytealigned=True)
        self.assertEqual(s, '0x0011ffff33')
        s = BitString('0x0123412341234')
        s.replace('0x23', '0xf', start=9, bytealigned=True)
        self.assertEqual(s, '0x012341f41f4')

    def testMultiplicativeFactorsCreation(self):
        s = BitString('1*0b1')
        self.assertEqual(s, '0b1')
        s = BitString('4*0xc')
        self.assertEqual(s, '0xcccc')
        s = BitString('0b1, 0*0b0')
        self.assertEqual(s, '0b1')
        s = BitString('0b1, 3*uint:8=34, 2*0o755')
        self.assertEqual(s, '0b1, uint:8=34, uint:8=34, uint:8=34, 0o755755')
        s = BitString('0*0b1001010')
        self.assertFalse(s)

    def testMultiplicativeFactorsReading(self):
        s = BitString('0xc')*5
        a, b, c, d, e = s.readlist('5*4')
        self.assertTrue(a == b == c == d == e == 12)
        s = Bits('2*0b101, 4*uint:7=3')
        a, b, c, d, e = s.readlist('2*bin:3, 3*uint:7')
        self.assertTrue(a == b == '0b101')
        self.assertTrue(c == d == e == 3)

    def testMultiplicativeFactorsPacking(self):
        s = pack('3*bin', '1', '001', '101')
        self.assertEqual(s, '0b1001101')
        s = pack('hex, 2*se=-56, 3*uint:37', '34', 1, 2, 3)
        a, b, c, d, e, f = s.unpack('hex:8, 2*se, 3*uint:37')
        self.assertEqual(a, '0x34')
        self.assertEqual(b, -56)
        self.assertEqual(c, -56)
        self.assertEqual((d, e, f), (1, 2, 3))
        # This isn't allowed yet. See comment in tokenparser.
        #s = pack('fluffy*uint:8', *range(3), fluffy=3)
        #a, b, c = s.readlist('2*uint:8, 1*uint:8, 0*uint:8')
        #self.assertEqual((a, b, c), (0, 1, 2))

    def testPackingDefaultIntWithKeyword(self):
        s = pack('12', 100)
        self.assertEqual(s.unpack('12')[0], 100)
        s = pack('oh_no_not_the_eyes=33', oh_no_not_the_eyes=17)
        self.assertEqual(s.uint, 33)
        self.assertEqual(s.len, 17)

    def testInitFromIterable(self):
        self.assertTrue(isinstance(range(10), collections.Iterable))
        s = Bits(range(12))
        self.assertEqual(s, '0x7ff')

    def testFunctionNegativeIndices(self):
        # insert
        s = BitString('0b0111')
        s.insert('0b0', -1)
        self.assertEqual(s, '0b01101')
        self.assertRaises(ValueError, s.insert, '0b0', -1000)

        # reverse
        s.reverse(-2)
        self.assertEqual(s, '0b01110')
        t = BitString('0x778899abcdef')
        t.reverse(-12, -4)
        self.assertEqual(t, '0x778899abc7bf')

        # reversebytes
        t.reversebytes(-40, -16)
        self.assertEqual(t, '0x77ab9988c7bf')

        # overwrite
        t.overwrite('0x666', -20)
        self.assertEqual(t, '0x77ab998666bf')

        # find
        found = t.find('0x998', bytealigned=True, start=-31)
        self.assertFalse(found)
        found = t.find('0x998', bytealigned=True, start=-32)
        self.assertTrue(found)
        self.assertEqual(t.pos, 16)
        t.pos = 0
        found = t.find('0x988', bytealigned=True, end=-21)
        self.assertFalse(found)
        found = t.find('0x998', bytealigned=True, end=-20)
        self.assertTrue(found)
        self.assertEqual(t.pos, 16)

        #findall
        s = BitString('0x1234151f')
        l = list(s.findall('0x1', bytealigned=True, start=-15))
        self.assertEqual(l, [24])
        l = list(s.findall('0x1', bytealigned=True, start=-16))
        self.assertEqual(l, [16, 24])
        l = list(s.findall('0x1', bytealigned=True, end=-5))
        self.assertEqual(l, [0, 16])
        l = list(s.findall('0x1', bytealigned=True, end=-4))
        self.assertEqual(l, [0, 16, 24])

        # rfind
        found = s.rfind('0x1f', end=-1)
        self.assertFalse(found)
        found = s.rfind('0x12', start=-31)
        self.assertFalse(found)

        # cut
        s = BitString('0x12345')
        l = list(s.cut(4, start=-12, end=-4))
        self.assertEqual(l, ['0x3', '0x4'])

        # split
        s = BitString('0xfe0012fe1200fe')
        l = list(s.split('0xfe', bytealigned=True, end=-1))
        self.assertEqual(l, ['', '0xfe0012', '0xfe1200f, 0b111'])
        l = list(s.split('0xfe', bytealigned=True, start=-8))
        self.assertEqual(l, ['', '0xfe'])

        # startswith
        self.assertTrue(s.startswith('0x00f', start=-16))
        self.assertTrue(s.startswith('0xfe00', end=-40))
        self.assertFalse(s.startswith('0xfe00', end=-41))

        # endswith
        self.assertTrue(s.endswith('0x00fe', start=-16))
        self.assertFalse(s.endswith('0x00fe', start=-15))
        self.assertFalse(s.endswith('0x00fe', end=-1))
        self.assertTrue(s.endswith('0x00f', end=-4))

        # replace
        s.replace('0xfe', '', end=-1)
        self.assertEqual(s, '0x00121200fe')
        s.replace('0x00', '', start=-24)
        self.assertEqual(s, '0x001212fe')

    def testAbc(self):
        a = Bits()
        b = BitString()
        self.assertTrue(isinstance(a, collections.Sequence))
        self.assertFalse(isinstance(a, collections.MutableSequence))
        self.assertTrue(isinstance(b, collections.MutableSequence))

    # TODO: write tests for all the ABC methods like count and extend that have been added.

    def testRotateStartAndEnd(self):
        a = BitString('0b110100001')
        a.rol(1, 3, 6)
        self.assertEqual(a, '0b110001001')
        a.ror(1, start=-4)
        self.assertEqual(a, '0b110001100')
        a.rol(202, end=-5)
        self.assertEqual(a, '0b001101100')
        a.ror(3, end=4)
        self.assertEqual(a, '0b011001100')
        self.assertRaises(ValueError, a.rol, 5, start=-4, end=-6)

    def testByteSwapInt(self):
        s = pack('5*uintle:16', *range(10, 15))
        self.assertEqual(list(range(10, 15)), s.unpack('5*uintle:16'))
        swaps = s.byteswap(2)
        self.assertEqual(list(range(10, 15)), s.unpack('5*uintbe:16'))
        self.assertEqual(swaps, 5)
        s = BitString('0xf234567f')
        swaps = s.byteswap(1, start=4)
        self.assertEqual(swaps, 3)
        self.assertEqual(s, '0xf234567f')
        s.byteswap(2, start=4)
        self.assertEqual(s, '0xf452367f')
        s.byteswap(2, start=4, end=-4)
        self.assertEqual(s, '0xf234567f')
        s.byteswap(3)
        self.assertEqual(s, '0x5634f27f')
        s.byteswap(2, repeat=False)
        self.assertEqual(s, '0x3456f27f')
        swaps = s.byteswap(5)
        self.assertEqual(swaps, 0)
        swaps = s.byteswap(4, repeat=False)
        self.assertEqual(swaps, 1)
        self.assertEqual(s, '0x7ff25634')

    def testByteSwapPackCode(self):
        s = BitString('0x0011223344556677')
        swaps = s.byteswap('b')
        self.assertEqual(s, '0x0011223344556677')
        self.assertEqual(swaps, 8)
        swaps = s.byteswap('>3h', repeat=False)
        self.assertEqual(s, '0x1100332255446677')
        self.assertEqual(swaps, 1)

    def testByteSwapIterable(self):
        s = BitString('0x0011223344556677')
        swaps = s.byteswap(range(1, 4), repeat=False)
        self.assertEqual(swaps, 1)
        self.assertEqual(s, '0x0022115544336677')
        swaps = s.byteswap([2], start=8)
        self.assertEqual(s, '0x0011224455663377')
        self.assertEqual(3, swaps)
        swaps = s.byteswap([2, 3], start=4)
        self.assertEqual(swaps, 1)
        self.assertEqual(s, '0x0120156452463377')

    def testByteSwapErrors(self):
        s = BitString('0x0011223344556677')
        self.assertRaises(ValueError, s.byteswap, 'z')
        self.assertRaises(ValueError, s.byteswap, 0)
        self.assertRaises(ValueError, s.byteswap, [-1])
        self.assertRaises(ValueError, s.byteswap, [1, 'e'])
        self.assertRaises(ValueError, s.byteswap, '!h')
        self.assertRaises(ValueError, s.byteswap, 2, start=-1000)

    def testByteSwapFromFile(self):
        s = BitString(filename='smalltestfile')
        swaps = s.byteswap('2bh')
        self.assertEqual(s, '0x0123674589abefcd')
        self.assertEqual(swaps, 2)

    def testBracketExpander(self):
        be = bitstring.expand_brackets
        self.assertEqual(be('hello'), 'hello')
        self.assertEqual(be('(hello)'), 'hello')
        self.assertEqual(be('1*(hello)'), 'hello')
        self.assertEqual(be('2*(hello)'), 'hello,hello')
        self.assertEqual(be('1*(a, b)'), 'a,b')
        self.assertEqual(be('2*(a, b)'), 'a,b,a,b')
        self.assertEqual(be('2*(a), 3*(b)'), 'a,a,b,b,b')
        self.assertEqual(be('2*(a, b, 3*(c, d), e)'), 'a,b,c,d,c,d,c,d,e,a,b,c,d,c,d,c,d,e')

    def testBracketTokens(self):
        s = BitString('3*(0x0, 0b1)')
        self.assertEqual(s, '0x0, 0b1, 0x0, 0b1, 0x0, 0b1')
        s = pack('2*(uint:12, 3*(7, 6))', *range(3, 17))
        a = s.unpack('12, 7, 6, 7, 6, 7, 6, 12, 7, 6, 7, 6, 7, 6')
        self.assertEqual(a, list(range(3, 17)))
        b = s.unpack('2*(12,3*(7,6))')
        self.assertEqual(a, b)

    def testPackCodeDicts(self):
        self.assertEqual(sorted(bitstring.REPLACEMENTS_BE.keys()),
                         sorted(bitstring.REPLACEMENTS_LE.keys()))
        self.assertEqual(sorted(bitstring.REPLACEMENTS_BE.keys()),
                         sorted(bitstring.PACK_CODE_SIZE.keys()))
        for key in bitstring.PACK_CODE_SIZE:
            be = pack(bitstring.REPLACEMENTS_BE[key], 0)
            le = pack(bitstring.REPLACEMENTS_LE[key], 0)
            self.assertEqual(be.len, bitstring.PACK_CODE_SIZE[key]*8)
            self.assertEqual(le.len, be.len)

    # These tests don't compile for Python 3, so they're commented out to save me stress.
    #def testUnicode(self):
        #a = Bits(u'uint:12=34')
        #self.assertEqual(a.uint, 34)
        #a += u'0xfe'
        #self.assertEqual(a[12:], '0xfe')
        #a = BitString('0x1122')
        #c = a.byteswap(u'h')
        #self.assertEqual(c, 1)
        #self.assertEqual(a, u'0x2211')

    #def testLongInt(self):
        #a = BitString(4L)
        #self.assertEqual(a, '0b0000')
        #a[1:3] = -1L
        #self.assertEqual(a, '0b0110')
        #a[0] = 1L
        #self.assertEqual(a, '0b1110')
        #a *= 4L
        #self.assertEqual(a, '0xeeee')
        #c = a.byteswap(2L)
        #self.assertEqual(c, 1)
        #a = BitString('0x11223344')
        #a.byteswap([1, 2L])
        #self.assertEqual(a, '0x11332244')
        #b = a*2L
        #self.assertEqual(b, '0x1133224411332244')
        #s = pack('uint:12', 46L)
        #self.assertEqual(s.uint, 46)

class UnpackWithDict(unittest.TestCase):

    def testLengthKeywords(self):
        a = Bits('2*13=100, 0b111')
        x, y, z = a.unpack('n, uint:m, bin:q', n=13, m=13, q=3)
        self.assertEqual(x, 100)
        self.assertEqual(y, 100)
        self.assertEqual(z, '0b111')

    def testLengthKeywordsWithStretch(self):
        a = Bits('0xff, 0b000, 0xf')
        x, y, z = a.unpack('hex:a, bin, hex:b', a=8, b=4)
        self.assertEqual(y, '0b000')

    def testUnusedKeyword(self):
        a = Bits('0b110')
        x, = a.unpack('bin:3', notused=33)
        self.assertEqual(x, '0b110')

    def testLengthKeywordErrors(self):
        a = pack('uint:p=33', p=12)
        self.assertRaises(ValueError, a.unpack, 'uint:p')
        self.assertRaises(ValueError, a.unpack, 'uint:p', p='a_string')


class ReadWithDict(unittest.TestCase):

    def testLengthKeywords(self):
        s = BitString('0x0102')
        x, y = s.readlist('a, hex:b', a=8, b=4)
        self.assertEqual((x, y), (1, '0x0'))
        self.assertEqual(s.pos, 12)

class PeekWithDict(unittest.TestCase):

    def testLengthKeywords(self):
        s = BitString('0x0102')
        x, y = s.peeklist('a, hex:b', a=8, b=4)
        self.assertEqual((x, y), (1, '0x0'))
        self.assertEqual(s.pos, 0)

def main():
    unittest.main()

if __name__ == '__main__':
    main()