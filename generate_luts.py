"""
This script generates the LUTs used for the various exotic floating point formats.
Its output is the luts.py file which is then used by the bitstring package.
"""

import pprint
import zlib
import shutil
from bitstring.mxfp import MXFPFormat
from bitstring.fp8 import Binary8Format

if __name__ == '__main__':

    mxfps = [MXFPFormat(exp_bits=2, mantissa_bits=1, bias=1, mxfp_overflow='saturate'),
             MXFPFormat(exp_bits=2, mantissa_bits=3, bias=1, mxfp_overflow='saturate'),
             MXFPFormat(exp_bits=3, mantissa_bits=2, bias=3, mxfp_overflow='saturate'),
             MXFPFormat(exp_bits=4, mantissa_bits=3, bias=7, mxfp_overflow='saturate'),
             MXFPFormat(exp_bits=5, mantissa_bits=2, bias=15, mxfp_overflow='saturate'),
             MXFPFormat(exp_bits=4, mantissa_bits=3, bias=7, mxfp_overflow='overflow'),
             MXFPFormat(exp_bits=5, mantissa_bits=2, bias=15, mxfp_overflow='overflow')
             ]
    binary8s = [Binary8Format(exp_bits=4, bias=8),
                Binary8Format(exp_bits=5, bias=16)
                ]

    with open('./bitstring/luts_temp.py', 'w') as f:
        f.write("#\n# This file is generated by generate_luts.py. DO NOT EDIT.\n#\n\n")

        mxfp_luts_compressed = {}
        for mxfp in mxfps:
            print(f"generating LUT for {mxfp}")
            mxfp.create_luts()
            lut_int_to_float_compressed = zlib.compress(mxfp.lut_int_to_float, 1)
            lut_float16_to_mxfp_compressed = zlib.compress(mxfp.lut_float16_to_mxfp, 1)
            mxfp_luts_compressed[(mxfp.exp_bits, mxfp.mantissa_bits, mxfp.bias, mxfp.mxfp_overflow)] = (lut_int_to_float_compressed, lut_float16_to_mxfp_compressed)
        f.write("mxfp_luts_compressed = \\\n")
        pprint.pp(mxfp_luts_compressed, width=120, stream=f)

        binary8_luts_compressed = {}
        for binary8 in binary8s:
            print(f"generating LUT for {binary8}")
            binary8.create_luts()
            lut_binary8_to_float_compressed = zlib.compress(binary8.lut_binary8_to_float, 1)
            lut_float16_to_binary8_compressed = zlib.compress(binary8.lut_float16_to_binary8, 1)
            binary8_luts_compressed[(binary8.exp_bits, binary8.bias)] = (lut_binary8_to_float_compressed, lut_float16_to_binary8_compressed)
        f.write("\n\nbinary8_luts_compressed = \\\n")
        pprint.pp(binary8_luts_compressed, width=120, stream=f)

    shutil.move('./bitstring/luts_temp.py', './bitstring/luts.py')