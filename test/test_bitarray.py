#!/usr/bin/env python
"""
Unit tests for the bitarray module.
"""

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