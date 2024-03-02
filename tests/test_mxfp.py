from __future__ import annotations

import pytest
import sys
import array
import struct
import math
import bitstring
from bitstring import Bits, BitArray, BitStream, Array, Dtype, ScaledArray
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
    assert x == '0b000000'
    x.e3m2float = -0.0625
    assert x == '0b100001'
    x.e3m2float = -0.1875
    assert x == '0b100011'
    x.e3m2float = -0.25
    assert x == '0b100100'
    x.e3m2float = -28.0
    assert x == '0b111111'

def test_getting_e2m3float_values():
    assert BitArray('0b000000').e2m3float == 0.0
    assert BitArray('0b000001').e2m3float == 0.125
    assert BitArray('0b000111').e2m3float == 0.875
    assert BitArray('0b001000').e2m3float == 1.0
    assert BitArray('0b011111').e2m3float == 7.5

def test_setting_e2m3float_values():
    x = BitArray('0b000000')
    x.e2m3float = 0.0
    assert x == '0b000000'
    x.e2m3float = -0.125
    assert x == '0b100001'
    x.e2m3float = -0.875
    assert x == '0b100111'
    x.e2m3float = -1.0
    assert x == '0b101000'
    x.e2m3float = -7.5
    assert x == '0b111111'

def test_getting_e2m1float_values():
    assert BitArray('0b0000').e2m1float == 0.0
    assert BitArray('0b0001').e2m1float == 0.5
    assert BitArray('0b0010').e2m1float == 1.0
    assert BitArray('0b0111').e2m1float == 6.0

def test_setting_e2m1float_values():
    x = BitArray('0b0000')
    x.e2m1float = 0.0
    assert x == '0b0000'
    x.e2m1float = -0.5
    assert x == '0b1001'
    x.e2m1float = -1.0
    assert x == '0b1010'
    x.e2m1float = -6.0
    assert x == '0b1111'


def test_e8m0float_value():
    x = BitArray('0x00')
    x.e8m0float = -127
    assert x == '0b00000000'
    x.e8m0float = 0
    assert x == '0b01111111'
    x.e8m0float = 127
    assert x == '0b11111110'
    x.e8m0float = float('nan')
    assert x == '0b11111111'
    assert math.isnan(x.e8m0float)


def test_scaled_array():
    sa = ScaledArray('uint8', 1, [100, 200, 300, 400, 500])
    assert sa.scale == 1
    assert sa[0] == 100
    assert sa[:] == [100, 200, 300, 400, 500]
    sa.scale = 2
    assert sa.scale == 2
    assert sa[0] == 200
    sa.scale = -2
    assert sa.tolist() == [12.5, 25.0, 37.5, 50.0, 62.5]



