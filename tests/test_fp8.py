from __future__ import annotations

import pytest
import sys
import array
import struct
import math
import bitstring
from bitstring import Bits, BitArray, BitStream
from bitstring.fp8 import p4binary_fmt, p3binary_fmt
from bitstring.mxfp import e4m3mxfp_fmt, e5m2mxfp_fmt
import gfloat

sys.path.insert(0, '..')


class TestFp8:

    def test_creation(self):
        a = Bits(p4binary=-14.0)
        assert a.p4binary == -14.0
        b = Bits('p3binary=3.0')
        assert b.p3binary == 3.0
        assert len(b) == 8
        c = Bits('p4binary=1000000000')
        assert c.hex == '7f'
        d = Bits('p3binary=-1e15774')
        assert d.hex == 'ff'
        e = Bits(p3binary=float('nan'))
        assert e.hex == '80'

    def test_reassignment(self):
        a = BitArray()
        a.p4binary = -0.25
        assert a.p4binary == -0.25
        a.p3binary = float('inf')
        assert a.hex == '7f'
        a.p4binary = -9000.0
        assert a.hex == 'ff'
        a.p3binary = -0.00000000001
        assert a.p3binary == 0.0

    def test_reading(self):
        a = BitStream('0x00fff')
        x = a.read('p3binary')
        assert x == 0.0
        assert a.pos == 8
        x = a.read('p4binary')
        assert x == -240.0
        assert a.pos == 16

    def test_read_list(self):
        v = [-6, -2, 0.125, 7, 10]
        a = bitstring.pack('5*p4binary', *v)
        vp = a.readlist('5*p4binary')
        assert v == vp

    def test_interpretations(self):
        a = BitArray('0x00')
        assert a.p4binary == 0.0
        assert a.p3binary == 0.0
        a += '0b1'
        with pytest.raises(bitstring.InterpretError):
            _ = a.p4binary
        with pytest.raises(bitstring.InterpretError):
            _ = a.p3binary


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


class TestCheckLUTs:

    def test_lut_int8_to_p4binary(self):
        lut_stored = p4binary_fmt.lut_int8_to_float
        assert len(lut_stored) == 256
        lut_calculated = createLUT_for_int8_to_float(4, 8)
        for i in range(len(lut_stored)):
            if lut_stored[i] != lut_calculated[i]:
                # Either they're equal or they're both nan (which doesn't compare as equal).
                assert math.isnan(lut_stored[i])
                assert math.isnan(lut_calculated[i])

    def test_lut_int8_to_p3binary(self):
        lut_stored = p3binary_fmt.lut_int8_to_float
        assert len(lut_stored) == 256
        lut_calculated = createLUT_for_int8_to_float(5, 16)
        for i in range(len(lut_stored)):
            if lut_stored[i] != lut_calculated[i]:
                # Either they're equal or they're both nan (which doesn't compare as equal).
                assert math.isnan(lut_stored[i])
                assert math.isnan(lut_calculated[i])

    def test_lut_float16_to_p4binary(self):
        lut_float16_to_p4binary = createLUT_for_float16_to_float8(p4binary_fmt.lut_int8_to_float)
        assert len(lut_float16_to_p4binary) == 65536
        assert lut_float16_to_p4binary == p4binary_fmt.lut_float16_to_float8

    def test_lut_float16_to_p3binary(self):
        lut_float16_to_p3binary = createLUT_for_float16_to_float8(p3binary_fmt.lut_int8_to_float)
        assert len(lut_float16_to_p3binary) == 65536
        assert lut_float16_to_p3binary == p3binary_fmt.lut_float16_to_float8


class TestConversionToFP8:

    def test_some143_values(self):
        zero = bitstring.Bits('0b0000 0000')
        assert p4binary_fmt.lut_int8_to_float[zero.uint] == 0.0
        max_normal = bitstring.Bits('0b0111 1111')
        assert p4binary_fmt.lut_int8_to_float[max_normal.uint] == 240.0
        max_normal_neg = bitstring.Bits('0b1111 1111')
        assert p4binary_fmt.lut_int8_to_float[max_normal_neg.uint] == -240.0
        min_normal = bitstring.Bits('0b0000 1000')
        assert p4binary_fmt.lut_int8_to_float[min_normal.uint] == 2**-7
        min_subnormal = bitstring.Bits('0b0000 0001')
        assert p4binary_fmt.lut_int8_to_float[min_subnormal.uint] == 2**-10
        max_subnormal = bitstring.Bits('0b0000 0111')
        assert p4binary_fmt.lut_int8_to_float[max_subnormal.uint] == 0.875 * 2**-7
        nan = bitstring.Bits('0b1000 0000')
        assert math.isnan(p4binary_fmt.lut_int8_to_float[nan.uint])

    def test_some152_values(self):
        zero = bitstring.Bits('0b0000 0000')
        assert p3binary_fmt.lut_int8_to_float[zero.uint] == 0.0
        max_normal = bitstring.Bits('0b0111 1111')
        assert p3binary_fmt.lut_int8_to_float[max_normal.uint] == 57344.0
        max_normal_neg = bitstring.Bits('0b1111 1111')
        assert p3binary_fmt.lut_int8_to_float[max_normal_neg.uint] == -57344.0
        min_normal = bitstring.Bits('0b0000 0100')
        assert p3binary_fmt.lut_int8_to_float[min_normal.uint] == 2**-15
        min_subnormal = bitstring.Bits('0b0000 0001')
        assert p3binary_fmt.lut_int8_to_float[min_subnormal.uint] == 0.25 * 2**-15
        max_subnormal = bitstring.Bits('0b0000 0011')
        assert p3binary_fmt.lut_int8_to_float[max_subnormal.uint] == 0.75 * 2**-15
        nan = bitstring.Bits('0b1000 0000')
        assert math.isnan(p3binary_fmt.lut_int8_to_float[nan.uint])

    def test_round_trip(self):
        # For each possible 8bit int, convert to float, then convert that float back to an int
        for fmt in [p4binary_fmt, p3binary_fmt]:
            for i in range(256):
                f = fmt.lut_int8_to_float[i]
                ip = fmt.float_to_int8(f)
                assert ip == i

    def test_float16_conversion(self):
        # Convert a float16 to a float8, then convert that to a Python float. Then convert back to a float16.
        # This value should have been rounded towards zero. Convert back to a float8 again - should be the
        # same value as before or the adjacent smaller value
        for fmt in [p4binary_fmt, p3binary_fmt]:
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
                assert f <= f16
                # But not rounded more than to the previous valid value
                assert f >= previous_value
                if f > previous_value:
                    previous_value = f

class TestComparisonWithGfloat:

    def test_p4binary_and_p3binary(self):
        for fi, lut in [(gfloat.formats.format_info_p3109(4), p4binary_fmt.lut_int8_to_float),
                        (gfloat.formats.format_info_p3109(3), p3binary_fmt.lut_int8_to_float)]:
            for i in range(256):
                f = lut[i]
                g = gfloat.decode_float(fi, i).fval
                if math.isinf(g):  # TODO: This should work once I change the float format to include inf.
                    continue
                if math.isnan(g):
                    assert math.isnan(f)
                else:
                    # The floats should be bitwise equal.
                    assert f == g

    def test_e4m3mxfp_and_e5m2mxfp(self):
        for fi, lut in [(gfloat.formats.format_info_ocp_e4m3, e4m3mxfp_fmt.lut_int_to_float),
                        (gfloat.formats.format_info_ocp_e5m2, e5m2mxfp_fmt.lut_int_to_float)]:
            for i in range(256):
                f = lut[i]
                g = gfloat.decode_float(fi, i).fval
                if math.isnan(f):
                    assert math.isnan(g)
                else:
                    assert f == g

