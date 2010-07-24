.. currentmodule:: bitstring

***********
Walkthrough
***********

A Brief Introduction
====================

The aim of the :mod:`bitstring` module is make dealing with binary data in Python as easy as possible. In this section I will take you through some of the features of the module to help you get started using it.

Only a few of the module's features will be covered in this walkthrough; the :ref:`manual` and :ref:`reference` provide a more thorough guide. The whole of this section can be safely skipped or skimmed over if you prefer to start with the manual. If however you'd like a gentler introduction then you might like to follow along the examples with a Python interpreter.

Prerequisites
-------------

* Python 2.6, 2.7 or 3.x. (If you're using Python 2.4 or 2.5 then you can use bitstring version 1.0, but that isn't covered here.)
* An installed bitstring module.
* A rudimentory knowledge of binary concepts.
* A little free time.

If you haven't yet downloaded and installed :mod:`bitstring` then please do so (it might be as easy as typing "``easy_install bitstring``" depending on your system). I'll be going through some examples using the interactive Python interpreter, so feel free to start up a Python session and follow along.

Getting started
---------------

::

    >>> from bitstring import Bits, BitString  
  
First things first, we're going to be typing 'bitstring' a lot, so importing directly saves us a lot of ``bitstring.BitString`` nonsense. The classes we have imported are :class:`Bits` which can be considered as an immutable container for our binary data and :class:`BitString` which is a mutable container. We'll mostly be using :class:`BitString`, as there are more things you can do if you're allowed to change the contents after creation but as we'll see there are some occasions when you really want the unchanging :class:`Bits`.

We can now create a couple of bitstrings::

    >>> a = BitString('0xff01')
    >>> b = BitString('0b110')
 
The first of these we made from the hexadecimal string ``0xff01`` - the ``0x`` prefix makes it hexadecimal just as ``0b`` means binary and ``0o`` means octal. Each hex digit represents four bits, so we have a bitstring of length 16 bits.

The second was created from a binary string. In this case it is just three bits long. Don't worry about it not being a whole number of bytes long, that's all been taken care of internally.

.. note::

 Be sure to remember the quotes around the hex and binary strings. If you forget them you would just have an ordinary Python integer, which would instead create a bitstring of that many '0' bits. For example ``0xff01`` is the same as the base-10 number 65281, so ``BitString(0xff01)`` would consist of 65281 zero bits! 

There are lots of things we can do with our new bitstrings, the simplest of which is just to print them::

    >>> print(a)
    0xff01
    >>> print(b)
    0b110
 
Now you would be forgiven for thinking that the strings that we used to create the two bitstrings had just been stored to be given back when printed, but that's not the case. Every bitstring should be considered just as a sequence of bits. As we'll see there are lots of ways to create and manipulate them, but they have no memory of how they were created. When they are printed they just pick the simplest hex or binary representation of themselves. If you prefer you can pick the representation that you want::

    >>> a.bin
    '0b1111111100000001'
    >>> b.oct
    '0o6'
    >>> b.int
    -2
    >>> a.bytes
    '\xff\x01'
 
There are a few things to note here:

* To get the different interpretations of the binary data we use properties such as :attr:`~Bits.bin`, :attr:`~Bits.hex`, :attr:`~Bits.oct`, :attr:`~Bits.int` and :attr:`~Bits.bytes`. You can probably guess what these all mean, but you don't need to know quite yet. The properties are calculated when you ask for them rather than being stored as part of the object itself.
* The :attr:`~Bits.bytes` property returns a ``bytes`` object. This is slightly different in Python 2 to Python 3 - in Python 3 you would get ``b'\xff\x01'`` returned instead.

Great - let's try some more::

    >>> b.hex
    bitstring.InterpretError: Cannot convert to hex unambiguously - not multiple of 4 bits.
 
Oh dear. The problem we have here is that ``b`` is 3 bits long, whereas each hex digit represents 4 bits. This means that there is no unambiguous way to represent it in hexadecimal. There are similar restrictions on other interpretations (octal must be a mulitple of 3 bits, bytes a multiple of 8 bits etc.)

An exception is raised rather than trying to guess the best hex representation as there are a multitude of ways to convert to hex. I occasionally get asked why it doesn't just do the 'obvious' conversion, which is invariably what that person expects from his own field of work. This could be truncating bits at the start or end, or padding at the start or end with either zeros or ones. Rather than try to guess what is meant we just raise an exception - if you want a particular behaviour then write it explicitly::

   >>> (b + [0]).hex
   '0xc'
   >>> ([0] + b).hex
   '0x6'

Here we've added a zero bit first to the end and then to the start. Don't worry too much about how it all works, but just to give you a taster the zero bit ``[0]`` could also have been written as ``Bits([0])``, ``BitString([0])``, ``Bits('0b0')``, ``Bits(bin='0')``, ``'0b0'`` or just ``1`` (this final method isn't a typo, it means construct a bitstring of length one, with all the bits initialised to zero - it does look a bit confusing though which is why I prefer [0] and [1] to represent single bits). Take a look at :ref:`auto_init` for more details.

Modifying bitstrings
--------------------

A :class:`BitString` can be treated just like a list of bits. You can slice it, delete sections, insert new bits and more using standard index notation::

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

To join together bitstrings you can use a variety of methods, including :meth:`~BitString.append`, :meth:`~BitString.prepend`, :meth:`~BitString.insert`, and plain :meth:`+<Bits.__add__>` or :meth:`+=<BitString.__iadd__>` operations::

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

    >>> a = Bits('0xa9f')
    >>> a.find('0x4f')
    (3,)
    
Here we have found the ``0x4f`` byte in our bitstring, though it wasn't obvious from the hexadecimal as it was at bit position 3. To see this clearer consider this equality::

    >>> a == '0b101, 0x4f, 0b1'
    True
    
in which we've broken the bitstring into three parts to show the found byte. This also illustrates using commas to join bitstring sections.

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

    from bitstring import BitString
    # create a BitString with a million zero bits.
    # The bits will be set to indicate that the bit position isn't prime.
    has_factors = BitString(1000000)
    for i in xrange(2, 1000000):
        if not has_factors[i]:
            print(i)
            # Set all multiples of our prime to 1.
            has_factors.set(True, xrange(i*2, 1000000, i))

I'll leave optimising the algorithm as an exercise for the reader, but it illustrates both bit checking and setting. One reason you might want to use a bitstring for this purpose (instead of a plain list for example) is that the million bits only take up a million bits in memory, whereas for a list of integers it would be much more. Try asking for a billion elements in a list - unless you've got some really nice hardware it will fail, whereas a billion element bitstring only takes 125MB.


