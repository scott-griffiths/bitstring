import array
import math

class MXFPFormat:
    """Defining an MXFP floating point format"""

    def __init__(self, exp_bits: int, mantissa_bits: int, bias: int):
        self.exp_bits = exp_bits
        self.mantissa_bits = mantissa_bits
        self.bias = bias
        self.lut_int_to_float = self.createLUT_for_int_to_float()

    def slow_float_to_int(self, f: float) -> int:
        # Slow, but easier to follow than the faster version.
        length = 1 + self.exp_bits + self.mantissa_bits
        values = 1 << length
        if f >= 0:
            for i in range(values // 2):
                if f < self.lut_int_to_float[i]:
                    return i - 1
            # Clip to positive max
            return (1 << (length -1)) - 1
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
            raise ValueError("nan is not supported in MXFP values, only in the scale.")


    def createLUT_for_int_to_float(self) -> array.array:
        """Create a LUT to convert an int in representing a MXFP float into a Python float"""
        from bitstring import BitArray
        i2f = []
        length = 1 + self.exp_bits + self.mantissa_bits
        for i in range(1 << length):
            b = BitArray(uint=i, length=length)
            sign = b[0]
            exponent = b[1:1 + self.exp_bits].u
            significand = b[1 + self.exp_bits:]
            if exponent == 0:
                significand.prepend([0])
                exponent = -self.bias + 1
            else:
                significand.prepend([1])
                exponent -= self.bias
            f = float(significand.u) / (2.0 ** self.mantissa_bits)
            f *= 2 ** exponent
            i2f.append(f if not sign else -f)
        return array.array('f', i2f)


