.. currentmodule:: bitstring

.. _walkthrough:

***********
Walkthrough
***********

A Brief Introduction
====================

The aim of the :mod:`bitstring` module is make dealing with binary data in Python as easy as possible. In this section I will take you through some of the features of the module to help you get started using it.

Only a few of the module's features will be covered in this walkthrough; the :ref:`manual` and :ref:`reference` provide a more thorough guide. The whole of this section can be safely skipped or skimmed over if you prefer to start with the manual. If however you'd like a gentler introduction then you might like to follow along the examples with a Python interpreter.

Prerequisites
-------------

* Python 2.7 or 3.x.
* An installed bitstring module.
* A rudimentary knowledge of binary concepts.
* A little free time.

If you haven't yet downloaded and installed :mod:`bitstring` then please do so (it should be as easy as typing "``pip install bitstring``"). I'll be going through some examples using the interactive Python interpreter, so feel free to start up a Python session and follow along.

Getting started
---------------

::

    >>> from bitstring import BitArray, BitStream  
  
First things first, we're going to be typing 'bitstring' a lot, so importing directly saves us a lot of ``bitstring.BitStream`` nonsense. The classes we have imported are :class:`BitArray` which is just a container for our binary data and :class:`BitStream` which adds a bit position and reading methods to treat the data as a stream. There are also immutable versions of both these classes that we won't be using here.

We can now create a couple of bitstrings::

    >>> a = BitArray('0xff01')
    >>> b = BitArray('0b110')
 
The first of these we made from the hexadecimal string ``0xff01`` - the ``0x`` prefix makes it hexadecimal just as ``0b`` means binary and ``0o`` means octal. Each hex digit represents four bits, so we have a bitstring of length 16 bits.

The second was created from a binary string. In this case it is just three bits long. Don't worry about it not being a whole number of bytes long, that's all been taken care of internally.

.. note::

 Be sure to remember the quotes around the hex and binary strings. If you forget them you would just have an ordinary Python integer, which would instead create a bitstring of that many '0' bits. For example ``0xff01`` is the same as the base-10 number 65281, so ``BitArray(0xff01)`` would consist of 65281 zero bits! 

There are lots of things we can do with our new bitstrings, the simplest of which is just to print them::

    >>> print(a)
    0xff01
    >>> print(b)
    0b110
 
Now you would be forgiven for thinking that the strings that we used to create the two bitstrings had just been stored to be given back when printed, but that's not the case. Every bitstring should be considered just as a sequence of bits. As we'll see there are lots of ways to create and manipulate them, but they have no memory of how they were created. When they are printed they just pick the simplest hex or binary representation of themselves. If you prefer you can pick the representation that you want::

    >>> a.bin
    '1111111100000001'
    >>> b.oct
    '6'
    >>> b.int
    -2
    >>> a.bytes
    '\xff\x01'
 
There are a few things to note here:

* To get the different interpretations of the binary data we use properties such as :attr:`~Bits.bin`, :attr:`~Bits.hex`, :attr:`~Bits.oct`, :attr:`~Bits.int` and :attr:`~Bits.bytes`. You can probably guess what these all mean, but you don't need to know quite yet. The properties are calculated when you ask for them rather than being stored as part of the object itself.
* The :attr:`~Bits.bytes` property returns a ``bytes`` object. This is slightly different in Python 2.7 to Python 3 - in Python 3 you would get ``b'\xff\x01'`` returned instead.

Great - let's try some more::

    >>> b.hex
    bitstring.InterpretError: Cannot convert to hex unambiguously - not multiple of 4 bits.
 
Oh dear. The problem we have here is that ``b`` is 3 bits long, whereas each hex digit represents 4 bits. This means that there is no unambiguous way to represent it in hexadecimal. There are similar restrictions on other interpretations (octal must be a multiple of 3 bits, bytes a multiple of 8 bits etc.)

An exception is raised rather than trying to guess the best hex representation as there are a multitude of ways to convert to hex. I occasionally get asked why it doesn't just do the 'obvious' conversion, which is invariably what that person expects from his own field of work. This could be truncating bits at the start or end, or padding at the start or end with either zeros or ones. Rather than try to guess what is meant we just raise an exception - if you want a particular behaviour then write it explicitly::

   >>> (b + [0]).hex
   'c'
   >>> ([0] + b).hex
   '6'

Here we've added a zero bit first to the end and then to the start. Don't worry too much about how it all works, but just to give you a taster the zero bit ``[0]`` could also have been written as ``BitArray([0])``, ``BitArray([0])``, ``BitArray('0b0')``, ``BitArray(bin='0')``, ``'0b0'`` or just ``1`` (this final method isn't a typo, it means construct a bitstring of length one, with all the bits initialised to zero - it does look a bit confusing though which is why I prefer [0] and [1] to represent single bits). Take a look at :ref:`auto_init` for more details.

Modifying bitstrings
--------------------

A :class:`BitArray` can be treated just like a list of bits. You can slice it, delete sections, insert new bits and more using standard index notation::

    >>> print(a[3:9])
    0b111110
    >>> del a[-6:]
    >>> print(a)
    0b1111111100

The slicing works just as it does for other containers, so the deletion above removes the final six bits.

If you ask for a single item, rather than a slice, a boolean is returned. Naturally enough ``1`` bits are ``True`` whereas ``0`` bits are ``False``. ::

    >>> a[0]
    True
    >>> a[-1]
    False

To join together bitstrings you can use a variety of methods, including :meth:`~BitArray.append`, :meth:`~BitArray.prepend`, :meth:`~BitArray.insert`, and plain :meth:`+<Bits.__add__>` or :meth:`+=<BitArray.__iadd__>` operations::

    >>> a.prepend('0b01')
    >>> a.append('0o7')
    >>> a += '0x06'
 
Here we first put two bits at the start of ``a``, then three bits on the end (a single octal digit) and finally another byte (two hex digits) on the end.

Note how we are just using ordinary strings to specify the new bitstrings we are adding. These get converted automatically to the right sequence of bits.

.. note::

 The length in bits of bitstrings specified with strings depends on the number of characters, including leading zeros. So each hex character is four bits, each octal character three bits and each binary character one bit.

Finding and Replacing
---------------------

A :meth:`~Bits.find` is provided to search for bit patterns within a bitstring. You can choose whether to search only on byte boundaries or at any bit position::

    >>> a = BitArray('0xa9f')
    >>> a.find('0x4f')
    (3,)
    
Here we have found the ``0x4f`` byte in our bitstring, though it wasn't obvious from the hexadecimal as it was at bit position 3. To see this clearer consider this equality::

    >>> a == '0b101, 0x4f, 0b1'
    True
    
in which we've broken the bitstring into three parts to show the found byte. This also illustrates using commas to join bitstring sections.


Constructing a bitstring
------------------------

Let's say you have a specification for a binary file type (or maybe a packet specification etc.) and you want to create a bitstring quickly and easily in Python. For this example I'm going to use a header from the MPEG-2 video standard. Here's how the header is described in the standard:

==================================== =============== ============
sequence_header()                    No. of bits     Mnemonic
==================================== =============== ============
sequence_header_code                 32              bslbf
horizontal_size_value                12              uimsbf
vertical_size_value                  12              uimsbf
aspect_ratio_information             4               uimsbf
frame_rate_code                      4               uimsbf
bit_rate_value                       18              uimsbf
marker_bit                           1               bslbf
vbv_buffer_size_value                10              uimsbf
constrained_parameters_flag          1               bslbf
load_intra_quantiser_matrix          1               uimsbf
if (load_intra_quantiser_matrix)
{ intra_quantiser_matrix[64] }       8*64            uimsbf
load_non_intra_quantiser_matrix      1               uimsbf
if (load_non_intra_quantiser_matrix)
{ non_intra_quantiser_matrix[64] }   8*64            uimsbf
next_start_code()
==================================== =============== ============

The mnemonics mean things like uimsbf = 'Unsigned integer, most significant bit first'.

So to create a sequence_header for your particular stream with width of 352 and height of 288 you could start like this::

    s = BitArray()
    s.append('0x000001b3')  # the sequence_header_code
    s.append('uint:12=352') # 12 bit unsigned integer
    s.append('uint:12=288')
    ...

which is fine, but if you wanted to be a bit more concise you could just write ::

    s = BitArray('0x000001b3, uint:12=352, uint:12=288')

This is better, but it might not be a good idea to have the width and height hard-wired in like that. We can make it more flexible by using a format string and the :func:`pack` function::

    width, height = 352, 288
    s = bitstring.pack('0x000001b3, 2*uint:12', width, height)

where we have also used ``2*uint:12`` as shorthand for ``uint:12, uint:12``.

The :func:`pack` function can also take a dictionary as a parameter which can replace the tokens in the format string. For example::

    fmt = 'sequence_header_code,
           uint:12=horizontal_size_value,
           uint:12=vertical_size_value,
           uint:4=aspect_ratio_information,
           ...
           '
    d = {'sequence_header_code': '0x000001b3',
         'horizontal_size_value': 352,
         'vertical_size_value': 288,
         'aspect_ratio_information': 1,
         ...
        }

    s = bitstring.pack(fmt, **d)
    
Parsing bitstreams
------------------

You might have noticed that :func:`pack` returned a :class:`BitStream` rather than a :class:`BitArray`. This isn't a problem as the :class:`BitStream` class just adds a few stream-like qualities to :class:`BitArray` which we'll take a quick look at here.

First, let's look at the stream we've just created::

    >>> s
    BitStream('0x000001b31601201')

The stream-ness of this object is via its bit position, and various reading and peeking methods. First let's try a read or two, and see how this affects the bit position::

    >>> s.pos
    0
    >>> s.read(24)
    BitStream('0x000001')
    >>> s.pos
    24
    >>> s.read('hex:8')
    'b3'
    >>> s.pos
    32

First we read 24 bits, which returned a new :class:`BitStream` object, then we used a format string to read 8 bits interpreted as a hexadecimal string. We know that the next two sets of 12 bits were created from integers, so to read them back we can say

    >>> s.readlist('2*uint:12')
    [352, 288]

If you don't want to use a bitstream then you can always use :meth:`~Bits.unpack`. This takes much the same form as :meth:`~ConstBitStream.readlist` except it just unpacks from the start of the bitstring. For example::

    >>> s.unpack('bytes:4, 2*uint:12, uint:4')
    ['\x00\x00\x01\xb3', 352, 288, 1]

Worked examples
===============

Below are a few examples of using the bitstring module, as I always find that a good example can help more than a lengthy reference manual.

Hamming distance
----------------

The Hamming distance between two bitstrings is the number of bit positions in which the two bitstrings differ. So for example the distance between 0b00110 and 0b01100 is 2 as the second and fourth bits are different.

Write a function that calculates the Hamming weight of two bitstrings. ::

    def hamming_weight(a, b):
        return (a^b).count(True)

Er, that's it. The :meth:`^<Bits.__xor__>` is a bit-wise exclusive or, which means that the bits in ``a^b`` are only set if they differ in ``a`` and ``b``. The :meth:`~Bits.count` method just counts the number of 1 (or True) bits. ::

    >>> a = Bits('0b00110')
    >>> hamming_weight(a, '0b01100')
    2


Sieve of Eratosthenes
---------------------

The sieve of Eratosthenes is an ancient (and very inefficient) method of finding prime numbers. The algorithm starts with the number 2 (which is prime) and marks all of its multiples as not prime, it then continues with the next unmarked integer (which will also be prime) and marks all of its multiples as not prime.

So to print all primes under a million you could write::

    from bitstring import BitArray
    # create a BitArray with a million zero bits.
    # The bits will be set to indicate that the bit position isn't prime.
    has_factors = BitArray(1000000)
    for i in xrange(2, 1000000):
        if not has_factors[i]:
            print(i)
            # Set all multiples of our prime to 1.
            has_factors.set(True, xrange(i*2, 1000000, i))

I'll leave optimising the algorithm as an exercise for the reader, but it illustrates both bit checking and setting. One reason you might want to use a bitstring for this purpose (instead of a plain list for example) is that the million bits only take up a million bits in memory, whereas for a list of integers it would be much more. Try asking for a billion elements in a list - unless you've got some really nice hardware it will fail, whereas a billion element bitstring only takes 125MB.
