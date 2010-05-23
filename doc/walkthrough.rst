***********
Walkthrough
***********

.. note::

This section is incomplete. I plan to complete it for the 2.0.0 final release.

A Brief Introduction
====================

The aim of the :mod:`bitstring` module is make dealing with binary data in Python as easy as possible. In this section I will take you through some of the features of the module to help you get started using it.

Only a few of the module's features will be covered in this walkthrough; the :ref:`manual` and :ref:`reference` provide a more thorough guide. The whole of this section can be safely skipped or skimmed over if you prefer to start with the manual. If however you'd like a gentler introduction then you might like to follow along the examples with a Python interpreter.

Prerequisites
-------------

* Python 2.4 or later. Preferably 2.6 or 3.1.
* An installed bitstring module.
* A rudimentory knowledge of binary concepts.
* A little free time.

If you haven't yet downloaded and installed :mod:`bitstring` then please do so (it might be as easy as typing "``easy_install bitstring``" depending on your system). I'll be going through some examples using the interactive Python interpreter, so feel free to start up a Python session and follow along.

Getting started
---------------

::

 >>> from bitstring import Bits, BitString  
  
First things first, we're going to be typing 'bitstring' a lot, so importing directly saves us a lot of ``bitstring.BitString`` nonsense. We can now create a couple of bitstrings::

 >>> a = BitString('0xff01')
 >>> b = BitString('0b110')
 
The first of these we made from the hexadecimal string '0xff01' - the ``0x`` prefix makes it hexadecimal just as ``0b`` means binary and ``0o`` means octal. Each hex digit represents four bits, so we have a bitstring of length 16 bits.

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

* To get the different interpretations of the binary data we use properties such as ``bin``, ``hex``, ``oct``, ``int`` and ``bytes``. You can probably guess what these all mean, but you don't need to know quite yet. The properties are calculated when you ask for them rather than being stored as part of the object itself.
* The ``bytes`` property returns a ``bytes`` object. This is slightly different in Python 2 to Python 3 - in Python 3 you would get ``b'\xff\x01'`` returned instead.

Great - let's try some more::

 >>> b.hex
 ValueError: Cannot convert to hex unambiguously - not multiple of 4 bits.
 
Oh dear. The problem we have here is that ``b`` is 3 bits long, whereas each hex digit represents 4 bits. This means that there is no unambiguous way to represent it in hexadecimal. There are other similar restrictions on other interpretations (octal must be mulitple of 3 bits, bytes a multiple of  8 bits etc.)

Modifying bitstrings
--------------------

A :class:`BitString` can be treated just like a list of bits. You can slice it, delete sections, insert new bits and more using standard index notation::

 >>> print(a[3:9])
 0b111110
 >>> del a[-6:]
 >>> print(a)
 0b1111111100

The slicing works just as it does for other containers, so the deletion above removes the final six bits.

To join together bitstrings you can use a variety of methods, including :meth:`BitString.append`, :meth:`BitString.prepend`, :meth:`BitString.insert`, and plain ``+`` or ``+=`` operations::

 >>> a.prepend('0b01')
 >>> a.append('0o7')
 >>> a += '0x06'
 
Here we first put two bits at the start of ``a``, then three bits on the end (a single octal digit) and finally another byte (two hex digits) on the end.

Note how we are just using ordinary strings to specify the new bitstrings we are adding. These get converted automatically to the right sequence of bits.

.. note::

 The length in bits of bitstrings specified with strings depends on the number of characters, including leading zeros. So each hex character is four bits, each octal character three bits and each binary character one bit.






