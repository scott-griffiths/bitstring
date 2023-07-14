.. currentmodule:: bitstring

.. _fp8:

8-bit Floating Point Types
==========================

Python floats are typically 64 bits long, but 32 and 16 bit sizes are also supported through the ``struct`` module.
These are the well-known and widely used IEEE formats.
Recently lower precision floating points have become more widely used, largely driven by the requirements of machine learning.

As well as the 'half' precision 16 bit standard, a truncated version of the 32 bit standard called 'bfloat16' is used which has the range of a single precision float but less precision.

The #bits value in the tables below show how the available bits are split into `sign` + `exponent` + `mantissa`.
There's always 1 bit to determine the sign of the floating point value.
The more bits in the exponent, the larger the range that can be represented.
The more bits in the mantissa, the greater the precision (~significant figures) of the values.

.. list-table::
   :header-rows: 1

   * - Type
     - # bits
     - Standard
     - Range
     - bitstring / struct format
   * - Double precision
     - 1 + 11 + 52
     - IEEE 754
     - 10\ :sup:`-308` → 10\ :sup:`308`
     - ``'float64'`` / ``'d'``
   * - Single precision
     - 1 + 8 + 23
     - IEEE 754
     - 10\ :sup:`-38` → 10\ :sup:`38`
     - ``'float32'`` / ``'f'``
   * - Half precision
     - 1 + 5 + 10
     - IEEE 754
     - 6×10\ :sup:`-8` → 65504
     - ``'float16'`` / ``'e'``
   * - bfloat
     - 1 + 8 + 7
     - ``-``
     - 10\ :sup:`-38` → 10\ :sup:`38`
     - ``'bfloat'`` / ``-``


Though not yet standardized, there are new formats emerging for representing floats in just 8 bits.
As there are just 256 possible values both the range and precision of these formats are extremely limited, and there are sophisticated methods of scaling values to ensure that useful calculations can still be done without overflows and underflows.

The formats supported by bitstring are from the proposal by `Graphcore, AMD and Qualcomm <https://www.graphcore.ai/posts/graphcore-and-amd-propose-8-bit-fp-ai-standard-with-qualcomm-support>`_.

.. list-table::
   :header-rows: 1

   * - Type
     - # bits
     - Range
     - bitstring format

   * - Float8E4M3FNUZ
     - 1 + 4 + 3
     - 10\ :sup:`-3` → 240
     - ``'float8_143'``

   * - Float8E5M2FNUZ
     - 1 + 5 + 2
     - 8×10\ :sup:`-6` → 57344
     - ``'float8_152'``


Given the limited ranges and precision it's remarkable that any useful calculations can be done, but both inference and training of large machine learning models can be done with these formats.

You can easily examine every possible value that these formats can represent using a line like this ::

    >>> [Bits(uint=x, length=8).float8_143 for x in range(256)]

You'll see that there is only 1 zero value, no 'inf' values and only one 'nan' value.

When converting from a Python float (which will typically be stored in 64-bits) values are rounded towards zero.
So anything larger than the largest representable value (including infinity) will get rounded to it.