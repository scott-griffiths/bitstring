from __future__ import annotations

import sys
import math
from bitstring import BitArray, Array, ScaledArray, ScaledDtype

sys.path.insert(0, '..')

def test_simple_scaled_dtype():
    d = ScaledDtype('u4', scale=2)
    assert d.scale == 2
    b = BitArray('0x01')
    assert d.parse(b) == 4
    d.scale = 0
    assert d.parse(b) == 1

def test_array_with_scaled_dtype():
    d = ScaledDtype('e3m2float', scale=5)
    a = Array(d, [1.0, 20, 300])
    print(a)
    a.dtype.scale = 0
    print(a)
    s = ScaledArray('e3m2float', [1.0, 20, 300], scale=5)
    print(s)
    assert a == s