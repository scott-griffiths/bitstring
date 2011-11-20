.. currentmodule:: bitstring

Slicing, Dicing and Splicing
============================

Manipulating binary data can be a bit of a challenge in Python. One of its strengths is that you don't have to worry about the low level data, but this can make life difficult when what you care about is precisely the thing that is safely hidden by high level abstractions.

In this section some more methods are described that treat data as a series of bits, rather than bytes.

Slicing
-------

Slicing takes three arguments: the first position you want, one past the last position you want and a multiplicative factor which defaults to 1. 

The third argument (the 'step') will be described shortly, but most of the time you'll probably just need the bit-wise slice, where for example ``a[10:12]`` will return a 2-bit bitstring of the 10th and 11th bits in ``a``, and ``a[32]`` will return just the 32nd bit. ::

 >>> a = BitArray('0b00011110')
 >>> b = a[3:7]
 >>> print(a, b)
 0x1e 0xf

For single bit indices (as opposed to slices) a boolean is returned; that is ``True`` for '1' bits and ``False`` for '0' bits::

    >>> a[0]
    False
    >>> a[4]
    True
    
If you want a single bit as a new bitstring then use a one-bit slice instead::

    >>> a[0:1]
    BitArray('0b0')

Indexing also works for missing and negative arguments, just as it does for other containers. ::

 >>> a = BitArray('0b00011110')
 >>> print(a[:5])         # first 5 bits
 0b00011            
 >>> print(a[3:])         # everything except first 3 bits
 0b11110
 >>> print(a[-4:])        # final 4 bits
 0xe
 >>> print(a[:-1])        # everything except last bit
 0b0001111
 >>> print(a[-6:-4])      # from 6 from the end to 4 from the end
 0b01

Stepping in slices
^^^^^^^^^^^^^^^^^^

The step parameter (also known as the stride) can be used in slices and has the same meaning as in the built-in containers:

    >>> s = BitArray(16)
    >>> s[::2] = [1]*8
    >>> s.bin
    '1010101010101010'
    >>> del s[8::2]
    >>> s.bin
    '101010100000'
    >>> s[::3].bin
    '1010'

Negative slices are also allowed, and should do what you'd expect. So for example ``s[::-1]`` returns a bit-reversed copy of ``s`` (which is similar to using ``s.reverse()``, which does the same operation on ``s`` in-place).

Joining
-------

To join together a couple of bitstring objects use the ``+`` or ``+=`` operators, or the :meth:`~BitArray.append` and :meth:`~BitArray.prepend` methods. ::

 # Six ways of creating the same BitArray:
 a1 = BitArray(bin='000') + BitArray(hex='f')
 a2 = BitArray('0b000') + BitArray('0xf')
 a3 = BitArray('0b000') + '0xf'
 a4 = BitArray('0b000')
 a4.append('0xf')
 a5 = BitArray('0xf')
 a5.prepend('0b000')
 a6 = BitArray('0b000')
 a6 += '0xf'

Note that the final three methods all modify a bitstring, and so will only work with :class:`BitArray` objects, not the immutable :class:`Bits` objects.

If you want to join a large number of bitstrings then the method :meth:`~Bits.join` can be used to improve efficiency and readability. It works like the ordinary string join function in that it uses the bitstring that it is called on as a separator when joining the list of bitstring objects it is given. If you don't want a separator then it can be called on an empty bitstring. ::

 bslist = [BitArray(uint=n, length=12) for n in xrange(1000)]
 s = BitArray('0b1111').join(bslist)

Truncating, inserting, deleting and overwriting
-----------------------------------------------

The functions in this section all modify the bitstring that they operate on and so are not available for :class:`Bits` objects.

Deleting and truncating
^^^^^^^^^^^^^^^^^^^^^^^

To delete bits just use ``del`` as you would with any other container::

 >>> a = BitArray('0b00011000')
 >>> del a[3:5]                # remove 2 bits at pos 3
 >>> a.bin
 ‘000000’
 >>> b = BitArray('0x112233445566')
 >>> del b[24:40]
 >>> b.hex
 '11223366'

You can of course use this to truncate the start or end bits just as easily::

 >>> a = BitArray('0x001122')
 >>> del a[-8:]   # remove last 8 bits
 >>> del a[:8]    # remove first 8 bits
 >>> a == '0x11'
 True


``insert``
^^^^^^^^^^

As you might expect, :meth:`~BitArray.insert` takes one :class:`BitArray` and inserts it into another. A bit position must be specified for :class:`BitArray` and :class:`Bits`, but for BitStreams if not present then the current :attr:`~ConstBitStream.pos` is used. ::

 >>> a = BitArray('0x00112233')
 >>> a.insert('0xffff', 16)
 >>> a.hex
 '0011ffff2233'

``overwrite``
^^^^^^^^^^^^^

:meth:`~BitArray.overwrite` does much the same as :meth:`~BitArray.insert`, but predictably the :class:`BitArray` object's data is overwritten by the new data. ::

 >>> a = BitStream('0x00112233')
 >>> a.pos = 4
 >>> a.overwrite('0b1111')         # Uses current pos as default
 >>> a.hex
 '0f112233'


The bitstring as a list
-----------------------

If you treat a bitstring object as a list whose elements are all either '1' or '0' then you won't go far wrong. The table below gives some of the equivalent ways of using methods and the standard slice notation.

===========================  ======================================
Using functions              Using slices
===========================  ======================================
``s.insert(bs, pos)``        ``s[pos:pos] = bs``
``s.overwrite(bs, pos)``     ``s[pos:pos + bs.len] = bs``
``s.append(bs)``             ``s[s.len:s.len] = bs``
``s.prepend(bs)``            ``s[0:0] = bs``
===========================  ======================================

Splitting
---------

``split``
^^^^^^^^^

Sometimes it can be very useful to use a delimiter to split a bitstring into sections. The :meth:`~Bits.split` method returns a generator for the sections. ::

 >>> a = BitArray('0x4700004711472222')
 >>> for s in a.split('0x47', bytealigned=True):
 ...     print(s.hex)
 
 470000
 4711
 472222

Note that the first item returned is always the bitstring before the first occurrence of the delimiter, even if it is empty.

``cut``
^^^^^^^

If you just want to split into equal parts then use the :meth:`~Bits.cut` method. This takes a number of bits as its first argument and returns a generator for chunks of that size. ::

 >>> a = BitArray('0x47001243')
 >>> for byte in a.cut(8):
 ...     print(byte.hex)
 47
 00
 12
 43
