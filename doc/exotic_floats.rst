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
     - +ive Range
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


IEEE 8-bit Floating Point Types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::
    This is an experimental feature and may be modified in future point releases.

    In bitstring prior to version 4.2 the `p4binary8` and `p3binary8` formats were called `e4m3float` and `e5m2float` respectively.
    The two formats are almost identical, the difference being the addition of `inf` values that replace the largest positive and negative values that were previously available.

    Neither should be confused with the `e4m3mxfp` and `e5m2mxfp` formats from the Open Compute Project described below.


The 'binary8' formats are part of an ongoing IEEE standardisation process.
This implementation here is based on a publicly available draft of the standard.
There are seven formats defined in the draft standard, but only two are supported here.
If you'd like the other precisions supported then raise a feature request!

The ``p4binary8`` has a single sign bit, 4 bits for the exponent and 3 bits for the mantissa.
For a bit more range and less precision you can use ``p3binary8`` which has 5 bits for the exponent and only 2 for the mantissa.
Note that in the standard they are called `binary8p4` and `binary8p3`, but for bitstring types any final digits should be the length of the type, so these slightly modified names were chosen.

.. list-table::
   :header-rows: 1

   * - Type
     - # bits
     - +ive Range
     - bitstring format

   * - binary8p4
     - 1 + 4 + 3
     - 10\ :sup:`-3` → 224
     - ``'p4binary8'``

   * - binary8p3
     - 1 + 5 + 2
     - 8×10\ :sup:`-6` → 49152
     - ``'p3binary8'``


As there are just 256 possible values, both the range and precision of these formats are extremely limited.
It's remarkable that any useful calculations can be performed, but both inference and training of large machine learning models can be done with these formats.

You can easily examine every possible value that these formats can represent using a line like this::

    >>> [Bits(uint=x, length=8).p3binary8 for x in range(256)]

or using the :class:`Array` type it's even more concise - we can create an Array and pretty print all the values with this line::

    >>> Array('p4binary8', bytearray(range(256))).pp(width=90)
    <Array fmt='p4binary', length=256, itemsize=8 bits, total data size=256 bytes>
    [
       0:           0.0  0.0009765625   0.001953125  0.0029296875    0.00390625  0.0048828125
       6:   0.005859375  0.0068359375     0.0078125  0.0087890625   0.009765625  0.0107421875
      12:    0.01171875  0.0126953125   0.013671875  0.0146484375      0.015625   0.017578125
      18:    0.01953125   0.021484375     0.0234375   0.025390625    0.02734375   0.029296875
      24:       0.03125    0.03515625     0.0390625    0.04296875      0.046875    0.05078125
      30:     0.0546875    0.05859375        0.0625     0.0703125      0.078125     0.0859375
      36:       0.09375     0.1015625      0.109375     0.1171875         0.125      0.140625
      42:       0.15625      0.171875        0.1875      0.203125       0.21875      0.234375
      48:          0.25       0.28125        0.3125       0.34375         0.375       0.40625
      54:        0.4375       0.46875           0.5        0.5625         0.625        0.6875
      60:          0.75        0.8125         0.875        0.9375           1.0         1.125
      66:          1.25         1.375           1.5         1.625          1.75         1.875
      72:           2.0          2.25           2.5          2.75           3.0          3.25
      78:           3.5          3.75           4.0           4.5           5.0           5.5
      84:           6.0           6.5           7.0           7.5           8.0           9.0
      90:          10.0          11.0          12.0          13.0          14.0          15.0
      96:          16.0          18.0          20.0          22.0          24.0          26.0
     102:          28.0          30.0          32.0          36.0          40.0          44.0
     108:          48.0          52.0          56.0          60.0          64.0          72.0
     114:          80.0          88.0          96.0         104.0         112.0         120.0
     120:         128.0         144.0         160.0         176.0         192.0         208.0
     126:         224.0           inf           nan -0.0009765625  -0.001953125 -0.0029296875
     132:   -0.00390625 -0.0048828125  -0.005859375 -0.0068359375    -0.0078125 -0.0087890625
     138:  -0.009765625 -0.0107421875   -0.01171875 -0.0126953125  -0.013671875 -0.0146484375
     144:     -0.015625  -0.017578125   -0.01953125  -0.021484375    -0.0234375  -0.025390625
     150:   -0.02734375  -0.029296875      -0.03125   -0.03515625    -0.0390625   -0.04296875
     156:     -0.046875   -0.05078125    -0.0546875   -0.05859375       -0.0625    -0.0703125
     162:     -0.078125    -0.0859375      -0.09375    -0.1015625     -0.109375    -0.1171875
     168:        -0.125     -0.140625      -0.15625     -0.171875       -0.1875     -0.203125
     174:      -0.21875     -0.234375         -0.25      -0.28125       -0.3125      -0.34375
     180:        -0.375      -0.40625       -0.4375      -0.46875          -0.5       -0.5625
     186:        -0.625       -0.6875         -0.75       -0.8125        -0.875       -0.9375
     192:          -1.0        -1.125         -1.25        -1.375          -1.5        -1.625
     198:         -1.75        -1.875          -2.0         -2.25          -2.5         -2.75
     204:          -3.0         -3.25          -3.5         -3.75          -4.0          -4.5
     210:          -5.0          -5.5          -6.0          -6.5          -7.0          -7.5
     216:          -8.0          -9.0         -10.0         -11.0         -12.0         -13.0
     222:         -14.0         -15.0         -16.0         -18.0         -20.0         -22.0
     228:         -24.0         -26.0         -28.0         -30.0         -32.0         -36.0
     234:         -40.0         -44.0         -48.0         -52.0         -56.0         -60.0
     240:         -64.0         -72.0         -80.0         -88.0         -96.0        -104.0
     246:        -112.0        -120.0        -128.0        -144.0        -160.0        -176.0
     252:        -192.0        -208.0        -224.0          -inf
    ]


You'll see that there is only 1 zero value and only one 'nan' value, together with positive and negative 'inf' values.

When converting from a Python float (which will typically be stored in 64-bits) unrepresented values are rounded to nearest, with ties-to-even.
This is the standard method used in IEEE 754.


Microscaling Formats
^^^^^^^^^^^^^^^^^^^^

.. note::
    This is an experimental feature and may be modified in future point releases.

A range of formats from the Microscaling Formats (MX) Alliance are supported. These are part of the Open Compute Project, and will usually have an external scale factor associated with them.

Eight-bit floats similar to the IEEE `p3binary8` and `p4binary8`  are available, though these seem rather arbitrary and ugly in places in comparison to the IEEE definitions.
There is also a format to use for the scaling factor, an int-like format which is really a float, and some sensible six and four bit float formats.


.. list-table::
   :header-rows: 1

   * - Type
     - # bits
     - +ive Range
     - bitstring format

   * - E5M2
     - 1 + 5 + 2
     - 10\ :sup:`-6` → 57344
     - ``'e5m2mxfp'``

   * - E4M3
     - 1 + 4 + 3
     - 2×10\ :sup:`-3` → 448
     - ``'e4m3mxfp'``

   * - E3M2
     - 1 + 3 + 2
     - 0.0625 → 28
     - ``'e3m2mxfp'``

   * - E2M3
     - 1 + 2 + 3
     - 0.125 → 7.5
     - ``'e2m3mxfp'``

   * - E2M1
     - 1 + 2 + 1
     - 0.5 → 6
     - ``'e2m1mxfp'``

   * - E8M0
     - 0 + 8 + 0
     - 10\ :sup:`-38` → 10\ :sup:`38`
     - ``'e8m0mxfp'``

   * - INT8
     - 8
     - 0.015625 → 1.984375
     - ``'mxint'``


* The E8M0 format is unsigned and designed to use as a scaling factor for blocks of the other formats.
* The INT8 format is like a signed two's complement 8-bit integer but with a scaling factor of 2\ :sup:`-6`. So despite its name it is actually a float. The standard doesn't specify whether the largest negative value (-2.0) is a supported number or not. This implementation allows it.
* The E4M3 format is similar to the `p4binary8` format but with a different exponent bias and it wastes some values. It has no 'inf' values, instead opting to have two 'nan' values and two zero values.
* The E5M2 format is similar to the `p3binary8` format but wastes even more values. It does have positive and negative 'inf' values, but also six 'nan' values and two zero values.

The MX formats are designed to work with an external scaling factor.
This should be in the E8M0 format, which uses a byte to encode the powers of two from 2\ :sup:`-127` to 2\ :sup:`127`, plus a 'nan' value.
This can be specified in bitstring as part of the `Dtype`, and is very useful inside an ``Array``. ::

        >>> d = b'some_byte_data'
        >>> a = Array(Dtype('e2m1mxfp', scale=2**10), d)
        >>> a.pp()
        <Array dtype='Dtype('e2m1mxfp', scale=2 ** 10)', length=28, itemsize=4 bits, total data size=14 bytes> [
          0:  6144.0  1536.0  4096.0 -6144.0  4096.0 -3072.0  4096.0  3072.0  3072.0 -6144.0  4096.0  1024.0  6144.0  -512.0
         14:  6144.0  2048.0  4096.0  3072.0  3072.0 -6144.0  4096.0  2048.0  4096.0   512.0  6144.0  2048.0  4096.0   512.0
        ]

To change the scale, replace the dtype in the `Array`::

        >>> a.dtype = Dtype('e2m1mxfp', scale=2**6)

When initialising an `Array` from a list of values, you can also use the string ``'auto'`` as the scale, and an appropriate scale will be calculated based on the data. ::

        >>> a = Array(Dtype('e2m1mxfp', scale='auto'), [0.0, 0.5, 40.5, 106.25, -52.0, -8.0])
        >>> a.pp()
        <Array dtype='Dtype('e2m1mxfp', scale=2 ** 4)', length=6, itemsize=4 bits, total data size=3 bytes> [
         0:     0.0     0.0    32.0    96.0   -48.0    -8.0
        ]

The scale is calculated based on the maximum absolute value of the data and the maximum representable value of the format.
The auto-scale feature is only available for 8-bit and smaller floating point formats, plus the IEEE 16-bit format.
If all of the data is zero, then the scale is set to 1.
For more details on this and these formats in general see the `OCP Microscaling formats specification. <https://www.opencompute.org/documents/ocp-microscaling-formats-mx-v1-0-spec-final-pdf>`_

Conversion
^^^^^^^^^^

When converting from a Python float to an any of the 8-or-fewer bit formats, the 'rounds to nearest, ties to even' rule is used.
This is the same as is used in the IEEE 754 standard.

Note that for efficiency reasons Python floats are converted to 16-bit IEEE floats before being converted to their final destination.
This can mean that in edge cases the rounding to the 16-bit float will cause the next rounding to go in the other direction.
The 16-bit float has 11 bits of precision, whereas the final format has at most 4 bits of precision, so this shouldn't be a real-world problem, but it could cause discrepancies when comparing with other methods.
I could add a slower, more accurate mode if this is a problem (add a bug report).

Values that are out of range after rounding are dealt with as follows:

- ``p3binary8`` - Out of range values are set to ``+inf`` or ``-inf``.
- ``p4binary8`` - Out of range values are set to ``+inf`` or ``-inf``.
- ``e5m2mxfp`` - Out of range values are dealt with according to the ``bitstring.options.mxfp_overflow`` setting:
    - ``'saturate'`` (the default): values are set to the largest positive or negative finite value, as appropriate. Infinities will also be set to the largest finite value, despite the fact that the format has infinities.
    - ``'overflow'``: Out of range values are set to ``+inf`` or ``-inf``.
- ``e4m3mxfp`` - Out of range values are dealt with according to the ``bitstring.options.mxfp_overflow`` setting:
    - ``'saturate'`` (the default): values are set to the largest positive or negative value, as appropriate.
    - ``'overflow'``: Out of range values are set to ``nan``.
- ``e3m2mxfp`` - Out of range values are saturated to the largest positive or negative value.
- ``e2m3mxfp`` - Out of range values are saturated to the largest positive or negative value.
- ``e2m1mxfp`` - Out of range values are saturated to the largest positive or negative value.
- ``mxint`` - Out of range values are saturated to the largest positive or negative value. Note that the most negative value in this case is ``-2.0``, which it is optional for an implementation to support.
- ``e8m0mxfp`` - No rounding is done. A ``ValueError`` will be raised if you try to convert a non-representable value. This is because the format is designed as a scaling factor, so it should generally be specified exactly.