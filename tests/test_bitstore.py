#!/usr/bin/env python

import unittest
import sys
sys.path.insert(0, '..')
import bitstring
from bitstring.bitstore import BitStore, offset_slice_indices_lsb0
import sys

sys.path.insert(0, '..')


class BasicFunctionality(unittest.TestCase):

    def testGettingInt(self):
        a = BitStore('001')
        self.assertEqual(a.getindex(0), 0)
        self.assertEqual(a.getindex(1), 0)
        self.assertEqual(a.getindex(2), 1)

        self.assertEqual(a.getindex(-1), 1)
        self.assertEqual(a.getindex(-2), 0)
        self.assertEqual(a.getindex(-3), 0)

        with self.assertRaises(IndexError):
            _ = a.getindex(3)
        with self.assertRaises(IndexError):
            _ = a.getindex(-4)


class BasicLSB0Functionality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bitstring.lsb0 = True

    @classmethod
    def tearDownClass(cls):
        bitstring.lsb0 = False

    def testGettingInt(self):
        a = BitStore('001')
        self.assertEqual(a.getindex(0), 1)
        self.assertEqual(a.getindex(1), 0)
        self.assertEqual(a.getindex(2), 0)

        self.assertEqual(a.getindex(-1), 0)
        self.assertEqual(a.getindex(-2), 0)
        self.assertEqual(a.getindex(-3), 1)

        with self.assertRaises(IndexError):
            _ = a.getindex(3)
        with self.assertRaises(IndexError):
            _ = a.getindex(-4)

    def testGettingSlice(self):
        a = BitStore(buffer=b'12345678')
        self.assertEqual(a.getslice(slice(None, None, None)).tobytes(), b'12345678')
        self.assertEqual(a.getslice(slice(None, -8, None)).tobytes(), b'2345678')
        self.assertEqual(a.getslice(slice(8, None, None)).tobytes(), b'1234567')
        self.assertEqual(a.getslice(slice(16, 24, None)).tobytes(), b'6')

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


class GettingSlices(unittest.TestCase):

    def tearDown(self) -> None:
        bitstring.lsb0 = False

    def testEverything(self):
        a = BitStore('010010001000110111001111101101001111')

        # Try combination of start and stop for msb0 and get the result.
        # Convert to start and stop needed for lsb0
        options = [5, 2, -2, 1, 7, -3, -9, 0, -1, -len(a), len(a), len(a) - 1, -len(a) - 1, -100, 100, None]
        for start_option in options:
            for end_option in options:
                bitstring.lsb0 = True
                lsb0 = a.getslice(slice(start_option, end_option, None))
                bitstring.lsb0 = False
                msb0 = a.getslice(slice(start_option, end_option, None))
                new_slice = offset_slice_indices_lsb0(slice(start_option, end_option, None), len(a), 0)
                new_start, new_end = new_slice.start, new_slice.stop
                self.assertEqual(len(msb0), len(lsb0), f"[{start_option}: {end_option}] -> [{new_start}: {new_end}]  len(msb0)={len(msb0)}, len(lsb0)={len(lsb0)}")