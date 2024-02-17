
import unittest
import sys
import bitstring as bs
from bitstring import Dtype, DtypeDefinition, Bits

sys.path.insert(0, '..')


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

    def testBuildErrors(self):
        dtype = Dtype('uint8')
        value = 'not_an_integer'
        with self.assertRaises(ValueError):
            dtype.build(value)

    def testBuild(self):
        dtype = Dtype('se')
        x = dtype.build(10001)
        self.assertEqual(x.se, 10001)

    def testParse(self):
        dtype = Dtype('uint:12')
        x = dtype.parse('0x3ff')
        self.assertEqual(x, 1023)



class ChangingTheRegister(unittest.TestCase):

    def testRetrievingMetaDtype(self):
        r = bs.dtype_register
        u = r['uint']
        u2 = r['u']
        self.assertEqual(u, u2)
        with self.assertRaises(KeyError):
            i = r['integer']

    def testRemovingType(self):
        r = bs.dtype_register
        del r['bfloat']
        with self.assertRaises(KeyError):
            i = r['bfloat']
        with self.assertRaises(KeyError):
            del r['penguin']


class CreatingNewDtypes(unittest.TestCase):

    def testNewAlias(self):
        bs.dtype_register.add_dtype_alias('bin', 'cat')
        a = bs.BitStream('0b110110')
        self.assertEqual(a.cat, '110110')
        self.assertEqual(a.read('cat4'), '1101')
        a.cat = '11110000'
        self.assertEqual(a.unpack('cat'), ['11110000'])

    def testNewType(self):
        md = DtypeDefinition('uint_r', bs.Bits._setuint, bs.Bits._getuint)
        bs.dtype_register.add_dtype(md)
        a = bs.BitArray('0xf')
        self.assertEqual(a.uint_r, 15)
        a.uint_r = 1
        self.assertEqual(a, '0x1')
        a += 'uint_r100=0'
        self.assertEqual(a, '0x1, 0b' + '0'*100)

    def testNewTypeWithGetter(self):
        def get_fn(bs):
            return bs.count(1)
        md = DtypeDefinition('counter', None, get_fn)
        bs.dtype_register.add_dtype(md)
        a = bs.BitStream('0x010f')
        self.assertEqual(a.counter, 5)
        self.assertEqual(a.readlist('2*counter8'), [1, 4])
        self.assertEqual(a.unpack('counter7, counter'), [0, 5])
        with self.assertRaises(AttributeError):
            a.counter = 4