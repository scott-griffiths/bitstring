import array
import math
import struct
import bitarray


class MXFPFormat:
    """Defining an MXFP micro-scaling floating point format"""

    def __init__(self, exp_bits: int, mantissa_bits: int, bias: int):
        self.exp_bits = exp_bits
        self.mantissa_bits = mantissa_bits
        self.bias = bias
        self.lut_int_to_float = self.createLUT_for_int_to_float()
        self.lut_float16_to_mxfp = self.createLUT_for_float16_to_mxfp()

    def slow_float_to_int(self, f: float) -> int:
        # Slow, but easier to follow than the faster version.
        length = 1 + self.exp_bits + self.mantissa_bits
        values = 1 << length
        if f >= 0:
            for i in range(values // 2):
                if f < self.lut_int_to_float[i]:
                    return i - 1
            # Clip to positive max
            return (1 << (length - 1)) - 1
        if f < 0:
            if f > self.lut_int_to_float[values // 2 + 1]:
                # Rounding upwards to zero
                return 0b000000  # There's no negative zero so this is a special case
            for i in range(values // 2 + 2, values):
                if f > self.lut_int_to_float[i]:
                    return i - 1
            # Clip to negative max
            return (1 << length) - 1
        if math.isnan(f):
            return 0  # Nan isn't supported so what value should this be? (TODO)

    def float_to_int(self, f: float) -> int:
        """Given a Python float convert to the best mxfp float (expressed as an int) that represents it."""
        # First convert the float to a float16, then a 16 bit uint
        try:
            b = struct.pack('>e', f)
        except (OverflowError, struct.error):
            # Return the largest representable positive or negative value
            # Special cases for e4m3 and e5m2
            if self.exp_bits == 4 and self.mantissa_bits == 3:
                return 0b01111110 if f > 0 else 0b11111110
            if self.exp_bits == 5 and self.mantissa_bits == 2:
                return 0b01111011 if f > 0 else 0b11111011
            return (1 << (self.exp_bits + self.mantissa_bits)) - 1 if f > 0 else (1 << (1 + self.exp_bits + self.mantissa_bits)) - 1
        f16_int = int.from_bytes(b, byteorder='big')
        # Then use this as an index to our large LUT
        return self.lut_float16_to_mxfp[f16_int]

    def createLUT_for_int_to_float(self) -> array.array:
        """Create a LUT to convert an int in representing a MXFP float into a Python float"""
        i2f = []
        length = 1 + self.exp_bits + self.mantissa_bits
        for i in range(1 << length):
            b = bitarray.util.int2ba(i, length=length, endian='big', signed=False)
            sign = b[0]
            exponent = bitarray.util.ba2int(b[1:1 + self.exp_bits])
            significand = b[1 + self.exp_bits:]
            if exponent == 0:
                significand = bitarray.bitarray('0') + significand
                exponent = -self.bias + 1
            else:
                significand = bitarray.bitarray('1') + significand
                exponent -= self.bias
            f = float(bitarray.util.ba2int(significand)) / (2.0 ** self.mantissa_bits)
            f *= 2 ** exponent
            if length == 8:
                # Some special cases
                if self.exp_bits == 5:
                    if i in [0b01111100, 0b11111100]:
                        f = float('inf')
                    if i in [0b01111101, 0b11111101, 0b01111110, 0b11111110, 0b01111111, 0b11111111]:
                        f = float('nan')
                if self.exp_bits == 4:
                    if i in [0b01111111, 0b11111111]:
                        f = float('nan')
            i2f.append(f if not sign else -f)
        return array.array('f', i2f)

    def createLUT_for_float16_to_mxfp(self) -> bytes:
        """Create a LUT to convert a float16 into a MXFP format"""
        # Used to create the LUT that was compressed and stored for the fp8 code
        fp16_to_fp8 = bytearray(1 << 16)
        for i in range(1 << 16):
            b = struct.pack('>H', i)
            f, = struct.unpack('>e', b)
            fp8_i = self.slow_float_to_int(f)
            fp16_to_fp8[i] = fp8_i
        return bytes(fp16_to_fp8)


e2m1mxfp_fmt = MXFPFormat(exp_bits=2, mantissa_bits=1, bias=1)
e2m3mxfp_fmt = MXFPFormat(exp_bits=2, mantissa_bits=3, bias=1)
e3m2mxfp_fmt = MXFPFormat(exp_bits=3, mantissa_bits=2, bias=3)
e4m3mxfp_fmt = MXFPFormat(exp_bits=4, mantissa_bits=3, bias=7)
e5m2mxfp_fmt = MXFPFormat(exp_bits=5, mantissa_bits=2, bias=15)
