#!/usr/bin/env python

import unittest
import sys
sys.path.insert(0, '..')
import bitstring
from bitstring import ConstBitArray as CBA

class Creation(unittest.TestCase):

    def testCreationFromData(self):
        s = CBA(bytes=b'\xa0\xff')
        self.assertEqual((s.len, s.hex), (16, '0xa0ff'))

    def testCreationFromDataWithOffset(self):
        s1 = CBA(bytes=b'\x0b\x1c\x2f', offset=0, length=20)
        s2 = CBA(bytes=b'\xa0\xb1\xC2', offset=4)
        self.assertEqual((s2.len, s2.hex), (20, '0x0b1c2'))
        self.assertEqual((s1.len, s1.hex), (20, '0x0b1c2'))
        self.assertTrue(s1 == s2)

    def testCreationFromHex(self):
        s = CBA(hex='0xA0ff')
        self.assertEqual((s.len, s.hex), (16, '0xa0ff'))
        s = CBA(hex='0x0x0X')
        self.assertEqual((s.length, s.hex), (0, ''))

    def testCreationFromHexWithWhitespace(self):
        s = CBA(hex='  \n0 X a  4e       \r3  \n')
        self.assertEqual(s.hex, '0xa4e3')


    def testCreationFromHexErrors(self):
        self.assertRaises(bitstring.CreationError, CBA, hex='0xx0')
        self.assertRaises(bitstring.CreationError, CBA, hex='0xX0')
        self.assertRaises(bitstring.CreationError, CBA, hex='0Xx0')
        self.assertRaises(bitstring.CreationError, CBA, hex='-2e')

    def testCreationFromBin(self):
        s = CBA(bin='1010000011111111')
        self.assertEqual((s.length, s.hex), (16, '0xa0ff'))
        s = CBA(bin='00')[:1]
        self.assertEqual(s.bin, '0b0')
        s = CBA(bin=' 0000 \n 0001\r ')
        self.assertEqual(s.bin, '0b00000001')

    def testCreationFromBinWithWhitespace(self):
        s = CBA(bin='  \r\r\n0   B    00   1 1 \t0 ')
        self.assertEqual(s.bin, '0b00110')

    def testCreationFromOctErrors(self):
        s = CBA('0b00011')
        self.assertRaises(bitstring.InterpretError, s._getoct)
        self.assertRaises(bitstring.CreationError, s._setoct, '8')

    #def testCreationFromIntWithoutLength(self):
    #    s = ConstBitStream(uint=5)
    #    self.assertEqual(s, '0b101')
    #    s = ConstBitStream(uint=0)
    #    self.assertEqual(s, [0])
    #    s = ConstBitStream(int=-1)
    #    self.assertEqual(s, [1])
    #    s = ConstBitStream(int=-2)
    #    self.assertEqual(s, '0b10')


    def testCreationFromUintWithOffset(self):
        self.assertRaises(bitstring.Error, CBA, uint=12, length=8, offset=1)

    def testCreationFromUintErrors(self):
        self.assertRaises(bitstring.CreationError, CBA, uint=-1, length=10)
        self.assertRaises(bitstring.CreationError, CBA, uint=12)
        self.assertRaises(bitstring.CreationError, CBA, uint=4, length=2)
        self.assertRaises(bitstring.CreationError, CBA, uint=0, length=0)
        self.assertRaises(bitstring.CreationError, CBA, uint=12, length=-12)

    def testCreationFromInt(self):
        s = CBA(int=0, length=4)
        self.assertEqual(s.bin, '0b0000')
        s = CBA(int=1, length=2)
        self.assertEqual(s.bin, '0b01')
        s = CBA(int=-1, length=11)
        self.assertEqual(s.bin, '0b11111111111')
        s = CBA(int=12, length=7)
        self.assertEqual(s.int, 12)
        s = CBA(int=-243, length=108)
        self.assertEqual((s.int, s.length), (-243, 108))
        for length in range(6, 10):
            for value in range(-17, 17):
                s = CBA(int=value, length=length)
                self.assertEqual((s.int, s.length), (value, length))
        s = CBA(int=10, length=8)

    def testCreationFromIntErrors(self):
        self.assertRaises(bitstring.CreationError, CBA, int=-1, length=0)
        self.assertRaises(bitstring.CreationError, CBA, int=12)
        self.assertRaises(bitstring.CreationError, CBA, int=4, length=3)
        self.assertRaises(bitstring.CreationError, CBA, int=-5, length=3)

    def testCreationFromSe(self):
        for i in range(-100, 10):
            s = CBA(se=i)
            self.assertEqual(s.se, i)

    def testCreationFromSeWithOffset(self):
        self.assertRaises(bitstring.CreationError, CBA, se=-13, offset=1)

    def testCreationFromSeErrors(self):
        self.assertRaises(bitstring.CreationError, CBA, se=-5, length=33)
        s = CBA(bin='001000')
        self.assertRaises(bitstring.InterpretError, s._getse)

    def testCreationFromUe(self):
        [self.assertEqual(CBA(ue=i).ue, i) for i in range(0, 20)]

    def testCreationFromUeWithOffset(self):
        self.assertRaises(bitstring.CreationError, CBA, ue=104, offset=2)

    def testCreationFromUeErrors(self):
        self.assertRaises(bitstring.CreationError, CBA, ue=-1)
        self.assertRaises(bitstring.CreationError, CBA, ue=1, length=12)
        s = CBA(bin='10')
        self.assertRaises(bitstring.InterpretError, s._getue)


class Initialisation(unittest.TestCase):
    
    def testEmptyInit(self):
        a = CBA()
        self.assertEqual(a, '')
        
    def testNoPos(self):
        a = CBA('0xabcdef')
        try:
            a.pos
        except AttributeError:
            pass
        else:
            assert False
            
    def testFind(self):
        a = CBA('0xabcd')
        r = a.find('0xbc')
        self.assertEqual(r[0], 4)
        r = a.find('0x23462346246', bytealigned=True)
        self.assertFalse(r)
        
    def testRfind(self):
        a = CBA('0b11101010010010')
        b = a.rfind('0b010')
        self.assertEqual(b[0], 11)
        
    def testFindAll(self):
        a = CBA('0b0010011')
        b = list(a.findall([1]))
        self.assertEqual(b, [2, 5, 6])
        
class Cut(unittest.TestCase):
    
    def testCut(self):
        s = CBA(30)
        for t in s.cut(3):
            self.assertEqual(t, [0]*3)

class InterleavedExpGolomb(unittest.TestCase):
    
    def testCreation(self):
        s1 = CBA(uie=0)
        s2 = CBA(uie=1)
        self.assertEqual(s1, [1])
        self.assertEqual(s2, [0, 0, 1])
        s1 = CBA(sie=0)
        s2 = CBA(sie=-1)
        s3 = CBA(sie=1)
        self.assertEqual(s1, [1])
        self.assertEqual(s2, [0, 0, 1, 1])
        self.assertEqual(s3, [0, 0, 1, 0])
        
    def testInterpretation(self):
        for x in range(101):
            self.assertEqual(CBA(uie=x).uie, x)
        for x in range(-100, 100):
            self.assertEqual(CBA(sie=x).sie, x)
            
    def testErrors(self):
        s = CBA([0,0])
        self.assertRaises(bitstring.InterpretError, s._getsie)
        self.assertRaises(bitstring.InterpretError, s._getuie)
        self.assertRaises(ValueError, CBA, 'uie=-10')
    
