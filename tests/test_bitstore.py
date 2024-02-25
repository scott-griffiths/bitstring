#!/usr/bin/env python

import pytest
import sys
sys.path.insert(0, '..')
import bitstring
from bitstring.bitstore import BitStore, offset_slice_indices_lsb0
import sys

sys.path.insert(0, '..')


class TestBasicFunctionality:

    def test_getting_int(self):
        a = BitStore('001')
        assert a.getindex(0) == 0
        assert a.getindex(1) == 0
        assert a.getindex(2) == 1

        assert a.getindex(-1) == 1
        assert a.getindex(-2) == 0
        assert a.getindex(-3) == 0

        with pytest.raises(IndexError):
            _ = a.getindex(3)
        with pytest.raises(IndexError):
            _ = a.getindex(-4)


class TestBasicLSB0Functionality:

    @classmethod
    def setup_class(cls):
        bitstring.lsb0 = True

    @classmethod
    def teardown_class(cls):
        bitstring.lsb0 = False

    def test_getting_int(self):
        a = BitStore('001')
        assert a.getindex(0) == 1
        assert a.getindex(1) == 0
        assert a.getindex(2) == 0

        assert a.getindex(-1) == 0
        assert a.getindex(-2) == 0
        assert a.getindex(-3) == 1

        with pytest.raises(IndexError):
            _ = a.getindex(3)
        with pytest.raises(IndexError):
            _ = a.getindex(-4)

    def test_getting_slice(self):
        a = BitStore.frombytes(b'12345678')
        assert a.getslice(None, None).tobytes() == b'12345678'
        assert a.getslice(None, -8).tobytes() == b'2345678'
        assert a.getslice(8, None).tobytes() == b'1234567'
        assert a.getslice(16, 24).tobytes() == b'6'

    def test_setting_int(self):
        a = BitStore('00000')
        a[0] = 1
        assert a.slice_to_bin() == '00001'
        a[-1] = 1
        assert a.slice_to_bin() == '10001'
        with pytest.raises(IndexError):
            a[5] = 1
        with pytest.raises(IndexError):
            a[-6] = 0


class TestGettingSlices:

    def teardown_method(self) -> None:
        bitstring.lsb0 = False

    def test_everything(self):
        a = BitStore('010010001000110111001111101101001111')

        # Try combination of start and stop for msb0 and get the result.
        # Convert to start and stop needed for lsb0
        options = [5, 2, -2, 1, 7, -3, -9, 0, -1, -len(a), len(a), len(a) - 1, -len(a) - 1, -100, 100, None]
        for start_option in options:
            for end_option in options:
                bitstring.lsb0 = True
                lsb0 = a.getslice(start_option, end_option)
                bitstring.lsb0 = False
                msb0 = a.getslice(start_option, end_option)
                new_slice = offset_slice_indices_lsb0(slice(start_option, end_option, None), len(a))
                new_start, new_end = new_slice.start, new_slice.stop
                assert len(msb0) == len(lsb0), f"[{start_option}: {end_option}] -> [{new_start}: {new_end}]  len(msb0)={len(msb0)}, len(lsb0)={len(lsb0)}"
