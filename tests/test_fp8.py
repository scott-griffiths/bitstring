from __future__ import annotations

import pytest
import sys
import math
import random
import bitstring
from bitstring import Bits, BitArray, Dtype, Reader, Array
from gfloat.formats import (format_info_ocp_e4m3, format_info_ocp_e5m2, format_info_p3109, format_info_ocp_e3m2,
                            format_info_ocp_e2m3, format_info_ocp_e2m1, format_info_ocp_int8, format_info_ocp_e8m0,
                            format_info_bfloat16)
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
        a = Reader(Bits('0x00fff'))
        x = a.read_value('p3binary')
        assert x == 0.0
        assert a.pos == 8
        x = a.read_value('p4binary')
        assert x == -float('inf')
        assert a.pos == 16

    def test_read_list(self):
        v = [-6, -2, 0.125, 7, 10]
        a = bitstring.pack('5*p4binary', *v)
        vp = Reader(a).read_list('5*p4binary')
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


class TestConversionToFP8:

    def test_some143_values(self):
        assert Bits('0b0000 0000').p4binary == 0.0
        assert Bits('0b0111 1110').p4binary == 224.0
        assert Bits('0b1111 1110').p4binary == -224.0
        assert Bits('0b0000 1000').p4binary == 2**-7
        assert Bits('0b0000 0001').p4binary == 2**-10
        assert Bits('0b0000 0111').p4binary == 0.875 * 2**-7
        assert math.isnan(Bits('0b1000 0000').p4binary)

    def test_some152_values(self):
        assert Bits('0b0000 0000').p3binary == 0.0
        assert Bits('0b0111 1110').p3binary == 49152.0
        assert Bits('0b1111 1110').p3binary == -49152.0
        assert Bits('0b0000 0100').p3binary == 2**-15
        assert Bits('0b0000 0001').p3binary == 0.25 * 2**-15
        assert Bits('0b0000 0011').p3binary == 0.75 * 2**-15
        assert math.isnan(Bits('0b1000 0000').p3binary)

    def test_round_trip(self):
        # For each possible 8bit int, convert to float, then convert that float back to an int
        for dt in [Dtype('p4binary'), Dtype('p3binary')]:
            for i in range(1 << 8):
                f = dt.unpack(BitArray(u=i, length=8))
                assert dt.pack(f).u == i

    def test_compare_8bit_floats_with_gfloat(self):
        for fi, dt in [(format_info_p3109(8, 4), Dtype('p4binary')),
                       (format_info_p3109(8, 3), Dtype('p3binary')),
                       (format_info_ocp_e4m3, Dtype('e4m3mxfp_saturate')),
                       (format_info_ocp_e5m2, Dtype('e5m2mxfp_saturate')),
                       ]:
            for i in range(1 << 8):
                f = dt.unpack(BitArray(u=i, length=8))
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
        f = Dtype('mxint8').unpack(BitArray(u=i, length=8))
        g = gfloat.decode_float(format_info_ocp_int8, i).fval
        assert f == g

def test_compare_e8m0_with_gfloat():
    for i in range(1 << 8):
        f = Dtype('e8m0mxfp').unpack(BitArray(u=i, length=8))
        g = gfloat.decode_float(format_info_ocp_e8m0, i).fval
        if math.isnan(g):
            assert math.isnan(f)
        else:
            assert f == g

def test_compare_6bit_floats_with_gfloat():
    for fi, dt in [(format_info_ocp_e3m2, Dtype('e3m2mxfp')),
                   (format_info_ocp_e2m3, Dtype('e2m3mxfp'))]:
        for i in range(1 << 6):
            f = dt.unpack(BitArray(u=i, length=6))
            g = gfloat.decode_float(fi, i).fval
            if math.isnan(g):
                assert math.isnan(f)
            else:
                assert f == g

def test_compare_4bit_floats_with_gfloat():
    fi = format_info_ocp_e2m1
    dt = Dtype('e2m1mxfp')
    for i in range(1 << 4):
        f = dt.unpack(BitArray(u=i, length=4))
        g = gfloat.decode_float(fi, i).fval
        if math.isnan(g):
            assert math.isnan(f)
        else:
            assert f == g


def test_compare_bfloat_with_gfloat():
    dt = Dtype('bfloat')
    for i in range(1 << 16):
        f = dt.unpack(BitArray(u=i, length=16))
        g = gfloat.decode_float(format_info_bfloat16, i).fval
        if math.isnan(g):
            assert math.isnan(f)
        else:
            assert f == g


def test_bfloat_rounding_consistent_to_gfloat():
    # bfloat packing rounds to nearest, ties-to-even. Before 5.0 it truncated towards
    # zero, which disagrees with gfloat on roughly half of all values, so this is the
    # guard on that change. sat is left False: bfloat has an infinity to overflow to.
    dt = Dtype('bfloat')
    rng = random.Random(4321)
    values = [0.0, -0.0, 1.0, -1.0, 3.4e38, -3.4e38, float('inf'), float('-inf')]
    values += [rng.uniform(-1e5, 1e5) for _ in range(2000)]
    values += [rng.uniform(-1.0, 1.0) for _ in range(2000)]
    for f in values:
        mine = dt.unpack(dt.pack(f))
        theirs = gfloat.round_float(format_info_bfloat16, f)
        if math.isnan(mine):
            assert math.isnan(theirs)
        else:
            assert mine == theirs, f"bfloat packing {f!r}: got {mine}, gfloat says {theirs}"


def test_rounding_consistent_to_gfloat():
    for fi, dt in [[format_info_p3109(8, 4), Dtype('p4binary')],
                   [format_info_p3109(8, 3), Dtype('p3binary')]]:
        for i in range(0, 1 << 16):
            f = BitArray(u=i, length=16).float
            mine = dt.unpack(dt.pack(f))
            theirs = gfloat.round_float(fi, f)
            if math.isnan(mine):
                assert math.isnan(theirs)
            else:
                assert mine == theirs


@pytest.mark.parametrize("name", ['bfloat', 'bfloatle', 'p3binary', 'p4binary',
                                  'e4m3mxfp_saturate', 'e4m3mxfp_overflow',
                                  'e5m2mxfp_saturate', 'e5m2mxfp_overflow',
                                  'e3m2mxfp', 'e2m3mxfp', 'e2m1mxfp', 'mxint'])
def test_packing_routes_agree(name):
    # Single values go through the per-element setter while an Array packs the whole
    # list in one tibs call. The two used to be different pieces of code and could
    # round differently; they must always produce the same bits.
    rng = random.Random(99)
    values = [0.0, -0.0, 0.5, -0.5, 1.0, 1.5, -1.5]
    values += [rng.uniform(-200.0, 200.0) for _ in range(200)]
    for v in values:
        single = Bits(**{name: v})
        packed = bitstring.pack(name, v)
        bulk = Array(name, [v]).data
        assert single == packed == bulk, f"{name} packing {v!r}: {single.bin} / {packed.bin} / {bulk.bin}"


def test_rounding_consistent_to_gfloat_from_f64():
    # As test_rounding_consistent_to_gfloat, but from full-precision Python floats
    # rather than only from values that a 16-bit float can hold exactly. Packing used
    # to go via a float16 before indexing a lookup table, so a value could be rounded
    # twice and land on the wrong side of a tie; these inputs are the ones that caught
    # it. Every format that rounds is covered, not just the two binary8 ones.
    # mxint is left out: it never went via a float16, and gfloat saturates it
    # symmetrically to -1.984375 where this format can hold -2.0.
    # sat says what the format does with a value too big for it: the binary8 formats
    # have an infinity to overflow to, the rest clamp to their largest finite value.
    formats = [(format_info_p3109(8, 4), Dtype('p4binary'), False),
               (format_info_p3109(8, 3), Dtype('p3binary'), False),
               (format_info_ocp_e4m3, Dtype('e4m3mxfp_saturate'), True),
               (format_info_ocp_e5m2, Dtype('e5m2mxfp_saturate'), True),
               (format_info_ocp_e3m2, Dtype('e3m2mxfp'), True),
               (format_info_ocp_e2m3, Dtype('e2m3mxfp'), True),
               (format_info_ocp_e2m1, Dtype('e2m1mxfp'), True)]
    rng = random.Random(1234)
    values = [rng.uniform(-1e5, 1e5) for _ in range(2000)]
    values += [rng.uniform(-1.0, 1.0) for _ in range(2000)]
    for fi, dt, sat in formats:
        for f in values:
            mine = dt.unpack(dt.pack(f))
            theirs = gfloat.round_float(fi, f, sat=sat)
            if math.isnan(mine):
                assert math.isnan(theirs)
            else:
                assert mine == theirs, f"{dt} packing {f!r}: got {mine}, gfloat says {theirs}"
