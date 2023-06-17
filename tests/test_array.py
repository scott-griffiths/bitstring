#!/usr/bin/env python
import io
import unittest
import sys

sys.path.insert(0, '..')
import bitstring
import array
import os
from bitstring import Array


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
