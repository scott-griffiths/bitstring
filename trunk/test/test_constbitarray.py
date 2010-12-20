#!/usr/bin/env python

import unittest
import sys
sys.path.insert(0, '..')
from bitstring import ConstBitArray as CBA

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
