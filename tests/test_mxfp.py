from __future__ import annotations

import sys
import math
from bitstring import BitArray, Dtype, Array

sys.path.insert(0, '..')


def test_creation_e3m2mxfp():
    x = BitArray('0b000000')
    assert x.e3m2mxfp == 0.0
    x.e3m2mxfp = 0.0
    assert x.e3m2mxfp == 0.0
    assert len(x) == 6

def test_getting_e3m2mxfp_values():
    assert BitArray('0b000000').e3m2mxfp == 0.0
    assert BitArray('0b000001').e3m2mxfp == 0.0625
    assert BitArray('0b000011').e3m2mxfp == 0.1875
    assert BitArray('0b000100').e3m2mxfp == 0.25
    assert BitArray('0b011111').e3m2mxfp == 28.0

def test_setting_e3m2mxfp_values():
    x = BitArray('0b000000')
    x.e3m2mxfp = 0.0
    assert x == '0b000000'
    x.e3m2mxfp = -0.0625
    assert x == '0b100001'
    x.e3m2mxfp = -0.1875
    assert x == '0b100011'
    x.e3m2mxfp = -0.25
    assert x == '0b100100'
    x.e3m2mxfp = -28.0
    assert x == '0b111111'

def test_getting_e2m3mxfp_values():
    assert BitArray('0b000000').e2m3mxfp == 0.0
    assert BitArray('0b000001').e2m3mxfp == 0.125
    assert BitArray('0b000111').e2m3mxfp == 0.875
    assert BitArray('0b001000').e2m3mxfp == 1.0
    assert BitArray('0b011111').e2m3mxfp == 7.5

def test_setting_e2m3mxfp_values():
    x = BitArray('0b000000')
    x.e2m3mxfp = 0.0
    assert x == '0b000000'
    x.e2m3mxfp = -0.125
    assert x == '0b100001'
    x.e2m3mxfp = -0.875
    assert x == '0b100111'
    x.e2m3mxfp = -1.0
    assert x == '0b101000'
    x.e2m3mxfp = -7.5
    assert x == '0b111111'

def test_getting_e2m1mxfp_values():
    assert BitArray('0b0000').e2m1mxfp == 0.0
    assert BitArray('0b0001').e2m1mxfp == 0.5
    assert BitArray('0b0010').e2m1mxfp == 1.0
    assert BitArray('0b0111').e2m1mxfp == 6.0

def test_setting_e2m1mxfp_values():
    x = BitArray('0b0000')
    x.e2m1mxfp = 0.0
    assert x == '0b0000'
    x.e2m1mxfp = -0.5
    assert x == '0b1001'
    x.e2m1mxfp = -1.0
    assert x == '0b1010'
    x.e2m1mxfp = -6.0
    assert x == '0b1111'


def test_e8m0mxfp_value():
    x = BitArray('0x00')
    assert x.e8m0mxfp == 2.0 ** -127
    x.uint = 127
    assert x.e8m0mxfp == 1.0
    x.uint = 254
    assert x.e8m0mxfp == 2.0 ** 127
    x.bin = '11111111'
    assert math.isnan(x.e8m0mxfp)

def test_getting_mxint_values():
    assert BitArray('0b00000000').mxint == 0.0
    assert BitArray('0b00000001').mxint == 1 * 2 ** -6
    assert BitArray('0b00000011').mxint == 3 * 2 ** -6
    assert BitArray('0b01111111').mxint == 127 * 2 ** -6
    assert BitArray('0b10000000').mxint == -2.0
    assert BitArray('0b11111111').mxint == -1 * 2 ** -6
    assert BitArray('0b11111110').mxint == -2 * 2 ** -6
    assert BitArray('0b10000001').mxint == -127 * 2 ** -6

def test_setting_mxint_values():
    x = BitArray('0b00000000')
    x.mxint = 0.0
    assert x == '0b00000000'
    x.mxint = 1 * 2 ** -6
    assert x == '0b00000001'
    x.mxint = -1 * 2 ** -6
    assert x == '0b11111111'


def test_scaled_array():
    sa = Array(Dtype('uint8', scale=2),[100, 200, 300, 400, 500])
    assert sa.dtype.scale == 2
    assert sa[0] == 100
    assert sa[:] == [100, 200, 300, 400, 500]
    sa.dtype = Dtype('uint8', scale=4)
    assert sa.dtype.scale == 4
    assert sa[0] == 200
    sa.dtype = Dtype('uint8', scale=0.25)
    assert sa.tolist() == [12.5, 25.0, 37.5, 50.0, 62.5]


def test_setting_scaled_array():
    sa = Array('e3m2mxfp')
    sa.append(4.0)
    assert sa[0] == 4.0
    assert sa.dtype.scale is None
    sa.dtype = Dtype('e3m2mxfp', scale = 0.5)
    assert sa[0] == 2.0
    sa.append(6.0)
    assert sa[1] == 6.0
    assert sa[:] == [2.0, 6.0]
    sa *= 2
    assert sa[:] == [4.0, 12.0]
    sa[:] = [0.0, 0.5, 1.0]
    assert sa[:] == [0.0, 0.5, 1.0]
    sa.dtype = Dtype('e3m2mxfp', scale = 1)
    assert sa[:] == [0.0, 1.0, 2.0]

def test_multiple_scaled_arrays():
    d = bytes(b'hello_everyone!')
    s1 = Array(Dtype('e2m1mxfp', scale=1), d)
    s2 = Array(Dtype('e2m1mxfp', scale=2**10), d)
    s3 = Array(Dtype('e2m1mxfp', scale=2**-10), d)
    assert s1.dtype.scale == 1
    assert s2.dtype.scale == 2**10
    assert s3.dtype.scale == 2**-10
    assert s1[0] * 2**10 == s2[0]
    assert s1[0] * 2**-10 == s3[0]

# def test_multiple_scaled_arrays2():
#     b = BitArray('0b011111')
#     assert b.e3m2mxfp == 28.0
#     s1 = ScaledArray('e3m2mxfp', [28], scale=0)
#     assert s1[0] == 28.0
#     assert b.e3m2mxfp == 28.0
#     s2 = ScaledArray('e3m2mxfp', [28], scale=0)
#     s2.scale = 4
#     assert s1[0] == 28.0
#     assert s2[0] == 28.0 * 2 ** 4
#     assert b.e3m2mxfp == 28.0

def test_setting_from_outside_range():
    b = BitArray(e2m1mxfp=0.0)
    b.e2m1mxfp = 6.0
    assert b.e2m1mxfp == 6.0
    b.e2m1mxfp = 7.0
    assert b.e2m1mxfp == 6.0
    b.e2m1mxfp = 10000000000.0
    assert b.e2m1mxfp == 6.0
    s = Array('e2m1mxfp', [-1000.0, 6.0, 7.0, 10000.0])
    assert s.tolist() == [-6.0, 6.0, 6.0, 6.0]
    s = Array(Dtype('e2m1mxfp', scale=2), [-1000.0, 6.0, 7.0, 10000000000.0])
    x = s.tolist()
    assert x == [-12.0, 6.0, 6.0, 12.0]

# def test_ops():
#     s = ScaledArray('e8m0mxfp', [0.5, 1.0, 2.0, 4.0, 8.0], scale=2)
#     t = s * 2
#     assert type(t) is ScaledArray
#     assert t.tolist() == [1.0, 2.0, 4.0, 8.0, 16.0]
#     assert t.scale == 2
#
#

