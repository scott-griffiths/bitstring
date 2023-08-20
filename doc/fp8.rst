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

    >>> [Bits(uint=x, length=8).float8_152 for x in range(256)]

or using the :class:`Array` type it's even more concise, and we can pretty print all the values with this line ::

    >>> Array('float8_143', bytearray(range(256))).pp()
       0:           0.0  0.0009765625   0.001953125  0.0029296875    0.00390625  0.0048828125   0.005859375  0.0068359375
       8:     0.0078125  0.0087890625   0.009765625  0.0107421875    0.01171875  0.0126953125   0.013671875  0.0146484375
      16:      0.015625   0.017578125    0.01953125   0.021484375     0.0234375   0.025390625    0.02734375   0.029296875
      24:       0.03125    0.03515625     0.0390625    0.04296875      0.046875    0.05078125     0.0546875    0.05859375
      32:        0.0625     0.0703125      0.078125     0.0859375       0.09375     0.1015625      0.109375     0.1171875
      40:         0.125      0.140625       0.15625      0.171875        0.1875      0.203125       0.21875      0.234375
      48:          0.25       0.28125        0.3125       0.34375         0.375       0.40625        0.4375       0.46875
      56:           0.5        0.5625         0.625        0.6875          0.75        0.8125         0.875        0.9375
      64:           1.0         1.125          1.25         1.375           1.5         1.625          1.75         1.875
      72:           2.0          2.25           2.5          2.75           3.0          3.25           3.5          3.75
      80:           4.0           4.5           5.0           5.5           6.0           6.5           7.0           7.5
      88:           8.0           9.0          10.0          11.0          12.0          13.0          14.0          15.0
      96:          16.0          18.0          20.0          22.0          24.0          26.0          28.0          30.0
     104:          32.0          36.0          40.0          44.0          48.0          52.0          56.0          60.0
     112:          64.0          72.0          80.0          88.0          96.0         104.0         112.0         120.0
     120:         128.0         144.0         160.0         176.0         192.0         208.0         224.0         240.0
     128:           nan -0.0009765625  -0.001953125 -0.0029296875   -0.00390625 -0.0048828125  -0.005859375 -0.0068359375
     136:    -0.0078125 -0.0087890625  -0.009765625 -0.0107421875   -0.01171875 -0.0126953125  -0.013671875 -0.0146484375
     144:     -0.015625  -0.017578125   -0.01953125  -0.021484375    -0.0234375  -0.025390625   -0.02734375  -0.029296875
     152:      -0.03125   -0.03515625    -0.0390625   -0.04296875     -0.046875   -0.05078125    -0.0546875   -0.05859375
     160:       -0.0625    -0.0703125     -0.078125    -0.0859375      -0.09375    -0.1015625     -0.109375    -0.1171875
     168:        -0.125     -0.140625      -0.15625     -0.171875       -0.1875     -0.203125      -0.21875     -0.234375
     176:         -0.25      -0.28125       -0.3125      -0.34375        -0.375      -0.40625       -0.4375      -0.46875
     184:          -0.5       -0.5625        -0.625       -0.6875         -0.75       -0.8125        -0.875       -0.9375
     192:          -1.0        -1.125         -1.25        -1.375          -1.5        -1.625         -1.75        -1.875
     200:          -2.0         -2.25          -2.5         -2.75          -3.0         -3.25          -3.5         -3.75
     208:          -4.0          -4.5          -5.0          -5.5          -6.0          -6.5          -7.0          -7.5
     216:          -8.0          -9.0         -10.0         -11.0         -12.0         -13.0         -14.0         -15.0
     224:         -16.0         -18.0         -20.0         -22.0         -24.0         -26.0         -28.0         -30.0
     232:         -32.0         -36.0         -40.0         -44.0         -48.0         -52.0         -56.0         -60.0
     240:         -64.0         -72.0         -80.0         -88.0         -96.0        -104.0        -112.0        -120.0
     248:        -128.0        -144.0        -160.0        -176.0        -192.0        -208.0        -224.0        -240.0


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