from __future__ import annotations

import pytest
import sys
import array
import struct
import math
import bitstring
from bitstring import Bits, BitArray, BitStream, Array, Dtype
from bitstring.fp8 import e4m3float_fmt, e5m2float_fmt
from hypothesis import given
import hypothesis.strategies as st

sys.path.insert(0, '..')


def test_creation_e3m2float():
    x = BitArray('0b000000')
    assert x.e3m2float == 0.0
    x.e3m2float = 0.0
    assert x.e3m2float == 0.0
    assert len(x) == 6

def test_getting_e3m2float_values():
    assert BitArray('0b000000').e3m2float == 0.0
    assert BitArray('0b000001').e3m2float == 0.0625
    assert BitArray('0b000011').e3m2float == 0.1875
    assert BitArray('0b000100').e3m2float == 0.25
    assert BitArray('0b011111').e3m2float == 28.0

def test_setting_e3m2float_values():
    x = BitArray('0b000000')
    x.e3m2float = 0.0
    assert x.e3m2float == 0.0
    x.e3m2float = 0.0625
    assert x.e3m2float == 0.0625
    x.e3m2float = 0.1875
    assert x.e3m2float == 0.1875
    x.e3m2float = 0.25
    assert x.e3m2float == 0.25
    x.e3m2float = 28.0
    assert x.e3m2float == 28.0


def createLUT_for_int6_to_float(exp_bits, mantissa_bits, bias) -> array.array[float]:
    """Create a LUT to convert an int in range 0-255 representing a float8 into a Python float"""
    i2f = []
    for i in range(64):
        b = BitArray(uint=i, length=6)
        sign = b[0]
        exponent = b[1:1 + exp_bits].u
        significand = b[1 + exp_bits:]
        if exponent == 0:
            significand.prepend([0])
            exponent = -bias + 1
        else:
            significand.prepend([1])
            exponent -= bias
        f = float(significand.u) / (2.0 ** mantissa_bits)
        f *= 2 ** exponent
        i2f.append(f if not sign else -f)
    # One special case for minus zero
    # i2f[0b10000000] = float('nan')
    return array.array('f', i2f)

def test_lut_int6_to_e3m2float():
    lut_calculated = createLUT_for_int6_to_float(3, 2, 3)
    assert lut_calculated[0b000000] == 0.0
    assert lut_calculated[0b100100] == -0.25
    assert lut_calculated[0b000001] == 0.0625
    assert lut_calculated[0b111111] == -28.0
    assert lut_calculated[0b000011] == 0.1875



