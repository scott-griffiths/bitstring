from __future__ import annotations

import sys
import unittest
import array
import struct
import math
import bitstring
from bitstring import Bits, BitArray, BitStream
from bitstring.fp8 import fp143_fmt, fp152_fmt

sys.path.insert(0, '..')


class Fp8(unittest.TestCase):

    def testCreation(self):
        a = Bits(float8_143=-14.0)
        self.assertEqual(a.float8_143, -14.0)
        b = Bits('float8_152=3.0')
        self.assertEqual(b.float8_152, 3.0)
        self.assertEqual(len(b), 8)
        c = Bits('float8_143=1000000000')
        self.assertEqual(c.hex, '7f')
        d = Bits('float8_152=-1e15774')
        self.assertEqual(d.hex, 'ff')
        e = Bits(float8_152=float('nan'))
        self.assertEqual(e.hex, '80')

    def testReassignment(self):
        a = BitArray()
        a.float8_143 = -0.25
        self.assertEqual(a.float8_143, -0.25)
        a.float8_152 = float('inf')
        self.assertEqual(a.hex, '7f')
        a.float8_143 = -9000.0
        self.assertEqual(a.hex, 'ff')
        a.float8_152 = -0.00000000001
        self.assertEqual(a.float8_152, 0.0)

    def testReading(self):
        a = BitStream('0x00fff')
        x = a.read('float8_152')
        self.assertEqual(x, 0.0)
        self.assertEqual(a.pos, 8)
        x = a.read('float8_143')
        self.assertEqual(x, -240.0)
        self.assertEqual(a.pos, 16)

    def testReadList(self):
        v = [-6, -2, 0.125, 7, 10]
        a = bitstring.pack('5*float8_143', *v)
        vp = a.readlist('5*float8_143')
        self.assertEqual(v, vp)


def createLUT_for_int8_to_float(exp_bits, bias) -> array.array[float]:
    """Create a LUT to convert an int in range 0-255 representing a float8 into a Python float"""
    i2f = []
    for i in range(256):
        b = BitArray(uint=i, length=8)
        sign = b[0]
        exponent = b[1:1 + exp_bits].u
        significand = b[1 + exp_bits:]
        if exponent == 0:
            significand.prepend([0])
            exponent = -bias + 1
        else:
            significand.prepend([1])
            exponent -= bias
        f = float(significand.u) / (2.0 ** (7 - exp_bits))
        f *= 2 ** exponent
        i2f.append(f if not sign else -f)
    # One special case for minus zero
    i2f[0b10000000] = float('nan')
    return array.array('f', i2f)

# Create a bytearray where the nth element is the 8 bit float corresponding to the fp16 value interpreted as n.
def createLUT_for_float16_to_float8(lut_int8_to_float) -> bytes:
    # Used to create the LUT that was compressed and stored for the fp8 code
    fp16_to_fp8 = bytearray(1 << 16)
    for i in range(1 << 16):
        b = struct.pack('>H', i)
        f, = struct.unpack('>e', b)
        fp8_i = slow_float_to_int8(lut_int8_to_float, f)
        fp16_to_fp8[i] = fp8_i
    return bytes(fp16_to_fp8)

def slow_float_to_int8(lut_int8_to_float, f: float) -> int:
    # Slow, but easier to follow than the faster version. Used only for validation.
    if f >= 0:
        for i in range(128):
            if f < lut_int8_to_float[i]:
                return i - 1
        # Clip to positive max
        return 0b01111111
    if f < 0:
        if f > lut_int8_to_float[129]:
            # Rounding upwards to zero
            return 0b00000000  # There's no negative zero so this is a special case
        for i in range(130, 256):
            if f > lut_int8_to_float[i]:
                return i - 1
        # Clip to negative max
        return 0b11111111
    # We only have one nan value
    return 0b10000000


class CheckLUTs(unittest.TestCase):

    def testLUT_int8_to_float8_143(self):
        lut_stored = fp143_fmt.lut_int8_to_float
        self.assertEqual(len(lut_stored), 256)
        lut_calculated = createLUT_for_int8_to_float(4, 8)
        for i in range(len(lut_stored)):
            if lut_stored[i] != lut_calculated[i]:
                # Either they're equal or they're both nan (which doesn't compare as equal).
                self.assertTrue(math.isnan(lut_stored[i]))
                self.assertTrue(math.isnan(lut_calculated[i]))

    def testLUT_int8_to_float8_152(self):
        lut_stored = fp152_fmt.lut_int8_to_float
        self.assertEqual(len(lut_stored), 256)
        lut_calculated = createLUT_for_int8_to_float(5, 16)
        for i in range(len(lut_stored)):
            if lut_stored[i] != lut_calculated[i]:
                # Either they're equal or they're both nan (which doesn't compare as equal).
                self.assertTrue(math.isnan(lut_stored[i]))
                self.assertTrue(math.isnan(lut_calculated[i]))

    def testLUT_float16_to_float8_143(self):
        lut_float16_to_float8_143 = createLUT_for_float16_to_float8(fp143_fmt.lut_int8_to_float)
        self.assertEqual(len(lut_float16_to_float8_143), 65536)
        self.assertEqual(lut_float16_to_float8_143, fp143_fmt.lut_float16_to_float8)

    def testLUT_float16_to_float8_152(self):
        lut_float16_to_float8_152 = createLUT_for_float16_to_float8(fp152_fmt.lut_int8_to_float)
        self.assertEqual(len(lut_float16_to_float8_152), 65536)
        self.assertEqual(lut_float16_to_float8_152, fp152_fmt.lut_float16_to_float8)


class ConversionToFP8(unittest.TestCase):

    def testSome143Values(self):
        zero = bitstring.Bits('0b0000 0000')
        self.assertEqual(fp143_fmt.lut_int8_to_float[zero.uint], 0.0)
        max_normal = bitstring.Bits('0b0111 1111')
        self.assertEqual(fp143_fmt.lut_int8_to_float[max_normal.uint], 240.0)
        max_normal_neg = bitstring.Bits('0b1111 1111')
        self.assertEqual(fp143_fmt.lut_int8_to_float[max_normal_neg.uint], -240.0)
        min_normal = bitstring.Bits('0b0000 1000')
        self.assertEqual(fp143_fmt.lut_int8_to_float[min_normal.uint], 2**-7)
        min_subnormal = bitstring.Bits('0b0000 0001')
        self.assertEqual(fp143_fmt.lut_int8_to_float[min_subnormal.uint], 2**-10)
        max_subnormal = bitstring.Bits('0b0000 0111')
        self.assertEqual(fp143_fmt.lut_int8_to_float[max_subnormal.uint], 0.875 * 2**-7)
        nan = bitstring.Bits('0b1000 0000')
        self.assertTrue(math.isnan(fp143_fmt.lut_int8_to_float[nan.uint]))

    def testSome152Values(self):
        zero = bitstring.Bits('0b0000 0000')
        self.assertEqual(fp152_fmt.lut_int8_to_float[zero.uint], 0.0)
        max_normal = bitstring.Bits('0b0111 1111')
        self.assertEqual(fp152_fmt.lut_int8_to_float[max_normal.uint], 57344.0)
        max_normal_neg = bitstring.Bits('0b1111 1111')
        self.assertEqual(fp152_fmt.lut_int8_to_float[max_normal_neg.uint], -57344.0)
        min_normal = bitstring.Bits('0b0000 0100')
        self.assertEqual(fp152_fmt.lut_int8_to_float[min_normal.uint], 2**-15)
        min_subnormal = bitstring.Bits('0b0000 0001')
        self.assertEqual(fp152_fmt.lut_int8_to_float[min_subnormal.uint], 0.25 * 2**-15)
        max_subnormal = bitstring.Bits('0b0000 0011')
        self.assertEqual(fp152_fmt.lut_int8_to_float[max_subnormal.uint], 0.75 * 2**-15)
        nan = bitstring.Bits('0b1000 0000')
        self.assertTrue(math.isnan(fp152_fmt.lut_int8_to_float[nan.uint]))

    def testRoundTrip(self):
        # For each possible 8bit int, convert to float, then convert that float back to an int
        for fmt in [fp143_fmt, fp152_fmt]:
            for i in range(256):
                f = fmt.lut_int8_to_float[i]
                ip = fmt.float_to_int8(f)
                self.assertEqual(ip, i)

    def testFloat16Conversion(self):
        # Convert a float16 to a float8, then convert that to a Python float. Then convert back to a float16.
        # This value should have been rounded towards zero. Convert back to a float8 again - should be the
        # same value as before or the adjacent smaller value
        for fmt in [fp143_fmt, fp152_fmt]:
            # Keeping sign bit == 0 so only positive numbers
            previous_value = 0.0
            for i in range(1 << 15):
                # Check that the f16 is a standard number
                b = struct.pack('>H', i)
                f16, = struct.unpack('>e', b)
                if math.isnan(f16):
                    continue
                # OK, it's an ordinary number - convert to a float8
                f8 = fmt.lut_float16_to_float8[i]
                # And convert back to a float
                f = fmt.lut_int8_to_float[f8]
                # This should have been rounded towards zero compared to the original
                self.assertTrue(f <= f16)
                # But not rounded more than to the previous valid value
                self.assertTrue(f >= previous_value)
                if f > previous_value:
                    previous_value = f



