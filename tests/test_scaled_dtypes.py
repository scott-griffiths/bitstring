from __future__ import annotations

import sys
from bitstring import BitArray, Dtype

sys.path.insert(0, '..')

def test_simple_scaled_dtype():
    d = Dtype('u4', scale=2)
    assert d.scale == 2
    b = BitArray('0x01')
    assert d.parse(b) == 2

