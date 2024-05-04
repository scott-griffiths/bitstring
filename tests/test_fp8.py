from __future__ import annotations

import pytest
import sys
import array
import math
import bitstring
from bitstring import Bits, BitArray, BitStream, Dtype
from bitstring.fp8 import p4binary_fmt, p3binary_fmt
from bitstring.mxfp import e4m3mxfp_saturate_fmt, e5m2mxfp_saturate_fmt, e3m2mxfp_fmt, e2m3mxfp_fmt, e2m1mxfp_fmt
from gfloat.formats import (format_info_ocp_e4m3, format_info_ocp_e5m2, format_info_p3109, format_info_ocp_e3m2,
                            format_info_ocp_e2m3, format_info_ocp_e2m1, format_info_ocp_int8, format_info_ocp_e8m0)
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
        assert math.isnan(e.p3binary)
        assert e.hex == '80'

    def test_reassignment(self):
        a = BitArray()
        a.p4binary = -0.25
        assert a.p4binary == -0.25
        a.p3binary = float('inf')
        assert a.hex == '7f'
        assert a.p4binary == float('inf')
        a.p4binary = -9000.0
        assert a.p4binary == float('-inf')
        a.p3binary = -0.00000000001
        assert a.p3binary == 0.0

    def test_reading(self):
        a = BitStream('0x00fff')
        x = a.read('p3binary')
        assert x == 0.0
        assert a.pos == 8
        x = a.read('p4binary')
        assert x == -float('inf')
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
    # and for positive and negative infinity
    i2f[0b01111111] = float('inf')
    i2f[0b11111111] = float('-inf')
    return array.array('f', i2f)


class TestCheckLUTs:

    def test_lut_int8_to_p4binary(self):
        lut_stored = p4binary_fmt.lut_binary8_to_float
        assert len(lut_stored) == 256
        lut_calculated = createLUT_for_int8_to_float(4, 8)
        for i in range(len(lut_stored)):
            if lut_stored[i] != lut_calculated[i]:
                # Either they're equal or they're both nan (which doesn't compare as equal).
                assert math.isnan(lut_stored[i])
                assert math.isnan(lut_calculated[i])

    def test_lut_int8_to_p3binary(self):
        lut_stored = p3binary_fmt.lut_binary8_to_float
        assert len(lut_stored) == 256
        lut_calculated = createLUT_for_int8_to_float(5, 16)
        for i in range(len(lut_stored)):
            if lut_stored[i] != lut_calculated[i]:
                # Either they're equal or they're both nan (which doesn't compare as equal).
                assert math.isnan(lut_stored[i])
                assert math.isnan(lut_calculated[i])

# def test_strange_failure():
#
#     x = (b'x\x01\xed\xdd\x05\xba\x96\x05\x00\x05\xe1\x9f\xee\x06\xe9FZA\xa4\xbb'
#          b'\xbb;\xa4SB\xba\xeb\xd2\xdd\x8dt\x97\x92J(\xa14\xa2\x84\x92\x8a\xa4\x82\xd2'
#          b'\x1d\x12.c\x9e\xcb7\xef\x0e\xcel\xe0\x84B\xb2\x80\x05,`\x01\x0bX\xc0\x02'
#          b'\x16\xb0\x80\x05,`\x01\x0bX\xc0\x02\x16\xb0\x80\x05\xde\xd7\x02\x11d'
#          b'\x01\x0b\x04\xb6@D\x05\xba@$\x05\xba@\xe4\x80\x8b\x12pQ\x03.Z\xc0E'
#          b'\x87\xc5\x80\xc5\x84\xc5\x82\xc5\x86\xc5\x81\xc5\x85\xc5\x83\xc5\x87%\x80%'
#          b'\x84%\x82%\x86%\x81}\x00K\nK\x06K\x0eK\x01K\tK\x05K\rK\x03K\x0bK'
#          b'\x07K\x0f\xcb\x00\xcb\x08\xcb\x04\xfb\x10\x96\x19\x96\x05\x96\x15\x96\r\x96'
#          b"\x1d\x96\x03\x96\x13\xf6\x11\xeccX.Xn\xd8'\xb0<\xb0Oaya\xf9`\xf9a\x05`"
#          b'\x05a\x85`\x85aE`Ea\xc5`\xc5a%`%a\xa5`\xa5ae`ea\xe5`\xe5a\x15`\x15a\x95`'
#          b'\x95aU`Ua\xd5`\xd5a5`5a\xb5`\xb5au`ua\xf5`\xf5a\r`\ra\x8d`\x8daM`'
#          b'\x9f\xc1\x9a\xc2\x9a\xc1\x9a\xc3Z\xc0Z\xc2Z\xc1Z\xc3\xda\xc0\xda\xc2'
#          b'\xda\xc1\xda\xc3:\xc0>\x87u\x84u\x82u\x86u\x81}\x01\xeb\n\xeb\x06\xeb\x0e'
#          b'\xeb\x01\xeb\t\xeb\x05\xeb\r\xeb\x03\xeb\x0b\xeb\x07\xeb\x0f\x1b\x00\x1b\x08'
#          b'\x1b\x04\x1b\x0c\x1b"\x0bX\xc0\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0'
#          b'\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0\x02\x16\xb0\x80\x05,`\x01\x0b'
#          b'X\xc0\x02\x16\xb0\x80\x05,\x10\xce\x0b\x0c\r\x93\x05,\x10\xd4\x02\xef'
#          b'\xeb\xaf\x99\xbb,`\x01\x0bX\xc0\x02\x16\xb0\x80\x05,`\x01\x0bX'
#          b'\xc0\x02\x16\xb0\x80\x05,`\x81Ph\x98,`\x81\xc0\x16\x18\xae@\x17\x18\xa1@'
#          b'\x17\x18\x19p\xa3\x02nt\xc0\x8d\t\xb8\xb1\xb0q\xb0\xf1\xb0\t\xb0'
#          b'\x89\xb0I\xb0\xc9\xb0)\xb0\xa9\xb0i\xb0\xe9\xb0\x19\xb0\x99\xb0Y\xb0'
#          b'\xd9\xb09\xb0\xb9\xb0y\xb0\xf9\xb0/a\x0b`\x0ba\x8b`\x8baK`Ka\xcb`\xcba+`+a'
#          b'\xab`\xabak`ka\xeb`\xeba\x1b`_\xc1\xbe\x86m\x84m\x82m\x86m\x81m\x85'
#          b'm\x83}\x03\xfb\x16\xb6\x1d\xb6\x03\xb6\x13\xb6\x0b\xf6\x1d\xec{\xd8n'
#          b'\xd8\x1e\xd8^\xd8>\xd8\x0f\xb0\x1fa\xfba\x07`\x07a\x87`\x87aG`Ga\xc7`?'
#          b'\xc1\x8e\xc3~\x86\xfd\x02;\x01;\t;\x05;\r\xfb\x15\xf6\x1b\xec\x0c\xec,\xec'
#          b'\x1c\xec<\xec\x02\xec"\xecw\xd8\x1f\xb0K\xb0?a\x97aW`Wa\xd7`\xd7a7`'
#          b'\x7f\xc1\xfe\x86\xdd\x84\xdd\x82\xfd\x03\xfb\x17v\x1bv\x07v\x17v\x0f'
#          b'v\x1f\xf6\x00\xf6\x10\xf6\x08\xf6\x18\xf6\x04\xf6\x14\xf6\x0c'
#          b'\xf6\x1c\xf6\x02\xf6\x12\xf6\n\xf6\x1f\xec5\xec\r\xec\xad,`\x01\x0b'
#          b'X\xc0\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0'
#          b'\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0\x02\x16\xb0@8/\xf0.\xa8\xc7\xe7\xee\xb6'
#          b'\x80\x05\xc2\xfe\x07j_rx')
#
#     y = (b'x\x01\xed\xdde\x9a\x90\x05\x00Ea\x1aIQZ\x1a\xa4\x94\x06\xa5A:\x04\xa4'
#          b'T\xba\x1b\xe9n\x90\x90.%$\xa5KP\x91\xeeV\xba\xbb\xbb\xbb\x9bE\xcc\x8f'
#          b'\xf3\xcc|\xe7\xdd\xc1=\x1b\xb8\xe1\xc2\xc9\x02\x16\xb0\x80\x05,`\x01'
#          b'\x0bX\xc0\x02\x16\xb0\x80\x05,`\x810_ \xbc,`\x01\x0bX \x88\x05"\xc8\x02A.'
#          b'\x10QA.\x10Il\x81\xc8\xc1\x16%\xe8\xa2\x06\xdbG\xa1]4VtZ\x0cVLZ,Vl\xda\xc7'
#          b'\xac8\xb4OX\x9f\xd2\xe2\xb2\xe2\xd1\xe2\xb3\x12\xd0\x12\xb2\x12\xd1\x12'
#          b'\xb3>\xa3%a%\xa5%c%\xa7\xa5`\xa5\xa4\xa5b\xa5\xa6\xa5a}NK\xcbJGK'
#          b"\xcf\xca@\xcb\xc8\xfa\x82\xf6%+\x13-3+\x0b-++\x1b-;+\x07-'+\x17\xed"
#          b'+\xd6\xd7\xb4\xdc\xac<\xb4\xbc\xac|\xb4\xfc\xac\x02\xb4\x82\xacB\xb4'
#          b'\xc2\xacohEXEi\xc5X\xc5i%X%i\xa5X\xa5ieXei\xdf\xb2\xca\xd1\xca\xb3*\xd0'
#          b'\xbecU\xa4UbU\xa6UaU\xa5}\xcf\xfa\x81\xf6#\xab\x1a\xad:\xab\x06\xad&\xab\x16'
#          b'\xad6\xab\x0e\xad.\xab\x1e\xad>\xab\x01\xad!\xab\x11\xad1\xab\t\xad)\xab\x19'
#          b"\xad9\xab\x05\xad%\xeb'Z+VkZ\x1bV[Z;V{Z\x07VGZ'VgZ\x17VWZ7VwZ\x0fVOZ/V\xef"
#          b'\x90\xea#\x0bX\xc0\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0\x02\x16\xb0\x80\x05,`'
#          b'\x01\x0bX\xc0\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0\x02\x16\xb0\x80\x05'
#          b',\x10\xca\x0b\xf4\x95\x05,\x10\xd4\x02a\xfe\xdf\xd0\x81\x16\xb0\x80\x05'
#          b',`\x01\x0bX\xc0\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0\x02\x16\x08p\x81~\n'
#          b't\x81\x9fe\x81 \x17\xe8\xaf \x17\x18 \xb6\xc0\xc0`\x1b\x14t\xbf\x04\xdb\xe0'
#          b'\xd0n\x08k(m\x18k8m\x04k$m\x14k4m\x0ck,\xedW\xd6o\xb4q\xac\xf1\xb4\t\xac'
#          b'\x89\xb4\xdfY\x93h\x93YShSY\xd3h\xd3Y\x7f\xd0f\xb0f\xd2f\xb1f\xd3\xe6\xb0'
#          b'\xe6\xd2\xe6\xb1\xe6\xd3\x16\xb0\x16\xd2\x16\xb1\xfe\xa4-f-\xa1\xfd\xc5'
#          b'\xfa\x9b\xf6\x0fk)\xed_\xd62\xdar\xd6\n\xdaJ\xd6*\xdaj\xd6\x1a\xdaZ'
#          b'\xd6:\xdaz\xd6\x06\xdaF\xd6&\xdaf\xd6\x16\xdaV\xd66\xdav\xd6\x0e\xda\x7f'
#          b"\xac\xffi;Y\xbbh\xbbY{h{Y\xfbh\xfbY\x07h\x07Y\x87h\x87YGhGY\xc7h\xc7Y'h'"
#          b'Y\xa7h\xa7YghgY\xe7h\xe7Y\x17h\x17Y\x97h\x97YWhWY\xd7h\xd7Y7h7Y\xb7h\xb7Ywhw'
#          b'Y\xf7h\xf7Y\x0fh\x0fY\x8fh\x8fYOhOY\xcfh\xcfY/h/Y\xafh\xafYohoY\xefB\xea'
#          b'\xbd,`\x01\x0bX\xc0\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0\x02\x16\xb0\x80\x05,'
#          b'`\x01\x0bX\xc0\x02\x16\xb0\x80\x05,`\x01\x0bX\xc0\x02\x16\xb0@(/\x10\xd4'
#          b'\xe3sw[\xc0\x02}?\x00\xacO\xfe\xf9')
#
#     import zlib
#     x = zlib.decompress(x)
#     y = zlib.decompress(y)
#     assert len(x) == len(y) == 65536
#     assert x == y


class TestConversionToFP8:

    def test_some143_values(self):
        zero = bitstring.Bits('0b0000 0000')
        assert p4binary_fmt.lut_binary8_to_float[zero.uint] == 0.0
        max_normal = bitstring.Bits('0b0111 1110')
        assert p4binary_fmt.lut_binary8_to_float[max_normal.uint] == 224.0
        max_normal_neg = bitstring.Bits('0b1111 1110')
        assert p4binary_fmt.lut_binary8_to_float[max_normal_neg.uint] == -224.0
        min_normal = bitstring.Bits('0b0000 1000')
        assert p4binary_fmt.lut_binary8_to_float[min_normal.uint] == 2**-7
        min_subnormal = bitstring.Bits('0b0000 0001')
        assert p4binary_fmt.lut_binary8_to_float[min_subnormal.uint] == 2**-10
        max_subnormal = bitstring.Bits('0b0000 0111')
        assert p4binary_fmt.lut_binary8_to_float[max_subnormal.uint] == 0.875 * 2**-7
        nan = bitstring.Bits('0b1000 0000')
        assert math.isnan(p4binary_fmt.lut_binary8_to_float[nan.uint])

    def test_some152_values(self):
        zero = bitstring.Bits('0b0000 0000')
        assert p3binary_fmt.lut_binary8_to_float[zero.uint] == 0.0
        max_normal = bitstring.Bits('0b0111 1110')
        assert p3binary_fmt.lut_binary8_to_float[max_normal.uint] == 49152.0
        max_normal_neg = bitstring.Bits('0b1111 1110')
        assert p3binary_fmt.lut_binary8_to_float[max_normal_neg.uint] == -49152.0
        min_normal = bitstring.Bits('0b0000 0100')
        assert p3binary_fmt.lut_binary8_to_float[min_normal.uint] == 2**-15
        min_subnormal = bitstring.Bits('0b0000 0001')
        assert p3binary_fmt.lut_binary8_to_float[min_subnormal.uint] == 0.25 * 2**-15
        max_subnormal = bitstring.Bits('0b0000 0011')
        assert p3binary_fmt.lut_binary8_to_float[max_subnormal.uint] == 0.75 * 2**-15
        nan = bitstring.Bits('0b1000 0000')
        assert math.isnan(p3binary_fmt.lut_binary8_to_float[nan.uint])

    def test_round_trip(self):
        # For each possible 8bit int, convert to float, then convert that float back to an int
        for fmt in [p4binary_fmt, p3binary_fmt]:
            for i in range(1 << 8):
                f = fmt.lut_binary8_to_float[i]
                ip = fmt.float_to_int8(f)
                assert ip == i

    def test_compare_8bit_floats_with_gfloat(self):
        for fi, lut in [(format_info_p3109(4), p4binary_fmt.lut_binary8_to_float),
                        (format_info_p3109(3), p3binary_fmt.lut_binary8_to_float),
                        (format_info_ocp_e4m3, e4m3mxfp_saturate_fmt.lut_int_to_float),
                        (format_info_ocp_e5m2, e5m2mxfp_saturate_fmt.lut_int_to_float),
                        ]:
            for i in range(1 << 8):
                f = lut[i]
                g = gfloat.decode_float(fi, i).fval
                if math.isnan(g):
                    assert math.isnan(f)
                else:
                    # The floats should be bitwise equal.
                    assert f == g

    def test_conversion_from_nan(self):
        x = BitArray(p4binary8=float('nan'))
        assert x == '0x80'
        x = BitArray(p3binary8=float('nan'))
        assert x == '0x80'

    def test_conversion_from_inf(self):
        x = BitArray(p4binary8=float('inf'))
        assert x == '0x7f'
        x = BitArray(p3binary8=float('inf'))
        assert x == '0x7f'
        x = BitArray(p4binary8=float('-inf'))
        assert x == '0xff'
        x = BitArray(p3binary8=float('-inf'))
        assert x == '0xff'

    def test_round_to_nearest(self):
        # Some exact values
        x = BitArray(p3binary=48.0)
        assert x.p3binary == 48.0
        x = BitArray(p3binary=56.0)
        assert x.p3binary == 56.0
        x = BitArray(p3binary=64.0)
        assert x.p3binary == 64.0

        x = BitArray(p3binary=51.9)
        assert x.p3binary == 48.0
        x = BitArray(p3binary=52.0)
        assert x.p3binary == 48.0
        assert x.bin[-1] == '0'
        x = BitArray(p3binary=52.1)
        assert x.p3binary == 56.0
        x = BitArray(p3binary=60.0)
        assert x.p3binary == 64.0
        assert x.bin[-1] == '0'

def test_compare_mxint8_with_gfloat():
    for i in range(1 << 8):
        f = Dtype('mxint8').parse(BitArray(uint=i, length=8))
        g = gfloat.decode_float(format_info_ocp_int8, i).fval
        assert f == g

def test_compare_e8m0_with_gfloat():
    for i in range(1 << 8):
        f = Dtype('e8m0mxfp').parse(BitArray(uint=i, length=8))
        g = gfloat.decode_float(format_info_ocp_e8m0, i).fval
        if math.isnan(g):
            assert math.isnan(f)
        else:
            assert f == g

def test_compare_6bit_floats_with_gfloat():
    for fi, lut in [(format_info_ocp_e3m2, e3m2mxfp_fmt.lut_int_to_float),
                    (format_info_ocp_e2m3, e2m3mxfp_fmt.lut_int_to_float)]:
        for i in range(1 << 6):
            f = lut[i]
            g = gfloat.decode_float(fi, i).fval
            if math.isnan(g):
                assert math.isnan(f)
            else:
                assert f == g

def test_compare_4bit_floats_with_gfloat():
    fi = format_info_ocp_e2m1
    lut = e2m1mxfp_fmt.lut_int_to_float

    for i in range(1 << 4):
        f = lut[i]
        g = gfloat.decode_float(fi, i).fval
        if math.isnan(g):
            assert math.isnan(f)
        else:
            assert f == g


def test_rounding_consistent_to_gfloat():
    for fi, dt in [[format_info_p3109(4), Dtype('p4binary')],
                   [format_info_p3109(3), Dtype('p3binary')]]:
        for i in range(0, 1 << 16):
            f = BitArray(uint=i, length=16).float
            mine = dt.parse(dt.build(f))
            theirs = gfloat.round_float(fi, f)
            if math.isnan(mine):
                assert math.isnan(theirs)
            else:
                assert mine == theirs

