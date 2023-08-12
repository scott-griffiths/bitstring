.. currentmodule:: bitstring

.. _Exotic floats:

Exotic Floating Point Formats
=============================

Python floats are typically 64 bits long, but 32 and 16 bit sizes are also supported through the ``struct`` module.
These are the well-known IEEE formats.
Recently, lower precision floating points have become more widely used, largely driven by the requirements of machine learning algorithms and hardware.

As well as the 'half' precision 16 bit standard, a truncated version of the 32 bit standard called 'bfloat16' is used which has the range of a 32-bit float but less precision.

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



An example of creation and interpretation of a bfloat::

    >>> a = Bits(bfloat=4.5e23)  # No need to specify length as always 16 bits
    >>> a
    Bits('0x66be')
    >>> a.bfloat
    4.486248158726163e+23  # Converted to Python float


8-bit Floating Point Types
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
    The 8-bit float formats used here are from a proposal supported by Graphcore, AMD and Qualcomm.
    There is a different but similar proposal from other companies, and there is an ongoing standardisation process.

    I (Scott Griffiths) currently work at Graphcore, but I have not been involved in the low-precision float work.
    This implementation is not part of my work at Graphcore (this counts as fun for me).
    I have been careful to only base my work here on public sources, and any misunderstandings or errors are my own.

    This is an experimental feature and may be modified in future point releases.

Two 8-bit floating point formats are supported as an experimental feature in bitstring 4.1.
These are also mainly of use in machine learning and have very limited ranges and precision.
There is no standardised format for these but there are a few candidates.

The formats supported by bitstring are from the proposal by `Graphcore, AMD and Qualcomm <https://www.graphcore.ai/posts/graphcore-and-amd-propose-8-bit-fp-ai-standard-with-qualcomm-support>`_ in `this paper <https://arxiv.org/abs/2206.02915>`_, and there is some useful information `here <https://github.com/openxla/stablehlo/blob/2fcdf9b25d622526f81cd1575c65d01a6db319d2/rfcs/20230321-fp8_fnuz.md>`_ too.

The 8-bit formats are named after how the byte is split between the sign-exponent-mantissa parts.
So ``float8_143`` has a single sign bit, 4 bits for the exponent and 3 bits for the mantissa.
For a bit more range and less precision you can use ``float8_152`` which has 5 bits for the exponent and only 2 for the mantissa.

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


As there are just 256 possible values, both the range and precision of these formats are extremely limited.
It's remarkable that any useful calculations can be performed, but both inference and training of large machine learning models can be done with these formats.

You can easily examine every possible value that these formats can represent using a line like this::

    >>> [Bits(uint=x, length=8).float8_143 for x in range(256)]

or using the :class:`Array` type it's even more concise::

    >>> Array('float8_152', bytearray(range(256)))

You'll see that there is only 1 zero value, no 'inf' values and only one 'nan' value.

When converting from a Python float (which will typically be stored in 64-bits) unrepresentable values are rounded towards zero.
The formats have no code for infinity, instead using the largest positive and negative values, so anything larger than the largest representable value (including infinity) will get rounded to it. ::


    >>> a = BitArray(float8_152=70)
    >>> print(a.bin)
    01011000
    >>> print(a.float8_152)
    64.0
    >>> a.float8_152 = 1000000.0
    >>> print(a.float8_152)
    57344.0