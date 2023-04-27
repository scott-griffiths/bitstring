#!/usr/bin/env python

import unittest
import sys
sys.path.insert(0, '..')
import bitstring
from bitstring import BitStore


class BasicFunctionality(unittest.TestCase):

    def testGettingInt(self):
        a = BitStore('001')
        self.assertEqual(a[0], 0)
        self.assertEqual(a[1], 0)
        self.assertEqual(a[2], 1)

        self.assertEqual(a[-1], 1)
        self.assertEqual(a[-2], 0)
        self.assertEqual(a[-3], 0)

        with self.assertRaises(IndexError):
            _ = a[3]
        with self.assertRaises(IndexError):
            _ = a[-4]


class BasicLSB0Functionality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bitstring.lsb0 = True

    @classmethod
    def tearDownClass(cls):
        bitstring.lsb0 = False

    def testGettingInt(self):
        a = BitStore('001')
        self.assertEqual(a[0], 1)
        self.assertEqual(a[1], 0)
        self.assertEqual(a[2], 0)

        self.assertEqual(a[-1], 0)
        self.assertEqual(a[-2], 0)
        self.assertEqual(a[-3], 1)

        with self.assertRaises(IndexError):
            _ = a[3]
        with self.assertRaises(IndexError):
            _ = a[-4]

    def testGettingSlice(self):
        a = BitStore(buffer=b'12345678')
        self.assertEqual(a[:].tobytes(), b'12345678')
        self.assertEqual(a[:-8].tobytes(), b'2345678')
        self.assertEqual(a[8:].tobytes(), b'1234567')
        self.assertEqual(a[16:24].tobytes(), b'6')

    def testSettingInt(self):
        a = BitStore('00000')
        a[0] = 1
        self.assertEqual(a.to01(), '00001')
        a[-1] = 1
        self.assertEqual(a.to01(), '10001')
        with self.assertRaises(IndexError):
            a[5] = 1
        with self.assertRaises(IndexError):
            a[-6] = 0