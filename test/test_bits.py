#!/usr/bin/env python
import io
import unittest
import sys

sys.path.insert(0, '..')
import bitstring
import array
from bitstring import MmapByteArray
from bitstring import Bits, BitArray, ConstByteStore


class Creation(unittest.TestCase):
    def testCreationFromBytes(self):
        s = Bits(bytes=b'\xa0\xff')
        self.assertEqual((s.len, s.hex), (16, 'a0ff'))
        s = Bits(bytes=b'abc', length=0)
        self.assertEqual(s, '')

    def testCreationFromBytesErrors(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(bytes=b'abc', length=25)

    def testCreationFromDataWithOffset(self):
        s1 = Bits(bytes=b'\x0b\x1c\x2f', offset=0, length=20)
        s2 = Bits(bytes=b'\xa0\xb1\xC2', offset=4)
        self.assertEqual((s2.len, s2.hex), (20, '0b1c2'))
        self.assertEqual((s1.len, s1.hex), (20, '0b1c2'))
        self.assertTrue(s1 == s2)

    def testCreationFromHex(self):
        s = Bits(hex='0xA0ff')
        self.assertEqual((s.len, s.hex), (16, 'a0ff'))
        s = Bits(hex='0x0x0X')
        self.assertEqual((s.length, s.hex), (0, ''))

    def testCreationFromHexWithWhitespace(self):
        s = Bits(hex='  \n0 X a  4e       \r3  \n')
        self.assertEqual(s.hex, 'a4e3')

    def testCreationFromHexErrors(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(hex='0xx0')
        with self.assertRaises(bitstring.CreationError):
            Bits(hex='0xX0')
        with self.assertRaises(bitstring.CreationError):
            Bits(hex='0Xx0')
        with self.assertRaises(bitstring.CreationError):
            Bits(hex='-2e')
        with self.assertRaises(bitstring.CreationError):
            Bits('0x2', length=2)
        with self.assertRaises(bitstring.CreationError):
            Bits('0x3', offset=1)

    def testCreationFromBin(self):
        s = Bits(bin='1010000011111111')
        self.assertEqual((s.length, s.hex), (16, 'a0ff'))
        s = Bits(bin='00')[:1]
        self.assertEqual(s.bin, '0')
        s = Bits(bin=' 0000 \n 0001\r ')
        self.assertEqual(s.bin, '00000001')

    def testCreationFromBinWithWhitespace(self):
        s = Bits(bin='  \r\r\n0   B    00   1 1 \t0 ')
        self.assertEqual(s.bin, '00110')

    def testCreationFromOctErrors(self):
        s = Bits('0b00011')
        with self.assertRaises(bitstring.InterpretError):
            _ = s.oct
        with self.assertRaises(bitstring.CreationError):
            _ = Bits('oct=8')

    def testCreationFromUintWithOffset(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(uint=12, length=8, offset=1)

    def testCreationFromUintErrors(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(uint=-1, length=10)
        with self.assertRaises(bitstring.CreationError):
            Bits(uint=12)
        with self.assertRaises(bitstring.CreationError):
            Bits(uint=4, length=2)
        with self.assertRaises(bitstring.CreationError):
            Bits(uint=0, length=0)
        with self.assertRaises(bitstring.CreationError):
            Bits(uint=12, length=-12)

    def testCreationFromInt(self):
        s = Bits(int=0, length=4)
        self.assertEqual(s.bin, '0000')
        s = Bits(int=1, length=2)
        self.assertEqual(s.bin, '01')
        s = Bits(int=-1, length=11)
        self.assertEqual(s.bin, '11111111111')
        s = Bits(int=12, length=7)
        self.assertEqual(s.int, 12)
        s = Bits(int=-243, length=108)
        self.assertEqual((s.int, s.length), (-243, 108))
        for length in range(6, 10):
            for value in range(-17, 17):
                s = Bits(int=value, length=length)
                self.assertEqual((s.int, s.length), (value, length))
        _ = Bits(int=10, length=8)

    def testCreationFromIntErrors(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(int=-1, length=0)
        with self.assertRaises(bitstring.CreationError):
            Bits(int=12)
        with self.assertRaises(bitstring.CreationError):
            Bits(int=4, length=3)
        with self.assertRaises(bitstring.CreationError):
            Bits(int=-5, length=3)

    def testCreationFromSe(self):
        for i in range(-100, 10):
            s = Bits(se=i)
            self.assertEqual(s.se, i)

    def testCreationFromSeWithOffset(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(se=-13, offset=1)

    def testCreationFromSeErrors(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(se=-5, length=33)
        s = Bits(bin='001000')
        with self.assertRaises(bitstring.InterpretError):
            _ = s.se

    def testCreationFromUe(self):
        [self.assertEqual(Bits(ue=i).ue, i) for i in range(0, 20)]

    def testCreationFromUeWithOffset(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(ue=104, offset=2)

    def testCreationFromUeErrors(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(ue=-1)
        with self.assertRaises(bitstring.CreationError):
            Bits(ue=1, length=12)
        s = Bits(bin='10')
        with self.assertRaises(bitstring.InterpretError):
            _ = s.ue

    def testCreationFromBool(self):
        a = Bits('bool=1')
        self.assertEqual(a, 'bool=1')
        b = Bits('bool:1=0')
        self.assertEqual(b, [0])
        c = bitstring.pack('bool=1, 2*bool', 0, 1)
        self.assertEqual(c, '0b101')
        d = bitstring.pack('bool:1=1, 2*bool:1', 1, 0)
        self.assertEqual(d, '0b110')

    def testCreationKeywordError(self):
        with self.assertRaises(bitstring.CreationError):
            Bits(squirrel=5)

    def testDataStoreType(self):
        a = Bits('0xf')
        self.assertEqual(type(a._datastore), bitstring.ConstByteStore)


class Initialisation(unittest.TestCase):
    def testEmptyInit(self):
        a = Bits()
        self.assertEqual(a, '')

    def testNoPos(self):
        a = Bits('0xabcdef')
        with self.assertRaises(AttributeError):
            _ = a.pos

    def testFind(self):
        a = Bits('0xabcd')
        r = a.find('0xbc')
        self.assertEqual(r[0], 4)
        r = a.find('0x23462346246', bytealigned=True)
        self.assertFalse(r)

    def testRfind(self):
        a = Bits('0b11101010010010')
        b = a.rfind('0b010')
        self.assertEqual(b[0], 11)

    def testFindAll(self):
        a = Bits('0b0010011')
        b = list(a.findall([1]))
        self.assertEqual(b, [2, 5, 6])


class Cut(unittest.TestCase):
    def testCut(self):
        s = Bits(30)
        for t in s.cut(3):
            self.assertEqual(t, [0] * 3)


class InterleavedExpGolomb(unittest.TestCase):
    def testCreation(self):
        s1 = Bits(uie=0)
        s2 = Bits(uie=1)
        self.assertEqual(s1, [1])
        self.assertEqual(s2, [0, 0, 1])
        s1 = Bits(sie=0)
        s2 = Bits(sie=-1)
        s3 = Bits(sie=1)
        self.assertEqual(s1, [1])
        self.assertEqual(s2, [0, 0, 1, 1])
        self.assertEqual(s3, [0, 0, 1, 0])

    def testCreationFromProperty(self):
        s = BitArray()
        s.uie = 45
        self.assertEqual(s.uie, 45)
        s.sie = -45
        self.assertEqual(s.sie, -45)

    def testInterpretation(self):
        for x in range(101):
            self.assertEqual(Bits(uie=x).uie, x)
        for x in range(-100, 100):
            self.assertEqual(Bits(sie=x).sie, x)

    def testErrors(self):
        for f in ['sie=100, 0b1001', '0b00', 'uie=100, 0b1001']:
            s = Bits(f)
            with self.assertRaises(bitstring.InterpretError):
                _ = s.sie
            with self.assertRaises(bitstring.InterpretError):
                _ = s.uie
        with self.assertRaises(ValueError):
            Bits(uie=-10)


class FileBased(unittest.TestCase):
    def setUp(self):
        self.a = Bits(filename='smalltestfile')
        self.b = Bits(filename='smalltestfile', offset=16)
        self.c = Bits(filename='smalltestfile', offset=20, length=16)
        self.d = Bits(filename='smalltestfile', offset=20, length=4)

    def testCreationWithOffset(self):
        self.assertEqual(self.a, '0x0123456789abcdef')
        self.assertEqual(self.b, '0x456789abcdef')
        self.assertEqual(self.c, '0x5678')

    def testBitOperators(self):
        x = self.b[4:20]
        self.assertEqual(x, '0x5678')
        self.assertEqual((x & self.c).hex, self.c.hex)
        self.assertEqual(self.c ^ self.b[4:20], 16)
        self.assertEqual(self.a[23:36] | self.c[3:], self.c[3:])

    def testAddition(self):
        _ = self.d + '0x1'
        x = self.a[20:24] + self.c[-4:] + self.c[8:12]
        self.assertEqual(x, '0x587')
        x = self.b + x
        self.assertEqual(x.hex, '456789abcdef587')
        x = BitArray(x)
        del x[12:24]
        self.assertEqual(x, '0x456abcdef587')
        

class Mmap(unittest.TestCase):
    def setUp(self):
        self.f = open('smalltestfile', 'rb')

    def tearDown(self):
        self.f.close()

    def testByteArrayEquivalence(self):
        a = MmapByteArray(self.f)
        self.assertEqual(a.bytelength, 8)
        self.assertEqual(len(a), 8)
        self.assertEqual(a[0], 0x01)
        self.assertEqual(a[1], 0x23)
        self.assertEqual(a[7], 0xef)
        self.assertEqual(a[0:1], bytearray([1]))
        self.assertEqual(a[:], bytearray([0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef]))
        self.assertEqual(a[2:4], bytearray([0x45, 0x67]))

    def testWithLength(self):
        a = MmapByteArray(self.f, 3)
        self.assertEqual(a[0], 0x01)
        self.assertEqual(len(a), 3)

    def testWithOffset(self):
        a = MmapByteArray(self.f, None, 5)
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0], 0xab)

    def testWithLengthAndOffset(self):
        a = MmapByteArray(self.f, 3, 3)
        self.assertEqual(len(a), 3)
        self.assertEqual(a[0], 0x67)
        self.assertEqual(a[:], bytearray([0x67, 0x89, 0xab]))


class Comparisons(unittest.TestCase):
    def testUnorderable(self):
        a = Bits(5)
        b = Bits(5)
        with self.assertRaises(TypeError):
            _ = a < b
        with self.assertRaises(TypeError):
            _ = a > b
        with self.assertRaises(TypeError):
            _ = a <= b
        with self.assertRaises(TypeError):
            _ = a >= b


class Subclassing(unittest.TestCase):

    def testIsInstance(self):
        class SubBits(bitstring.Bits):
            pass
        a = SubBits()
        self.assertTrue(isinstance(a, SubBits))

    def testClassType(self):
        class SubBits(bitstring.Bits):
            pass
        self.assertEqual(SubBits().__class__, SubBits)


class LongBoolConversion(unittest.TestCase):

    def testLongBool(self):
        a = Bits(1000)
        b = bool(a)
        self.assertTrue(b is False)


# Some basic tests for the private ByteStore classes

class ConstByteStoreCreation(unittest.TestCase):

    def testProperties(self):
        a = ConstByteStore(bytearray(b'abc'))
        self.assertEqual(a.bytelength, 3)
        self.assertEqual(a.offset, 0)
        self.assertEqual(a.bitlength, 24)
        self.assertEqual(a.rawarray, b'abc')

    def testGetBit(self):
        a = ConstByteStore(bytearray([0x0f]))
        self.assertEqual(a.getbit(0), False)
        self.assertEqual(a.getbit(3), False)
        self.assertEqual(a.getbit(4), True)
        self.assertEqual(a.getbit(7), True)

        b = ConstByteStore(bytearray([0x0f]), 7, 1)
        self.assertEqual(b.getbit(2), False)
        self.assertEqual(b.getbit(3), True)

    def testGetByte(self):
        a = ConstByteStore(bytearray(b'abcde'), 1, 13)
        self.assertEqual(a.getbyte(0), 97)
        self.assertEqual(a.getbyte(1), 98)
        self.assertEqual(a.getbyte(4), 101)


class PadToken(unittest.TestCase):

    def testCreation(self):
        a = Bits('pad:10')
        self.assertEqual(a, Bits(10))
        b = Bits('pad:0')
        self.assertEqual(b, Bits())
        c = Bits('0b11, pad:1, 0b111')
        self.assertEqual(c, Bits('0b110111'))

    def testPack(self):
        s = bitstring.pack('0b11, pad:3=5, 0b1')
        self.assertEqual(s.bin, '110001')
        d = bitstring.pack('pad:c', c=12)
        self.assertEqual(d, Bits(12))
        e = bitstring.pack('0xf, uint:12, pad:1, bin, pad:4, 0b10', 0, '111')
        self.assertEqual(e.bin, '11110000000000000111000010')

    def testUnpack(self):
        s = Bits('0b111000111')
        x, y = s.unpack('3, pad:3, 3')
        self.assertEqual((x, y.uint), ('0b111', 7))
        x, y = s.unpack('2, pad:2, bin')
        self.assertEqual((x.uint, y), (3, '00111'))
        x = s.unpack('pad:1, pad:2, pad:3')
        self.assertEqual(x, [])


class ModifiedByAddingBug(unittest.TestCase):

    def testAdding(self):
        a = Bits('0b0')
        b = Bits('0b11')
        c = a + b
        self.assertEqual(c, '0b011')
        self.assertEqual(a, '0b0')
        self.assertEqual(b, '0b11')

    def testAdding2(self):
        a = Bits(100)
        b = Bits(101)
        c = a + b
        self.assertEqual(a, 100)
        self.assertEqual(b, 101)
        self.assertEqual(c, 201)


class WrongTypeBug(unittest.TestCase):

    def testAppendToBits(self):
        a = Bits(BitArray())
        with self.assertRaises(AttributeError):
            a.append('0b1')
        self.assertEqual(type(a), Bits)
        b = bitstring.ConstBitStream(bitstring.BitStream())
        self.assertEqual(type(b), bitstring.ConstBitStream)


class InitFromArray(unittest.TestCase):

    def testEmptyArray(self):
        a = array.array('B')
        b = Bits(a)
        self.assertEqual(b.length, 0)

    def testSingleByte(self):
        a = array.array('B', b'\xff')
        b = Bits(a)
        self.assertEqual(b.length, 8)
        self.assertEqual(b.hex, 'ff')

    def testSignedShort(self):
        a = array.array('h')
        a.append(10)
        a.append(-1)
        b = Bits(a)
        self.assertEqual(b.length, 32)
        self.assertEqual(b.bytes, a.tobytes())

    def testDouble(self):
        a = array.array('d', [0.0, 1.0, 2.5])
        b = Bits(a)
        self.assertEqual(b.length, 192)
        c, d, e = b.unpack('3*floatne:64')
        self.assertEqual((c, d, e), (0.0, 1.0, 2.5))


class Iteration(unittest.TestCase):

    def testIterateEmptyBits(self):
        self.assertEqual(list(Bits([])), [])
        self.assertEqual(list(Bits([1, 0])[1:1]), [])

    def testIterateNonEmptyBits(self):
        self.assertEqual(list(Bits([1, 0])), [True, False])
        self.assertEqual(list(Bits([1, 0, 0, 1])[1:3]), [False, False])

    def testIterateLongBits(self):
        self.assertEqual(
            list(Bits([1, 0]) * 1024),
            [True, False] * 1024
        )

        
class ContainsBug(unittest.TestCase):

    def testContains(self):
        a = Bits('0b1, 0x0001dead0001')
        self.assertTrue('0xdead' in a)
        self.assertFalse('0xfeed' in a)

        self.assertTrue('0b1' in Bits('0xf'))
        self.assertFalse('0b0' in Bits('0xf'))


class ByteStoreImmutablity(unittest.TestCase):
    
    def testBitsDataStoreType(self):
        a = Bits('0b1')
        b = Bits('0b111')
        c = a + b
        self.assertEqual(type(a._datastore), ConstByteStore)
        self.assertEqual(type(b._datastore), ConstByteStore)
        self.assertEqual(type(c._datastore), ConstByteStore)

    def testImmutabilityBugAppend(self):
        a = Bits('0b111')
        b = a + '0b000'
        c = BitArray(b)
        c[1] = 0
        self.assertEqual(c.bin, '101000')
        self.assertEqual(a.bin, '111')
        self.assertEqual(b.bin, '111000')
        self.assertEqual(type(b._datastore), ConstByteStore)

    def testImmutabilityBugPrepend(self):
        a = Bits('0b111')
        b = '0b000' + a
        c = BitArray(b)
        c[1] = 1
        self.assertEqual(b.bin, '000111')
        self.assertEqual(c.bin, '010111')

    def testImmutabilityBugCreation(self):
        a = Bits()
        self.assertEqual(type(a._datastore), ConstByteStore)


class Lsb0Indexing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bitstring.set_lsb0(True)

    @classmethod
    def tearDownClass(cls):
        bitstring.set_lsb0(False)

    def testGetSingleBit(self):
        a = Bits('0b000001111')
        self.assertEqual(a[0], True)
        self.assertEqual(a[3], True)
        self.assertEqual(a[4], False)
        self.assertEqual(a[8], False)
        with self.assertRaises(IndexError):
            _ = a[9]
        self.assertEqual(a[-1], False)
        self.assertEqual(a[-5], False)
        self.assertEqual(a[-6], True)
        self.assertEqual(a[-9], True)
        with self.assertRaises(IndexError):
            _ = a[-10]

    def testSimpleSlicing(self):
        a = Bits('0xabcdef')
        self.assertEqual(a[0:4], '0xf')
        self.assertEqual(a[4:8], '0xe')
        self.assertEqual(a[:], '0xabcdef')
        self.assertEqual(a[4:], '0xabcde')
        self.assertEqual(a[-4:], '0xa')
        self.assertEqual(a[-8:-4], '0xb')
        self.assertEqual(a[:-8], '0xcdef')

    def testExtendedSlicing(self):
        a = Bits('0b100000100100100')
        self.assertEqual(a[2::3], '0b10111')

    def testAll(self):
        a = Bits('0b000111')
        self.assertTrue(a.all(1, [0, 1, 2]))
        self.assertTrue(a.all(0, [3, 4, 5]))

    def testAny(self):
        a = Bits('0b00000110')
        self.assertTrue(a.any(1, [0, 1]))
        self.assertTrue(a.any(0, [5, 6]))

    def testStartswith(self):
        a = Bits('0b0000000111')
        self.assertTrue(a.startswith('0b111'))
        self.assertFalse(a.startswith(1))
        self.assertTrue(a.startswith('0b011', start=1))
        self.assertFalse(a.startswith('0b0111', end=3))
        self.assertTrue(a.startswith('0b0111', end=4))

    def testEndsWith(self):
        a = Bits('0x1234abcd')
        self.assertTrue(a.endswith('0x123'))
        self.assertFalse(a.endswith('0xabcd'))


class Lsb0Interpretations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bitstring.set_lsb0(True)

    @classmethod
    def tearDownClass(cls):
        bitstring.set_lsb0(False)

    def testUint(self):
        a = Bits('0x01')
        self.assertEqual(a, '0b00000001')
        self.assertEqual(a.uint, 1)


class UnderscoresInLiterals(unittest.TestCase):

    def testHexCreation(self):
        a = Bits(hex='ab_cd__ef')
        self.assertEqual(a.hex, 'abcdef')
        b = Bits('0x0102_0304')
        self.assertEqual(b.uint, 0x0102_0304)

    def testBinaryCreation(self):
        a = Bits(bin='0000_0001_0010')
        self.assertEqual(a.bin, '000000010010')
        b = Bits('0b0011_1100_1111_0000')
        self.assertEqual(b.bin, '0011110011110000')
        v = 0b1010_0000
        c = Bits(uint=0b1010_0000, length=8)
        self.assertEqual(c.uint, v)

    def testOctalCreation(self):
        a = Bits(oct='0011_2233_4455_6677')
        self.assertEqual(a.uint, 0o001122334455_6677)
        b = Bits('0o123_321_123_321')
        self.assertEqual(b.uint, 0o123_321_123321)


class PrettyPrinting(unittest.TestCase):

    def testSimplestCases(self):
        a = Bits('0b101011110000')
        s = io.StringIO()
        a.pp(stream=s)
        self.assertEqual(s.getvalue(), ' 0: 10101111 0000\n')

        s = io.StringIO()
        a.pp('hex', stream=s)
        self.assertEqual(s.getvalue(), ' 0: af 0\n')

        s = io.StringIO()
        a.pp('oct', stream=s)
        self.assertEqual(s.getvalue(), ' 0: 5360\n')

    def testSmallWidth(self):
        a = Bits(20)
        s = io.StringIO()
        a.pp(stream=s, width=5)
        self.assertEqual(s.getvalue(), ' 0: 00000000\n'
                                       ' 8: 00000000\n'
                                       '16: 0000    \n')

    def testSeparator(self):
        a = Bits('0x0f0f')*9
        s = io.StringIO()
        a.pp('hex', sep='!-!', stream=s, bits_per_group=32)
        self.assertEqual(s.getvalue(), '  0: 0f0f0f0f!-!0f0f0f0f!-!0f0f0f0f!-!0f0f0f0f!-!0f0f\n')

    def testMultiLine(self):
        a = Bits(100)
        s = io.StringIO()
        a.pp(sep=None, stream=s)
        self.assertEqual(s.getvalue(), '  0: 000000000000000000000000000000000000000000000000000000000000000000000000\n'
                                       ' 72: 0000000000000000000000000000                                            \n')

    def testMultiformat(self):
        a = Bits('0b1111000011110000')
        s = io.StringIO()
        a.pp(stream=s, fmt='bin, hex')
        self.assertEqual(s.getvalue(), ' 0: 11110000 11110000   f0 f0\n')
        s = io.StringIO()
        a.pp(stream=s, fmt='hex, bin', bits_per_group=12)
        self.assertEqual(s.getvalue(), ' 0: f0f 0   111100001111 0000\n')

    def testMultiLineMultiFormat(self):
        a = Bits(int=-1, length=112)
        s = io.StringIO()
        a.pp(stream=s, fmt='bin, hex', width=42)
        self.assertEqual(s.getvalue(), '  0: 11111111 11111111 11111111   ff ff ff\n'            
                                       ' 24: 11111111 11111111 11111111   ff ff ff\n'
                                       ' 48: 11111111 11111111 11111111   ff ff ff\n'
                                       ' 72: 11111111 11111111 11111111   ff ff ff\n'
                                       ' 96: 11111111 11111111            ff ff\n')
        s = io.StringIO()
        a.pp(stream=s, fmt='bin, hex', width=41)
        self.assertEqual(s.getvalue(), '  0: 11111111 11111111   ff ff\n'            
                                       ' 16: 11111111 11111111   ff ff\n'
                                       ' 32: 11111111 11111111   ff ff\n'
                                       ' 48: 11111111 11111111   ff ff\n'
                                       ' 64: 11111111 11111111   ff ff\n'
                                       ' 80: 11111111 11111111   ff ff\n'
                                       ' 96: 11111111 11111111   ff ff\n')

    def testGroupSizeErrors(self):
        a = Bits(120)
        with self.assertRaises(ValueError):
            a.pp('hex', bits_per_group=3)
        with self.assertRaises(ValueError):
            a.pp('hex, oct', bits_per_group=4)
        with self.assertRaises(ValueError):
            a.pp(bits_per_group=-1)

    def testZeroGroupSize(self):
        a = Bits(400)
        s = io.StringIO()
        a.pp(stream=s, bits_per_group=0, show_offset=False)
        expected_output = ('0' * 80 + '\n') * 5
        self.assertEqual(s.getvalue(), expected_output)

        s = io.StringIO()
        a.pp(stream=s, bits_per_group=0, fmt='hex', show_offset=False)
        expected_output = ('0' * 80 + '\n') + ('0' * 20 + ' ' * 60 + '\n')
        self.assertEqual(s.getvalue(), expected_output)

        s = io.StringIO()
        a = Bits(uint=10, length=48)
        a.pp(stream=s, width=20, fmt='hex, oct', show_offset=False, bits_per_group=0)
        expected_output = ("000000   00000000\n"
                           "00000a   00000012\n")
        self.assertEqual(s.getvalue(), expected_output)


# class PrettyPrinting_LSB0(unittest.TestCase):
#
#     def setUp(self) -> None:
#         bitstring.set_lsb0()
#
#     def tearDown(self) -> None:
#         bitstring.set_msb0()
#
#     def test_lsb0(self):
#         a = Bits(20)
#         s = io.StringIO()
#         a.pp(stream=s, width=5)
#         self.assertEqual(s.getvalue(), '    0000 :16\n'
#                                        '00000000 : 8\n'
#                                        '00000000 : 0\n')

class Copy(unittest.TestCase):

    def testCopyMethod(self):
        s = Bits('0xc00dee')
        t = s.copy()
        self.assertEqual(s, t)
