#!/usr/bin/env python

import pytest
import sys
sys.path.insert(0, '..')
import bitstring
import sys
MutableBitStore = bitstring.bitstore.MutableBitStore

sys.path.insert(0, '..')


class TestBasicFunctionality:

    def test_getting_int(self):
        a = MutableBitStore.from_bin('001')
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
