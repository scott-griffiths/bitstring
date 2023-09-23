
import unittest
import sys
sys.path.insert(0, '..')
import bitstring as bs
from bitstring import Dtype


class BasicFunctionality(unittest.TestCase):

    def testSettingBool(self):
        b = Dtype('bool')
        self.assertEqual(str(b), 'bool')
        self.assertEqual(b.name, 'bool')
        self.assertEqual(b.length, 1)

        b2 = Dtype('bool:1')
        self.assertEqual(b, b2)
        # self.assertTrue(b is b2)

    def testReading(self):
        b = Dtype('u8')
        a = bs.BitStream('0xff00ff')
        # x = a.read(b)
        # self.assertEqual(x, 255)
        # x = a.read(b)
        # self.assertEqual(x, 0)
