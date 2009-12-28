
.. _exp-golomb:

Exponential-Golomb Codes
========================

As this type of representation of integers isn't as well known as the standard base-2 representation I thought that a short explanation of them might be welcome. This section can be safely skipped if you're not interested.

Exponential-Golomb codes represent integers using bit patterns that get longer for larger numbers. For unsigned and signed numbers (the bitstring properties :attr:`ue` and :attr:`se` respectively) the patterns start like this:

=============  ===========  ===========
Bit pattern    Unsigned     Signed 
=============  ===========  ===========
``1``          0            0
``010``        1            1
``011``        2            -1
``00100``      3            2
``00101``      4            -2
``00110``      5            3
``00111``      6            -3
``0001000``    7            4
``0001001``    8            -4
``0001010``    9            5
``0001011``    10           -5
``0001100``    11           6
``...``        ...          ...
=============  ===========  ===========

They consist of a sequence of n '0' bits, followed by a '1' bit, followed by n more bits. The bits after the first '1' bit count upwards as ordinary base-2 binary numbers until they run out of space and an extra '0' bit needs to get included at the start.

The advantage of this method of representing integers over many other methods is that it can be quite efficient at representing small numbers without imposing a limit on the maximum number that can be represented.

Exercise: Using the table above decode this sequence of unsigned Exponential Golomb codes:

``001001101101101011000100100101``

The answer is that it decodes to 3, 0, 0, 2, 2, 1, 0, 0, 8, 4. Note how you don’t need to know how many bits are used for each code in advance - there’s only one way to decode it. To create this bitstring you could have written something like::

 a = BitString().join([BitString(ue=i) for i in [3,0,0,2,2,1,0,0,8,4]])

and to read it back::

 while a.pos != a.len:
     print(a.read('ue'))

The notation ``ue`` and ``se`` for the exponential-Golomb code properties comes from the H.264 video standard, which uses these types of code a lot. The particular way that the signed integers are represented might be peculiar to this standard as I haven't seen it elsewhere (and an obvious alternative is minus the one given here), but the unsigned mapping seems to be universal.