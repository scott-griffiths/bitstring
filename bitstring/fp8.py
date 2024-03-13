"""
The 8-bit float formats used here are from a proposal supported by Graphcore, AMD and Qualcomm.
See https://arxiv.org/abs/2206.02915

"""

import struct
import zlib
import array
import bitarray
from bitstring.luts import binary8_luts_compressed


def slow_float_to_int8(lut_binary8_to_float, f: float) -> int:
    # Slow, but easier to follow than the faster version. Used only for validation.
    if f >= 0:
        for i in range(128):
            if f < lut_binary8_to_float[i]:
                return i - 1
        # Clip to positive max
        return 0b01111111
    if f < 0:
        if f > lut_binary8_to_float[129]:
            # Rounding upwards to zero
            return 0b00000000  # There's no negative zero so this is a special case
        for i in range(130, 256):
            if f > lut_binary8_to_float[i]:
                return i - 1
        # Clip to negative max
        return 0b11111111
    # We only have one nan value
    return 0b10000000

def createLUT_for_binary8_to_float(exp_bits, bias):
    """Create a LUT to convert an int in range 0-255 representing a float8 into a Python float"""
    i2f = []
    for i in range(256):
        b = bitarray.util.int2ba(i, length=8, endian='big', signed=False)
        sign = b[0]
        exponent = bitarray.util.ba2int(b[1:1 + exp_bits])
        significand = b[1 + exp_bits:]
        if exponent == 0:
            significand = bitarray.bitarray('0') + significand
            exponent = -bias + 1
        else:
            significand = bitarray.bitarray('1') + significand
            exponent -= bias
        f = float(bitarray.util.ba2int(significand)) / (2.0 ** (7 - exp_bits))
        f *= 2 ** exponent
        i2f.append(f if not sign else -f)
    # One special case for minus zero
    i2f[0b10000000] = float('nan')
    # and for plus and minus infinity
    i2f[0b01111111] = float('inf')
    i2f[0b11111111] = float('-inf')
    return array.array('f', i2f)


def createLUT_for_float16_to_binary8(lut_binary8_to_float) -> bytes:
    # Used to create the LUT that was compressed and stored for the fp8 code
    fp16_to_fp8 = bytearray(1 << 16)
    for i in range(1 << 16):
        b = struct.pack('>H', i)
        f, = struct.unpack('>e', b)
        fp8_i = slow_float_to_int8(lut_binary8_to_float, f)
        fp16_to_fp8[i] = fp8_i
    return bytes(fp16_to_fp8)


class Binary8Format:
    """8-bit floating point formats based on draft IEEE binary8"""

    def __init__(self, exp_bits: int, bias: int):
        # We use look up tables to go from an IEEE float16 to the best float8 representation.
        # For startup efficiency they've been precalculated and zipped up
        self.exp_bits = exp_bits
        self.bias = bias

        binary8_to_float_compressed, float16_to_binary8_compressed = binary8_luts_compressed[(exp_bits, bias)]
        self.lut_float16_to_binary8 = zlib.decompress(float16_to_binary8_compressed)
        dec = zlib.decompress(binary8_to_float_compressed)
        self.lut_binary8_to_float = struct.unpack(f'<{len(dec) // 4}f', dec)

    def float_to_int8(self, f: float) -> int:
        """Given a Python float convert to the best float8 (expressed as an integer in 0-255 range)."""
        # First convert the float to a float16, then a 16 bit uint
        try:
            b = struct.pack('>e', f)
        except (OverflowError, struct.error):
            # Return the largest representable positive or negative value
            return 0b01111111 if f > 0 else 0b11111111
        f16_int = int.from_bytes(b, byteorder='big')
        # Then use this as an index to our large LUT
        return self.lut_float16_to_binary8[f16_int]


# We create the 1.5.2 and 1.4.3 formats.
p4binary_fmt = Binary8Format(exp_bits=4, bias=8)
p3binary_fmt = Binary8Format(exp_bits=5, bias=16)