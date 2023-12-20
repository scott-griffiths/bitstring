
import unittest
import sys

import bitstring

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
        x = a.read(b)
        self.assertEqual(x, 255)
        x = a.read(b)
        self.assertEqual(x, 0)

    def testSettingWithLength(self):
        d = Dtype('uint', 12)
        self.assertEqual(str(d), 'uint12')
        self.assertEqual(d.length, 12)
        self.assertEqual(d.name, 'uint')


class ChangingTheRegister(unittest.TestCase):

    def testRetrievingMetaDtype(self):
        r = bitstring.dtype_register
        u = r['uint']
        u2 = r['u']
        self.assertEqual(u, u2)
        with self.assertRaises(KeyError):
            i = r['integer']

    def testRemovingType(self):
        r = bitstring.dtype_register
        del r['bfloat']
        with self.assertRaises(KeyError):
            i = r['bfloat']
        with self.assertRaises(KeyError):
            del r['penguin']

# class CreatingNewDtypes(unittest.TestCase):

    # def testNewAlias(self):
    #     bs.Bits._register.add_meta_dtype_alias('bin', 'cat')
    #     a = bs.BitStream('0b110110')
    #     self.assertEqual(a.cat, '110110')
    #     self.assertEqual(a.read('cat4'), '1101')
    #     a.cat = '11110000'
    #     # self.assertEqual(a.unpack('cat'), '11110000')