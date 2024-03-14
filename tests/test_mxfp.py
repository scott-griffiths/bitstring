from __future__ import annotations

import sys
import math
from bitstring import BitArray, Dtype, Array, options
from bitstring.mxfp import createLUT_for_int_to_float, createLUT_for_float16_to_mxfp
import pytest
from bitstring.luts import mxfp_luts_compressed
import zlib
import struct

sys.path.insert(0, '..')


def test_creation_e3m2mxfp():
    x = BitArray('0b000000')
    assert x.e3m2mxfp == 0.0
    x.e3m2mxfp = 0.0
    assert x.e3m2mxfp == 0.0
    assert len(x) == 6

def test_getting_e4m3mxfp_values():
    assert BitArray('0b00000000').e4m3mxfp == 0.0
    assert BitArray('0b01111110').e4m3mxfp == 448.0
    assert BitArray('0b11111110').e4m3mxfp == -448.0
    assert BitArray('0b00001000').e4m3mxfp == 2**-6
    assert math.isnan(BitArray('0b01111111').e4m3mxfp)
    assert math.isnan(BitArray('0b11111111').e4m3mxfp)

def test_setting_e4m3mxfp_values():
    x = BitArray('0b00000000')
    x.e4m3mxfp = 0.0
    assert x == '0b00000000'
    x.e4m3mxfp = -(2 ** -9)
    assert x == '0b10000001'
    x.e4m3mxfp = 99999
    assert x.e4m3mxfp == 448.0

def test_getting_e5m2mxfp_values():
    assert BitArray('0b00000000').e5m2mxfp == 0.0
    assert BitArray('0b01111011').e5m2mxfp == 57344
    for b in ['0b01111101', '0b11111101', '0b01111110', '0b11111110', '0b01111111', '0b11111111']:
        assert math.isnan(BitArray(b).e5m2mxfp)
    assert BitArray('0b01111100').e5m2mxfp == float('inf')
    assert BitArray('0b11111100').e5m2mxfp == float('-inf')
    assert BitArray('0b00000001').e5m2mxfp == 2 ** -16
    assert BitArray('0b00000100').e5m2mxfp == 2 ** -14

def test_setting_e5m2mxfp_values():
    x = BitArray('0b00000000')
    x.e5m2mxfp = 0.0
    assert x == '0b00000000'
    x.e5m2mxfp = -(2 ** -16)
    assert x == '0b10000001'
    x.e5m2mxfp = 99999
    assert x.e5m2mxfp == 57344.0


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

def test_multiple_scaled_arrays2():
    b = BitArray('0b011111')
    assert b.e3m2mxfp == 28.0
    s1 = Array('e3m2mxfp', [28])
    assert s1[0] == 28.0
    assert b.e3m2mxfp == 28.0
    s2 = Array('e3m2mxfp', [28])
    s2.dtype = Dtype('e3m2mxfp', scale=2**4)
    assert s1[0] == 28.0
    assert s2[0] == 28.0 * 2 ** 4
    assert b.e3m2mxfp == 28.0

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
    assert x == [-12.0, 6.0, 8.0, 12.0]

def test_ops():
    s = Array(Dtype('e8m0mxfp', scale=2**2), [0.5, 1.0, 2.0, 4.0, 8.0])
    t = s * 2
    assert type(t) is Array
    assert t.tolist() == [1.0, 2.0, 4.0, 8.0, 16.0]
    assert t.dtype.scale == 2 ** 2

def test_auto_scaling():
    f = [0.0, 100.0, 256.0, -150.0]
    for dtype in ['e3m2mxfp', 'e2m3mxfp', 'e2m1mxfp', 'mxint8', 'p3binary', 'p4binary']:
        d = Dtype(dtype, scale='auto')
        a = Array(d, f)
        assert a[2] == 256.0

def test_auto_scaling2():
    some_floats = [-4, 100.0, -9999, 0.5, 42, 666]
    a = Array(Dtype('float16', scale='auto'), some_floats)
    assert a[2] == -10000.0
    a = Array(Dtype('e2m1mxfp', scale='auto'), [1e200])
    assert a.dtype.scale == 2 ** 127
    a = Array(Dtype('e2m1mxfp', scale='auto'), [1e-200])
    assert a.dtype.scale == 2 ** -127
    a = Array(Dtype('e2m1mxfp', scale='auto'), [0, 0, 0, 0])
    assert a.dtype.scale == 1


def test_scaled_array_errors():
    with pytest.raises(ValueError):
        _ = Array(Dtype('bfloat', scale='auto'), [0.0, 100.0, 256.0, -150.0])
    with pytest.raises(ValueError):
        _ = Array(Dtype('uint9', scale='auto'), [0.0, 100.0, 256.0, -150.0])
    with pytest.raises(ValueError):
        _ = Dtype('e3m2mxfp', scale=0)
    with pytest.raises(TypeError):
        _ = Array(Dtype('e3m2mxfp', scale='auto'), b'hello')
    with pytest.raises(TypeError):
        _ = Array(Dtype('e3m2mxfp', scale='auto'), 100)


def test_changing_to_auto_scaled_array():
    a = Array('int16', [0, 2003, -43, 104, 6, 1, 99])
    with pytest.raises(ValueError):
        a.dtype = Dtype('e3m2mxfp', scale='auto')

def test_conversion_to_e8m0():
    x = BitArray(e8m0mxfp=1.0)
    assert x.e8m0mxfp == 1.0
    x = BitArray(e8m0mxfp=2**127)
    assert x.e8m0mxfp == 2**127
    x = BitArray(e8m0mxfp=2**-127)
    assert x.e8m0mxfp == 2**-127
    x = BitArray(e8m0mxfp=float('nan'))
    assert math.isnan(x.e8m0mxfp)
    with pytest.raises(ValueError):
        _ = BitArray(e8m0mxfp=2**128)
    with pytest.raises(ValueError):
        _ = BitArray(e8m0mxfp=-2**128)
    with pytest.raises(ValueError):
        _ = BitArray(e8m0mxfp=0.0)
    with pytest.raises(ValueError):
        _ = BitArray(e8m0mxfp=1.1)


def test_rounding_to_even():
    # When rounding to even, the value chosen when two are equidistant should end in a zero bit.
    x = BitArray(e4m3mxfp=21.0)
    assert x.e4m3mxfp == 20.0
    a = BitArray(e4m3mxfp=20.0).bin
    b = BitArray(e4m3mxfp=22.0).bin
    assert a[:-1] == b[:-1]
    assert a[-1] == '0'
    assert b[-1] == '1'
    x = BitArray(e4m3mxfp=22.0)
    assert x.e4m3mxfp == 22.0
    x = BitArray(e4m3mxfp=23.0)
    assert x.e4m3mxfp == 24.0
    x = BitArray(e4m3mxfp=24.0)
    assert x.e4m3mxfp == 24.0

    x = BitArray(e4m3mxfp=-50)  # Midway between -48 and -52
    assert x.e4m3mxfp == -48.0  # Rounds towards zero
    assert x.bin[-1] == '0'
    x = BitArray(e4m3mxfp=-54)  # Midway between -52 and -56
    assert x.e4m3mxfp == -56.0  # Rounds away from zero
    assert x.bin[-1] == '0'

def test_lut_are_consistent():
    for (exp_bits, mantissa_bits, bias) in [(2, 1, 1), (2, 3, 1), (3, 2, 3), (4, 3, 7), (5, 2, 15)]:
        # First calculate the LUT the long way
        lut_int_to_float = createLUT_for_int_to_float(exp_bits, mantissa_bits, bias)
        lut_float16_to_mxfp = createLUT_for_float16_to_mxfp(lut_int_to_float, exp_bits, mantissa_bits, 'saturate')

        # Then get the LUTs from the compressed data
        int_to_float_compressed, float16_to_mxfp_compressed = mxfp_luts_compressed[(exp_bits, mantissa_bits, bias, 'saturate')]
        lut_float16_to_mxfp2 = zlib.decompress(float16_to_mxfp_compressed)
        dec = zlib.decompress(int_to_float_compressed)
        lut_int_to_float2 = struct.unpack(f'<{len(dec) // 4}f', dec)

        # Then compare them
        for i in range(len(lut_int_to_float)):
            if math.isnan(lut_int_to_float[i]):
                assert math.isnan(lut_int_to_float2[i])
            else:
                assert lut_int_to_float[i] == lut_int_to_float2[i]
        assert lut_float16_to_mxfp == lut_float16_to_mxfp2

def test_conversion_from_nan():
    x = BitArray(e4m3mxfp=float('nan'))
    assert x == '0b11111111'
    x = BitArray(e5m2mxfp=float('nan'))
    assert x == '0b11111111'
    with pytest.raises(ValueError):
        _ = BitArray(e3m2mxfp=float('nan'))
    with pytest.raises(ValueError):
        _ = BitArray(e2m3mxfp=float('nan'))
    with pytest.raises(ValueError):
        _ = BitArray(e2m1mxfp=float('nan'))
    with pytest.raises(ValueError):
        _ = BitArray(mxint=float('nan'))
    x = BitArray(e8m0mxfp=float('nan'))
    assert x == '0b11111111'

def test_conversion_from_inf():
    x = BitArray(e3m2mxfp=float('inf'))
    assert x.e3m2mxfp == 28.0
    x = BitArray(e3m2mxfp=float('-inf'))
    assert x.e3m2mxfp == -28.0

    x = BitArray(e2m3mxfp=float('inf'))
    assert x.e2m3mxfp == 7.5
    x = BitArray(e2m3mxfp=float('-inf'))
    assert x.e2m3mxfp == -7.5

    x = BitArray(e2m1mxfp=float('inf'))
    assert x.e2m1mxfp == 6.0
    x = BitArray(e2m1mxfp=float('-inf'))
    assert x.e2m1mxfp == -6.0

    x = BitArray(mxint=float('inf'))
    assert x.mxint == 1.984375
    x = BitArray(mxint=float('-inf'))
    assert x.mxint == -2.0

    with pytest.raises(ValueError):
        _ = BitArray(e8m0mxfp=float('inf'))
    with pytest.raises(ValueError):
        _ = BitArray(e8m0mxfp=float('-inf'))

def test_conversion_to_8bit_with_saturate():
    assert options.mxfp_overflow == 'saturate'
    x = BitArray(e5m2mxfp=float('inf'))
    assert x.e5m2mxfp == 57344.0
    x = BitArray(e5m2mxfp=float('-inf'))
    assert x.e5m2mxfp == -57344.0

    x = BitArray(e5m2mxfp=1e10)
    assert x.e5m2mxfp == 57344.0
    x = BitArray(e5m2mxfp=-1e10)
    assert x.e5m2mxfp == -57344.0

    x = BitArray(e4m3mxfp=float('inf'))
    assert x.e4m3mxfp == 448.0
    x = BitArray(e4m3mxfp=float('-inf'))
    assert x.e4m3mxfp == -448.0

    x = BitArray(e4m3mxfp=1e10)
    assert x.e4m3mxfp == 448.0
    x = BitArray(e4m3mxfp=-1e10)
    assert x.e4m3mxfp == -448.0

@pytest.fixture
def switch_to_overflow():
    options.mxfp_overflow = 'overflow'
    yield
    options.mxfp_overflow = 'saturate'

@pytest.mark.usefixtures('switch_to_overflow')
def test_conversion_to_8bit_with_overflow():
    x = BitArray(e5m2mxfp=float('inf'))
    assert x.e5m2mxfp == float('inf')
    x = BitArray(e5m2mxfp=float('-inf'))
    assert x.e5m2mxfp == float('-inf')

    x = BitArray(e5m2mxfp=1e10)
    assert x.e5m2mxfp == float('inf')
    x = BitArray(e5m2mxfp=-1e10)
    assert x.e5m2mxfp == float('-inf')

    x = BitArray(e4m3mxfp=float('inf'))
    assert math.isnan(x.e4m3mxfp)
    x = BitArray(e4m3mxfp=float('-inf'))
    assert math.isnan(x.e4m3mxfp)

    x = BitArray(e4m3mxfp=1e10)
    assert math.isnan(x.e4m3mxfp)
    x = BitArray(e4m3mxfp=-1e10)
    assert math.isnan(x.e4m3mxfp)
