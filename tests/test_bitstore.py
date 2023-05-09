#!/usr/bin/env python

import unittest
import sys
sys.path.insert(0, '..')
import bitstring
from bitstring import BitStore, _convert_start_and_stop_from_lsb0_to_msb0, MmapBitStore
import os


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
                lsb0 = a[start_option: end_option]
                bitstring.lsb0 = False
                msb0 = a[start_option: end_option]
                new_start, new_end =_convert_start_and_stop_from_lsb0_to_msb0(start_option, end_option, len(a))
                self.assertEqual(len(msb0), len(lsb0), f"[{start_option}: {end_option}] -> [{new_start}: {new_end}]  len(msb0)={len(msb0)}, len(lsb0)={len(lsb0)}")

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class MmapBitStoreTests(unittest.TestCase):

    def testSimpleCase(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        with open(filename, 'rb') as f:
            mba = MmapBitStore(f)
            start_code = '000001b3'
            x = mba[:32].tobytes().hex()
            self.assertEqual(x, start_code)
            self.assertEqual(mba[0], 0)
            self.assertEqual(mba[23], 1)

    def testOffsetCase(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        with open(filename, 'rb') as f:
            mba = MmapBitStore(f, offset=10)
            self.assertEqual(mba[12], 0)
            self.assertEqual(mba[13], 1)
            self.assertEqual(mba[13:22].to01(), '110110011')

    def testLimits(self):
        filename = os.path.join(THIS_DIR, 'test.m1v')
        with open(filename, 'rb') as f:
            mba = MmapBitStore(f)
            full_length = len(mba)
            mba = MmapBitStore(f, offset=999, length=1001)
            self.assertEqual(len(mba), 1001)
            _ = mba[1000]
            _ = mba[-1001]
            with self.assertRaises(IndexError):
                _ = mba[1001]
            with self.assertRaises(IndexError):
                _ = mba[-1002]