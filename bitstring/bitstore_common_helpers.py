from __future__ import annotations

import struct
import math
import functools
from typing import Union, Optional, Dict, Callable
import bitarray
import bitstring
from bitstring.fp8 import p4binary_fmt, p3binary_fmt
from bitstring.mxfp import (e3m2mxfp_fmt, e2m3mxfp_fmt, e2m1mxfp_fmt, e4m3mxfp_saturate_fmt,
                            e5m2mxfp_saturate_fmt, e4m3mxfp_overflow_fmt, e5m2mxfp_overflow_fmt)
from bitstring.helpers import tidy_input_string

helpers = bitstring.bitstore_helpers
BitStore = bitstring.bitstore.BitStore


def ue2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i < 0:
        raise bitstring.CreationError("Cannot use negative initialiser for unsigned exponential-Golomb.")
    if i == 0:
        return BitStore.from_binary_string('1')
    tmp = i + 1
    leadingzeros = -1
    while tmp > 0:
        tmp >>= 1
        leadingzeros += 1
    remainingpart = i + 1 - (1 << leadingzeros)
    return BitStore.from_binary_string('0' * leadingzeros + '1') + helpers.int2bitstore(remainingpart, leadingzeros, False)


def se2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i > 0:
        u = (i * 2) - 1
    else:
        u = -2 * i
    return ue2bitstore(u)


def uie2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i < 0:
        raise bitstring.CreationError("Cannot use negative initialiser for unsigned interleaved exponential-Golomb.")
    return BitStore.from_binary_string('1' if i == 0 else '0' + '0'.join(bin(i + 1)[3:]) + '1')


def sie2bitstore(i: Union[str, int]) -> BitStore:
    i = int(i)
    if i == 0:
        return BitStore.from_binary_string('1')
    else:
        return uie2bitstore(abs(i)) + (BitStore.from_binary_string('1') if i < 0 else BitStore.from_binary_string('0'))